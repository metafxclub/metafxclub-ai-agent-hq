var e1=Object.defineProperty;var t1=(r,e,i)=>e in r?e1(r,e,{enumerable:!0,configurable:!0,writable:!0,value:i}):r[e]=i;var Ox=(r,e,i)=>t1(r,typeof e!="symbol"?e+"":e,i);var $d={exports:{}},Rl={};/**
 * @license React
 * react-jsx-runtime.production.js
 *
 * Copyright (c) Meta Platforms, Inc. and affiliates.
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 */var Px;function n1(){if(Px)return Rl;Px=1;var r=Symbol.for("react.transitional.element"),e=Symbol.for("react.fragment");function i(s,l,c){var f=null;if(c!==void 0&&(f=""+c),l.key!==void 0&&(f=""+l.key),"key"in l){c={};for(var h in l)h!=="key"&&(c[h]=l[h])}else c=l;return l=c.ref,{$$typeof:r,type:s,key:f,ref:l!==void 0?l:null,props:c}}return Rl.Fragment=e,Rl.jsx=i,Rl.jsxs=i,Rl}var zx;function i1(){return zx||(zx=1,$d.exports=n1()),$d.exports}var U=i1(),eh={exports:{}},yt={};/**
 * @license React
 * react.production.js
 *
 * Copyright (c) Meta Platforms, Inc. and affiliates.
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 */var Fx;function a1(){if(Fx)return yt;Fx=1;var r=Symbol.for("react.transitional.element"),e=Symbol.for("react.portal"),i=Symbol.for("react.fragment"),s=Symbol.for("react.strict_mode"),l=Symbol.for("react.profiler"),c=Symbol.for("react.consumer"),f=Symbol.for("react.context"),h=Symbol.for("react.forward_ref"),m=Symbol.for("react.suspense"),p=Symbol.for("react.memo"),g=Symbol.for("react.lazy"),v=Symbol.for("react.activity"),x=Symbol.iterator;function _(D){return D===null||typeof D!="object"?null:(D=x&&D[x]||D["@@iterator"],typeof D=="function"?D:null)}var E={isMounted:function(){return!1},enqueueForceUpdate:function(){},enqueueReplaceState:function(){},enqueueSetState:function(){}},R=Object.assign,b={};function S(D,se,_e){this.props=D,this.context=se,this.refs=b,this.updater=_e||E}S.prototype.isReactComponent={},S.prototype.setState=function(D,se){if(typeof D!="object"&&typeof D!="function"&&D!=null)throw Error("takes an object of state variables to update or a function which returns an object of state variables.");this.updater.enqueueSetState(this,D,se,"setState")},S.prototype.forceUpdate=function(D){this.updater.enqueueForceUpdate(this,D,"forceUpdate")};function F(){}F.prototype=S.prototype;function G(D,se,_e){this.props=D,this.context=se,this.refs=b,this.updater=_e||E}var w=G.prototype=new F;w.constructor=G,R(w,S.prototype),w.isPureReactComponent=!0;var N=Array.isArray;function L(){}var z={H:null,A:null,T:null,S:null},T=Object.prototype.hasOwnProperty;function O(D,se,_e){var De=_e.ref;return{$$typeof:r,type:D,key:se,ref:De!==void 0?De:null,props:_e}}function I(D,se){return O(D.type,se,D.props)}function W(D){return typeof D=="object"&&D!==null&&D.$$typeof===r}function J(D){var se={"=":"=0",":":"=2"};return"$"+D.replace(/[=:]/g,function(_e){return se[_e]})}var re=/\/+/g;function k(D,se){return typeof D=="object"&&D!==null&&D.key!=null?J(""+D.key):se.toString(36)}function K(D){switch(D.status){case"fulfilled":return D.value;case"rejected":throw D.reason;default:switch(typeof D.status=="string"?D.then(L,L):(D.status="pending",D.then(function(se){D.status==="pending"&&(D.status="fulfilled",D.value=se)},function(se){D.status==="pending"&&(D.status="rejected",D.reason=se)})),D.status){case"fulfilled":return D.value;case"rejected":throw D.reason}}throw D}function B(D,se,_e,De,ze){var Xe=typeof D;(Xe==="undefined"||Xe==="boolean")&&(D=null);var ue=!1;if(D===null)ue=!0;else switch(Xe){case"bigint":case"string":case"number":ue=!0;break;case"object":switch(D.$$typeof){case r:case e:ue=!0;break;case g:return ue=D._init,B(ue(D._payload),se,_e,De,ze)}}if(ue)return ze=ze(D),ue=De===""?"."+k(D,0):De,N(ze)?(_e="",ue!=null&&(_e=ue.replace(re,"$&/")+"/"),B(ze,se,_e,"",function(at){return at})):ze!=null&&(W(ze)&&(ze=I(ze,_e+(ze.key==null||D&&D.key===ze.key?"":(""+ze.key).replace(re,"$&/")+"/")+ue)),se.push(ze)),1;ue=0;var Se=De===""?".":De+":";if(N(D))for(var Re=0;Re<D.length;Re++)De=D[Re],Xe=Se+k(De,Re),ue+=B(De,se,_e,Xe,ze);else if(Re=_(D),typeof Re=="function")for(D=Re.call(D),Re=0;!(De=D.next()).done;)De=De.value,Xe=Se+k(De,Re++),ue+=B(De,se,_e,Xe,ze);else if(Xe==="object"){if(typeof D.then=="function")return B(K(D),se,_e,De,ze);throw se=String(D),Error("Objects are not valid as a React child (found: "+(se==="[object Object]"?"object with keys {"+Object.keys(D).join(", ")+"}":se)+"). If you meant to render a collection of children, use an array instead.")}return ue}function V(D,se,_e){if(D==null)return D;var De=[],ze=0;return B(D,De,"","",function(Xe){return se.call(_e,Xe,ze++)}),De}function ee(D){if(D._status===-1){var se=D._result;se=se(),se.then(function(_e){(D._status===0||D._status===-1)&&(D._status=1,D._result=_e)},function(_e){(D._status===0||D._status===-1)&&(D._status=2,D._result=_e)}),D._status===-1&&(D._status=0,D._result=se)}if(D._status===1)return D._result.default;throw D._result}var oe=typeof reportError=="function"?reportError:function(D){if(typeof window=="object"&&typeof window.ErrorEvent=="function"){var se=new window.ErrorEvent("error",{bubbles:!0,cancelable:!0,message:typeof D=="object"&&D!==null&&typeof D.message=="string"?String(D.message):String(D),error:D});if(!window.dispatchEvent(se))return}else if(typeof process=="object"&&typeof process.emit=="function"){process.emit("uncaughtException",D);return}console.error(D)},fe={map:V,forEach:function(D,se,_e){V(D,function(){se.apply(this,arguments)},_e)},count:function(D){var se=0;return V(D,function(){se++}),se},toArray:function(D){return V(D,function(se){return se})||[]},only:function(D){if(!W(D))throw Error("React.Children.only expected to receive a single React element child.");return D}};return yt.Activity=v,yt.Children=fe,yt.Component=S,yt.Fragment=i,yt.Profiler=l,yt.PureComponent=G,yt.StrictMode=s,yt.Suspense=m,yt.__CLIENT_INTERNALS_DO_NOT_USE_OR_WARN_USERS_THEY_CANNOT_UPGRADE=z,yt.__COMPILER_RUNTIME={__proto__:null,c:function(D){return z.H.useMemoCache(D)}},yt.cache=function(D){return function(){return D.apply(null,arguments)}},yt.cacheSignal=function(){return null},yt.cloneElement=function(D,se,_e){if(D==null)throw Error("The argument must be a React element, but you passed "+D+".");var De=R({},D.props),ze=D.key;if(se!=null)for(Xe in se.key!==void 0&&(ze=""+se.key),se)!T.call(se,Xe)||Xe==="key"||Xe==="__self"||Xe==="__source"||Xe==="ref"&&se.ref===void 0||(De[Xe]=se[Xe]);var Xe=arguments.length-2;if(Xe===1)De.children=_e;else if(1<Xe){for(var ue=Array(Xe),Se=0;Se<Xe;Se++)ue[Se]=arguments[Se+2];De.children=ue}return O(D.type,ze,De)},yt.createContext=function(D){return D={$$typeof:f,_currentValue:D,_currentValue2:D,_threadCount:0,Provider:null,Consumer:null},D.Provider=D,D.Consumer={$$typeof:c,_context:D},D},yt.createElement=function(D,se,_e){var De,ze={},Xe=null;if(se!=null)for(De in se.key!==void 0&&(Xe=""+se.key),se)T.call(se,De)&&De!=="key"&&De!=="__self"&&De!=="__source"&&(ze[De]=se[De]);var ue=arguments.length-2;if(ue===1)ze.children=_e;else if(1<ue){for(var Se=Array(ue),Re=0;Re<ue;Re++)Se[Re]=arguments[Re+2];ze.children=Se}if(D&&D.defaultProps)for(De in ue=D.defaultProps,ue)ze[De]===void 0&&(ze[De]=ue[De]);return O(D,Xe,ze)},yt.createRef=function(){return{current:null}},yt.forwardRef=function(D){return{$$typeof:h,render:D}},yt.isValidElement=W,yt.lazy=function(D){return{$$typeof:g,_payload:{_status:-1,_result:D},_init:ee}},yt.memo=function(D,se){return{$$typeof:p,type:D,compare:se===void 0?null:se}},yt.startTransition=function(D){var se=z.T,_e={};z.T=_e;try{var De=D(),ze=z.S;ze!==null&&ze(_e,De),typeof De=="object"&&De!==null&&typeof De.then=="function"&&De.then(L,oe)}catch(Xe){oe(Xe)}finally{se!==null&&_e.types!==null&&(se.types=_e.types),z.T=se}},yt.unstable_useCacheRefresh=function(){return z.H.useCacheRefresh()},yt.use=function(D){return z.H.use(D)},yt.useActionState=function(D,se,_e){return z.H.useActionState(D,se,_e)},yt.useCallback=function(D,se){return z.H.useCallback(D,se)},yt.useContext=function(D){return z.H.useContext(D)},yt.useDebugValue=function(){},yt.useDeferredValue=function(D,se){return z.H.useDeferredValue(D,se)},yt.useEffect=function(D,se){return z.H.useEffect(D,se)},yt.useEffectEvent=function(D){return z.H.useEffectEvent(D)},yt.useId=function(){return z.H.useId()},yt.useImperativeHandle=function(D,se,_e){return z.H.useImperativeHandle(D,se,_e)},yt.useInsertionEffect=function(D,se){return z.H.useInsertionEffect(D,se)},yt.useLayoutEffect=function(D,se){return z.H.useLayoutEffect(D,se)},yt.useMemo=function(D,se){return z.H.useMemo(D,se)},yt.useOptimistic=function(D,se){return z.H.useOptimistic(D,se)},yt.useReducer=function(D,se,_e){return z.H.useReducer(D,se,_e)},yt.useRef=function(D){return z.H.useRef(D)},yt.useState=function(D){return z.H.useState(D)},yt.useSyncExternalStore=function(D,se,_e){return z.H.useSyncExternalStore(D,se,_e)},yt.useTransition=function(){return z.H.useTransition()},yt.version="19.2.0",yt}var Bx;function Pp(){return Bx||(Bx=1,eh.exports=a1()),eh.exports}var nt=Pp(),th={exports:{}},Ul={},nh={exports:{}},ih={};/**
 * @license React
 * scheduler.production.js
 *
 * Copyright (c) Meta Platforms, Inc. and affiliates.
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 */var Ix;function r1(){return Ix||(Ix=1,(function(r){function e(B,V){var ee=B.length;B.push(V);e:for(;0<ee;){var oe=ee-1>>>1,fe=B[oe];if(0<l(fe,V))B[oe]=V,B[ee]=fe,ee=oe;else break e}}function i(B){return B.length===0?null:B[0]}function s(B){if(B.length===0)return null;var V=B[0],ee=B.pop();if(ee!==V){B[0]=ee;e:for(var oe=0,fe=B.length,D=fe>>>1;oe<D;){var se=2*(oe+1)-1,_e=B[se],De=se+1,ze=B[De];if(0>l(_e,ee))De<fe&&0>l(ze,_e)?(B[oe]=ze,B[De]=ee,oe=De):(B[oe]=_e,B[se]=ee,oe=se);else if(De<fe&&0>l(ze,ee))B[oe]=ze,B[De]=ee,oe=De;else break e}}return V}function l(B,V){var ee=B.sortIndex-V.sortIndex;return ee!==0?ee:B.id-V.id}if(r.unstable_now=void 0,typeof performance=="object"&&typeof performance.now=="function"){var c=performance;r.unstable_now=function(){return c.now()}}else{var f=Date,h=f.now();r.unstable_now=function(){return f.now()-h}}var m=[],p=[],g=1,v=null,x=3,_=!1,E=!1,R=!1,b=!1,S=typeof setTimeout=="function"?setTimeout:null,F=typeof clearTimeout=="function"?clearTimeout:null,G=typeof setImmediate<"u"?setImmediate:null;function w(B){for(var V=i(p);V!==null;){if(V.callback===null)s(p);else if(V.startTime<=B)s(p),V.sortIndex=V.expirationTime,e(m,V);else break;V=i(p)}}function N(B){if(R=!1,w(B),!E)if(i(m)!==null)E=!0,L||(L=!0,J());else{var V=i(p);V!==null&&K(N,V.startTime-B)}}var L=!1,z=-1,T=5,O=-1;function I(){return b?!0:!(r.unstable_now()-O<T)}function W(){if(b=!1,L){var B=r.unstable_now();O=B;var V=!0;try{e:{E=!1,R&&(R=!1,F(z),z=-1),_=!0;var ee=x;try{t:{for(w(B),v=i(m);v!==null&&!(v.expirationTime>B&&I());){var oe=v.callback;if(typeof oe=="function"){v.callback=null,x=v.priorityLevel;var fe=oe(v.expirationTime<=B);if(B=r.unstable_now(),typeof fe=="function"){v.callback=fe,w(B),V=!0;break t}v===i(m)&&s(m),w(B)}else s(m);v=i(m)}if(v!==null)V=!0;else{var D=i(p);D!==null&&K(N,D.startTime-B),V=!1}}break e}finally{v=null,x=ee,_=!1}V=void 0}}finally{V?J():L=!1}}}var J;if(typeof G=="function")J=function(){G(W)};else if(typeof MessageChannel<"u"){var re=new MessageChannel,k=re.port2;re.port1.onmessage=W,J=function(){k.postMessage(null)}}else J=function(){S(W,0)};function K(B,V){z=S(function(){B(r.unstable_now())},V)}r.unstable_IdlePriority=5,r.unstable_ImmediatePriority=1,r.unstable_LowPriority=4,r.unstable_NormalPriority=3,r.unstable_Profiling=null,r.unstable_UserBlockingPriority=2,r.unstable_cancelCallback=function(B){B.callback=null},r.unstable_forceFrameRate=function(B){0>B||125<B?console.error("forceFrameRate takes a positive int between 0 and 125, forcing frame rates higher than 125 fps is not supported"):T=0<B?Math.floor(1e3/B):5},r.unstable_getCurrentPriorityLevel=function(){return x},r.unstable_next=function(B){switch(x){case 1:case 2:case 3:var V=3;break;default:V=x}var ee=x;x=V;try{return B()}finally{x=ee}},r.unstable_requestPaint=function(){b=!0},r.unstable_runWithPriority=function(B,V){switch(B){case 1:case 2:case 3:case 4:case 5:break;default:B=3}var ee=x;x=B;try{return V()}finally{x=ee}},r.unstable_scheduleCallback=function(B,V,ee){var oe=r.unstable_now();switch(typeof ee=="object"&&ee!==null?(ee=ee.delay,ee=typeof ee=="number"&&0<ee?oe+ee:oe):ee=oe,B){case 1:var fe=-1;break;case 2:fe=250;break;case 5:fe=1073741823;break;case 4:fe=1e4;break;default:fe=5e3}return fe=ee+fe,B={id:g++,callback:V,priorityLevel:B,startTime:ee,expirationTime:fe,sortIndex:-1},ee>oe?(B.sortIndex=ee,e(p,B),i(m)===null&&B===i(p)&&(R?(F(z),z=-1):R=!0,K(N,ee-oe))):(B.sortIndex=fe,e(m,B),E||_||(E=!0,L||(L=!0,J()))),B},r.unstable_shouldYield=I,r.unstable_wrapCallback=function(B){var V=x;return function(){var ee=x;x=V;try{return B.apply(this,arguments)}finally{x=ee}}}})(ih)),ih}var Hx;function s1(){return Hx||(Hx=1,nh.exports=r1()),nh.exports}var ah={exports:{}},fi={};/**
 * @license React
 * react-dom.production.js
 *
 * Copyright (c) Meta Platforms, Inc. and affiliates.
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 */var Gx;function o1(){if(Gx)return fi;Gx=1;var r=Pp();function e(m){var p="https://react.dev/errors/"+m;if(1<arguments.length){p+="?args[]="+encodeURIComponent(arguments[1]);for(var g=2;g<arguments.length;g++)p+="&args[]="+encodeURIComponent(arguments[g])}return"Minified React error #"+m+"; visit "+p+" for the full message or use the non-minified dev environment for full errors and additional helpful warnings."}function i(){}var s={d:{f:i,r:function(){throw Error(e(522))},D:i,C:i,L:i,m:i,X:i,S:i,M:i},p:0,findDOMNode:null},l=Symbol.for("react.portal");function c(m,p,g){var v=3<arguments.length&&arguments[3]!==void 0?arguments[3]:null;return{$$typeof:l,key:v==null?null:""+v,children:m,containerInfo:p,implementation:g}}var f=r.__CLIENT_INTERNALS_DO_NOT_USE_OR_WARN_USERS_THEY_CANNOT_UPGRADE;function h(m,p){if(m==="font")return"";if(typeof p=="string")return p==="use-credentials"?p:""}return fi.__DOM_INTERNALS_DO_NOT_USE_OR_WARN_USERS_THEY_CANNOT_UPGRADE=s,fi.createPortal=function(m,p){var g=2<arguments.length&&arguments[2]!==void 0?arguments[2]:null;if(!p||p.nodeType!==1&&p.nodeType!==9&&p.nodeType!==11)throw Error(e(299));return c(m,p,null,g)},fi.flushSync=function(m){var p=f.T,g=s.p;try{if(f.T=null,s.p=2,m)return m()}finally{f.T=p,s.p=g,s.d.f()}},fi.preconnect=function(m,p){typeof m=="string"&&(p?(p=p.crossOrigin,p=typeof p=="string"?p==="use-credentials"?p:"":void 0):p=null,s.d.C(m,p))},fi.prefetchDNS=function(m){typeof m=="string"&&s.d.D(m)},fi.preinit=function(m,p){if(typeof m=="string"&&p&&typeof p.as=="string"){var g=p.as,v=h(g,p.crossOrigin),x=typeof p.integrity=="string"?p.integrity:void 0,_=typeof p.fetchPriority=="string"?p.fetchPriority:void 0;g==="style"?s.d.S(m,typeof p.precedence=="string"?p.precedence:void 0,{crossOrigin:v,integrity:x,fetchPriority:_}):g==="script"&&s.d.X(m,{crossOrigin:v,integrity:x,fetchPriority:_,nonce:typeof p.nonce=="string"?p.nonce:void 0})}},fi.preinitModule=function(m,p){if(typeof m=="string")if(typeof p=="object"&&p!==null){if(p.as==null||p.as==="script"){var g=h(p.as,p.crossOrigin);s.d.M(m,{crossOrigin:g,integrity:typeof p.integrity=="string"?p.integrity:void 0,nonce:typeof p.nonce=="string"?p.nonce:void 0})}}else p==null&&s.d.M(m)},fi.preload=function(m,p){if(typeof m=="string"&&typeof p=="object"&&p!==null&&typeof p.as=="string"){var g=p.as,v=h(g,p.crossOrigin);s.d.L(m,g,{crossOrigin:v,integrity:typeof p.integrity=="string"?p.integrity:void 0,nonce:typeof p.nonce=="string"?p.nonce:void 0,type:typeof p.type=="string"?p.type:void 0,fetchPriority:typeof p.fetchPriority=="string"?p.fetchPriority:void 0,referrerPolicy:typeof p.referrerPolicy=="string"?p.referrerPolicy:void 0,imageSrcSet:typeof p.imageSrcSet=="string"?p.imageSrcSet:void 0,imageSizes:typeof p.imageSizes=="string"?p.imageSizes:void 0,media:typeof p.media=="string"?p.media:void 0})}},fi.preloadModule=function(m,p){if(typeof m=="string")if(p){var g=h(p.as,p.crossOrigin);s.d.m(m,{as:typeof p.as=="string"&&p.as!=="script"?p.as:void 0,crossOrigin:g,integrity:typeof p.integrity=="string"?p.integrity:void 0})}else s.d.m(m)},fi.requestFormReset=function(m){s.d.r(m)},fi.unstable_batchedUpdates=function(m,p){return m(p)},fi.useFormState=function(m,p,g){return f.H.useFormState(m,p,g)},fi.useFormStatus=function(){return f.H.useHostTransitionStatus()},fi.version="19.2.0",fi}var Vx;function l1(){if(Vx)return ah.exports;Vx=1;function r(){if(!(typeof __REACT_DEVTOOLS_GLOBAL_HOOK__>"u"||typeof __REACT_DEVTOOLS_GLOBAL_HOOK__.checkDCE!="function"))try{__REACT_DEVTOOLS_GLOBAL_HOOK__.checkDCE(r)}catch(e){console.error(e)}}return r(),ah.exports=o1(),ah.exports}/**
 * @license React
 * react-dom-client.production.js
 *
 * Copyright (c) Meta Platforms, Inc. and affiliates.
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 */var kx;function c1(){if(kx)return Ul;kx=1;var r=s1(),e=Pp(),i=l1();function s(t){var n="https://react.dev/errors/"+t;if(1<arguments.length){n+="?args[]="+encodeURIComponent(arguments[1]);for(var a=2;a<arguments.length;a++)n+="&args[]="+encodeURIComponent(arguments[a])}return"Minified React error #"+t+"; visit "+n+" for the full message or use the non-minified dev environment for full errors and additional helpful warnings."}function l(t){return!(!t||t.nodeType!==1&&t.nodeType!==9&&t.nodeType!==11)}function c(t){var n=t,a=t;if(t.alternate)for(;n.return;)n=n.return;else{t=n;do n=t,(n.flags&4098)!==0&&(a=n.return),t=n.return;while(t)}return n.tag===3?a:null}function f(t){if(t.tag===13){var n=t.memoizedState;if(n===null&&(t=t.alternate,t!==null&&(n=t.memoizedState)),n!==null)return n.dehydrated}return null}function h(t){if(t.tag===31){var n=t.memoizedState;if(n===null&&(t=t.alternate,t!==null&&(n=t.memoizedState)),n!==null)return n.dehydrated}return null}function m(t){if(c(t)!==t)throw Error(s(188))}function p(t){var n=t.alternate;if(!n){if(n=c(t),n===null)throw Error(s(188));return n!==t?null:t}for(var a=t,o=n;;){var u=a.return;if(u===null)break;var d=u.alternate;if(d===null){if(o=u.return,o!==null){a=o;continue}break}if(u.child===d.child){for(d=u.child;d;){if(d===a)return m(u),t;if(d===o)return m(u),n;d=d.sibling}throw Error(s(188))}if(a.return!==o.return)a=u,o=d;else{for(var y=!1,C=u.child;C;){if(C===a){y=!0,a=u,o=d;break}if(C===o){y=!0,o=u,a=d;break}C=C.sibling}if(!y){for(C=d.child;C;){if(C===a){y=!0,a=d,o=u;break}if(C===o){y=!0,o=d,a=u;break}C=C.sibling}if(!y)throw Error(s(189))}}if(a.alternate!==o)throw Error(s(190))}if(a.tag!==3)throw Error(s(188));return a.stateNode.current===a?t:n}function g(t){var n=t.tag;if(n===5||n===26||n===27||n===6)return t;for(t=t.child;t!==null;){if(n=g(t),n!==null)return n;t=t.sibling}return null}var v=Object.assign,x=Symbol.for("react.element"),_=Symbol.for("react.transitional.element"),E=Symbol.for("react.portal"),R=Symbol.for("react.fragment"),b=Symbol.for("react.strict_mode"),S=Symbol.for("react.profiler"),F=Symbol.for("react.consumer"),G=Symbol.for("react.context"),w=Symbol.for("react.forward_ref"),N=Symbol.for("react.suspense"),L=Symbol.for("react.suspense_list"),z=Symbol.for("react.memo"),T=Symbol.for("react.lazy"),O=Symbol.for("react.activity"),I=Symbol.for("react.memo_cache_sentinel"),W=Symbol.iterator;function J(t){return t===null||typeof t!="object"?null:(t=W&&t[W]||t["@@iterator"],typeof t=="function"?t:null)}var re=Symbol.for("react.client.reference");function k(t){if(t==null)return null;if(typeof t=="function")return t.$$typeof===re?null:t.displayName||t.name||null;if(typeof t=="string")return t;switch(t){case R:return"Fragment";case S:return"Profiler";case b:return"StrictMode";case N:return"Suspense";case L:return"SuspenseList";case O:return"Activity"}if(typeof t=="object")switch(t.$$typeof){case E:return"Portal";case G:return t.displayName||"Context";case F:return(t._context.displayName||"Context")+".Consumer";case w:var n=t.render;return t=t.displayName,t||(t=n.displayName||n.name||"",t=t!==""?"ForwardRef("+t+")":"ForwardRef"),t;case z:return n=t.displayName||null,n!==null?n:k(t.type)||"Memo";case T:n=t._payload,t=t._init;try{return k(t(n))}catch{}}return null}var K=Array.isArray,B=e.__CLIENT_INTERNALS_DO_NOT_USE_OR_WARN_USERS_THEY_CANNOT_UPGRADE,V=i.__DOM_INTERNALS_DO_NOT_USE_OR_WARN_USERS_THEY_CANNOT_UPGRADE,ee={pending:!1,data:null,method:null,action:null},oe=[],fe=-1;function D(t){return{current:t}}function se(t){0>fe||(t.current=oe[fe],oe[fe]=null,fe--)}function _e(t,n){fe++,oe[fe]=t.current,t.current=n}var De=D(null),ze=D(null),Xe=D(null),ue=D(null);function Se(t,n){switch(_e(Xe,n),_e(ze,t),_e(De,null),n.nodeType){case 9:case 11:t=(t=n.documentElement)&&(t=t.namespaceURI)?ix(t):0;break;default:if(t=n.tagName,n=n.namespaceURI)n=ix(n),t=ax(n,t);else switch(t){case"svg":t=1;break;case"math":t=2;break;default:t=0}}se(De),_e(De,t)}function Re(){se(De),se(ze),se(Xe)}function at(t){t.memoizedState!==null&&_e(ue,t);var n=De.current,a=ax(n,t.type);n!==a&&(_e(ze,t),_e(De,a))}function Ge(t){ze.current===t&&(se(De),se(ze)),ue.current===t&&(se(ue),Tl._currentValue=ee)}var mt,un;function ut(t){if(mt===void 0)try{throw Error()}catch(a){var n=a.stack.trim().match(/\n( *(at )?)/);mt=n&&n[1]||"",un=-1<a.stack.indexOf(`
    at`)?" (<anonymous>)":-1<a.stack.indexOf("@")?"@unknown:0:0":""}return`
`+mt+t+un}var xt=!1;function bt(t,n){if(!t||xt)return"";xt=!0;var a=Error.prepareStackTrace;Error.prepareStackTrace=void 0;try{var o={DetermineComponentFrameRoot:function(){try{if(n){var Te=function(){throw Error()};if(Object.defineProperty(Te.prototype,"props",{set:function(){throw Error()}}),typeof Reflect=="object"&&Reflect.construct){try{Reflect.construct(Te,[])}catch(ve){var me=ve}Reflect.construct(t,[],Te)}else{try{Te.call()}catch(ve){me=ve}t.call(Te.prototype)}}else{try{throw Error()}catch(ve){me=ve}(Te=t())&&typeof Te.catch=="function"&&Te.catch(function(){})}}catch(ve){if(ve&&me&&typeof ve.stack=="string")return[ve.stack,me.stack]}return[null,null]}};o.DetermineComponentFrameRoot.displayName="DetermineComponentFrameRoot";var u=Object.getOwnPropertyDescriptor(o.DetermineComponentFrameRoot,"name");u&&u.configurable&&Object.defineProperty(o.DetermineComponentFrameRoot,"name",{value:"DetermineComponentFrameRoot"});var d=o.DetermineComponentFrameRoot(),y=d[0],C=d[1];if(y&&C){var H=y.split(`
`),he=C.split(`
`);for(u=o=0;o<H.length&&!H[o].includes("DetermineComponentFrameRoot");)o++;for(;u<he.length&&!he[u].includes("DetermineComponentFrameRoot");)u++;if(o===H.length||u===he.length)for(o=H.length-1,u=he.length-1;1<=o&&0<=u&&H[o]!==he[u];)u--;for(;1<=o&&0<=u;o--,u--)if(H[o]!==he[u]){if(o!==1||u!==1)do if(o--,u--,0>u||H[o]!==he[u]){var Me=`
`+H[o].replace(" at new "," at ");return t.displayName&&Me.includes("<anonymous>")&&(Me=Me.replace("<anonymous>",t.displayName)),Me}while(1<=o&&0<=u);break}}}finally{xt=!1,Error.prepareStackTrace=a}return(a=t?t.displayName||t.name:"")?ut(a):""}function pt(t,n){switch(t.tag){case 26:case 27:case 5:return ut(t.type);case 16:return ut("Lazy");case 13:return t.child!==n&&n!==null?ut("Suspense Fallback"):ut("Suspense");case 19:return ut("SuspenseList");case 0:case 15:return bt(t.type,!1);case 11:return bt(t.type.render,!1);case 1:return bt(t.type,!0);case 31:return ut("Activity");default:return""}}function vt(t){try{var n="",a=null;do n+=pt(t,a),a=t,t=t.return;while(t);return n}catch(o){return`
Error generating stack: `+o.message+`
`+o.stack}}var Gt=Object.prototype.hasOwnProperty,vn=r.unstable_scheduleCallback,Xt=r.unstable_cancelCallback,fn=r.unstable_shouldYield,j=r.unstable_requestPaint,Ft=r.unstable_now,Ut=r.unstable_getCurrentPriorityLevel,P=r.unstable_ImmediatePriority,M=r.unstable_UserBlockingPriority,Z=r.unstable_NormalPriority,ce=r.unstable_LowPriority,xe=r.unstable_IdlePriority,ne=r.log,Ae=r.unstable_setDisableYieldValue,pe=null,ye=null;function Ne(t){if(typeof ne=="function"&&Ae(t),ye&&typeof ye.setStrictMode=="function")try{ye.setStrictMode(pe,t)}catch{}}var Ze=Math.clz32?Math.clz32:rt,He=Math.log,Fe=Math.LN2;function rt(t){return t>>>=0,t===0?32:31-(He(t)/Fe|0)|0}var lt=256,dt=262144,q=4194304;function Oe(t){var n=t&42;if(n!==0)return n;switch(t&-t){case 1:return 1;case 2:return 2;case 4:return 4;case 8:return 8;case 16:return 16;case 32:return 32;case 64:return 64;case 128:return 128;case 256:case 512:case 1024:case 2048:case 4096:case 8192:case 16384:case 32768:case 65536:case 131072:return t&261888;case 262144:case 524288:case 1048576:case 2097152:return t&3932160;case 4194304:case 8388608:case 16777216:case 33554432:return t&62914560;case 67108864:return 67108864;case 134217728:return 134217728;case 268435456:return 268435456;case 536870912:return 536870912;case 1073741824:return 0;default:return t}}function be(t,n,a){var o=t.pendingLanes;if(o===0)return 0;var u=0,d=t.suspendedLanes,y=t.pingedLanes;t=t.warmLanes;var C=o&134217727;return C!==0?(o=C&~d,o!==0?u=Oe(o):(y&=C,y!==0?u=Oe(y):a||(a=C&~t,a!==0&&(u=Oe(a))))):(C=o&~d,C!==0?u=Oe(C):y!==0?u=Oe(y):a||(a=o&~t,a!==0&&(u=Oe(a)))),u===0?0:n!==0&&n!==u&&(n&d)===0&&(d=u&-u,a=n&-n,d>=a||d===32&&(a&4194048)!==0)?n:u}function Pe(t,n){return(t.pendingLanes&~(t.suspendedLanes&~t.pingedLanes)&n)===0}function Ve(t,n){switch(t){case 1:case 2:case 4:case 8:case 64:return n+250;case 16:case 32:case 128:case 256:case 512:case 1024:case 2048:case 4096:case 8192:case 16384:case 32768:case 65536:case 131072:case 262144:case 524288:case 1048576:case 2097152:return n+5e3;case 4194304:case 8388608:case 16777216:case 33554432:return-1;case 67108864:case 134217728:case 268435456:case 536870912:case 1073741824:return-1;default:return-1}}function we(){var t=q;return q<<=1,(q&62914560)===0&&(q=4194304),t}function et(t){for(var n=[],a=0;31>a;a++)n.push(t);return n}function Je(t,n){t.pendingLanes|=n,n!==268435456&&(t.suspendedLanes=0,t.pingedLanes=0,t.warmLanes=0)}function Qt(t,n,a,o,u,d){var y=t.pendingLanes;t.pendingLanes=a,t.suspendedLanes=0,t.pingedLanes=0,t.warmLanes=0,t.expiredLanes&=a,t.entangledLanes&=a,t.errorRecoveryDisabledLanes&=a,t.shellSuspendCounter=0;var C=t.entanglements,H=t.expirationTimes,he=t.hiddenUpdates;for(a=y&~a;0<a;){var Me=31-Ze(a),Te=1<<Me;C[Me]=0,H[Me]=-1;var me=he[Me];if(me!==null)for(he[Me]=null,Me=0;Me<me.length;Me++){var ve=me[Me];ve!==null&&(ve.lane&=-536870913)}a&=~Te}o!==0&&Nt(t,o,0),d!==0&&u===0&&t.tag!==0&&(t.suspendedLanes|=d&~(y&~n))}function Nt(t,n,a){t.pendingLanes|=n,t.suspendedLanes&=~n;var o=31-Ze(n);t.entangledLanes|=n,t.entanglements[o]=t.entanglements[o]|1073741824|a&261930}function ei(t,n){var a=t.entangledLanes|=n;for(t=t.entanglements;a;){var o=31-Ze(a),u=1<<o;u&n|t[o]&n&&(t[o]|=n),a&=~u}}function ti(t,n){var a=n&-n;return a=(a&42)!==0?1:Zi(a),(a&(t.suspendedLanes|n))!==0?0:a}function Zi(t){switch(t){case 2:t=1;break;case 8:t=4;break;case 32:t=16;break;case 256:case 512:case 1024:case 2048:case 4096:case 8192:case 16384:case 32768:case 65536:case 131072:case 262144:case 524288:case 1048576:case 2097152:case 4194304:case 8388608:case 16777216:case 33554432:t=128;break;case 268435456:t=134217728;break;default:t=0}return t}function ls(t){return t&=-t,2<t?8<t?(t&134217727)!==0?32:268435456:8:2}function Ra(){var t=V.p;return t!==0?t:(t=window.event,t===void 0?32:wx(t.type))}function da(t,n){var a=V.p;try{return V.p=t,n()}finally{V.p=a}}var vi=Math.random().toString(36).slice(2),Sn="__reactFiber$"+vi,In="__reactProps$"+vi,Kn="__reactContainer$"+vi,Wt="__reactEvents$"+vi,bn="__reactListeners$"+vi,Er="__reactHandles$"+vi,Ua="__reactResources$"+vi,qt="__reactMarker$"+vi;function Ki(t){delete t[Sn],delete t[In],delete t[Wt],delete t[bn],delete t[Er]}function Pi(t){var n=t[Sn];if(n)return n;for(var a=t.parentNode;a;){if(n=a[Kn]||a[Sn]){if(a=n.alternate,n.child!==null||a!==null&&a.child!==null)for(t=fx(t);t!==null;){if(a=t[Sn])return a;t=fx(t)}return n}t=a,a=t.parentNode}return null}function zi(t){if(t=t[Sn]||t[Kn]){var n=t.tag;if(n===5||n===6||n===13||n===31||n===26||n===27||n===3)return t}return null}function ha(t){var n=t.tag;if(n===5||n===26||n===27||n===6)return t.stateNode;throw Error(s(33))}function pa(t){var n=t[Ua];return n||(n=t[Ua]={hoistableStyles:new Map,hoistableScripts:new Map}),n}function sn(t){t[qt]=!0}var Da=new Set,_i={};function A(t,n){X(t,n),X(t+"Capture",n)}function X(t,n){for(_i[t]=n,t=0;t<n.length;t++)Da.add(n[t])}var ge=RegExp("^[:A-Z_a-z\\u00C0-\\u00D6\\u00D8-\\u00F6\\u00F8-\\u02FF\\u0370-\\u037D\\u037F-\\u1FFF\\u200C-\\u200D\\u2070-\\u218F\\u2C00-\\u2FEF\\u3001-\\uD7FF\\uF900-\\uFDCF\\uFDF0-\\uFFFD][:A-Z_a-z\\u00C0-\\u00D6\\u00D8-\\u00F6\\u00F8-\\u02FF\\u0370-\\u037D\\u037F-\\u1FFF\\u200C-\\u200D\\u2070-\\u218F\\u2C00-\\u2FEF\\u3001-\\uD7FF\\uF900-\\uFDCF\\uFDF0-\\uFFFD\\-.0-9\\u00B7\\u0300-\\u036F\\u203F-\\u2040]*$"),ie={},ae={};function Be(t){return Gt.call(ae,t)?!0:Gt.call(ie,t)?!1:ge.test(t)?ae[t]=!0:(ie[t]=!0,!1)}function We(t,n,a){if(Be(n))if(a===null)t.removeAttribute(n);else{switch(typeof a){case"undefined":case"function":case"symbol":t.removeAttribute(n);return;case"boolean":var o=n.toLowerCase().slice(0,5);if(o!=="data-"&&o!=="aria-"){t.removeAttribute(n);return}}t.setAttribute(n,""+a)}}function Ie(t,n,a){if(a===null)t.removeAttribute(n);else{switch(typeof a){case"undefined":case"function":case"symbol":case"boolean":t.removeAttribute(n);return}t.setAttribute(n,""+a)}}function qe(t,n,a,o){if(o===null)t.removeAttribute(a);else{switch(typeof o){case"undefined":case"function":case"symbol":case"boolean":t.removeAttribute(a);return}t.setAttributeNS(n,a,""+o)}}function Ye(t){switch(typeof t){case"bigint":case"boolean":case"number":case"string":case"undefined":return t;case"object":return t;default:return""}}function gt(t){var n=t.type;return(t=t.nodeName)&&t.toLowerCase()==="input"&&(n==="checkbox"||n==="radio")}function Tt(t,n,a){var o=Object.getOwnPropertyDescriptor(t.constructor.prototype,n);if(!t.hasOwnProperty(n)&&typeof o<"u"&&typeof o.get=="function"&&typeof o.set=="function"){var u=o.get,d=o.set;return Object.defineProperty(t,n,{configurable:!0,get:function(){return u.call(this)},set:function(y){a=""+y,d.call(this,y)}}),Object.defineProperty(t,n,{enumerable:o.enumerable}),{getValue:function(){return a},setValue:function(y){a=""+y},stopTracking:function(){t._valueTracker=null,delete t[n]}}}}function $e(t){if(!t._valueTracker){var n=gt(t)?"checked":"value";t._valueTracker=Tt(t,n,""+t[n])}}function Bt(t){if(!t)return!1;var n=t._valueTracker;if(!n)return!0;var a=n.getValue(),o="";return t&&(o=gt(t)?t.checked?"true":"false":t.value),t=o,t!==a?(n.setValue(t),!0):!1}function dn(t){if(t=t||(typeof document<"u"?document:void 0),typeof t>"u")return null;try{return t.activeElement||t.body}catch{return t.body}}var rn=/[\n"\\]/g;function Mt(t){return t.replace(rn,function(n){return"\\"+n.charCodeAt(0).toString(16)+" "})}function Tn(t,n,a,o,u,d,y,C){t.name="",y!=null&&typeof y!="function"&&typeof y!="symbol"&&typeof y!="boolean"?t.type=y:t.removeAttribute("type"),n!=null?y==="number"?(n===0&&t.value===""||t.value!=n)&&(t.value=""+Ye(n)):t.value!==""+Ye(n)&&(t.value=""+Ye(n)):y!=="submit"&&y!=="reset"||t.removeAttribute("value"),n!=null?Rn(t,y,Ye(n)):a!=null?Rn(t,y,Ye(a)):o!=null&&t.removeAttribute("value"),u==null&&d!=null&&(t.defaultChecked=!!d),u!=null&&(t.checked=u&&typeof u!="function"&&typeof u!="symbol"),C!=null&&typeof C!="function"&&typeof C!="symbol"&&typeof C!="boolean"?t.name=""+Ye(C):t.removeAttribute("name")}function Ke(t,n,a,o,u,d,y,C){if(d!=null&&typeof d!="function"&&typeof d!="symbol"&&typeof d!="boolean"&&(t.type=d),n!=null||a!=null){if(!(d!=="submit"&&d!=="reset"||n!=null)){$e(t);return}a=a!=null?""+Ye(a):"",n=n!=null?""+Ye(n):a,C||n===t.value||(t.value=n),t.defaultValue=n}o=o??u,o=typeof o!="function"&&typeof o!="symbol"&&!!o,t.checked=C?t.checked:!!o,t.defaultChecked=!!o,y!=null&&typeof y!="function"&&typeof y!="symbol"&&typeof y!="boolean"&&(t.name=y),$e(t)}function Rn(t,n,a){n==="number"&&dn(t.ownerDocument)===t||t.defaultValue===""+a||(t.defaultValue=""+a)}function Et(t,n,a,o){if(t=t.options,n){n={};for(var u=0;u<a.length;u++)n["$"+a[u]]=!0;for(a=0;a<t.length;a++)u=n.hasOwnProperty("$"+t[a].value),t[a].selected!==u&&(t[a].selected=u),u&&o&&(t[a].defaultSelected=!0)}else{for(a=""+Ye(a),n=null,u=0;u<t.length;u++){if(t[u].value===a){t[u].selected=!0,o&&(t[u].defaultSelected=!0);return}n!==null||t[u].disabled||(n=t[u])}n!==null&&(n.selected=!0)}}function Qn(t,n,a){if(n!=null&&(n=""+Ye(n),n!==t.value&&(t.value=n),a==null)){t.defaultValue!==n&&(t.defaultValue=n);return}t.defaultValue=a!=null?""+Ye(a):""}function ci(t,n,a,o){if(n==null){if(o!=null){if(a!=null)throw Error(s(92));if(K(o)){if(1<o.length)throw Error(s(93));o=o[0]}a=o}a==null&&(a=""),n=a}a=Ye(n),t.defaultValue=a,o=t.textContent,o===a&&o!==""&&o!==null&&(t.value=o),$e(t)}function ni(t,n){if(n){var a=t.firstChild;if(a&&a===t.lastChild&&a.nodeType===3){a.nodeValue=n;return}}t.textContent=n}var Qi=new Set("animationIterationCount aspectRatio borderImageOutset borderImageSlice borderImageWidth boxFlex boxFlexGroup boxOrdinalGroup columnCount columns flex flexGrow flexPositive flexShrink flexNegative flexOrder gridArea gridRow gridRowEnd gridRowSpan gridRowStart gridColumn gridColumnEnd gridColumnSpan gridColumnStart fontWeight lineClamp lineHeight opacity order orphans scale tabSize widows zIndex zoom fillOpacity floodOpacity stopOpacity strokeDasharray strokeDashoffset strokeMiterlimit strokeOpacity strokeWidth MozAnimationIterationCount MozBoxFlex MozBoxFlexGroup MozLineClamp msAnimationIterationCount msFlex msZoom msFlexGrow msFlexNegative msFlexOrder msFlexPositive msFlexShrink msGridColumn msGridColumnSpan msGridRow msGridRowSpan WebkitAnimationIterationCount WebkitBoxFlex WebKitBoxFlexGroup WebkitBoxOrdinalGroup WebkitColumnCount WebkitColumns WebkitFlex WebkitFlexGrow WebkitFlexPositive WebkitFlexShrink WebkitLineClamp".split(" "));function jt(t,n,a){var o=n.indexOf("--")===0;a==null||typeof a=="boolean"||a===""?o?t.setProperty(n,""):n==="float"?t.cssFloat="":t[n]="":o?t.setProperty(n,a):typeof a!="number"||a===0||Qi.has(n)?n==="float"?t.cssFloat=a:t[n]=(""+a).trim():t[n]=a+"px"}function gn(t,n,a){if(n!=null&&typeof n!="object")throw Error(s(62));if(t=t.style,a!=null){for(var o in a)!a.hasOwnProperty(o)||n!=null&&n.hasOwnProperty(o)||(o.indexOf("--")===0?t.setProperty(o,""):o==="float"?t.cssFloat="":t[o]="");for(var u in n)o=n[u],n.hasOwnProperty(u)&&a[u]!==o&&jt(t,u,o)}else for(var d in n)n.hasOwnProperty(d)&&jt(t,d,n[d])}function Ai(t){if(t.indexOf("-")===-1)return!1;switch(t){case"annotation-xml":case"color-profile":case"font-face":case"font-face-src":case"font-face-uri":case"font-face-format":case"font-face-name":case"missing-glyph":return!1;default:return!0}}var en=new Map([["acceptCharset","accept-charset"],["htmlFor","for"],["httpEquiv","http-equiv"],["crossOrigin","crossorigin"],["accentHeight","accent-height"],["alignmentBaseline","alignment-baseline"],["arabicForm","arabic-form"],["baselineShift","baseline-shift"],["capHeight","cap-height"],["clipPath","clip-path"],["clipRule","clip-rule"],["colorInterpolation","color-interpolation"],["colorInterpolationFilters","color-interpolation-filters"],["colorProfile","color-profile"],["colorRendering","color-rendering"],["dominantBaseline","dominant-baseline"],["enableBackground","enable-background"],["fillOpacity","fill-opacity"],["fillRule","fill-rule"],["floodColor","flood-color"],["floodOpacity","flood-opacity"],["fontFamily","font-family"],["fontSize","font-size"],["fontSizeAdjust","font-size-adjust"],["fontStretch","font-stretch"],["fontStyle","font-style"],["fontVariant","font-variant"],["fontWeight","font-weight"],["glyphName","glyph-name"],["glyphOrientationHorizontal","glyph-orientation-horizontal"],["glyphOrientationVertical","glyph-orientation-vertical"],["horizAdvX","horiz-adv-x"],["horizOriginX","horiz-origin-x"],["imageRendering","image-rendering"],["letterSpacing","letter-spacing"],["lightingColor","lighting-color"],["markerEnd","marker-end"],["markerMid","marker-mid"],["markerStart","marker-start"],["overlinePosition","overline-position"],["overlineThickness","overline-thickness"],["paintOrder","paint-order"],["panose-1","panose-1"],["pointerEvents","pointer-events"],["renderingIntent","rendering-intent"],["shapeRendering","shape-rendering"],["stopColor","stop-color"],["stopOpacity","stop-opacity"],["strikethroughPosition","strikethrough-position"],["strikethroughThickness","strikethrough-thickness"],["strokeDasharray","stroke-dasharray"],["strokeDashoffset","stroke-dashoffset"],["strokeLinecap","stroke-linecap"],["strokeLinejoin","stroke-linejoin"],["strokeMiterlimit","stroke-miterlimit"],["strokeOpacity","stroke-opacity"],["strokeWidth","stroke-width"],["textAnchor","text-anchor"],["textDecoration","text-decoration"],["textRendering","text-rendering"],["transformOrigin","transform-origin"],["underlinePosition","underline-position"],["underlineThickness","underline-thickness"],["unicodeBidi","unicode-bidi"],["unicodeRange","unicode-range"],["unitsPerEm","units-per-em"],["vAlphabetic","v-alphabetic"],["vHanging","v-hanging"],["vIdeographic","v-ideographic"],["vMathematical","v-mathematical"],["vectorEffect","vector-effect"],["vertAdvY","vert-adv-y"],["vertOriginX","vert-origin-x"],["vertOriginY","vert-origin-y"],["wordSpacing","word-spacing"],["writingMode","writing-mode"],["xmlnsXlink","xmlns:xlink"],["xHeight","x-height"]]),Ji=/^[\u0000-\u001F ]*j[\r\n\t]*a[\r\n\t]*v[\r\n\t]*a[\r\n\t]*s[\r\n\t]*c[\r\n\t]*r[\r\n\t]*i[\r\n\t]*p[\r\n\t]*t[\r\n\t]*:/i;function Fi(t){return Ji.test(""+t)?"javascript:throw new Error('React has blocked a javascript: URL as a security precaution.')":t}function yi(){}var Is=null;function Hs(t){return t=t.target||t.srcElement||window,t.correspondingUseElement&&(t=t.correspondingUseElement),t.nodeType===3?t.parentNode:t}var qa=null,Ya=null;function Wo(t){var n=zi(t);if(n&&(t=n.stateNode)){var a=t[In]||null;e:switch(t=n.stateNode,n.type){case"input":if(Tn(t,a.value,a.defaultValue,a.defaultValue,a.checked,a.defaultChecked,a.type,a.name),n=a.name,a.type==="radio"&&n!=null){for(a=t;a.parentNode;)a=a.parentNode;for(a=a.querySelectorAll('input[name="'+Mt(""+n)+'"][type="radio"]'),n=0;n<a.length;n++){var o=a[n];if(o!==t&&o.form===t.form){var u=o[In]||null;if(!u)throw Error(s(90));Tn(o,u.value,u.defaultValue,u.defaultValue,u.checked,u.defaultChecked,u.type,u.name)}}for(n=0;n<a.length;n++)o=a[n],o.form===t.form&&Bt(o)}break e;case"textarea":Qn(t,a.value,a.defaultValue);break e;case"select":n=a.value,n!=null&&Et(t,!!a.multiple,n,!1)}}}var le=!1;function te(t,n,a){if(le)return t(n,a);le=!0;try{var o=t(n);return o}finally{if(le=!1,(qa!==null||Ya!==null)&&(zc(),qa&&(n=qa,t=Ya,Ya=qa=null,Wo(n),t)))for(n=0;n<t.length;n++)Wo(t[n])}}function Ue(t,n){var a=t.stateNode;if(a===null)return null;var o=a[In]||null;if(o===null)return null;a=o[n];e:switch(n){case"onClick":case"onClickCapture":case"onDoubleClick":case"onDoubleClickCapture":case"onMouseDown":case"onMouseDownCapture":case"onMouseMove":case"onMouseMoveCapture":case"onMouseUp":case"onMouseUpCapture":case"onMouseEnter":(o=!o.disabled)||(t=t.type,o=!(t==="button"||t==="input"||t==="select"||t==="textarea")),t=!o;break e;default:t=!1}if(t)return null;if(a&&typeof a!="function")throw Error(s(231,n,typeof a));return a}var Ce=!(typeof window>"u"||typeof window.document>"u"||typeof window.document.createElement>"u"),Qe=!1;if(Ce)try{var Lt={};Object.defineProperty(Lt,"passive",{get:function(){Qe=!0}}),window.addEventListener("test",Lt,Lt),window.removeEventListener("test",Lt,Lt)}catch{Qe=!1}var Le=null,st=null,_t=null;function Ot(){if(_t)return _t;var t,n=st,a=n.length,o,u="value"in Le?Le.value:Le.textContent,d=u.length;for(t=0;t<a&&n[t]===u[t];t++);var y=a-t;for(o=1;o<=y&&n[a-o]===u[d-o];o++);return _t=u.slice(t,1<o?1-o:void 0)}function Yt(t){var n=t.keyCode;return"charCode"in t?(t=t.charCode,t===0&&n===13&&(t=13)):t=n,t===10&&(t=13),32<=t||t===13?t:0}function Wn(){return!0}function it(){return!1}function ke(t){function n(a,o,u,d,y){this._reactName=a,this._targetInst=u,this.type=o,this.nativeEvent=d,this.target=y,this.currentTarget=null;for(var C in t)t.hasOwnProperty(C)&&(a=t[C],this[C]=a?a(d):d[C]);return this.isDefaultPrevented=(d.defaultPrevented!=null?d.defaultPrevented:d.returnValue===!1)?Wn:it,this.isPropagationStopped=it,this}return v(n.prototype,{preventDefault:function(){this.defaultPrevented=!0;var a=this.nativeEvent;a&&(a.preventDefault?a.preventDefault():typeof a.returnValue!="unknown"&&(a.returnValue=!1),this.isDefaultPrevented=Wn)},stopPropagation:function(){var a=this.nativeEvent;a&&(a.stopPropagation?a.stopPropagation():typeof a.cancelBubble!="unknown"&&(a.cancelBubble=!0),this.isPropagationStopped=Wn)},persist:function(){},isPersistent:Wn}),n}var tn={eventPhase:0,bubbles:0,cancelable:0,timeStamp:function(t){return t.timeStamp||Date.now()},defaultPrevented:0,isTrusted:0},An=ke(tn),wn=v({},tn,{view:0,detail:0}),ma=ke(wn),Un,On,wi,Na=v({},wn,{screenX:0,screenY:0,clientX:0,clientY:0,pageX:0,pageY:0,ctrlKey:0,shiftKey:0,altKey:0,metaKey:0,getModifierState:af,button:0,buttons:0,relatedTarget:function(t){return t.relatedTarget===void 0?t.fromElement===t.srcElement?t.toElement:t.fromElement:t.relatedTarget},movementX:function(t){return"movementX"in t?t.movementX:(t!==wi&&(wi&&t.type==="mousemove"?(Un=t.screenX-wi.screenX,On=t.screenY-wi.screenY):On=Un=0,wi=t),Un)},movementY:function(t){return"movementY"in t?t.movementY:On}}),La=ke(Na),ja=v({},Na,{dataTransfer:0}),nn=ke(ja),ui=v({},wn,{relatedTarget:0}),$i=ke(ui),ga=v({},tn,{animationName:0,elapsedTime:0,pseudoElement:0}),xa=ke(ga),ea=v({},tn,{clipboardData:function(t){return"clipboardData"in t?t.clipboardData:window.clipboardData}}),Za=ke(ea),Tr=v({},tn,{data:0}),Ci=ke(Tr),Ar={Esc:"Escape",Spacebar:" ",Left:"ArrowLeft",Up:"ArrowUp",Right:"ArrowRight",Down:"ArrowDown",Del:"Delete",Win:"OS",Menu:"ContextMenu",Apps:"ContextMenu",Scroll:"ScrollLock",MozPrintableKey:"Unidentified"},wr={8:"Backspace",9:"Tab",12:"Clear",13:"Enter",16:"Shift",17:"Control",18:"Alt",19:"Pause",20:"CapsLock",27:"Escape",32:" ",33:"PageUp",34:"PageDown",35:"End",36:"Home",37:"ArrowLeft",38:"ArrowUp",39:"ArrowRight",40:"ArrowDown",45:"Insert",46:"Delete",112:"F1",113:"F2",114:"F3",115:"F4",116:"F5",117:"F6",118:"F7",119:"F8",120:"F9",121:"F10",122:"F11",123:"F12",144:"NumLock",145:"ScrollLock",224:"Meta"},ii={Alt:"altKey",Control:"ctrlKey",Meta:"metaKey",Shift:"shiftKey"};function uy(t){var n=this.nativeEvent;return n.getModifierState?n.getModifierState(t):(t=ii[t])?!!n[t]:!1}function af(){return uy}var fy=v({},wn,{key:function(t){if(t.key){var n=Ar[t.key]||t.key;if(n!=="Unidentified")return n}return t.type==="keypress"?(t=Yt(t),t===13?"Enter":String.fromCharCode(t)):t.type==="keydown"||t.type==="keyup"?wr[t.keyCode]||"Unidentified":""},code:0,location:0,ctrlKey:0,shiftKey:0,altKey:0,metaKey:0,repeat:0,locale:0,getModifierState:af,charCode:function(t){return t.type==="keypress"?Yt(t):0},keyCode:function(t){return t.type==="keydown"||t.type==="keyup"?t.keyCode:0},which:function(t){return t.type==="keypress"?Yt(t):t.type==="keydown"||t.type==="keyup"?t.keyCode:0}}),dy=ke(fy),hy=v({},Na,{pointerId:0,width:0,height:0,pressure:0,tangentialPressure:0,tiltX:0,tiltY:0,twist:0,pointerType:0,isPrimary:0}),lm=ke(hy),py=v({},wn,{touches:0,targetTouches:0,changedTouches:0,altKey:0,metaKey:0,ctrlKey:0,shiftKey:0,getModifierState:af}),my=ke(py),gy=v({},tn,{propertyName:0,elapsedTime:0,pseudoElement:0}),xy=ke(gy),vy=v({},Na,{deltaX:function(t){return"deltaX"in t?t.deltaX:"wheelDeltaX"in t?-t.wheelDeltaX:0},deltaY:function(t){return"deltaY"in t?t.deltaY:"wheelDeltaY"in t?-t.wheelDeltaY:"wheelDelta"in t?-t.wheelDelta:0},deltaZ:0,deltaMode:0}),_y=ke(vy),yy=v({},tn,{newState:0,oldState:0}),Sy=ke(yy),by=[9,13,27,32],rf=Ce&&"CompositionEvent"in window,qo=null;Ce&&"documentMode"in document&&(qo=document.documentMode);var My=Ce&&"TextEvent"in window&&!qo,cm=Ce&&(!rf||qo&&8<qo&&11>=qo),um=" ",fm=!1;function dm(t,n){switch(t){case"keyup":return by.indexOf(n.keyCode)!==-1;case"keydown":return n.keyCode!==229;case"keypress":case"mousedown":case"focusout":return!0;default:return!1}}function hm(t){return t=t.detail,typeof t=="object"&&"data"in t?t.data:null}var Gs=!1;function Ey(t,n){switch(t){case"compositionend":return hm(n);case"keypress":return n.which!==32?null:(fm=!0,um);case"textInput":return t=n.data,t===um&&fm?null:t;default:return null}}function Ty(t,n){if(Gs)return t==="compositionend"||!rf&&dm(t,n)?(t=Ot(),_t=st=Le=null,Gs=!1,t):null;switch(t){case"paste":return null;case"keypress":if(!(n.ctrlKey||n.altKey||n.metaKey)||n.ctrlKey&&n.altKey){if(n.char&&1<n.char.length)return n.char;if(n.which)return String.fromCharCode(n.which)}return null;case"compositionend":return cm&&n.locale!=="ko"?null:n.data;default:return null}}var Ay={color:!0,date:!0,datetime:!0,"datetime-local":!0,email:!0,month:!0,number:!0,password:!0,range:!0,search:!0,tel:!0,text:!0,time:!0,url:!0,week:!0};function pm(t){var n=t&&t.nodeName&&t.nodeName.toLowerCase();return n==="input"?!!Ay[t.type]:n==="textarea"}function mm(t,n,a,o){qa?Ya?Ya.push(o):Ya=[o]:qa=o,n=kc(n,"onChange"),0<n.length&&(a=new An("onChange","change",null,a,o),t.push({event:a,listeners:n}))}var Yo=null,jo=null;function wy(t){Qg(t,0)}function tc(t){var n=ha(t);if(Bt(n))return t}function gm(t,n){if(t==="change")return n}var xm=!1;if(Ce){var sf;if(Ce){var of="oninput"in document;if(!of){var vm=document.createElement("div");vm.setAttribute("oninput","return;"),of=typeof vm.oninput=="function"}sf=of}else sf=!1;xm=sf&&(!document.documentMode||9<document.documentMode)}function _m(){Yo&&(Yo.detachEvent("onpropertychange",ym),jo=Yo=null)}function ym(t){if(t.propertyName==="value"&&tc(jo)){var n=[];mm(n,jo,t,Hs(t)),te(wy,n)}}function Cy(t,n,a){t==="focusin"?(_m(),Yo=n,jo=a,Yo.attachEvent("onpropertychange",ym)):t==="focusout"&&_m()}function Ry(t){if(t==="selectionchange"||t==="keyup"||t==="keydown")return tc(jo)}function Uy(t,n){if(t==="click")return tc(n)}function Dy(t,n){if(t==="input"||t==="change")return tc(n)}function Ny(t,n){return t===n&&(t!==0||1/t===1/n)||t!==t&&n!==n}var Bi=typeof Object.is=="function"?Object.is:Ny;function Zo(t,n){if(Bi(t,n))return!0;if(typeof t!="object"||t===null||typeof n!="object"||n===null)return!1;var a=Object.keys(t),o=Object.keys(n);if(a.length!==o.length)return!1;for(o=0;o<a.length;o++){var u=a[o];if(!Gt.call(n,u)||!Bi(t[u],n[u]))return!1}return!0}function Sm(t){for(;t&&t.firstChild;)t=t.firstChild;return t}function bm(t,n){var a=Sm(t);t=0;for(var o;a;){if(a.nodeType===3){if(o=t+a.textContent.length,t<=n&&o>=n)return{node:a,offset:n-t};t=o}e:{for(;a;){if(a.nextSibling){a=a.nextSibling;break e}a=a.parentNode}a=void 0}a=Sm(a)}}function Mm(t,n){return t&&n?t===n?!0:t&&t.nodeType===3?!1:n&&n.nodeType===3?Mm(t,n.parentNode):"contains"in t?t.contains(n):t.compareDocumentPosition?!!(t.compareDocumentPosition(n)&16):!1:!1}function Em(t){t=t!=null&&t.ownerDocument!=null&&t.ownerDocument.defaultView!=null?t.ownerDocument.defaultView:window;for(var n=dn(t.document);n instanceof t.HTMLIFrameElement;){try{var a=typeof n.contentWindow.location.href=="string"}catch{a=!1}if(a)t=n.contentWindow;else break;n=dn(t.document)}return n}function lf(t){var n=t&&t.nodeName&&t.nodeName.toLowerCase();return n&&(n==="input"&&(t.type==="text"||t.type==="search"||t.type==="tel"||t.type==="url"||t.type==="password")||n==="textarea"||t.contentEditable==="true")}var Ly=Ce&&"documentMode"in document&&11>=document.documentMode,Vs=null,cf=null,Ko=null,uf=!1;function Tm(t,n,a){var o=a.window===a?a.document:a.nodeType===9?a:a.ownerDocument;uf||Vs==null||Vs!==dn(o)||(o=Vs,"selectionStart"in o&&lf(o)?o={start:o.selectionStart,end:o.selectionEnd}:(o=(o.ownerDocument&&o.ownerDocument.defaultView||window).getSelection(),o={anchorNode:o.anchorNode,anchorOffset:o.anchorOffset,focusNode:o.focusNode,focusOffset:o.focusOffset}),Ko&&Zo(Ko,o)||(Ko=o,o=kc(cf,"onSelect"),0<o.length&&(n=new An("onSelect","select",null,n,a),t.push({event:n,listeners:o}),n.target=Vs)))}function cs(t,n){var a={};return a[t.toLowerCase()]=n.toLowerCase(),a["Webkit"+t]="webkit"+n,a["Moz"+t]="moz"+n,a}var ks={animationend:cs("Animation","AnimationEnd"),animationiteration:cs("Animation","AnimationIteration"),animationstart:cs("Animation","AnimationStart"),transitionrun:cs("Transition","TransitionRun"),transitionstart:cs("Transition","TransitionStart"),transitioncancel:cs("Transition","TransitionCancel"),transitionend:cs("Transition","TransitionEnd")},ff={},Am={};Ce&&(Am=document.createElement("div").style,"AnimationEvent"in window||(delete ks.animationend.animation,delete ks.animationiteration.animation,delete ks.animationstart.animation),"TransitionEvent"in window||delete ks.transitionend.transition);function us(t){if(ff[t])return ff[t];if(!ks[t])return t;var n=ks[t],a;for(a in n)if(n.hasOwnProperty(a)&&a in Am)return ff[t]=n[a];return t}var wm=us("animationend"),Cm=us("animationiteration"),Rm=us("animationstart"),Oy=us("transitionrun"),Py=us("transitionstart"),zy=us("transitioncancel"),Um=us("transitionend"),Dm=new Map,df="abort auxClick beforeToggle cancel canPlay canPlayThrough click close contextMenu copy cut drag dragEnd dragEnter dragExit dragLeave dragOver dragStart drop durationChange emptied encrypted ended error gotPointerCapture input invalid keyDown keyPress keyUp load loadedData loadedMetadata loadStart lostPointerCapture mouseDown mouseMove mouseOut mouseOver mouseUp paste pause play playing pointerCancel pointerDown pointerMove pointerOut pointerOver pointerUp progress rateChange reset resize seeked seeking stalled submit suspend timeUpdate touchCancel touchEnd touchStart volumeChange scroll toggle touchMove waiting wheel".split(" ");df.push("scrollEnd");function va(t,n){Dm.set(t,n),A(n,[t])}var nc=typeof reportError=="function"?reportError:function(t){if(typeof window=="object"&&typeof window.ErrorEvent=="function"){var n=new window.ErrorEvent("error",{bubbles:!0,cancelable:!0,message:typeof t=="object"&&t!==null&&typeof t.message=="string"?String(t.message):String(t),error:t});if(!window.dispatchEvent(n))return}else if(typeof process=="object"&&typeof process.emit=="function"){process.emit("uncaughtException",t);return}console.error(t)},ta=[],Xs=0,hf=0;function ic(){for(var t=Xs,n=hf=Xs=0;n<t;){var a=ta[n];ta[n++]=null;var o=ta[n];ta[n++]=null;var u=ta[n];ta[n++]=null;var d=ta[n];if(ta[n++]=null,o!==null&&u!==null){var y=o.pending;y===null?u.next=u:(u.next=y.next,y.next=u),o.pending=u}d!==0&&Nm(a,u,d)}}function ac(t,n,a,o){ta[Xs++]=t,ta[Xs++]=n,ta[Xs++]=a,ta[Xs++]=o,hf|=o,t.lanes|=o,t=t.alternate,t!==null&&(t.lanes|=o)}function pf(t,n,a,o){return ac(t,n,a,o),rc(t)}function fs(t,n){return ac(t,null,null,n),rc(t)}function Nm(t,n,a){t.lanes|=a;var o=t.alternate;o!==null&&(o.lanes|=a);for(var u=!1,d=t.return;d!==null;)d.childLanes|=a,o=d.alternate,o!==null&&(o.childLanes|=a),d.tag===22&&(t=d.stateNode,t===null||t._visibility&1||(u=!0)),t=d,d=d.return;return t.tag===3?(d=t.stateNode,u&&n!==null&&(u=31-Ze(a),t=d.hiddenUpdates,o=t[u],o===null?t[u]=[n]:o.push(n),n.lane=a|536870912),d):null}function rc(t){if(50<vl)throw vl=0,Md=null,Error(s(185));for(var n=t.return;n!==null;)t=n,n=t.return;return t.tag===3?t.stateNode:null}var Ws={};function Fy(t,n,a,o){this.tag=t,this.key=a,this.sibling=this.child=this.return=this.stateNode=this.type=this.elementType=null,this.index=0,this.refCleanup=this.ref=null,this.pendingProps=n,this.dependencies=this.memoizedState=this.updateQueue=this.memoizedProps=null,this.mode=o,this.subtreeFlags=this.flags=0,this.deletions=null,this.childLanes=this.lanes=0,this.alternate=null}function Ii(t,n,a,o){return new Fy(t,n,a,o)}function mf(t){return t=t.prototype,!(!t||!t.isReactComponent)}function Ka(t,n){var a=t.alternate;return a===null?(a=Ii(t.tag,n,t.key,t.mode),a.elementType=t.elementType,a.type=t.type,a.stateNode=t.stateNode,a.alternate=t,t.alternate=a):(a.pendingProps=n,a.type=t.type,a.flags=0,a.subtreeFlags=0,a.deletions=null),a.flags=t.flags&65011712,a.childLanes=t.childLanes,a.lanes=t.lanes,a.child=t.child,a.memoizedProps=t.memoizedProps,a.memoizedState=t.memoizedState,a.updateQueue=t.updateQueue,n=t.dependencies,a.dependencies=n===null?null:{lanes:n.lanes,firstContext:n.firstContext},a.sibling=t.sibling,a.index=t.index,a.ref=t.ref,a.refCleanup=t.refCleanup,a}function Lm(t,n){t.flags&=65011714;var a=t.alternate;return a===null?(t.childLanes=0,t.lanes=n,t.child=null,t.subtreeFlags=0,t.memoizedProps=null,t.memoizedState=null,t.updateQueue=null,t.dependencies=null,t.stateNode=null):(t.childLanes=a.childLanes,t.lanes=a.lanes,t.child=a.child,t.subtreeFlags=0,t.deletions=null,t.memoizedProps=a.memoizedProps,t.memoizedState=a.memoizedState,t.updateQueue=a.updateQueue,t.type=a.type,n=a.dependencies,t.dependencies=n===null?null:{lanes:n.lanes,firstContext:n.firstContext}),t}function sc(t,n,a,o,u,d){var y=0;if(o=t,typeof t=="function")mf(t)&&(y=1);else if(typeof t=="string")y=VS(t,a,De.current)?26:t==="html"||t==="head"||t==="body"?27:5;else e:switch(t){case O:return t=Ii(31,a,n,u),t.elementType=O,t.lanes=d,t;case R:return ds(a.children,u,d,n);case b:y=8,u|=24;break;case S:return t=Ii(12,a,n,u|2),t.elementType=S,t.lanes=d,t;case N:return t=Ii(13,a,n,u),t.elementType=N,t.lanes=d,t;case L:return t=Ii(19,a,n,u),t.elementType=L,t.lanes=d,t;default:if(typeof t=="object"&&t!==null)switch(t.$$typeof){case G:y=10;break e;case F:y=9;break e;case w:y=11;break e;case z:y=14;break e;case T:y=16,o=null;break e}y=29,a=Error(s(130,t===null?"null":typeof t,"")),o=null}return n=Ii(y,a,n,u),n.elementType=t,n.type=o,n.lanes=d,n}function ds(t,n,a,o){return t=Ii(7,t,o,n),t.lanes=a,t}function gf(t,n,a){return t=Ii(6,t,null,n),t.lanes=a,t}function Om(t){var n=Ii(18,null,null,0);return n.stateNode=t,n}function xf(t,n,a){return n=Ii(4,t.children!==null?t.children:[],t.key,n),n.lanes=a,n.stateNode={containerInfo:t.containerInfo,pendingChildren:null,implementation:t.implementation},n}var Pm=new WeakMap;function na(t,n){if(typeof t=="object"&&t!==null){var a=Pm.get(t);return a!==void 0?a:(n={value:t,source:n,stack:vt(n)},Pm.set(t,n),n)}return{value:t,source:n,stack:vt(n)}}var qs=[],Ys=0,oc=null,Qo=0,ia=[],aa=0,Cr=null,Oa=1,Pa="";function Qa(t,n){qs[Ys++]=Qo,qs[Ys++]=oc,oc=t,Qo=n}function zm(t,n,a){ia[aa++]=Oa,ia[aa++]=Pa,ia[aa++]=Cr,Cr=t;var o=Oa;t=Pa;var u=32-Ze(o)-1;o&=~(1<<u),a+=1;var d=32-Ze(n)+u;if(30<d){var y=u-u%5;d=(o&(1<<y)-1).toString(32),o>>=y,u-=y,Oa=1<<32-Ze(n)+u|a<<u|o,Pa=d+t}else Oa=1<<d|a<<u|o,Pa=t}function vf(t){t.return!==null&&(Qa(t,1),zm(t,1,0))}function _f(t){for(;t===oc;)oc=qs[--Ys],qs[Ys]=null,Qo=qs[--Ys],qs[Ys]=null;for(;t===Cr;)Cr=ia[--aa],ia[aa]=null,Pa=ia[--aa],ia[aa]=null,Oa=ia[--aa],ia[aa]=null}function Fm(t,n){ia[aa++]=Oa,ia[aa++]=Pa,ia[aa++]=Cr,Oa=n.id,Pa=n.overflow,Cr=t}var ai=null,_n=null,Vt=!1,Rr=null,ra=!1,yf=Error(s(519));function Ur(t){var n=Error(s(418,1<arguments.length&&arguments[1]!==void 0&&arguments[1]?"text":"HTML",""));throw Jo(na(n,t)),yf}function Bm(t){var n=t.stateNode,a=t.type,o=t.memoizedProps;switch(n[Sn]=t,n[In]=o,a){case"dialog":zt("cancel",n),zt("close",n);break;case"iframe":case"object":case"embed":zt("load",n);break;case"video":case"audio":for(a=0;a<yl.length;a++)zt(yl[a],n);break;case"source":zt("error",n);break;case"img":case"image":case"link":zt("error",n),zt("load",n);break;case"details":zt("toggle",n);break;case"input":zt("invalid",n),Ke(n,o.value,o.defaultValue,o.checked,o.defaultChecked,o.type,o.name,!0);break;case"select":zt("invalid",n);break;case"textarea":zt("invalid",n),ci(n,o.value,o.defaultValue,o.children)}a=o.children,typeof a!="string"&&typeof a!="number"&&typeof a!="bigint"||n.textContent===""+a||o.suppressHydrationWarning===!0||tx(n.textContent,a)?(o.popover!=null&&(zt("beforetoggle",n),zt("toggle",n)),o.onScroll!=null&&zt("scroll",n),o.onScrollEnd!=null&&zt("scrollend",n),o.onClick!=null&&(n.onclick=yi),n=!0):n=!1,n||Ur(t,!0)}function Im(t){for(ai=t.return;ai;)switch(ai.tag){case 5:case 31:case 13:ra=!1;return;case 27:case 3:ra=!0;return;default:ai=ai.return}}function js(t){if(t!==ai)return!1;if(!Vt)return Im(t),Vt=!0,!1;var n=t.tag,a;if((a=n!==3&&n!==27)&&((a=n===5)&&(a=t.type,a=!(a!=="form"&&a!=="button")||Bd(t.type,t.memoizedProps)),a=!a),a&&_n&&Ur(t),Im(t),n===13){if(t=t.memoizedState,t=t!==null?t.dehydrated:null,!t)throw Error(s(317));_n=ux(t)}else if(n===31){if(t=t.memoizedState,t=t!==null?t.dehydrated:null,!t)throw Error(s(317));_n=ux(t)}else n===27?(n=_n,Xr(t.type)?(t=kd,kd=null,_n=t):_n=n):_n=ai?oa(t.stateNode.nextSibling):null;return!0}function hs(){_n=ai=null,Vt=!1}function Sf(){var t=Rr;return t!==null&&(Ni===null?Ni=t:Ni.push.apply(Ni,t),Rr=null),t}function Jo(t){Rr===null?Rr=[t]:Rr.push(t)}var bf=D(null),ps=null,Ja=null;function Dr(t,n,a){_e(bf,n._currentValue),n._currentValue=a}function $a(t){t._currentValue=bf.current,se(bf)}function Mf(t,n,a){for(;t!==null;){var o=t.alternate;if((t.childLanes&n)!==n?(t.childLanes|=n,o!==null&&(o.childLanes|=n)):o!==null&&(o.childLanes&n)!==n&&(o.childLanes|=n),t===a)break;t=t.return}}function Ef(t,n,a,o){var u=t.child;for(u!==null&&(u.return=t);u!==null;){var d=u.dependencies;if(d!==null){var y=u.child;d=d.firstContext;e:for(;d!==null;){var C=d;d=u;for(var H=0;H<n.length;H++)if(C.context===n[H]){d.lanes|=a,C=d.alternate,C!==null&&(C.lanes|=a),Mf(d.return,a,t),o||(y=null);break e}d=C.next}}else if(u.tag===18){if(y=u.return,y===null)throw Error(s(341));y.lanes|=a,d=y.alternate,d!==null&&(d.lanes|=a),Mf(y,a,t),y=null}else y=u.child;if(y!==null)y.return=u;else for(y=u;y!==null;){if(y===t){y=null;break}if(u=y.sibling,u!==null){u.return=y.return,y=u;break}y=y.return}u=y}}function Zs(t,n,a,o){t=null;for(var u=n,d=!1;u!==null;){if(!d){if((u.flags&524288)!==0)d=!0;else if((u.flags&262144)!==0)break}if(u.tag===10){var y=u.alternate;if(y===null)throw Error(s(387));if(y=y.memoizedProps,y!==null){var C=u.type;Bi(u.pendingProps.value,y.value)||(t!==null?t.push(C):t=[C])}}else if(u===ue.current){if(y=u.alternate,y===null)throw Error(s(387));y.memoizedState.memoizedState!==u.memoizedState.memoizedState&&(t!==null?t.push(Tl):t=[Tl])}u=u.return}t!==null&&Ef(n,t,a,o),n.flags|=262144}function lc(t){for(t=t.firstContext;t!==null;){if(!Bi(t.context._currentValue,t.memoizedValue))return!0;t=t.next}return!1}function ms(t){ps=t,Ja=null,t=t.dependencies,t!==null&&(t.firstContext=null)}function ri(t){return Hm(ps,t)}function cc(t,n){return ps===null&&ms(t),Hm(t,n)}function Hm(t,n){var a=n._currentValue;if(n={context:n,memoizedValue:a,next:null},Ja===null){if(t===null)throw Error(s(308));Ja=n,t.dependencies={lanes:0,firstContext:n},t.flags|=524288}else Ja=Ja.next=n;return a}var By=typeof AbortController<"u"?AbortController:function(){var t=[],n=this.signal={aborted:!1,addEventListener:function(a,o){t.push(o)}};this.abort=function(){n.aborted=!0,t.forEach(function(a){return a()})}},Iy=r.unstable_scheduleCallback,Hy=r.unstable_NormalPriority,Hn={$$typeof:G,Consumer:null,Provider:null,_currentValue:null,_currentValue2:null,_threadCount:0};function Tf(){return{controller:new By,data:new Map,refCount:0}}function $o(t){t.refCount--,t.refCount===0&&Iy(Hy,function(){t.controller.abort()})}var el=null,Af=0,Ks=0,Qs=null;function Gy(t,n){if(el===null){var a=el=[];Af=0,Ks=Rd(),Qs={status:"pending",value:void 0,then:function(o){a.push(o)}}}return Af++,n.then(Gm,Gm),n}function Gm(){if(--Af===0&&el!==null){Qs!==null&&(Qs.status="fulfilled");var t=el;el=null,Ks=0,Qs=null;for(var n=0;n<t.length;n++)(0,t[n])()}}function Vy(t,n){var a=[],o={status:"pending",value:null,reason:null,then:function(u){a.push(u)}};return t.then(function(){o.status="fulfilled",o.value=n;for(var u=0;u<a.length;u++)(0,a[u])(n)},function(u){for(o.status="rejected",o.reason=u,u=0;u<a.length;u++)(0,a[u])(void 0)}),o}var Vm=B.S;B.S=function(t,n){Tg=Ft(),typeof n=="object"&&n!==null&&typeof n.then=="function"&&Gy(t,n),Vm!==null&&Vm(t,n)};var gs=D(null);function wf(){var t=gs.current;return t!==null?t:xn.pooledCache}function uc(t,n){n===null?_e(gs,gs.current):_e(gs,n.pool)}function km(){var t=wf();return t===null?null:{parent:Hn._currentValue,pool:t}}var Js=Error(s(460)),Cf=Error(s(474)),fc=Error(s(542)),dc={then:function(){}};function Xm(t){return t=t.status,t==="fulfilled"||t==="rejected"}function Wm(t,n,a){switch(a=t[a],a===void 0?t.push(n):a!==n&&(n.then(yi,yi),n=a),n.status){case"fulfilled":return n.value;case"rejected":throw t=n.reason,Ym(t),t;default:if(typeof n.status=="string")n.then(yi,yi);else{if(t=xn,t!==null&&100<t.shellSuspendCounter)throw Error(s(482));t=n,t.status="pending",t.then(function(o){if(n.status==="pending"){var u=n;u.status="fulfilled",u.value=o}},function(o){if(n.status==="pending"){var u=n;u.status="rejected",u.reason=o}})}switch(n.status){case"fulfilled":return n.value;case"rejected":throw t=n.reason,Ym(t),t}throw vs=n,Js}}function xs(t){try{var n=t._init;return n(t._payload)}catch(a){throw a!==null&&typeof a=="object"&&typeof a.then=="function"?(vs=a,Js):a}}var vs=null;function qm(){if(vs===null)throw Error(s(459));var t=vs;return vs=null,t}function Ym(t){if(t===Js||t===fc)throw Error(s(483))}var $s=null,tl=0;function hc(t){var n=tl;return tl+=1,$s===null&&($s=[]),Wm($s,t,n)}function nl(t,n){n=n.props.ref,t.ref=n!==void 0?n:null}function pc(t,n){throw n.$$typeof===x?Error(s(525)):(t=Object.prototype.toString.call(n),Error(s(31,t==="[object Object]"?"object with keys {"+Object.keys(n).join(", ")+"}":t)))}function jm(t){function n($,Y){if(t){var de=$.deletions;de===null?($.deletions=[Y],$.flags|=16):de.push(Y)}}function a($,Y){if(!t)return null;for(;Y!==null;)n($,Y),Y=Y.sibling;return null}function o($){for(var Y=new Map;$!==null;)$.key!==null?Y.set($.key,$):Y.set($.index,$),$=$.sibling;return Y}function u($,Y){return $=Ka($,Y),$.index=0,$.sibling=null,$}function d($,Y,de){return $.index=de,t?(de=$.alternate,de!==null?(de=de.index,de<Y?($.flags|=67108866,Y):de):($.flags|=67108866,Y)):($.flags|=1048576,Y)}function y($){return t&&$.alternate===null&&($.flags|=67108866),$}function C($,Y,de,Ee){return Y===null||Y.tag!==6?(Y=gf(de,$.mode,Ee),Y.return=$,Y):(Y=u(Y,de),Y.return=$,Y)}function H($,Y,de,Ee){var ct=de.type;return ct===R?Me($,Y,de.props.children,Ee,de.key):Y!==null&&(Y.elementType===ct||typeof ct=="object"&&ct!==null&&ct.$$typeof===T&&xs(ct)===Y.type)?(Y=u(Y,de.props),nl(Y,de),Y.return=$,Y):(Y=sc(de.type,de.key,de.props,null,$.mode,Ee),nl(Y,de),Y.return=$,Y)}function he($,Y,de,Ee){return Y===null||Y.tag!==4||Y.stateNode.containerInfo!==de.containerInfo||Y.stateNode.implementation!==de.implementation?(Y=xf(de,$.mode,Ee),Y.return=$,Y):(Y=u(Y,de.children||[]),Y.return=$,Y)}function Me($,Y,de,Ee,ct){return Y===null||Y.tag!==7?(Y=ds(de,$.mode,Ee,ct),Y.return=$,Y):(Y=u(Y,de),Y.return=$,Y)}function Te($,Y,de){if(typeof Y=="string"&&Y!==""||typeof Y=="number"||typeof Y=="bigint")return Y=gf(""+Y,$.mode,de),Y.return=$,Y;if(typeof Y=="object"&&Y!==null){switch(Y.$$typeof){case _:return de=sc(Y.type,Y.key,Y.props,null,$.mode,de),nl(de,Y),de.return=$,de;case E:return Y=xf(Y,$.mode,de),Y.return=$,Y;case T:return Y=xs(Y),Te($,Y,de)}if(K(Y)||J(Y))return Y=ds(Y,$.mode,de,null),Y.return=$,Y;if(typeof Y.then=="function")return Te($,hc(Y),de);if(Y.$$typeof===G)return Te($,cc($,Y),de);pc($,Y)}return null}function me($,Y,de,Ee){var ct=Y!==null?Y.key:null;if(typeof de=="string"&&de!==""||typeof de=="number"||typeof de=="bigint")return ct!==null?null:C($,Y,""+de,Ee);if(typeof de=="object"&&de!==null){switch(de.$$typeof){case _:return de.key===ct?H($,Y,de,Ee):null;case E:return de.key===ct?he($,Y,de,Ee):null;case T:return de=xs(de),me($,Y,de,Ee)}if(K(de)||J(de))return ct!==null?null:Me($,Y,de,Ee,null);if(typeof de.then=="function")return me($,Y,hc(de),Ee);if(de.$$typeof===G)return me($,Y,cc($,de),Ee);pc($,de)}return null}function ve($,Y,de,Ee,ct){if(typeof Ee=="string"&&Ee!==""||typeof Ee=="number"||typeof Ee=="bigint")return $=$.get(de)||null,C(Y,$,""+Ee,ct);if(typeof Ee=="object"&&Ee!==null){switch(Ee.$$typeof){case _:return $=$.get(Ee.key===null?de:Ee.key)||null,H(Y,$,Ee,ct);case E:return $=$.get(Ee.key===null?de:Ee.key)||null,he(Y,$,Ee,ct);case T:return Ee=xs(Ee),ve($,Y,de,Ee,ct)}if(K(Ee)||J(Ee))return $=$.get(de)||null,Me(Y,$,Ee,ct,null);if(typeof Ee.then=="function")return ve($,Y,de,hc(Ee),ct);if(Ee.$$typeof===G)return ve($,Y,de,cc(Y,Ee),ct);pc(Y,Ee)}return null}function tt($,Y,de,Ee){for(var ct=null,Jt=null,ot=Y,Ct=Y=0,Ht=null;ot!==null&&Ct<de.length;Ct++){ot.index>Ct?(Ht=ot,ot=null):Ht=ot.sibling;var $t=me($,ot,de[Ct],Ee);if($t===null){ot===null&&(ot=Ht);break}t&&ot&&$t.alternate===null&&n($,ot),Y=d($t,Y,Ct),Jt===null?ct=$t:Jt.sibling=$t,Jt=$t,ot=Ht}if(Ct===de.length)return a($,ot),Vt&&Qa($,Ct),ct;if(ot===null){for(;Ct<de.length;Ct++)ot=Te($,de[Ct],Ee),ot!==null&&(Y=d(ot,Y,Ct),Jt===null?ct=ot:Jt.sibling=ot,Jt=ot);return Vt&&Qa($,Ct),ct}for(ot=o(ot);Ct<de.length;Ct++)Ht=ve(ot,$,Ct,de[Ct],Ee),Ht!==null&&(t&&Ht.alternate!==null&&ot.delete(Ht.key===null?Ct:Ht.key),Y=d(Ht,Y,Ct),Jt===null?ct=Ht:Jt.sibling=Ht,Jt=Ht);return t&&ot.forEach(function(Zr){return n($,Zr)}),Vt&&Qa($,Ct),ct}function ft($,Y,de,Ee){if(de==null)throw Error(s(151));for(var ct=null,Jt=null,ot=Y,Ct=Y=0,Ht=null,$t=de.next();ot!==null&&!$t.done;Ct++,$t=de.next()){ot.index>Ct?(Ht=ot,ot=null):Ht=ot.sibling;var Zr=me($,ot,$t.value,Ee);if(Zr===null){ot===null&&(ot=Ht);break}t&&ot&&Zr.alternate===null&&n($,ot),Y=d(Zr,Y,Ct),Jt===null?ct=Zr:Jt.sibling=Zr,Jt=Zr,ot=Ht}if($t.done)return a($,ot),Vt&&Qa($,Ct),ct;if(ot===null){for(;!$t.done;Ct++,$t=de.next())$t=Te($,$t.value,Ee),$t!==null&&(Y=d($t,Y,Ct),Jt===null?ct=$t:Jt.sibling=$t,Jt=$t);return Vt&&Qa($,Ct),ct}for(ot=o(ot);!$t.done;Ct++,$t=de.next())$t=ve(ot,$,Ct,$t.value,Ee),$t!==null&&(t&&$t.alternate!==null&&ot.delete($t.key===null?Ct:$t.key),Y=d($t,Y,Ct),Jt===null?ct=$t:Jt.sibling=$t,Jt=$t);return t&&ot.forEach(function($S){return n($,$S)}),Vt&&Qa($,Ct),ct}function mn($,Y,de,Ee){if(typeof de=="object"&&de!==null&&de.type===R&&de.key===null&&(de=de.props.children),typeof de=="object"&&de!==null){switch(de.$$typeof){case _:e:{for(var ct=de.key;Y!==null;){if(Y.key===ct){if(ct=de.type,ct===R){if(Y.tag===7){a($,Y.sibling),Ee=u(Y,de.props.children),Ee.return=$,$=Ee;break e}}else if(Y.elementType===ct||typeof ct=="object"&&ct!==null&&ct.$$typeof===T&&xs(ct)===Y.type){a($,Y.sibling),Ee=u(Y,de.props),nl(Ee,de),Ee.return=$,$=Ee;break e}a($,Y);break}else n($,Y);Y=Y.sibling}de.type===R?(Ee=ds(de.props.children,$.mode,Ee,de.key),Ee.return=$,$=Ee):(Ee=sc(de.type,de.key,de.props,null,$.mode,Ee),nl(Ee,de),Ee.return=$,$=Ee)}return y($);case E:e:{for(ct=de.key;Y!==null;){if(Y.key===ct)if(Y.tag===4&&Y.stateNode.containerInfo===de.containerInfo&&Y.stateNode.implementation===de.implementation){a($,Y.sibling),Ee=u(Y,de.children||[]),Ee.return=$,$=Ee;break e}else{a($,Y);break}else n($,Y);Y=Y.sibling}Ee=xf(de,$.mode,Ee),Ee.return=$,$=Ee}return y($);case T:return de=xs(de),mn($,Y,de,Ee)}if(K(de))return tt($,Y,de,Ee);if(J(de)){if(ct=J(de),typeof ct!="function")throw Error(s(150));return de=ct.call(de),ft($,Y,de,Ee)}if(typeof de.then=="function")return mn($,Y,hc(de),Ee);if(de.$$typeof===G)return mn($,Y,cc($,de),Ee);pc($,de)}return typeof de=="string"&&de!==""||typeof de=="number"||typeof de=="bigint"?(de=""+de,Y!==null&&Y.tag===6?(a($,Y.sibling),Ee=u(Y,de),Ee.return=$,$=Ee):(a($,Y),Ee=gf(de,$.mode,Ee),Ee.return=$,$=Ee),y($)):a($,Y)}return function($,Y,de,Ee){try{tl=0;var ct=mn($,Y,de,Ee);return $s=null,ct}catch(ot){if(ot===Js||ot===fc)throw ot;var Jt=Ii(29,ot,null,$.mode);return Jt.lanes=Ee,Jt.return=$,Jt}finally{}}}var _s=jm(!0),Zm=jm(!1),Nr=!1;function Rf(t){t.updateQueue={baseState:t.memoizedState,firstBaseUpdate:null,lastBaseUpdate:null,shared:{pending:null,lanes:0,hiddenCallbacks:null},callbacks:null}}function Uf(t,n){t=t.updateQueue,n.updateQueue===t&&(n.updateQueue={baseState:t.baseState,firstBaseUpdate:t.firstBaseUpdate,lastBaseUpdate:t.lastBaseUpdate,shared:t.shared,callbacks:null})}function Lr(t){return{lane:t,tag:0,payload:null,callback:null,next:null}}function Or(t,n,a){var o=t.updateQueue;if(o===null)return null;if(o=o.shared,(an&2)!==0){var u=o.pending;return u===null?n.next=n:(n.next=u.next,u.next=n),o.pending=n,n=rc(t),Nm(t,null,a),n}return ac(t,o,n,a),rc(t)}function il(t,n,a){if(n=n.updateQueue,n!==null&&(n=n.shared,(a&4194048)!==0)){var o=n.lanes;o&=t.pendingLanes,a|=o,n.lanes=a,ei(t,a)}}function Df(t,n){var a=t.updateQueue,o=t.alternate;if(o!==null&&(o=o.updateQueue,a===o)){var u=null,d=null;if(a=a.firstBaseUpdate,a!==null){do{var y={lane:a.lane,tag:a.tag,payload:a.payload,callback:null,next:null};d===null?u=d=y:d=d.next=y,a=a.next}while(a!==null);d===null?u=d=n:d=d.next=n}else u=d=n;a={baseState:o.baseState,firstBaseUpdate:u,lastBaseUpdate:d,shared:o.shared,callbacks:o.callbacks},t.updateQueue=a;return}t=a.lastBaseUpdate,t===null?a.firstBaseUpdate=n:t.next=n,a.lastBaseUpdate=n}var Nf=!1;function al(){if(Nf){var t=Qs;if(t!==null)throw t}}function rl(t,n,a,o){Nf=!1;var u=t.updateQueue;Nr=!1;var d=u.firstBaseUpdate,y=u.lastBaseUpdate,C=u.shared.pending;if(C!==null){u.shared.pending=null;var H=C,he=H.next;H.next=null,y===null?d=he:y.next=he,y=H;var Me=t.alternate;Me!==null&&(Me=Me.updateQueue,C=Me.lastBaseUpdate,C!==y&&(C===null?Me.firstBaseUpdate=he:C.next=he,Me.lastBaseUpdate=H))}if(d!==null){var Te=u.baseState;y=0,Me=he=H=null,C=d;do{var me=C.lane&-536870913,ve=me!==C.lane;if(ve?(It&me)===me:(o&me)===me){me!==0&&me===Ks&&(Nf=!0),Me!==null&&(Me=Me.next={lane:0,tag:C.tag,payload:C.payload,callback:null,next:null});e:{var tt=t,ft=C;me=n;var mn=a;switch(ft.tag){case 1:if(tt=ft.payload,typeof tt=="function"){Te=tt.call(mn,Te,me);break e}Te=tt;break e;case 3:tt.flags=tt.flags&-65537|128;case 0:if(tt=ft.payload,me=typeof tt=="function"?tt.call(mn,Te,me):tt,me==null)break e;Te=v({},Te,me);break e;case 2:Nr=!0}}me=C.callback,me!==null&&(t.flags|=64,ve&&(t.flags|=8192),ve=u.callbacks,ve===null?u.callbacks=[me]:ve.push(me))}else ve={lane:me,tag:C.tag,payload:C.payload,callback:C.callback,next:null},Me===null?(he=Me=ve,H=Te):Me=Me.next=ve,y|=me;if(C=C.next,C===null){if(C=u.shared.pending,C===null)break;ve=C,C=ve.next,ve.next=null,u.lastBaseUpdate=ve,u.shared.pending=null}}while(!0);Me===null&&(H=Te),u.baseState=H,u.firstBaseUpdate=he,u.lastBaseUpdate=Me,d===null&&(u.shared.lanes=0),Ir|=y,t.lanes=y,t.memoizedState=Te}}function Km(t,n){if(typeof t!="function")throw Error(s(191,t));t.call(n)}function Qm(t,n){var a=t.callbacks;if(a!==null)for(t.callbacks=null,t=0;t<a.length;t++)Km(a[t],n)}var eo=D(null),mc=D(0);function Jm(t,n){t=lr,_e(mc,t),_e(eo,n),lr=t|n.baseLanes}function Lf(){_e(mc,lr),_e(eo,eo.current)}function Of(){lr=mc.current,se(eo),se(mc)}var Hi=D(null),sa=null;function Pr(t){var n=t.alternate;_e(Pn,Pn.current&1),_e(Hi,t),sa===null&&(n===null||eo.current!==null||n.memoizedState!==null)&&(sa=t)}function Pf(t){_e(Pn,Pn.current),_e(Hi,t),sa===null&&(sa=t)}function $m(t){t.tag===22?(_e(Pn,Pn.current),_e(Hi,t),sa===null&&(sa=t)):zr()}function zr(){_e(Pn,Pn.current),_e(Hi,Hi.current)}function Gi(t){se(Hi),sa===t&&(sa=null),se(Pn)}var Pn=D(0);function gc(t){for(var n=t;n!==null;){if(n.tag===13){var a=n.memoizedState;if(a!==null&&(a=a.dehydrated,a===null||Gd(a)||Vd(a)))return n}else if(n.tag===19&&(n.memoizedProps.revealOrder==="forwards"||n.memoizedProps.revealOrder==="backwards"||n.memoizedProps.revealOrder==="unstable_legacy-backwards"||n.memoizedProps.revealOrder==="together")){if((n.flags&128)!==0)return n}else if(n.child!==null){n.child.return=n,n=n.child;continue}if(n===t)break;for(;n.sibling===null;){if(n.return===null||n.return===t)return null;n=n.return}n.sibling.return=n.return,n=n.sibling}return null}var er=0,At=null,hn=null,Gn=null,xc=!1,to=!1,ys=!1,vc=0,sl=0,no=null,ky=0;function Dn(){throw Error(s(321))}function zf(t,n){if(n===null)return!1;for(var a=0;a<n.length&&a<t.length;a++)if(!Bi(t[a],n[a]))return!1;return!0}function Ff(t,n,a,o,u,d){return er=d,At=n,n.memoizedState=null,n.updateQueue=null,n.lanes=0,B.H=t===null||t.memoizedState===null?z0:Jf,ys=!1,d=a(o,u),ys=!1,to&&(d=t0(n,a,o,u)),e0(t),d}function e0(t){B.H=cl;var n=hn!==null&&hn.next!==null;if(er=0,Gn=hn=At=null,xc=!1,sl=0,no=null,n)throw Error(s(300));t===null||Vn||(t=t.dependencies,t!==null&&lc(t)&&(Vn=!0))}function t0(t,n,a,o){At=t;var u=0;do{if(to&&(no=null),sl=0,to=!1,25<=u)throw Error(s(301));if(u+=1,Gn=hn=null,t.updateQueue!=null){var d=t.updateQueue;d.lastEffect=null,d.events=null,d.stores=null,d.memoCache!=null&&(d.memoCache.index=0)}B.H=F0,d=n(a,o)}while(to);return d}function Xy(){var t=B.H,n=t.useState()[0];return n=typeof n.then=="function"?ol(n):n,t=t.useState()[0],(hn!==null?hn.memoizedState:null)!==t&&(At.flags|=1024),n}function Bf(){var t=vc!==0;return vc=0,t}function If(t,n,a){n.updateQueue=t.updateQueue,n.flags&=-2053,t.lanes&=~a}function Hf(t){if(xc){for(t=t.memoizedState;t!==null;){var n=t.queue;n!==null&&(n.pending=null),t=t.next}xc=!1}er=0,Gn=hn=At=null,to=!1,sl=vc=0,no=null}function Si(){var t={memoizedState:null,baseState:null,baseQueue:null,queue:null,next:null};return Gn===null?At.memoizedState=Gn=t:Gn=Gn.next=t,Gn}function zn(){if(hn===null){var t=At.alternate;t=t!==null?t.memoizedState:null}else t=hn.next;var n=Gn===null?At.memoizedState:Gn.next;if(n!==null)Gn=n,hn=t;else{if(t===null)throw At.alternate===null?Error(s(467)):Error(s(310));hn=t,t={memoizedState:hn.memoizedState,baseState:hn.baseState,baseQueue:hn.baseQueue,queue:hn.queue,next:null},Gn===null?At.memoizedState=Gn=t:Gn=Gn.next=t}return Gn}function _c(){return{lastEffect:null,events:null,stores:null,memoCache:null}}function ol(t){var n=sl;return sl+=1,no===null&&(no=[]),t=Wm(no,t,n),n=At,(Gn===null?n.memoizedState:Gn.next)===null&&(n=n.alternate,B.H=n===null||n.memoizedState===null?z0:Jf),t}function yc(t){if(t!==null&&typeof t=="object"){if(typeof t.then=="function")return ol(t);if(t.$$typeof===G)return ri(t)}throw Error(s(438,String(t)))}function Gf(t){var n=null,a=At.updateQueue;if(a!==null&&(n=a.memoCache),n==null){var o=At.alternate;o!==null&&(o=o.updateQueue,o!==null&&(o=o.memoCache,o!=null&&(n={data:o.data.map(function(u){return u.slice()}),index:0})))}if(n==null&&(n={data:[],index:0}),a===null&&(a=_c(),At.updateQueue=a),a.memoCache=n,a=n.data[n.index],a===void 0)for(a=n.data[n.index]=Array(t),o=0;o<t;o++)a[o]=I;return n.index++,a}function tr(t,n){return typeof n=="function"?n(t):n}function Sc(t){var n=zn();return Vf(n,hn,t)}function Vf(t,n,a){var o=t.queue;if(o===null)throw Error(s(311));o.lastRenderedReducer=a;var u=t.baseQueue,d=o.pending;if(d!==null){if(u!==null){var y=u.next;u.next=d.next,d.next=y}n.baseQueue=u=d,o.pending=null}if(d=t.baseState,u===null)t.memoizedState=d;else{n=u.next;var C=y=null,H=null,he=n,Me=!1;do{var Te=he.lane&-536870913;if(Te!==he.lane?(It&Te)===Te:(er&Te)===Te){var me=he.revertLane;if(me===0)H!==null&&(H=H.next={lane:0,revertLane:0,gesture:null,action:he.action,hasEagerState:he.hasEagerState,eagerState:he.eagerState,next:null}),Te===Ks&&(Me=!0);else if((er&me)===me){he=he.next,me===Ks&&(Me=!0);continue}else Te={lane:0,revertLane:he.revertLane,gesture:null,action:he.action,hasEagerState:he.hasEagerState,eagerState:he.eagerState,next:null},H===null?(C=H=Te,y=d):H=H.next=Te,At.lanes|=me,Ir|=me;Te=he.action,ys&&a(d,Te),d=he.hasEagerState?he.eagerState:a(d,Te)}else me={lane:Te,revertLane:he.revertLane,gesture:he.gesture,action:he.action,hasEagerState:he.hasEagerState,eagerState:he.eagerState,next:null},H===null?(C=H=me,y=d):H=H.next=me,At.lanes|=Te,Ir|=Te;he=he.next}while(he!==null&&he!==n);if(H===null?y=d:H.next=C,!Bi(d,t.memoizedState)&&(Vn=!0,Me&&(a=Qs,a!==null)))throw a;t.memoizedState=d,t.baseState=y,t.baseQueue=H,o.lastRenderedState=d}return u===null&&(o.lanes=0),[t.memoizedState,o.dispatch]}function kf(t){var n=zn(),a=n.queue;if(a===null)throw Error(s(311));a.lastRenderedReducer=t;var o=a.dispatch,u=a.pending,d=n.memoizedState;if(u!==null){a.pending=null;var y=u=u.next;do d=t(d,y.action),y=y.next;while(y!==u);Bi(d,n.memoizedState)||(Vn=!0),n.memoizedState=d,n.baseQueue===null&&(n.baseState=d),a.lastRenderedState=d}return[d,o]}function n0(t,n,a){var o=At,u=zn(),d=Vt;if(d){if(a===void 0)throw Error(s(407));a=a()}else a=n();var y=!Bi((hn||u).memoizedState,a);if(y&&(u.memoizedState=a,Vn=!0),u=u.queue,qf(r0.bind(null,o,u,t),[t]),u.getSnapshot!==n||y||Gn!==null&&Gn.memoizedState.tag&1){if(o.flags|=2048,io(9,{destroy:void 0},a0.bind(null,o,u,a,n),null),xn===null)throw Error(s(349));d||(er&127)!==0||i0(o,n,a)}return a}function i0(t,n,a){t.flags|=16384,t={getSnapshot:n,value:a},n=At.updateQueue,n===null?(n=_c(),At.updateQueue=n,n.stores=[t]):(a=n.stores,a===null?n.stores=[t]:a.push(t))}function a0(t,n,a,o){n.value=a,n.getSnapshot=o,s0(n)&&o0(t)}function r0(t,n,a){return a(function(){s0(n)&&o0(t)})}function s0(t){var n=t.getSnapshot;t=t.value;try{var a=n();return!Bi(t,a)}catch{return!0}}function o0(t){var n=fs(t,2);n!==null&&Li(n,t,2)}function Xf(t){var n=Si();if(typeof t=="function"){var a=t;if(t=a(),ys){Ne(!0);try{a()}finally{Ne(!1)}}}return n.memoizedState=n.baseState=t,n.queue={pending:null,lanes:0,dispatch:null,lastRenderedReducer:tr,lastRenderedState:t},n}function l0(t,n,a,o){return t.baseState=a,Vf(t,hn,typeof o=="function"?o:tr)}function Wy(t,n,a,o,u){if(Ec(t))throw Error(s(485));if(t=n.action,t!==null){var d={payload:u,action:t,next:null,isTransition:!0,status:"pending",value:null,reason:null,listeners:[],then:function(y){d.listeners.push(y)}};B.T!==null?a(!0):d.isTransition=!1,o(d),a=n.pending,a===null?(d.next=n.pending=d,c0(n,d)):(d.next=a.next,n.pending=a.next=d)}}function c0(t,n){var a=n.action,o=n.payload,u=t.state;if(n.isTransition){var d=B.T,y={};B.T=y;try{var C=a(u,o),H=B.S;H!==null&&H(y,C),u0(t,n,C)}catch(he){Wf(t,n,he)}finally{d!==null&&y.types!==null&&(d.types=y.types),B.T=d}}else try{d=a(u,o),u0(t,n,d)}catch(he){Wf(t,n,he)}}function u0(t,n,a){a!==null&&typeof a=="object"&&typeof a.then=="function"?a.then(function(o){f0(t,n,o)},function(o){return Wf(t,n,o)}):f0(t,n,a)}function f0(t,n,a){n.status="fulfilled",n.value=a,d0(n),t.state=a,n=t.pending,n!==null&&(a=n.next,a===n?t.pending=null:(a=a.next,n.next=a,c0(t,a)))}function Wf(t,n,a){var o=t.pending;if(t.pending=null,o!==null){o=o.next;do n.status="rejected",n.reason=a,d0(n),n=n.next;while(n!==o)}t.action=null}function d0(t){t=t.listeners;for(var n=0;n<t.length;n++)(0,t[n])()}function h0(t,n){return n}function p0(t,n){if(Vt){var a=xn.formState;if(a!==null){e:{var o=At;if(Vt){if(_n){t:{for(var u=_n,d=ra;u.nodeType!==8;){if(!d){u=null;break t}if(u=oa(u.nextSibling),u===null){u=null;break t}}d=u.data,u=d==="F!"||d==="F"?u:null}if(u){_n=oa(u.nextSibling),o=u.data==="F!";break e}}Ur(o)}o=!1}o&&(n=a[0])}}return a=Si(),a.memoizedState=a.baseState=n,o={pending:null,lanes:0,dispatch:null,lastRenderedReducer:h0,lastRenderedState:n},a.queue=o,a=L0.bind(null,At,o),o.dispatch=a,o=Xf(!1),d=Qf.bind(null,At,!1,o.queue),o=Si(),u={state:n,dispatch:null,action:t,pending:null},o.queue=u,a=Wy.bind(null,At,u,d,a),u.dispatch=a,o.memoizedState=t,[n,a,!1]}function m0(t){var n=zn();return g0(n,hn,t)}function g0(t,n,a){if(n=Vf(t,n,h0)[0],t=Sc(tr)[0],typeof n=="object"&&n!==null&&typeof n.then=="function")try{var o=ol(n)}catch(y){throw y===Js?fc:y}else o=n;n=zn();var u=n.queue,d=u.dispatch;return a!==n.memoizedState&&(At.flags|=2048,io(9,{destroy:void 0},qy.bind(null,u,a),null)),[o,d,t]}function qy(t,n){t.action=n}function x0(t){var n=zn(),a=hn;if(a!==null)return g0(n,a,t);zn(),n=n.memoizedState,a=zn();var o=a.queue.dispatch;return a.memoizedState=t,[n,o,!1]}function io(t,n,a,o){return t={tag:t,create:a,deps:o,inst:n,next:null},n=At.updateQueue,n===null&&(n=_c(),At.updateQueue=n),a=n.lastEffect,a===null?n.lastEffect=t.next=t:(o=a.next,a.next=t,t.next=o,n.lastEffect=t),t}function v0(){return zn().memoizedState}function bc(t,n,a,o){var u=Si();At.flags|=t,u.memoizedState=io(1|n,{destroy:void 0},a,o===void 0?null:o)}function Mc(t,n,a,o){var u=zn();o=o===void 0?null:o;var d=u.memoizedState.inst;hn!==null&&o!==null&&zf(o,hn.memoizedState.deps)?u.memoizedState=io(n,d,a,o):(At.flags|=t,u.memoizedState=io(1|n,d,a,o))}function _0(t,n){bc(8390656,8,t,n)}function qf(t,n){Mc(2048,8,t,n)}function Yy(t){At.flags|=4;var n=At.updateQueue;if(n===null)n=_c(),At.updateQueue=n,n.events=[t];else{var a=n.events;a===null?n.events=[t]:a.push(t)}}function y0(t){var n=zn().memoizedState;return Yy({ref:n,nextImpl:t}),function(){if((an&2)!==0)throw Error(s(440));return n.impl.apply(void 0,arguments)}}function S0(t,n){return Mc(4,2,t,n)}function b0(t,n){return Mc(4,4,t,n)}function M0(t,n){if(typeof n=="function"){t=t();var a=n(t);return function(){typeof a=="function"?a():n(null)}}if(n!=null)return t=t(),n.current=t,function(){n.current=null}}function E0(t,n,a){a=a!=null?a.concat([t]):null,Mc(4,4,M0.bind(null,n,t),a)}function Yf(){}function T0(t,n){var a=zn();n=n===void 0?null:n;var o=a.memoizedState;return n!==null&&zf(n,o[1])?o[0]:(a.memoizedState=[t,n],t)}function A0(t,n){var a=zn();n=n===void 0?null:n;var o=a.memoizedState;if(n!==null&&zf(n,o[1]))return o[0];if(o=t(),ys){Ne(!0);try{t()}finally{Ne(!1)}}return a.memoizedState=[o,n],o}function jf(t,n,a){return a===void 0||(er&1073741824)!==0&&(It&261930)===0?t.memoizedState=n:(t.memoizedState=a,t=wg(),At.lanes|=t,Ir|=t,a)}function w0(t,n,a,o){return Bi(a,n)?a:eo.current!==null?(t=jf(t,a,o),Bi(t,n)||(Vn=!0),t):(er&42)===0||(er&1073741824)!==0&&(It&261930)===0?(Vn=!0,t.memoizedState=a):(t=wg(),At.lanes|=t,Ir|=t,n)}function C0(t,n,a,o,u){var d=V.p;V.p=d!==0&&8>d?d:8;var y=B.T,C={};B.T=C,Qf(t,!1,n,a);try{var H=u(),he=B.S;if(he!==null&&he(C,H),H!==null&&typeof H=="object"&&typeof H.then=="function"){var Me=Vy(H,o);ll(t,n,Me,Xi(t))}else ll(t,n,o,Xi(t))}catch(Te){ll(t,n,{then:function(){},status:"rejected",reason:Te},Xi())}finally{V.p=d,y!==null&&C.types!==null&&(y.types=C.types),B.T=y}}function jy(){}function Zf(t,n,a,o){if(t.tag!==5)throw Error(s(476));var u=R0(t).queue;C0(t,u,n,ee,a===null?jy:function(){return U0(t),a(o)})}function R0(t){var n=t.memoizedState;if(n!==null)return n;n={memoizedState:ee,baseState:ee,baseQueue:null,queue:{pending:null,lanes:0,dispatch:null,lastRenderedReducer:tr,lastRenderedState:ee},next:null};var a={};return n.next={memoizedState:a,baseState:a,baseQueue:null,queue:{pending:null,lanes:0,dispatch:null,lastRenderedReducer:tr,lastRenderedState:a},next:null},t.memoizedState=n,t=t.alternate,t!==null&&(t.memoizedState=n),n}function U0(t){var n=R0(t);n.next===null&&(n=t.alternate.memoizedState),ll(t,n.next.queue,{},Xi())}function Kf(){return ri(Tl)}function D0(){return zn().memoizedState}function N0(){return zn().memoizedState}function Zy(t){for(var n=t.return;n!==null;){switch(n.tag){case 24:case 3:var a=Xi();t=Lr(a);var o=Or(n,t,a);o!==null&&(Li(o,n,a),il(o,n,a)),n={cache:Tf()},t.payload=n;return}n=n.return}}function Ky(t,n,a){var o=Xi();a={lane:o,revertLane:0,gesture:null,action:a,hasEagerState:!1,eagerState:null,next:null},Ec(t)?O0(n,a):(a=pf(t,n,a,o),a!==null&&(Li(a,t,o),P0(a,n,o)))}function L0(t,n,a){var o=Xi();ll(t,n,a,o)}function ll(t,n,a,o){var u={lane:o,revertLane:0,gesture:null,action:a,hasEagerState:!1,eagerState:null,next:null};if(Ec(t))O0(n,u);else{var d=t.alternate;if(t.lanes===0&&(d===null||d.lanes===0)&&(d=n.lastRenderedReducer,d!==null))try{var y=n.lastRenderedState,C=d(y,a);if(u.hasEagerState=!0,u.eagerState=C,Bi(C,y))return ac(t,n,u,0),xn===null&&ic(),!1}catch{}finally{}if(a=pf(t,n,u,o),a!==null)return Li(a,t,o),P0(a,n,o),!0}return!1}function Qf(t,n,a,o){if(o={lane:2,revertLane:Rd(),gesture:null,action:o,hasEagerState:!1,eagerState:null,next:null},Ec(t)){if(n)throw Error(s(479))}else n=pf(t,a,o,2),n!==null&&Li(n,t,2)}function Ec(t){var n=t.alternate;return t===At||n!==null&&n===At}function O0(t,n){to=xc=!0;var a=t.pending;a===null?n.next=n:(n.next=a.next,a.next=n),t.pending=n}function P0(t,n,a){if((a&4194048)!==0){var o=n.lanes;o&=t.pendingLanes,a|=o,n.lanes=a,ei(t,a)}}var cl={readContext:ri,use:yc,useCallback:Dn,useContext:Dn,useEffect:Dn,useImperativeHandle:Dn,useLayoutEffect:Dn,useInsertionEffect:Dn,useMemo:Dn,useReducer:Dn,useRef:Dn,useState:Dn,useDebugValue:Dn,useDeferredValue:Dn,useTransition:Dn,useSyncExternalStore:Dn,useId:Dn,useHostTransitionStatus:Dn,useFormState:Dn,useActionState:Dn,useOptimistic:Dn,useMemoCache:Dn,useCacheRefresh:Dn};cl.useEffectEvent=Dn;var z0={readContext:ri,use:yc,useCallback:function(t,n){return Si().memoizedState=[t,n===void 0?null:n],t},useContext:ri,useEffect:_0,useImperativeHandle:function(t,n,a){a=a!=null?a.concat([t]):null,bc(4194308,4,M0.bind(null,n,t),a)},useLayoutEffect:function(t,n){return bc(4194308,4,t,n)},useInsertionEffect:function(t,n){bc(4,2,t,n)},useMemo:function(t,n){var a=Si();n=n===void 0?null:n;var o=t();if(ys){Ne(!0);try{t()}finally{Ne(!1)}}return a.memoizedState=[o,n],o},useReducer:function(t,n,a){var o=Si();if(a!==void 0){var u=a(n);if(ys){Ne(!0);try{a(n)}finally{Ne(!1)}}}else u=n;return o.memoizedState=o.baseState=u,t={pending:null,lanes:0,dispatch:null,lastRenderedReducer:t,lastRenderedState:u},o.queue=t,t=t.dispatch=Ky.bind(null,At,t),[o.memoizedState,t]},useRef:function(t){var n=Si();return t={current:t},n.memoizedState=t},useState:function(t){t=Xf(t);var n=t.queue,a=L0.bind(null,At,n);return n.dispatch=a,[t.memoizedState,a]},useDebugValue:Yf,useDeferredValue:function(t,n){var a=Si();return jf(a,t,n)},useTransition:function(){var t=Xf(!1);return t=C0.bind(null,At,t.queue,!0,!1),Si().memoizedState=t,[!1,t]},useSyncExternalStore:function(t,n,a){var o=At,u=Si();if(Vt){if(a===void 0)throw Error(s(407));a=a()}else{if(a=n(),xn===null)throw Error(s(349));(It&127)!==0||i0(o,n,a)}u.memoizedState=a;var d={value:a,getSnapshot:n};return u.queue=d,_0(r0.bind(null,o,d,t),[t]),o.flags|=2048,io(9,{destroy:void 0},a0.bind(null,o,d,a,n),null),a},useId:function(){var t=Si(),n=xn.identifierPrefix;if(Vt){var a=Pa,o=Oa;a=(o&~(1<<32-Ze(o)-1)).toString(32)+a,n="_"+n+"R_"+a,a=vc++,0<a&&(n+="H"+a.toString(32)),n+="_"}else a=ky++,n="_"+n+"r_"+a.toString(32)+"_";return t.memoizedState=n},useHostTransitionStatus:Kf,useFormState:p0,useActionState:p0,useOptimistic:function(t){var n=Si();n.memoizedState=n.baseState=t;var a={pending:null,lanes:0,dispatch:null,lastRenderedReducer:null,lastRenderedState:null};return n.queue=a,n=Qf.bind(null,At,!0,a),a.dispatch=n,[t,n]},useMemoCache:Gf,useCacheRefresh:function(){return Si().memoizedState=Zy.bind(null,At)},useEffectEvent:function(t){var n=Si(),a={impl:t};return n.memoizedState=a,function(){if((an&2)!==0)throw Error(s(440));return a.impl.apply(void 0,arguments)}}},Jf={readContext:ri,use:yc,useCallback:T0,useContext:ri,useEffect:qf,useImperativeHandle:E0,useInsertionEffect:S0,useLayoutEffect:b0,useMemo:A0,useReducer:Sc,useRef:v0,useState:function(){return Sc(tr)},useDebugValue:Yf,useDeferredValue:function(t,n){var a=zn();return w0(a,hn.memoizedState,t,n)},useTransition:function(){var t=Sc(tr)[0],n=zn().memoizedState;return[typeof t=="boolean"?t:ol(t),n]},useSyncExternalStore:n0,useId:D0,useHostTransitionStatus:Kf,useFormState:m0,useActionState:m0,useOptimistic:function(t,n){var a=zn();return l0(a,hn,t,n)},useMemoCache:Gf,useCacheRefresh:N0};Jf.useEffectEvent=y0;var F0={readContext:ri,use:yc,useCallback:T0,useContext:ri,useEffect:qf,useImperativeHandle:E0,useInsertionEffect:S0,useLayoutEffect:b0,useMemo:A0,useReducer:kf,useRef:v0,useState:function(){return kf(tr)},useDebugValue:Yf,useDeferredValue:function(t,n){var a=zn();return hn===null?jf(a,t,n):w0(a,hn.memoizedState,t,n)},useTransition:function(){var t=kf(tr)[0],n=zn().memoizedState;return[typeof t=="boolean"?t:ol(t),n]},useSyncExternalStore:n0,useId:D0,useHostTransitionStatus:Kf,useFormState:x0,useActionState:x0,useOptimistic:function(t,n){var a=zn();return hn!==null?l0(a,hn,t,n):(a.baseState=t,[t,a.queue.dispatch])},useMemoCache:Gf,useCacheRefresh:N0};F0.useEffectEvent=y0;function $f(t,n,a,o){n=t.memoizedState,a=a(o,n),a=a==null?n:v({},n,a),t.memoizedState=a,t.lanes===0&&(t.updateQueue.baseState=a)}var ed={enqueueSetState:function(t,n,a){t=t._reactInternals;var o=Xi(),u=Lr(o);u.payload=n,a!=null&&(u.callback=a),n=Or(t,u,o),n!==null&&(Li(n,t,o),il(n,t,o))},enqueueReplaceState:function(t,n,a){t=t._reactInternals;var o=Xi(),u=Lr(o);u.tag=1,u.payload=n,a!=null&&(u.callback=a),n=Or(t,u,o),n!==null&&(Li(n,t,o),il(n,t,o))},enqueueForceUpdate:function(t,n){t=t._reactInternals;var a=Xi(),o=Lr(a);o.tag=2,n!=null&&(o.callback=n),n=Or(t,o,a),n!==null&&(Li(n,t,a),il(n,t,a))}};function B0(t,n,a,o,u,d,y){return t=t.stateNode,typeof t.shouldComponentUpdate=="function"?t.shouldComponentUpdate(o,d,y):n.prototype&&n.prototype.isPureReactComponent?!Zo(a,o)||!Zo(u,d):!0}function I0(t,n,a,o){t=n.state,typeof n.componentWillReceiveProps=="function"&&n.componentWillReceiveProps(a,o),typeof n.UNSAFE_componentWillReceiveProps=="function"&&n.UNSAFE_componentWillReceiveProps(a,o),n.state!==t&&ed.enqueueReplaceState(n,n.state,null)}function Ss(t,n){var a=n;if("ref"in n){a={};for(var o in n)o!=="ref"&&(a[o]=n[o])}if(t=t.defaultProps){a===n&&(a=v({},a));for(var u in t)a[u]===void 0&&(a[u]=t[u])}return a}function H0(t){nc(t)}function G0(t){console.error(t)}function V0(t){nc(t)}function Tc(t,n){try{var a=t.onUncaughtError;a(n.value,{componentStack:n.stack})}catch(o){setTimeout(function(){throw o})}}function k0(t,n,a){try{var o=t.onCaughtError;o(a.value,{componentStack:a.stack,errorBoundary:n.tag===1?n.stateNode:null})}catch(u){setTimeout(function(){throw u})}}function td(t,n,a){return a=Lr(a),a.tag=3,a.payload={element:null},a.callback=function(){Tc(t,n)},a}function X0(t){return t=Lr(t),t.tag=3,t}function W0(t,n,a,o){var u=a.type.getDerivedStateFromError;if(typeof u=="function"){var d=o.value;t.payload=function(){return u(d)},t.callback=function(){k0(n,a,o)}}var y=a.stateNode;y!==null&&typeof y.componentDidCatch=="function"&&(t.callback=function(){k0(n,a,o),typeof u!="function"&&(Hr===null?Hr=new Set([this]):Hr.add(this));var C=o.stack;this.componentDidCatch(o.value,{componentStack:C!==null?C:""})})}function Qy(t,n,a,o,u){if(a.flags|=32768,o!==null&&typeof o=="object"&&typeof o.then=="function"){if(n=a.alternate,n!==null&&Zs(n,a,u,!0),a=Hi.current,a!==null){switch(a.tag){case 31:case 13:return sa===null?Fc():a.alternate===null&&Nn===0&&(Nn=3),a.flags&=-257,a.flags|=65536,a.lanes=u,o===dc?a.flags|=16384:(n=a.updateQueue,n===null?a.updateQueue=new Set([o]):n.add(o),Ad(t,o,u)),!1;case 22:return a.flags|=65536,o===dc?a.flags|=16384:(n=a.updateQueue,n===null?(n={transitions:null,markerInstances:null,retryQueue:new Set([o])},a.updateQueue=n):(a=n.retryQueue,a===null?n.retryQueue=new Set([o]):a.add(o)),Ad(t,o,u)),!1}throw Error(s(435,a.tag))}return Ad(t,o,u),Fc(),!1}if(Vt)return n=Hi.current,n!==null?((n.flags&65536)===0&&(n.flags|=256),n.flags|=65536,n.lanes=u,o!==yf&&(t=Error(s(422),{cause:o}),Jo(na(t,a)))):(o!==yf&&(n=Error(s(423),{cause:o}),Jo(na(n,a))),t=t.current.alternate,t.flags|=65536,u&=-u,t.lanes|=u,o=na(o,a),u=td(t.stateNode,o,u),Df(t,u),Nn!==4&&(Nn=2)),!1;var d=Error(s(520),{cause:o});if(d=na(d,a),xl===null?xl=[d]:xl.push(d),Nn!==4&&(Nn=2),n===null)return!0;o=na(o,a),a=n;do{switch(a.tag){case 3:return a.flags|=65536,t=u&-u,a.lanes|=t,t=td(a.stateNode,o,t),Df(a,t),!1;case 1:if(n=a.type,d=a.stateNode,(a.flags&128)===0&&(typeof n.getDerivedStateFromError=="function"||d!==null&&typeof d.componentDidCatch=="function"&&(Hr===null||!Hr.has(d))))return a.flags|=65536,u&=-u,a.lanes|=u,u=X0(u),W0(u,t,a,o),Df(a,u),!1}a=a.return}while(a!==null);return!1}var nd=Error(s(461)),Vn=!1;function si(t,n,a,o){n.child=t===null?Zm(n,null,a,o):_s(n,t.child,a,o)}function q0(t,n,a,o,u){a=a.render;var d=n.ref;if("ref"in o){var y={};for(var C in o)C!=="ref"&&(y[C]=o[C])}else y=o;return ms(n),o=Ff(t,n,a,y,d,u),C=Bf(),t!==null&&!Vn?(If(t,n,u),nr(t,n,u)):(Vt&&C&&vf(n),n.flags|=1,si(t,n,o,u),n.child)}function Y0(t,n,a,o,u){if(t===null){var d=a.type;return typeof d=="function"&&!mf(d)&&d.defaultProps===void 0&&a.compare===null?(n.tag=15,n.type=d,j0(t,n,d,o,u)):(t=sc(a.type,null,o,n,n.mode,u),t.ref=n.ref,t.return=n,n.child=t)}if(d=t.child,!ud(t,u)){var y=d.memoizedProps;if(a=a.compare,a=a!==null?a:Zo,a(y,o)&&t.ref===n.ref)return nr(t,n,u)}return n.flags|=1,t=Ka(d,o),t.ref=n.ref,t.return=n,n.child=t}function j0(t,n,a,o,u){if(t!==null){var d=t.memoizedProps;if(Zo(d,o)&&t.ref===n.ref)if(Vn=!1,n.pendingProps=o=d,ud(t,u))(t.flags&131072)!==0&&(Vn=!0);else return n.lanes=t.lanes,nr(t,n,u)}return id(t,n,a,o,u)}function Z0(t,n,a,o){var u=o.children,d=t!==null?t.memoizedState:null;if(t===null&&n.stateNode===null&&(n.stateNode={_visibility:1,_pendingMarkers:null,_retryCache:null,_transitions:null}),o.mode==="hidden"){if((n.flags&128)!==0){if(d=d!==null?d.baseLanes|a:a,t!==null){for(o=n.child=t.child,u=0;o!==null;)u=u|o.lanes|o.childLanes,o=o.sibling;o=u&~d}else o=0,n.child=null;return K0(t,n,d,a,o)}if((a&536870912)!==0)n.memoizedState={baseLanes:0,cachePool:null},t!==null&&uc(n,d!==null?d.cachePool:null),d!==null?Jm(n,d):Lf(),$m(n);else return o=n.lanes=536870912,K0(t,n,d!==null?d.baseLanes|a:a,a,o)}else d!==null?(uc(n,d.cachePool),Jm(n,d),zr(),n.memoizedState=null):(t!==null&&uc(n,null),Lf(),zr());return si(t,n,u,a),n.child}function ul(t,n){return t!==null&&t.tag===22||n.stateNode!==null||(n.stateNode={_visibility:1,_pendingMarkers:null,_retryCache:null,_transitions:null}),n.sibling}function K0(t,n,a,o,u){var d=wf();return d=d===null?null:{parent:Hn._currentValue,pool:d},n.memoizedState={baseLanes:a,cachePool:d},t!==null&&uc(n,null),Lf(),$m(n),t!==null&&Zs(t,n,o,!0),n.childLanes=u,null}function Ac(t,n){return n=Cc({mode:n.mode,children:n.children},t.mode),n.ref=t.ref,t.child=n,n.return=t,n}function Q0(t,n,a){return _s(n,t.child,null,a),t=Ac(n,n.pendingProps),t.flags|=2,Gi(n),n.memoizedState=null,t}function Jy(t,n,a){var o=n.pendingProps,u=(n.flags&128)!==0;if(n.flags&=-129,t===null){if(Vt){if(o.mode==="hidden")return t=Ac(n,o),n.lanes=536870912,ul(null,t);if(Pf(n),(t=_n)?(t=cx(t,ra),t=t!==null&&t.data==="&"?t:null,t!==null&&(n.memoizedState={dehydrated:t,treeContext:Cr!==null?{id:Oa,overflow:Pa}:null,retryLane:536870912,hydrationErrors:null},a=Om(t),a.return=n,n.child=a,ai=n,_n=null)):t=null,t===null)throw Ur(n);return n.lanes=536870912,null}return Ac(n,o)}var d=t.memoizedState;if(d!==null){var y=d.dehydrated;if(Pf(n),u)if(n.flags&256)n.flags&=-257,n=Q0(t,n,a);else if(n.memoizedState!==null)n.child=t.child,n.flags|=128,n=null;else throw Error(s(558));else if(Vn||Zs(t,n,a,!1),u=(a&t.childLanes)!==0,Vn||u){if(o=xn,o!==null&&(y=ti(o,a),y!==0&&y!==d.retryLane))throw d.retryLane=y,fs(t,y),Li(o,t,y),nd;Fc(),n=Q0(t,n,a)}else t=d.treeContext,_n=oa(y.nextSibling),ai=n,Vt=!0,Rr=null,ra=!1,t!==null&&Fm(n,t),n=Ac(n,o),n.flags|=4096;return n}return t=Ka(t.child,{mode:o.mode,children:o.children}),t.ref=n.ref,n.child=t,t.return=n,t}function wc(t,n){var a=n.ref;if(a===null)t!==null&&t.ref!==null&&(n.flags|=4194816);else{if(typeof a!="function"&&typeof a!="object")throw Error(s(284));(t===null||t.ref!==a)&&(n.flags|=4194816)}}function id(t,n,a,o,u){return ms(n),a=Ff(t,n,a,o,void 0,u),o=Bf(),t!==null&&!Vn?(If(t,n,u),nr(t,n,u)):(Vt&&o&&vf(n),n.flags|=1,si(t,n,a,u),n.child)}function J0(t,n,a,o,u,d){return ms(n),n.updateQueue=null,a=t0(n,o,a,u),e0(t),o=Bf(),t!==null&&!Vn?(If(t,n,d),nr(t,n,d)):(Vt&&o&&vf(n),n.flags|=1,si(t,n,a,d),n.child)}function $0(t,n,a,o,u){if(ms(n),n.stateNode===null){var d=Ws,y=a.contextType;typeof y=="object"&&y!==null&&(d=ri(y)),d=new a(o,d),n.memoizedState=d.state!==null&&d.state!==void 0?d.state:null,d.updater=ed,n.stateNode=d,d._reactInternals=n,d=n.stateNode,d.props=o,d.state=n.memoizedState,d.refs={},Rf(n),y=a.contextType,d.context=typeof y=="object"&&y!==null?ri(y):Ws,d.state=n.memoizedState,y=a.getDerivedStateFromProps,typeof y=="function"&&($f(n,a,y,o),d.state=n.memoizedState),typeof a.getDerivedStateFromProps=="function"||typeof d.getSnapshotBeforeUpdate=="function"||typeof d.UNSAFE_componentWillMount!="function"&&typeof d.componentWillMount!="function"||(y=d.state,typeof d.componentWillMount=="function"&&d.componentWillMount(),typeof d.UNSAFE_componentWillMount=="function"&&d.UNSAFE_componentWillMount(),y!==d.state&&ed.enqueueReplaceState(d,d.state,null),rl(n,o,d,u),al(),d.state=n.memoizedState),typeof d.componentDidMount=="function"&&(n.flags|=4194308),o=!0}else if(t===null){d=n.stateNode;var C=n.memoizedProps,H=Ss(a,C);d.props=H;var he=d.context,Me=a.contextType;y=Ws,typeof Me=="object"&&Me!==null&&(y=ri(Me));var Te=a.getDerivedStateFromProps;Me=typeof Te=="function"||typeof d.getSnapshotBeforeUpdate=="function",C=n.pendingProps!==C,Me||typeof d.UNSAFE_componentWillReceiveProps!="function"&&typeof d.componentWillReceiveProps!="function"||(C||he!==y)&&I0(n,d,o,y),Nr=!1;var me=n.memoizedState;d.state=me,rl(n,o,d,u),al(),he=n.memoizedState,C||me!==he||Nr?(typeof Te=="function"&&($f(n,a,Te,o),he=n.memoizedState),(H=Nr||B0(n,a,H,o,me,he,y))?(Me||typeof d.UNSAFE_componentWillMount!="function"&&typeof d.componentWillMount!="function"||(typeof d.componentWillMount=="function"&&d.componentWillMount(),typeof d.UNSAFE_componentWillMount=="function"&&d.UNSAFE_componentWillMount()),typeof d.componentDidMount=="function"&&(n.flags|=4194308)):(typeof d.componentDidMount=="function"&&(n.flags|=4194308),n.memoizedProps=o,n.memoizedState=he),d.props=o,d.state=he,d.context=y,o=H):(typeof d.componentDidMount=="function"&&(n.flags|=4194308),o=!1)}else{d=n.stateNode,Uf(t,n),y=n.memoizedProps,Me=Ss(a,y),d.props=Me,Te=n.pendingProps,me=d.context,he=a.contextType,H=Ws,typeof he=="object"&&he!==null&&(H=ri(he)),C=a.getDerivedStateFromProps,(he=typeof C=="function"||typeof d.getSnapshotBeforeUpdate=="function")||typeof d.UNSAFE_componentWillReceiveProps!="function"&&typeof d.componentWillReceiveProps!="function"||(y!==Te||me!==H)&&I0(n,d,o,H),Nr=!1,me=n.memoizedState,d.state=me,rl(n,o,d,u),al();var ve=n.memoizedState;y!==Te||me!==ve||Nr||t!==null&&t.dependencies!==null&&lc(t.dependencies)?(typeof C=="function"&&($f(n,a,C,o),ve=n.memoizedState),(Me=Nr||B0(n,a,Me,o,me,ve,H)||t!==null&&t.dependencies!==null&&lc(t.dependencies))?(he||typeof d.UNSAFE_componentWillUpdate!="function"&&typeof d.componentWillUpdate!="function"||(typeof d.componentWillUpdate=="function"&&d.componentWillUpdate(o,ve,H),typeof d.UNSAFE_componentWillUpdate=="function"&&d.UNSAFE_componentWillUpdate(o,ve,H)),typeof d.componentDidUpdate=="function"&&(n.flags|=4),typeof d.getSnapshotBeforeUpdate=="function"&&(n.flags|=1024)):(typeof d.componentDidUpdate!="function"||y===t.memoizedProps&&me===t.memoizedState||(n.flags|=4),typeof d.getSnapshotBeforeUpdate!="function"||y===t.memoizedProps&&me===t.memoizedState||(n.flags|=1024),n.memoizedProps=o,n.memoizedState=ve),d.props=o,d.state=ve,d.context=H,o=Me):(typeof d.componentDidUpdate!="function"||y===t.memoizedProps&&me===t.memoizedState||(n.flags|=4),typeof d.getSnapshotBeforeUpdate!="function"||y===t.memoizedProps&&me===t.memoizedState||(n.flags|=1024),o=!1)}return d=o,wc(t,n),o=(n.flags&128)!==0,d||o?(d=n.stateNode,a=o&&typeof a.getDerivedStateFromError!="function"?null:d.render(),n.flags|=1,t!==null&&o?(n.child=_s(n,t.child,null,u),n.child=_s(n,null,a,u)):si(t,n,a,u),n.memoizedState=d.state,t=n.child):t=nr(t,n,u),t}function eg(t,n,a,o){return hs(),n.flags|=256,si(t,n,a,o),n.child}var ad={dehydrated:null,treeContext:null,retryLane:0,hydrationErrors:null};function rd(t){return{baseLanes:t,cachePool:km()}}function sd(t,n,a){return t=t!==null?t.childLanes&~a:0,n&&(t|=ki),t}function tg(t,n,a){var o=n.pendingProps,u=!1,d=(n.flags&128)!==0,y;if((y=d)||(y=t!==null&&t.memoizedState===null?!1:(Pn.current&2)!==0),y&&(u=!0,n.flags&=-129),y=(n.flags&32)!==0,n.flags&=-33,t===null){if(Vt){if(u?Pr(n):zr(),(t=_n)?(t=cx(t,ra),t=t!==null&&t.data!=="&"?t:null,t!==null&&(n.memoizedState={dehydrated:t,treeContext:Cr!==null?{id:Oa,overflow:Pa}:null,retryLane:536870912,hydrationErrors:null},a=Om(t),a.return=n,n.child=a,ai=n,_n=null)):t=null,t===null)throw Ur(n);return Vd(t)?n.lanes=32:n.lanes=536870912,null}var C=o.children;return o=o.fallback,u?(zr(),u=n.mode,C=Cc({mode:"hidden",children:C},u),o=ds(o,u,a,null),C.return=n,o.return=n,C.sibling=o,n.child=C,o=n.child,o.memoizedState=rd(a),o.childLanes=sd(t,y,a),n.memoizedState=ad,ul(null,o)):(Pr(n),od(n,C))}var H=t.memoizedState;if(H!==null&&(C=H.dehydrated,C!==null)){if(d)n.flags&256?(Pr(n),n.flags&=-257,n=ld(t,n,a)):n.memoizedState!==null?(zr(),n.child=t.child,n.flags|=128,n=null):(zr(),C=o.fallback,u=n.mode,o=Cc({mode:"visible",children:o.children},u),C=ds(C,u,a,null),C.flags|=2,o.return=n,C.return=n,o.sibling=C,n.child=o,_s(n,t.child,null,a),o=n.child,o.memoizedState=rd(a),o.childLanes=sd(t,y,a),n.memoizedState=ad,n=ul(null,o));else if(Pr(n),Vd(C)){if(y=C.nextSibling&&C.nextSibling.dataset,y)var he=y.dgst;y=he,o=Error(s(419)),o.stack="",o.digest=y,Jo({value:o,source:null,stack:null}),n=ld(t,n,a)}else if(Vn||Zs(t,n,a,!1),y=(a&t.childLanes)!==0,Vn||y){if(y=xn,y!==null&&(o=ti(y,a),o!==0&&o!==H.retryLane))throw H.retryLane=o,fs(t,o),Li(y,t,o),nd;Gd(C)||Fc(),n=ld(t,n,a)}else Gd(C)?(n.flags|=192,n.child=t.child,n=null):(t=H.treeContext,_n=oa(C.nextSibling),ai=n,Vt=!0,Rr=null,ra=!1,t!==null&&Fm(n,t),n=od(n,o.children),n.flags|=4096);return n}return u?(zr(),C=o.fallback,u=n.mode,H=t.child,he=H.sibling,o=Ka(H,{mode:"hidden",children:o.children}),o.subtreeFlags=H.subtreeFlags&65011712,he!==null?C=Ka(he,C):(C=ds(C,u,a,null),C.flags|=2),C.return=n,o.return=n,o.sibling=C,n.child=o,ul(null,o),o=n.child,C=t.child.memoizedState,C===null?C=rd(a):(u=C.cachePool,u!==null?(H=Hn._currentValue,u=u.parent!==H?{parent:H,pool:H}:u):u=km(),C={baseLanes:C.baseLanes|a,cachePool:u}),o.memoizedState=C,o.childLanes=sd(t,y,a),n.memoizedState=ad,ul(t.child,o)):(Pr(n),a=t.child,t=a.sibling,a=Ka(a,{mode:"visible",children:o.children}),a.return=n,a.sibling=null,t!==null&&(y=n.deletions,y===null?(n.deletions=[t],n.flags|=16):y.push(t)),n.child=a,n.memoizedState=null,a)}function od(t,n){return n=Cc({mode:"visible",children:n},t.mode),n.return=t,t.child=n}function Cc(t,n){return t=Ii(22,t,null,n),t.lanes=0,t}function ld(t,n,a){return _s(n,t.child,null,a),t=od(n,n.pendingProps.children),t.flags|=2,n.memoizedState=null,t}function ng(t,n,a){t.lanes|=n;var o=t.alternate;o!==null&&(o.lanes|=n),Mf(t.return,n,a)}function cd(t,n,a,o,u,d){var y=t.memoizedState;y===null?t.memoizedState={isBackwards:n,rendering:null,renderingStartTime:0,last:o,tail:a,tailMode:u,treeForkCount:d}:(y.isBackwards=n,y.rendering=null,y.renderingStartTime=0,y.last=o,y.tail=a,y.tailMode=u,y.treeForkCount=d)}function ig(t,n,a){var o=n.pendingProps,u=o.revealOrder,d=o.tail;o=o.children;var y=Pn.current,C=(y&2)!==0;if(C?(y=y&1|2,n.flags|=128):y&=1,_e(Pn,y),si(t,n,o,a),o=Vt?Qo:0,!C&&t!==null&&(t.flags&128)!==0)e:for(t=n.child;t!==null;){if(t.tag===13)t.memoizedState!==null&&ng(t,a,n);else if(t.tag===19)ng(t,a,n);else if(t.child!==null){t.child.return=t,t=t.child;continue}if(t===n)break e;for(;t.sibling===null;){if(t.return===null||t.return===n)break e;t=t.return}t.sibling.return=t.return,t=t.sibling}switch(u){case"forwards":for(a=n.child,u=null;a!==null;)t=a.alternate,t!==null&&gc(t)===null&&(u=a),a=a.sibling;a=u,a===null?(u=n.child,n.child=null):(u=a.sibling,a.sibling=null),cd(n,!1,u,a,d,o);break;case"backwards":case"unstable_legacy-backwards":for(a=null,u=n.child,n.child=null;u!==null;){if(t=u.alternate,t!==null&&gc(t)===null){n.child=u;break}t=u.sibling,u.sibling=a,a=u,u=t}cd(n,!0,a,null,d,o);break;case"together":cd(n,!1,null,null,void 0,o);break;default:n.memoizedState=null}return n.child}function nr(t,n,a){if(t!==null&&(n.dependencies=t.dependencies),Ir|=n.lanes,(a&n.childLanes)===0)if(t!==null){if(Zs(t,n,a,!1),(a&n.childLanes)===0)return null}else return null;if(t!==null&&n.child!==t.child)throw Error(s(153));if(n.child!==null){for(t=n.child,a=Ka(t,t.pendingProps),n.child=a,a.return=n;t.sibling!==null;)t=t.sibling,a=a.sibling=Ka(t,t.pendingProps),a.return=n;a.sibling=null}return n.child}function ud(t,n){return(t.lanes&n)!==0?!0:(t=t.dependencies,!!(t!==null&&lc(t)))}function $y(t,n,a){switch(n.tag){case 3:Se(n,n.stateNode.containerInfo),Dr(n,Hn,t.memoizedState.cache),hs();break;case 27:case 5:at(n);break;case 4:Se(n,n.stateNode.containerInfo);break;case 10:Dr(n,n.type,n.memoizedProps.value);break;case 31:if(n.memoizedState!==null)return n.flags|=128,Pf(n),null;break;case 13:var o=n.memoizedState;if(o!==null)return o.dehydrated!==null?(Pr(n),n.flags|=128,null):(a&n.child.childLanes)!==0?tg(t,n,a):(Pr(n),t=nr(t,n,a),t!==null?t.sibling:null);Pr(n);break;case 19:var u=(t.flags&128)!==0;if(o=(a&n.childLanes)!==0,o||(Zs(t,n,a,!1),o=(a&n.childLanes)!==0),u){if(o)return ig(t,n,a);n.flags|=128}if(u=n.memoizedState,u!==null&&(u.rendering=null,u.tail=null,u.lastEffect=null),_e(Pn,Pn.current),o)break;return null;case 22:return n.lanes=0,Z0(t,n,a,n.pendingProps);case 24:Dr(n,Hn,t.memoizedState.cache)}return nr(t,n,a)}function ag(t,n,a){if(t!==null)if(t.memoizedProps!==n.pendingProps)Vn=!0;else{if(!ud(t,a)&&(n.flags&128)===0)return Vn=!1,$y(t,n,a);Vn=(t.flags&131072)!==0}else Vn=!1,Vt&&(n.flags&1048576)!==0&&zm(n,Qo,n.index);switch(n.lanes=0,n.tag){case 16:e:{var o=n.pendingProps;if(t=xs(n.elementType),n.type=t,typeof t=="function")mf(t)?(o=Ss(t,o),n.tag=1,n=$0(null,n,t,o,a)):(n.tag=0,n=id(null,n,t,o,a));else{if(t!=null){var u=t.$$typeof;if(u===w){n.tag=11,n=q0(null,n,t,o,a);break e}else if(u===z){n.tag=14,n=Y0(null,n,t,o,a);break e}}throw n=k(t)||t,Error(s(306,n,""))}}return n;case 0:return id(t,n,n.type,n.pendingProps,a);case 1:return o=n.type,u=Ss(o,n.pendingProps),$0(t,n,o,u,a);case 3:e:{if(Se(n,n.stateNode.containerInfo),t===null)throw Error(s(387));o=n.pendingProps;var d=n.memoizedState;u=d.element,Uf(t,n),rl(n,o,null,a);var y=n.memoizedState;if(o=y.cache,Dr(n,Hn,o),o!==d.cache&&Ef(n,[Hn],a,!0),al(),o=y.element,d.isDehydrated)if(d={element:o,isDehydrated:!1,cache:y.cache},n.updateQueue.baseState=d,n.memoizedState=d,n.flags&256){n=eg(t,n,o,a);break e}else if(o!==u){u=na(Error(s(424)),n),Jo(u),n=eg(t,n,o,a);break e}else{switch(t=n.stateNode.containerInfo,t.nodeType){case 9:t=t.body;break;default:t=t.nodeName==="HTML"?t.ownerDocument.body:t}for(_n=oa(t.firstChild),ai=n,Vt=!0,Rr=null,ra=!0,a=Zm(n,null,o,a),n.child=a;a;)a.flags=a.flags&-3|4096,a=a.sibling}else{if(hs(),o===u){n=nr(t,n,a);break e}si(t,n,o,a)}n=n.child}return n;case 26:return wc(t,n),t===null?(a=mx(n.type,null,n.pendingProps,null))?n.memoizedState=a:Vt||(a=n.type,t=n.pendingProps,o=Xc(Xe.current).createElement(a),o[Sn]=n,o[In]=t,oi(o,a,t),sn(o),n.stateNode=o):n.memoizedState=mx(n.type,t.memoizedProps,n.pendingProps,t.memoizedState),null;case 27:return at(n),t===null&&Vt&&(o=n.stateNode=dx(n.type,n.pendingProps,Xe.current),ai=n,ra=!0,u=_n,Xr(n.type)?(kd=u,_n=oa(o.firstChild)):_n=u),si(t,n,n.pendingProps.children,a),wc(t,n),t===null&&(n.flags|=4194304),n.child;case 5:return t===null&&Vt&&((u=o=_n)&&(o=RS(o,n.type,n.pendingProps,ra),o!==null?(n.stateNode=o,ai=n,_n=oa(o.firstChild),ra=!1,u=!0):u=!1),u||Ur(n)),at(n),u=n.type,d=n.pendingProps,y=t!==null?t.memoizedProps:null,o=d.children,Bd(u,d)?o=null:y!==null&&Bd(u,y)&&(n.flags|=32),n.memoizedState!==null&&(u=Ff(t,n,Xy,null,null,a),Tl._currentValue=u),wc(t,n),si(t,n,o,a),n.child;case 6:return t===null&&Vt&&((t=a=_n)&&(a=US(a,n.pendingProps,ra),a!==null?(n.stateNode=a,ai=n,_n=null,t=!0):t=!1),t||Ur(n)),null;case 13:return tg(t,n,a);case 4:return Se(n,n.stateNode.containerInfo),o=n.pendingProps,t===null?n.child=_s(n,null,o,a):si(t,n,o,a),n.child;case 11:return q0(t,n,n.type,n.pendingProps,a);case 7:return si(t,n,n.pendingProps,a),n.child;case 8:return si(t,n,n.pendingProps.children,a),n.child;case 12:return si(t,n,n.pendingProps.children,a),n.child;case 10:return o=n.pendingProps,Dr(n,n.type,o.value),si(t,n,o.children,a),n.child;case 9:return u=n.type._context,o=n.pendingProps.children,ms(n),u=ri(u),o=o(u),n.flags|=1,si(t,n,o,a),n.child;case 14:return Y0(t,n,n.type,n.pendingProps,a);case 15:return j0(t,n,n.type,n.pendingProps,a);case 19:return ig(t,n,a);case 31:return Jy(t,n,a);case 22:return Z0(t,n,a,n.pendingProps);case 24:return ms(n),o=ri(Hn),t===null?(u=wf(),u===null&&(u=xn,d=Tf(),u.pooledCache=d,d.refCount++,d!==null&&(u.pooledCacheLanes|=a),u=d),n.memoizedState={parent:o,cache:u},Rf(n),Dr(n,Hn,u)):((t.lanes&a)!==0&&(Uf(t,n),rl(n,null,null,a),al()),u=t.memoizedState,d=n.memoizedState,u.parent!==o?(u={parent:o,cache:o},n.memoizedState=u,n.lanes===0&&(n.memoizedState=n.updateQueue.baseState=u),Dr(n,Hn,o)):(o=d.cache,Dr(n,Hn,o),o!==u.cache&&Ef(n,[Hn],a,!0))),si(t,n,n.pendingProps.children,a),n.child;case 29:throw n.pendingProps}throw Error(s(156,n.tag))}function ir(t){t.flags|=4}function fd(t,n,a,o,u){if((n=(t.mode&32)!==0)&&(n=!1),n){if(t.flags|=16777216,(u&335544128)===u)if(t.stateNode.complete)t.flags|=8192;else if(Dg())t.flags|=8192;else throw vs=dc,Cf}else t.flags&=-16777217}function rg(t,n){if(n.type!=="stylesheet"||(n.state.loading&4)!==0)t.flags&=-16777217;else if(t.flags|=16777216,!yx(n))if(Dg())t.flags|=8192;else throw vs=dc,Cf}function Rc(t,n){n!==null&&(t.flags|=4),t.flags&16384&&(n=t.tag!==22?we():536870912,t.lanes|=n,oo|=n)}function fl(t,n){if(!Vt)switch(t.tailMode){case"hidden":n=t.tail;for(var a=null;n!==null;)n.alternate!==null&&(a=n),n=n.sibling;a===null?t.tail=null:a.sibling=null;break;case"collapsed":a=t.tail;for(var o=null;a!==null;)a.alternate!==null&&(o=a),a=a.sibling;o===null?n||t.tail===null?t.tail=null:t.tail.sibling=null:o.sibling=null}}function yn(t){var n=t.alternate!==null&&t.alternate.child===t.child,a=0,o=0;if(n)for(var u=t.child;u!==null;)a|=u.lanes|u.childLanes,o|=u.subtreeFlags&65011712,o|=u.flags&65011712,u.return=t,u=u.sibling;else for(u=t.child;u!==null;)a|=u.lanes|u.childLanes,o|=u.subtreeFlags,o|=u.flags,u.return=t,u=u.sibling;return t.subtreeFlags|=o,t.childLanes=a,n}function eS(t,n,a){var o=n.pendingProps;switch(_f(n),n.tag){case 16:case 15:case 0:case 11:case 7:case 8:case 12:case 9:case 14:return yn(n),null;case 1:return yn(n),null;case 3:return a=n.stateNode,o=null,t!==null&&(o=t.memoizedState.cache),n.memoizedState.cache!==o&&(n.flags|=2048),$a(Hn),Re(),a.pendingContext&&(a.context=a.pendingContext,a.pendingContext=null),(t===null||t.child===null)&&(js(n)?ir(n):t===null||t.memoizedState.isDehydrated&&(n.flags&256)===0||(n.flags|=1024,Sf())),yn(n),null;case 26:var u=n.type,d=n.memoizedState;return t===null?(ir(n),d!==null?(yn(n),rg(n,d)):(yn(n),fd(n,u,null,o,a))):d?d!==t.memoizedState?(ir(n),yn(n),rg(n,d)):(yn(n),n.flags&=-16777217):(t=t.memoizedProps,t!==o&&ir(n),yn(n),fd(n,u,t,o,a)),null;case 27:if(Ge(n),a=Xe.current,u=n.type,t!==null&&n.stateNode!=null)t.memoizedProps!==o&&ir(n);else{if(!o){if(n.stateNode===null)throw Error(s(166));return yn(n),null}t=De.current,js(n)?Bm(n):(t=dx(u,o,a),n.stateNode=t,ir(n))}return yn(n),null;case 5:if(Ge(n),u=n.type,t!==null&&n.stateNode!=null)t.memoizedProps!==o&&ir(n);else{if(!o){if(n.stateNode===null)throw Error(s(166));return yn(n),null}if(d=De.current,js(n))Bm(n);else{var y=Xc(Xe.current);switch(d){case 1:d=y.createElementNS("http://www.w3.org/2000/svg",u);break;case 2:d=y.createElementNS("http://www.w3.org/1998/Math/MathML",u);break;default:switch(u){case"svg":d=y.createElementNS("http://www.w3.org/2000/svg",u);break;case"math":d=y.createElementNS("http://www.w3.org/1998/Math/MathML",u);break;case"script":d=y.createElement("div"),d.innerHTML="<script><\/script>",d=d.removeChild(d.firstChild);break;case"select":d=typeof o.is=="string"?y.createElement("select",{is:o.is}):y.createElement("select"),o.multiple?d.multiple=!0:o.size&&(d.size=o.size);break;default:d=typeof o.is=="string"?y.createElement(u,{is:o.is}):y.createElement(u)}}d[Sn]=n,d[In]=o;e:for(y=n.child;y!==null;){if(y.tag===5||y.tag===6)d.appendChild(y.stateNode);else if(y.tag!==4&&y.tag!==27&&y.child!==null){y.child.return=y,y=y.child;continue}if(y===n)break e;for(;y.sibling===null;){if(y.return===null||y.return===n)break e;y=y.return}y.sibling.return=y.return,y=y.sibling}n.stateNode=d;e:switch(oi(d,u,o),u){case"button":case"input":case"select":case"textarea":o=!!o.autoFocus;break e;case"img":o=!0;break e;default:o=!1}o&&ir(n)}}return yn(n),fd(n,n.type,t===null?null:t.memoizedProps,n.pendingProps,a),null;case 6:if(t&&n.stateNode!=null)t.memoizedProps!==o&&ir(n);else{if(typeof o!="string"&&n.stateNode===null)throw Error(s(166));if(t=Xe.current,js(n)){if(t=n.stateNode,a=n.memoizedProps,o=null,u=ai,u!==null)switch(u.tag){case 27:case 5:o=u.memoizedProps}t[Sn]=n,t=!!(t.nodeValue===a||o!==null&&o.suppressHydrationWarning===!0||tx(t.nodeValue,a)),t||Ur(n,!0)}else t=Xc(t).createTextNode(o),t[Sn]=n,n.stateNode=t}return yn(n),null;case 31:if(a=n.memoizedState,t===null||t.memoizedState!==null){if(o=js(n),a!==null){if(t===null){if(!o)throw Error(s(318));if(t=n.memoizedState,t=t!==null?t.dehydrated:null,!t)throw Error(s(557));t[Sn]=n}else hs(),(n.flags&128)===0&&(n.memoizedState=null),n.flags|=4;yn(n),t=!1}else a=Sf(),t!==null&&t.memoizedState!==null&&(t.memoizedState.hydrationErrors=a),t=!0;if(!t)return n.flags&256?(Gi(n),n):(Gi(n),null);if((n.flags&128)!==0)throw Error(s(558))}return yn(n),null;case 13:if(o=n.memoizedState,t===null||t.memoizedState!==null&&t.memoizedState.dehydrated!==null){if(u=js(n),o!==null&&o.dehydrated!==null){if(t===null){if(!u)throw Error(s(318));if(u=n.memoizedState,u=u!==null?u.dehydrated:null,!u)throw Error(s(317));u[Sn]=n}else hs(),(n.flags&128)===0&&(n.memoizedState=null),n.flags|=4;yn(n),u=!1}else u=Sf(),t!==null&&t.memoizedState!==null&&(t.memoizedState.hydrationErrors=u),u=!0;if(!u)return n.flags&256?(Gi(n),n):(Gi(n),null)}return Gi(n),(n.flags&128)!==0?(n.lanes=a,n):(a=o!==null,t=t!==null&&t.memoizedState!==null,a&&(o=n.child,u=null,o.alternate!==null&&o.alternate.memoizedState!==null&&o.alternate.memoizedState.cachePool!==null&&(u=o.alternate.memoizedState.cachePool.pool),d=null,o.memoizedState!==null&&o.memoizedState.cachePool!==null&&(d=o.memoizedState.cachePool.pool),d!==u&&(o.flags|=2048)),a!==t&&a&&(n.child.flags|=8192),Rc(n,n.updateQueue),yn(n),null);case 4:return Re(),t===null&&Ld(n.stateNode.containerInfo),yn(n),null;case 10:return $a(n.type),yn(n),null;case 19:if(se(Pn),o=n.memoizedState,o===null)return yn(n),null;if(u=(n.flags&128)!==0,d=o.rendering,d===null)if(u)fl(o,!1);else{if(Nn!==0||t!==null&&(t.flags&128)!==0)for(t=n.child;t!==null;){if(d=gc(t),d!==null){for(n.flags|=128,fl(o,!1),t=d.updateQueue,n.updateQueue=t,Rc(n,t),n.subtreeFlags=0,t=a,a=n.child;a!==null;)Lm(a,t),a=a.sibling;return _e(Pn,Pn.current&1|2),Vt&&Qa(n,o.treeForkCount),n.child}t=t.sibling}o.tail!==null&&Ft()>Oc&&(n.flags|=128,u=!0,fl(o,!1),n.lanes=4194304)}else{if(!u)if(t=gc(d),t!==null){if(n.flags|=128,u=!0,t=t.updateQueue,n.updateQueue=t,Rc(n,t),fl(o,!0),o.tail===null&&o.tailMode==="hidden"&&!d.alternate&&!Vt)return yn(n),null}else 2*Ft()-o.renderingStartTime>Oc&&a!==536870912&&(n.flags|=128,u=!0,fl(o,!1),n.lanes=4194304);o.isBackwards?(d.sibling=n.child,n.child=d):(t=o.last,t!==null?t.sibling=d:n.child=d,o.last=d)}return o.tail!==null?(t=o.tail,o.rendering=t,o.tail=t.sibling,o.renderingStartTime=Ft(),t.sibling=null,a=Pn.current,_e(Pn,u?a&1|2:a&1),Vt&&Qa(n,o.treeForkCount),t):(yn(n),null);case 22:case 23:return Gi(n),Of(),o=n.memoizedState!==null,t!==null?t.memoizedState!==null!==o&&(n.flags|=8192):o&&(n.flags|=8192),o?(a&536870912)!==0&&(n.flags&128)===0&&(yn(n),n.subtreeFlags&6&&(n.flags|=8192)):yn(n),a=n.updateQueue,a!==null&&Rc(n,a.retryQueue),a=null,t!==null&&t.memoizedState!==null&&t.memoizedState.cachePool!==null&&(a=t.memoizedState.cachePool.pool),o=null,n.memoizedState!==null&&n.memoizedState.cachePool!==null&&(o=n.memoizedState.cachePool.pool),o!==a&&(n.flags|=2048),t!==null&&se(gs),null;case 24:return a=null,t!==null&&(a=t.memoizedState.cache),n.memoizedState.cache!==a&&(n.flags|=2048),$a(Hn),yn(n),null;case 25:return null;case 30:return null}throw Error(s(156,n.tag))}function tS(t,n){switch(_f(n),n.tag){case 1:return t=n.flags,t&65536?(n.flags=t&-65537|128,n):null;case 3:return $a(Hn),Re(),t=n.flags,(t&65536)!==0&&(t&128)===0?(n.flags=t&-65537|128,n):null;case 26:case 27:case 5:return Ge(n),null;case 31:if(n.memoizedState!==null){if(Gi(n),n.alternate===null)throw Error(s(340));hs()}return t=n.flags,t&65536?(n.flags=t&-65537|128,n):null;case 13:if(Gi(n),t=n.memoizedState,t!==null&&t.dehydrated!==null){if(n.alternate===null)throw Error(s(340));hs()}return t=n.flags,t&65536?(n.flags=t&-65537|128,n):null;case 19:return se(Pn),null;case 4:return Re(),null;case 10:return $a(n.type),null;case 22:case 23:return Gi(n),Of(),t!==null&&se(gs),t=n.flags,t&65536?(n.flags=t&-65537|128,n):null;case 24:return $a(Hn),null;case 25:return null;default:return null}}function sg(t,n){switch(_f(n),n.tag){case 3:$a(Hn),Re();break;case 26:case 27:case 5:Ge(n);break;case 4:Re();break;case 31:n.memoizedState!==null&&Gi(n);break;case 13:Gi(n);break;case 19:se(Pn);break;case 10:$a(n.type);break;case 22:case 23:Gi(n),Of(),t!==null&&se(gs);break;case 24:$a(Hn)}}function dl(t,n){try{var a=n.updateQueue,o=a!==null?a.lastEffect:null;if(o!==null){var u=o.next;a=u;do{if((a.tag&t)===t){o=void 0;var d=a.create,y=a.inst;o=d(),y.destroy=o}a=a.next}while(a!==u)}}catch(C){ln(n,n.return,C)}}function Fr(t,n,a){try{var o=n.updateQueue,u=o!==null?o.lastEffect:null;if(u!==null){var d=u.next;o=d;do{if((o.tag&t)===t){var y=o.inst,C=y.destroy;if(C!==void 0){y.destroy=void 0,u=n;var H=a,he=C;try{he()}catch(Me){ln(u,H,Me)}}}o=o.next}while(o!==d)}}catch(Me){ln(n,n.return,Me)}}function og(t){var n=t.updateQueue;if(n!==null){var a=t.stateNode;try{Qm(n,a)}catch(o){ln(t,t.return,o)}}}function lg(t,n,a){a.props=Ss(t.type,t.memoizedProps),a.state=t.memoizedState;try{a.componentWillUnmount()}catch(o){ln(t,n,o)}}function hl(t,n){try{var a=t.ref;if(a!==null){switch(t.tag){case 26:case 27:case 5:var o=t.stateNode;break;case 30:o=t.stateNode;break;default:o=t.stateNode}typeof a=="function"?t.refCleanup=a(o):a.current=o}}catch(u){ln(t,n,u)}}function za(t,n){var a=t.ref,o=t.refCleanup;if(a!==null)if(typeof o=="function")try{o()}catch(u){ln(t,n,u)}finally{t.refCleanup=null,t=t.alternate,t!=null&&(t.refCleanup=null)}else if(typeof a=="function")try{a(null)}catch(u){ln(t,n,u)}else a.current=null}function cg(t){var n=t.type,a=t.memoizedProps,o=t.stateNode;try{e:switch(n){case"button":case"input":case"select":case"textarea":a.autoFocus&&o.focus();break e;case"img":a.src?o.src=a.src:a.srcSet&&(o.srcset=a.srcSet)}}catch(u){ln(t,t.return,u)}}function dd(t,n,a){try{var o=t.stateNode;MS(o,t.type,a,n),o[In]=n}catch(u){ln(t,t.return,u)}}function ug(t){return t.tag===5||t.tag===3||t.tag===26||t.tag===27&&Xr(t.type)||t.tag===4}function hd(t){e:for(;;){for(;t.sibling===null;){if(t.return===null||ug(t.return))return null;t=t.return}for(t.sibling.return=t.return,t=t.sibling;t.tag!==5&&t.tag!==6&&t.tag!==18;){if(t.tag===27&&Xr(t.type)||t.flags&2||t.child===null||t.tag===4)continue e;t.child.return=t,t=t.child}if(!(t.flags&2))return t.stateNode}}function pd(t,n,a){var o=t.tag;if(o===5||o===6)t=t.stateNode,n?(a.nodeType===9?a.body:a.nodeName==="HTML"?a.ownerDocument.body:a).insertBefore(t,n):(n=a.nodeType===9?a.body:a.nodeName==="HTML"?a.ownerDocument.body:a,n.appendChild(t),a=a._reactRootContainer,a!=null||n.onclick!==null||(n.onclick=yi));else if(o!==4&&(o===27&&Xr(t.type)&&(a=t.stateNode,n=null),t=t.child,t!==null))for(pd(t,n,a),t=t.sibling;t!==null;)pd(t,n,a),t=t.sibling}function Uc(t,n,a){var o=t.tag;if(o===5||o===6)t=t.stateNode,n?a.insertBefore(t,n):a.appendChild(t);else if(o!==4&&(o===27&&Xr(t.type)&&(a=t.stateNode),t=t.child,t!==null))for(Uc(t,n,a),t=t.sibling;t!==null;)Uc(t,n,a),t=t.sibling}function fg(t){var n=t.stateNode,a=t.memoizedProps;try{for(var o=t.type,u=n.attributes;u.length;)n.removeAttributeNode(u[0]);oi(n,o,a),n[Sn]=t,n[In]=a}catch(d){ln(t,t.return,d)}}var ar=!1,kn=!1,md=!1,dg=typeof WeakSet=="function"?WeakSet:Set,Jn=null;function nS(t,n){if(t=t.containerInfo,zd=Qc,t=Em(t),lf(t)){if("selectionStart"in t)var a={start:t.selectionStart,end:t.selectionEnd};else e:{a=(a=t.ownerDocument)&&a.defaultView||window;var o=a.getSelection&&a.getSelection();if(o&&o.rangeCount!==0){a=o.anchorNode;var u=o.anchorOffset,d=o.focusNode;o=o.focusOffset;try{a.nodeType,d.nodeType}catch{a=null;break e}var y=0,C=-1,H=-1,he=0,Me=0,Te=t,me=null;t:for(;;){for(var ve;Te!==a||u!==0&&Te.nodeType!==3||(C=y+u),Te!==d||o!==0&&Te.nodeType!==3||(H=y+o),Te.nodeType===3&&(y+=Te.nodeValue.length),(ve=Te.firstChild)!==null;)me=Te,Te=ve;for(;;){if(Te===t)break t;if(me===a&&++he===u&&(C=y),me===d&&++Me===o&&(H=y),(ve=Te.nextSibling)!==null)break;Te=me,me=Te.parentNode}Te=ve}a=C===-1||H===-1?null:{start:C,end:H}}else a=null}a=a||{start:0,end:0}}else a=null;for(Fd={focusedElem:t,selectionRange:a},Qc=!1,Jn=n;Jn!==null;)if(n=Jn,t=n.child,(n.subtreeFlags&1028)!==0&&t!==null)t.return=n,Jn=t;else for(;Jn!==null;){switch(n=Jn,d=n.alternate,t=n.flags,n.tag){case 0:if((t&4)!==0&&(t=n.updateQueue,t=t!==null?t.events:null,t!==null))for(a=0;a<t.length;a++)u=t[a],u.ref.impl=u.nextImpl;break;case 11:case 15:break;case 1:if((t&1024)!==0&&d!==null){t=void 0,a=n,u=d.memoizedProps,d=d.memoizedState,o=a.stateNode;try{var tt=Ss(a.type,u);t=o.getSnapshotBeforeUpdate(tt,d),o.__reactInternalSnapshotBeforeUpdate=t}catch(ft){ln(a,a.return,ft)}}break;case 3:if((t&1024)!==0){if(t=n.stateNode.containerInfo,a=t.nodeType,a===9)Hd(t);else if(a===1)switch(t.nodeName){case"HEAD":case"HTML":case"BODY":Hd(t);break;default:t.textContent=""}}break;case 5:case 26:case 27:case 6:case 4:case 17:break;default:if((t&1024)!==0)throw Error(s(163))}if(t=n.sibling,t!==null){t.return=n.return,Jn=t;break}Jn=n.return}}function hg(t,n,a){var o=a.flags;switch(a.tag){case 0:case 11:case 15:sr(t,a),o&4&&dl(5,a);break;case 1:if(sr(t,a),o&4)if(t=a.stateNode,n===null)try{t.componentDidMount()}catch(y){ln(a,a.return,y)}else{var u=Ss(a.type,n.memoizedProps);n=n.memoizedState;try{t.componentDidUpdate(u,n,t.__reactInternalSnapshotBeforeUpdate)}catch(y){ln(a,a.return,y)}}o&64&&og(a),o&512&&hl(a,a.return);break;case 3:if(sr(t,a),o&64&&(t=a.updateQueue,t!==null)){if(n=null,a.child!==null)switch(a.child.tag){case 27:case 5:n=a.child.stateNode;break;case 1:n=a.child.stateNode}try{Qm(t,n)}catch(y){ln(a,a.return,y)}}break;case 27:n===null&&o&4&&fg(a);case 26:case 5:sr(t,a),n===null&&o&4&&cg(a),o&512&&hl(a,a.return);break;case 12:sr(t,a);break;case 31:sr(t,a),o&4&&gg(t,a);break;case 13:sr(t,a),o&4&&xg(t,a),o&64&&(t=a.memoizedState,t!==null&&(t=t.dehydrated,t!==null&&(a=fS.bind(null,a),DS(t,a))));break;case 22:if(o=a.memoizedState!==null||ar,!o){n=n!==null&&n.memoizedState!==null||kn,u=ar;var d=kn;ar=o,(kn=n)&&!d?or(t,a,(a.subtreeFlags&8772)!==0):sr(t,a),ar=u,kn=d}break;case 30:break;default:sr(t,a)}}function pg(t){var n=t.alternate;n!==null&&(t.alternate=null,pg(n)),t.child=null,t.deletions=null,t.sibling=null,t.tag===5&&(n=t.stateNode,n!==null&&Ki(n)),t.stateNode=null,t.return=null,t.dependencies=null,t.memoizedProps=null,t.memoizedState=null,t.pendingProps=null,t.stateNode=null,t.updateQueue=null}var Mn=null,Ri=!1;function rr(t,n,a){for(a=a.child;a!==null;)mg(t,n,a),a=a.sibling}function mg(t,n,a){if(ye&&typeof ye.onCommitFiberUnmount=="function")try{ye.onCommitFiberUnmount(pe,a)}catch{}switch(a.tag){case 26:kn||za(a,n),rr(t,n,a),a.memoizedState?a.memoizedState.count--:a.stateNode&&(a=a.stateNode,a.parentNode.removeChild(a));break;case 27:kn||za(a,n);var o=Mn,u=Ri;Xr(a.type)&&(Mn=a.stateNode,Ri=!1),rr(t,n,a),bl(a.stateNode),Mn=o,Ri=u;break;case 5:kn||za(a,n);case 6:if(o=Mn,u=Ri,Mn=null,rr(t,n,a),Mn=o,Ri=u,Mn!==null)if(Ri)try{(Mn.nodeType===9?Mn.body:Mn.nodeName==="HTML"?Mn.ownerDocument.body:Mn).removeChild(a.stateNode)}catch(d){ln(a,n,d)}else try{Mn.removeChild(a.stateNode)}catch(d){ln(a,n,d)}break;case 18:Mn!==null&&(Ri?(t=Mn,ox(t.nodeType===9?t.body:t.nodeName==="HTML"?t.ownerDocument.body:t,a.stateNode),go(t)):ox(Mn,a.stateNode));break;case 4:o=Mn,u=Ri,Mn=a.stateNode.containerInfo,Ri=!0,rr(t,n,a),Mn=o,Ri=u;break;case 0:case 11:case 14:case 15:Fr(2,a,n),kn||Fr(4,a,n),rr(t,n,a);break;case 1:kn||(za(a,n),o=a.stateNode,typeof o.componentWillUnmount=="function"&&lg(a,n,o)),rr(t,n,a);break;case 21:rr(t,n,a);break;case 22:kn=(o=kn)||a.memoizedState!==null,rr(t,n,a),kn=o;break;default:rr(t,n,a)}}function gg(t,n){if(n.memoizedState===null&&(t=n.alternate,t!==null&&(t=t.memoizedState,t!==null))){t=t.dehydrated;try{go(t)}catch(a){ln(n,n.return,a)}}}function xg(t,n){if(n.memoizedState===null&&(t=n.alternate,t!==null&&(t=t.memoizedState,t!==null&&(t=t.dehydrated,t!==null))))try{go(t)}catch(a){ln(n,n.return,a)}}function iS(t){switch(t.tag){case 31:case 13:case 19:var n=t.stateNode;return n===null&&(n=t.stateNode=new dg),n;case 22:return t=t.stateNode,n=t._retryCache,n===null&&(n=t._retryCache=new dg),n;default:throw Error(s(435,t.tag))}}function Dc(t,n){var a=iS(t);n.forEach(function(o){if(!a.has(o)){a.add(o);var u=dS.bind(null,t,o);o.then(u,u)}})}function Ui(t,n){var a=n.deletions;if(a!==null)for(var o=0;o<a.length;o++){var u=a[o],d=t,y=n,C=y;e:for(;C!==null;){switch(C.tag){case 27:if(Xr(C.type)){Mn=C.stateNode,Ri=!1;break e}break;case 5:Mn=C.stateNode,Ri=!1;break e;case 3:case 4:Mn=C.stateNode.containerInfo,Ri=!0;break e}C=C.return}if(Mn===null)throw Error(s(160));mg(d,y,u),Mn=null,Ri=!1,d=u.alternate,d!==null&&(d.return=null),u.return=null}if(n.subtreeFlags&13886)for(n=n.child;n!==null;)vg(n,t),n=n.sibling}var _a=null;function vg(t,n){var a=t.alternate,o=t.flags;switch(t.tag){case 0:case 11:case 14:case 15:Ui(n,t),Di(t),o&4&&(Fr(3,t,t.return),dl(3,t),Fr(5,t,t.return));break;case 1:Ui(n,t),Di(t),o&512&&(kn||a===null||za(a,a.return)),o&64&&ar&&(t=t.updateQueue,t!==null&&(o=t.callbacks,o!==null&&(a=t.shared.hiddenCallbacks,t.shared.hiddenCallbacks=a===null?o:a.concat(o))));break;case 26:var u=_a;if(Ui(n,t),Di(t),o&512&&(kn||a===null||za(a,a.return)),o&4){var d=a!==null?a.memoizedState:null;if(o=t.memoizedState,a===null)if(o===null)if(t.stateNode===null){e:{o=t.type,a=t.memoizedProps,u=u.ownerDocument||u;t:switch(o){case"title":d=u.getElementsByTagName("title")[0],(!d||d[qt]||d[Sn]||d.namespaceURI==="http://www.w3.org/2000/svg"||d.hasAttribute("itemprop"))&&(d=u.createElement(o),u.head.insertBefore(d,u.querySelector("head > title"))),oi(d,o,a),d[Sn]=t,sn(d),o=d;break e;case"link":var y=vx("link","href",u).get(o+(a.href||""));if(y){for(var C=0;C<y.length;C++)if(d=y[C],d.getAttribute("href")===(a.href==null||a.href===""?null:a.href)&&d.getAttribute("rel")===(a.rel==null?null:a.rel)&&d.getAttribute("title")===(a.title==null?null:a.title)&&d.getAttribute("crossorigin")===(a.crossOrigin==null?null:a.crossOrigin)){y.splice(C,1);break t}}d=u.createElement(o),oi(d,o,a),u.head.appendChild(d);break;case"meta":if(y=vx("meta","content",u).get(o+(a.content||""))){for(C=0;C<y.length;C++)if(d=y[C],d.getAttribute("content")===(a.content==null?null:""+a.content)&&d.getAttribute("name")===(a.name==null?null:a.name)&&d.getAttribute("property")===(a.property==null?null:a.property)&&d.getAttribute("http-equiv")===(a.httpEquiv==null?null:a.httpEquiv)&&d.getAttribute("charset")===(a.charSet==null?null:a.charSet)){y.splice(C,1);break t}}d=u.createElement(o),oi(d,o,a),u.head.appendChild(d);break;default:throw Error(s(468,o))}d[Sn]=t,sn(d),o=d}t.stateNode=o}else _x(u,t.type,t.stateNode);else t.stateNode=xx(u,o,t.memoizedProps);else d!==o?(d===null?a.stateNode!==null&&(a=a.stateNode,a.parentNode.removeChild(a)):d.count--,o===null?_x(u,t.type,t.stateNode):xx(u,o,t.memoizedProps)):o===null&&t.stateNode!==null&&dd(t,t.memoizedProps,a.memoizedProps)}break;case 27:Ui(n,t),Di(t),o&512&&(kn||a===null||za(a,a.return)),a!==null&&o&4&&dd(t,t.memoizedProps,a.memoizedProps);break;case 5:if(Ui(n,t),Di(t),o&512&&(kn||a===null||za(a,a.return)),t.flags&32){u=t.stateNode;try{ni(u,"")}catch(tt){ln(t,t.return,tt)}}o&4&&t.stateNode!=null&&(u=t.memoizedProps,dd(t,u,a!==null?a.memoizedProps:u)),o&1024&&(md=!0);break;case 6:if(Ui(n,t),Di(t),o&4){if(t.stateNode===null)throw Error(s(162));o=t.memoizedProps,a=t.stateNode;try{a.nodeValue=o}catch(tt){ln(t,t.return,tt)}}break;case 3:if(Yc=null,u=_a,_a=Wc(n.containerInfo),Ui(n,t),_a=u,Di(t),o&4&&a!==null&&a.memoizedState.isDehydrated)try{go(n.containerInfo)}catch(tt){ln(t,t.return,tt)}md&&(md=!1,_g(t));break;case 4:o=_a,_a=Wc(t.stateNode.containerInfo),Ui(n,t),Di(t),_a=o;break;case 12:Ui(n,t),Di(t);break;case 31:Ui(n,t),Di(t),o&4&&(o=t.updateQueue,o!==null&&(t.updateQueue=null,Dc(t,o)));break;case 13:Ui(n,t),Di(t),t.child.flags&8192&&t.memoizedState!==null!=(a!==null&&a.memoizedState!==null)&&(Lc=Ft()),o&4&&(o=t.updateQueue,o!==null&&(t.updateQueue=null,Dc(t,o)));break;case 22:u=t.memoizedState!==null;var H=a!==null&&a.memoizedState!==null,he=ar,Me=kn;if(ar=he||u,kn=Me||H,Ui(n,t),kn=Me,ar=he,Di(t),o&8192)e:for(n=t.stateNode,n._visibility=u?n._visibility&-2:n._visibility|1,u&&(a===null||H||ar||kn||bs(t)),a=null,n=t;;){if(n.tag===5||n.tag===26){if(a===null){H=a=n;try{if(d=H.stateNode,u)y=d.style,typeof y.setProperty=="function"?y.setProperty("display","none","important"):y.display="none";else{C=H.stateNode;var Te=H.memoizedProps.style,me=Te!=null&&Te.hasOwnProperty("display")?Te.display:null;C.style.display=me==null||typeof me=="boolean"?"":(""+me).trim()}}catch(tt){ln(H,H.return,tt)}}}else if(n.tag===6){if(a===null){H=n;try{H.stateNode.nodeValue=u?"":H.memoizedProps}catch(tt){ln(H,H.return,tt)}}}else if(n.tag===18){if(a===null){H=n;try{var ve=H.stateNode;u?lx(ve,!0):lx(H.stateNode,!1)}catch(tt){ln(H,H.return,tt)}}}else if((n.tag!==22&&n.tag!==23||n.memoizedState===null||n===t)&&n.child!==null){n.child.return=n,n=n.child;continue}if(n===t)break e;for(;n.sibling===null;){if(n.return===null||n.return===t)break e;a===n&&(a=null),n=n.return}a===n&&(a=null),n.sibling.return=n.return,n=n.sibling}o&4&&(o=t.updateQueue,o!==null&&(a=o.retryQueue,a!==null&&(o.retryQueue=null,Dc(t,a))));break;case 19:Ui(n,t),Di(t),o&4&&(o=t.updateQueue,o!==null&&(t.updateQueue=null,Dc(t,o)));break;case 30:break;case 21:break;default:Ui(n,t),Di(t)}}function Di(t){var n=t.flags;if(n&2){try{for(var a,o=t.return;o!==null;){if(ug(o)){a=o;break}o=o.return}if(a==null)throw Error(s(160));switch(a.tag){case 27:var u=a.stateNode,d=hd(t);Uc(t,d,u);break;case 5:var y=a.stateNode;a.flags&32&&(ni(y,""),a.flags&=-33);var C=hd(t);Uc(t,C,y);break;case 3:case 4:var H=a.stateNode.containerInfo,he=hd(t);pd(t,he,H);break;default:throw Error(s(161))}}catch(Me){ln(t,t.return,Me)}t.flags&=-3}n&4096&&(t.flags&=-4097)}function _g(t){if(t.subtreeFlags&1024)for(t=t.child;t!==null;){var n=t;_g(n),n.tag===5&&n.flags&1024&&n.stateNode.reset(),t=t.sibling}}function sr(t,n){if(n.subtreeFlags&8772)for(n=n.child;n!==null;)hg(t,n.alternate,n),n=n.sibling}function bs(t){for(t=t.child;t!==null;){var n=t;switch(n.tag){case 0:case 11:case 14:case 15:Fr(4,n,n.return),bs(n);break;case 1:za(n,n.return);var a=n.stateNode;typeof a.componentWillUnmount=="function"&&lg(n,n.return,a),bs(n);break;case 27:bl(n.stateNode);case 26:case 5:za(n,n.return),bs(n);break;case 22:n.memoizedState===null&&bs(n);break;case 30:bs(n);break;default:bs(n)}t=t.sibling}}function or(t,n,a){for(a=a&&(n.subtreeFlags&8772)!==0,n=n.child;n!==null;){var o=n.alternate,u=t,d=n,y=d.flags;switch(d.tag){case 0:case 11:case 15:or(u,d,a),dl(4,d);break;case 1:if(or(u,d,a),o=d,u=o.stateNode,typeof u.componentDidMount=="function")try{u.componentDidMount()}catch(he){ln(o,o.return,he)}if(o=d,u=o.updateQueue,u!==null){var C=o.stateNode;try{var H=u.shared.hiddenCallbacks;if(H!==null)for(u.shared.hiddenCallbacks=null,u=0;u<H.length;u++)Km(H[u],C)}catch(he){ln(o,o.return,he)}}a&&y&64&&og(d),hl(d,d.return);break;case 27:fg(d);case 26:case 5:or(u,d,a),a&&o===null&&y&4&&cg(d),hl(d,d.return);break;case 12:or(u,d,a);break;case 31:or(u,d,a),a&&y&4&&gg(u,d);break;case 13:or(u,d,a),a&&y&4&&xg(u,d);break;case 22:d.memoizedState===null&&or(u,d,a),hl(d,d.return);break;case 30:break;default:or(u,d,a)}n=n.sibling}}function gd(t,n){var a=null;t!==null&&t.memoizedState!==null&&t.memoizedState.cachePool!==null&&(a=t.memoizedState.cachePool.pool),t=null,n.memoizedState!==null&&n.memoizedState.cachePool!==null&&(t=n.memoizedState.cachePool.pool),t!==a&&(t!=null&&t.refCount++,a!=null&&$o(a))}function xd(t,n){t=null,n.alternate!==null&&(t=n.alternate.memoizedState.cache),n=n.memoizedState.cache,n!==t&&(n.refCount++,t!=null&&$o(t))}function ya(t,n,a,o){if(n.subtreeFlags&10256)for(n=n.child;n!==null;)yg(t,n,a,o),n=n.sibling}function yg(t,n,a,o){var u=n.flags;switch(n.tag){case 0:case 11:case 15:ya(t,n,a,o),u&2048&&dl(9,n);break;case 1:ya(t,n,a,o);break;case 3:ya(t,n,a,o),u&2048&&(t=null,n.alternate!==null&&(t=n.alternate.memoizedState.cache),n=n.memoizedState.cache,n!==t&&(n.refCount++,t!=null&&$o(t)));break;case 12:if(u&2048){ya(t,n,a,o),t=n.stateNode;try{var d=n.memoizedProps,y=d.id,C=d.onPostCommit;typeof C=="function"&&C(y,n.alternate===null?"mount":"update",t.passiveEffectDuration,-0)}catch(H){ln(n,n.return,H)}}else ya(t,n,a,o);break;case 31:ya(t,n,a,o);break;case 13:ya(t,n,a,o);break;case 23:break;case 22:d=n.stateNode,y=n.alternate,n.memoizedState!==null?d._visibility&2?ya(t,n,a,o):pl(t,n):d._visibility&2?ya(t,n,a,o):(d._visibility|=2,ao(t,n,a,o,(n.subtreeFlags&10256)!==0||!1)),u&2048&&gd(y,n);break;case 24:ya(t,n,a,o),u&2048&&xd(n.alternate,n);break;default:ya(t,n,a,o)}}function ao(t,n,a,o,u){for(u=u&&((n.subtreeFlags&10256)!==0||!1),n=n.child;n!==null;){var d=t,y=n,C=a,H=o,he=y.flags;switch(y.tag){case 0:case 11:case 15:ao(d,y,C,H,u),dl(8,y);break;case 23:break;case 22:var Me=y.stateNode;y.memoizedState!==null?Me._visibility&2?ao(d,y,C,H,u):pl(d,y):(Me._visibility|=2,ao(d,y,C,H,u)),u&&he&2048&&gd(y.alternate,y);break;case 24:ao(d,y,C,H,u),u&&he&2048&&xd(y.alternate,y);break;default:ao(d,y,C,H,u)}n=n.sibling}}function pl(t,n){if(n.subtreeFlags&10256)for(n=n.child;n!==null;){var a=t,o=n,u=o.flags;switch(o.tag){case 22:pl(a,o),u&2048&&gd(o.alternate,o);break;case 24:pl(a,o),u&2048&&xd(o.alternate,o);break;default:pl(a,o)}n=n.sibling}}var ml=8192;function ro(t,n,a){if(t.subtreeFlags&ml)for(t=t.child;t!==null;)Sg(t,n,a),t=t.sibling}function Sg(t,n,a){switch(t.tag){case 26:ro(t,n,a),t.flags&ml&&t.memoizedState!==null&&kS(a,_a,t.memoizedState,t.memoizedProps);break;case 5:ro(t,n,a);break;case 3:case 4:var o=_a;_a=Wc(t.stateNode.containerInfo),ro(t,n,a),_a=o;break;case 22:t.memoizedState===null&&(o=t.alternate,o!==null&&o.memoizedState!==null?(o=ml,ml=16777216,ro(t,n,a),ml=o):ro(t,n,a));break;default:ro(t,n,a)}}function bg(t){var n=t.alternate;if(n!==null&&(t=n.child,t!==null)){n.child=null;do n=t.sibling,t.sibling=null,t=n;while(t!==null)}}function gl(t){var n=t.deletions;if((t.flags&16)!==0){if(n!==null)for(var a=0;a<n.length;a++){var o=n[a];Jn=o,Eg(o,t)}bg(t)}if(t.subtreeFlags&10256)for(t=t.child;t!==null;)Mg(t),t=t.sibling}function Mg(t){switch(t.tag){case 0:case 11:case 15:gl(t),t.flags&2048&&Fr(9,t,t.return);break;case 3:gl(t);break;case 12:gl(t);break;case 22:var n=t.stateNode;t.memoizedState!==null&&n._visibility&2&&(t.return===null||t.return.tag!==13)?(n._visibility&=-3,Nc(t)):gl(t);break;default:gl(t)}}function Nc(t){var n=t.deletions;if((t.flags&16)!==0){if(n!==null)for(var a=0;a<n.length;a++){var o=n[a];Jn=o,Eg(o,t)}bg(t)}for(t=t.child;t!==null;){switch(n=t,n.tag){case 0:case 11:case 15:Fr(8,n,n.return),Nc(n);break;case 22:a=n.stateNode,a._visibility&2&&(a._visibility&=-3,Nc(n));break;default:Nc(n)}t=t.sibling}}function Eg(t,n){for(;Jn!==null;){var a=Jn;switch(a.tag){case 0:case 11:case 15:Fr(8,a,n);break;case 23:case 22:if(a.memoizedState!==null&&a.memoizedState.cachePool!==null){var o=a.memoizedState.cachePool.pool;o!=null&&o.refCount++}break;case 24:$o(a.memoizedState.cache)}if(o=a.child,o!==null)o.return=a,Jn=o;else e:for(a=t;Jn!==null;){o=Jn;var u=o.sibling,d=o.return;if(pg(o),o===a){Jn=null;break e}if(u!==null){u.return=d,Jn=u;break e}Jn=d}}}var aS={getCacheForType:function(t){var n=ri(Hn),a=n.data.get(t);return a===void 0&&(a=t(),n.data.set(t,a)),a},cacheSignal:function(){return ri(Hn).controller.signal}},rS=typeof WeakMap=="function"?WeakMap:Map,an=0,xn=null,Pt=null,It=0,on=0,Vi=null,Br=!1,so=!1,vd=!1,lr=0,Nn=0,Ir=0,Ms=0,_d=0,ki=0,oo=0,xl=null,Ni=null,yd=!1,Lc=0,Tg=0,Oc=1/0,Pc=null,Hr=null,qn=0,Gr=null,lo=null,cr=0,Sd=0,bd=null,Ag=null,vl=0,Md=null;function Xi(){return(an&2)!==0&&It!==0?It&-It:B.T!==null?Rd():Ra()}function wg(){if(ki===0)if((It&536870912)===0||Vt){var t=dt;dt<<=1,(dt&3932160)===0&&(dt=262144),ki=t}else ki=536870912;return t=Hi.current,t!==null&&(t.flags|=32),ki}function Li(t,n,a){(t===xn&&(on===2||on===9)||t.cancelPendingCommit!==null)&&(co(t,0),Vr(t,It,ki,!1)),Je(t,a),((an&2)===0||t!==xn)&&(t===xn&&((an&2)===0&&(Ms|=a),Nn===4&&Vr(t,It,ki,!1)),Fa(t))}function Cg(t,n,a){if((an&6)!==0)throw Error(s(327));var o=!a&&(n&127)===0&&(n&t.expiredLanes)===0||Pe(t,n),u=o?lS(t,n):Td(t,n,!0),d=o;do{if(u===0){so&&!o&&Vr(t,n,0,!1);break}else{if(a=t.current.alternate,d&&!sS(a)){u=Td(t,n,!1),d=!1;continue}if(u===2){if(d=n,t.errorRecoveryDisabledLanes&d)var y=0;else y=t.pendingLanes&-536870913,y=y!==0?y:y&536870912?536870912:0;if(y!==0){n=y;e:{var C=t;u=xl;var H=C.current.memoizedState.isDehydrated;if(H&&(co(C,y).flags|=256),y=Td(C,y,!1),y!==2){if(vd&&!H){C.errorRecoveryDisabledLanes|=d,Ms|=d,u=4;break e}d=Ni,Ni=u,d!==null&&(Ni===null?Ni=d:Ni.push.apply(Ni,d))}u=y}if(d=!1,u!==2)continue}}if(u===1){co(t,0),Vr(t,n,0,!0);break}e:{switch(o=t,d=u,d){case 0:case 1:throw Error(s(345));case 4:if((n&4194048)!==n)break;case 6:Vr(o,n,ki,!Br);break e;case 2:Ni=null;break;case 3:case 5:break;default:throw Error(s(329))}if((n&62914560)===n&&(u=Lc+300-Ft(),10<u)){if(Vr(o,n,ki,!Br),be(o,0,!0)!==0)break e;cr=n,o.timeoutHandle=rx(Rg.bind(null,o,a,Ni,Pc,yd,n,ki,Ms,oo,Br,d,"Throttled",-0,0),u);break e}Rg(o,a,Ni,Pc,yd,n,ki,Ms,oo,Br,d,null,-0,0)}}break}while(!0);Fa(t)}function Rg(t,n,a,o,u,d,y,C,H,he,Me,Te,me,ve){if(t.timeoutHandle=-1,Te=n.subtreeFlags,Te&8192||(Te&16785408)===16785408){Te={stylesheets:null,count:0,imgCount:0,imgBytes:0,suspenseyImages:[],waitingForImages:!0,waitingForViewTransition:!1,unsuspend:yi},Sg(n,d,Te);var tt=(d&62914560)===d?Lc-Ft():(d&4194048)===d?Tg-Ft():0;if(tt=XS(Te,tt),tt!==null){cr=d,t.cancelPendingCommit=tt(Fg.bind(null,t,n,d,a,o,u,y,C,H,Me,Te,null,me,ve)),Vr(t,d,y,!he);return}}Fg(t,n,d,a,o,u,y,C,H)}function sS(t){for(var n=t;;){var a=n.tag;if((a===0||a===11||a===15)&&n.flags&16384&&(a=n.updateQueue,a!==null&&(a=a.stores,a!==null)))for(var o=0;o<a.length;o++){var u=a[o],d=u.getSnapshot;u=u.value;try{if(!Bi(d(),u))return!1}catch{return!1}}if(a=n.child,n.subtreeFlags&16384&&a!==null)a.return=n,n=a;else{if(n===t)break;for(;n.sibling===null;){if(n.return===null||n.return===t)return!0;n=n.return}n.sibling.return=n.return,n=n.sibling}}return!0}function Vr(t,n,a,o){n&=~_d,n&=~Ms,t.suspendedLanes|=n,t.pingedLanes&=~n,o&&(t.warmLanes|=n),o=t.expirationTimes;for(var u=n;0<u;){var d=31-Ze(u),y=1<<d;o[d]=-1,u&=~y}a!==0&&Nt(t,a,n)}function zc(){return(an&6)===0?(_l(0),!1):!0}function Ed(){if(Pt!==null){if(on===0)var t=Pt.return;else t=Pt,Ja=ps=null,Hf(t),$s=null,tl=0,t=Pt;for(;t!==null;)sg(t.alternate,t),t=t.return;Pt=null}}function co(t,n){var a=t.timeoutHandle;a!==-1&&(t.timeoutHandle=-1,AS(a)),a=t.cancelPendingCommit,a!==null&&(t.cancelPendingCommit=null,a()),cr=0,Ed(),xn=t,Pt=a=Ka(t.current,null),It=n,on=0,Vi=null,Br=!1,so=Pe(t,n),vd=!1,oo=ki=_d=Ms=Ir=Nn=0,Ni=xl=null,yd=!1,(n&8)!==0&&(n|=n&32);var o=t.entangledLanes;if(o!==0)for(t=t.entanglements,o&=n;0<o;){var u=31-Ze(o),d=1<<u;n|=t[u],o&=~d}return lr=n,ic(),a}function Ug(t,n){At=null,B.H=cl,n===Js||n===fc?(n=qm(),on=3):n===Cf?(n=qm(),on=4):on=n===nd?8:n!==null&&typeof n=="object"&&typeof n.then=="function"?6:1,Vi=n,Pt===null&&(Nn=1,Tc(t,na(n,t.current)))}function Dg(){var t=Hi.current;return t===null?!0:(It&4194048)===It?sa===null:(It&62914560)===It||(It&536870912)!==0?t===sa:!1}function Ng(){var t=B.H;return B.H=cl,t===null?cl:t}function Lg(){var t=B.A;return B.A=aS,t}function Fc(){Nn=4,Br||(It&4194048)!==It&&Hi.current!==null||(so=!0),(Ir&134217727)===0&&(Ms&134217727)===0||xn===null||Vr(xn,It,ki,!1)}function Td(t,n,a){var o=an;an|=2;var u=Ng(),d=Lg();(xn!==t||It!==n)&&(Pc=null,co(t,n)),n=!1;var y=Nn;e:do try{if(on!==0&&Pt!==null){var C=Pt,H=Vi;switch(on){case 8:Ed(),y=6;break e;case 3:case 2:case 9:case 6:Hi.current===null&&(n=!0);var he=on;if(on=0,Vi=null,uo(t,C,H,he),a&&so){y=0;break e}break;default:he=on,on=0,Vi=null,uo(t,C,H,he)}}oS(),y=Nn;break}catch(Me){Ug(t,Me)}while(!0);return n&&t.shellSuspendCounter++,Ja=ps=null,an=o,B.H=u,B.A=d,Pt===null&&(xn=null,It=0,ic()),y}function oS(){for(;Pt!==null;)Og(Pt)}function lS(t,n){var a=an;an|=2;var o=Ng(),u=Lg();xn!==t||It!==n?(Pc=null,Oc=Ft()+500,co(t,n)):so=Pe(t,n);e:do try{if(on!==0&&Pt!==null){n=Pt;var d=Vi;t:switch(on){case 1:on=0,Vi=null,uo(t,n,d,1);break;case 2:case 9:if(Xm(d)){on=0,Vi=null,Pg(n);break}n=function(){on!==2&&on!==9||xn!==t||(on=7),Fa(t)},d.then(n,n);break e;case 3:on=7;break e;case 4:on=5;break e;case 7:Xm(d)?(on=0,Vi=null,Pg(n)):(on=0,Vi=null,uo(t,n,d,7));break;case 5:var y=null;switch(Pt.tag){case 26:y=Pt.memoizedState;case 5:case 27:var C=Pt;if(y?yx(y):C.stateNode.complete){on=0,Vi=null;var H=C.sibling;if(H!==null)Pt=H;else{var he=C.return;he!==null?(Pt=he,Bc(he)):Pt=null}break t}}on=0,Vi=null,uo(t,n,d,5);break;case 6:on=0,Vi=null,uo(t,n,d,6);break;case 8:Ed(),Nn=6;break e;default:throw Error(s(462))}}cS();break}catch(Me){Ug(t,Me)}while(!0);return Ja=ps=null,B.H=o,B.A=u,an=a,Pt!==null?0:(xn=null,It=0,ic(),Nn)}function cS(){for(;Pt!==null&&!fn();)Og(Pt)}function Og(t){var n=ag(t.alternate,t,lr);t.memoizedProps=t.pendingProps,n===null?Bc(t):Pt=n}function Pg(t){var n=t,a=n.alternate;switch(n.tag){case 15:case 0:n=J0(a,n,n.pendingProps,n.type,void 0,It);break;case 11:n=J0(a,n,n.pendingProps,n.type.render,n.ref,It);break;case 5:Hf(n);default:sg(a,n),n=Pt=Lm(n,lr),n=ag(a,n,lr)}t.memoizedProps=t.pendingProps,n===null?Bc(t):Pt=n}function uo(t,n,a,o){Ja=ps=null,Hf(n),$s=null,tl=0;var u=n.return;try{if(Qy(t,u,n,a,It)){Nn=1,Tc(t,na(a,t.current)),Pt=null;return}}catch(d){if(u!==null)throw Pt=u,d;Nn=1,Tc(t,na(a,t.current)),Pt=null;return}n.flags&32768?(Vt||o===1?t=!0:so||(It&536870912)!==0?t=!1:(Br=t=!0,(o===2||o===9||o===3||o===6)&&(o=Hi.current,o!==null&&o.tag===13&&(o.flags|=16384))),zg(n,t)):Bc(n)}function Bc(t){var n=t;do{if((n.flags&32768)!==0){zg(n,Br);return}t=n.return;var a=eS(n.alternate,n,lr);if(a!==null){Pt=a;return}if(n=n.sibling,n!==null){Pt=n;return}Pt=n=t}while(n!==null);Nn===0&&(Nn=5)}function zg(t,n){do{var a=tS(t.alternate,t);if(a!==null){a.flags&=32767,Pt=a;return}if(a=t.return,a!==null&&(a.flags|=32768,a.subtreeFlags=0,a.deletions=null),!n&&(t=t.sibling,t!==null)){Pt=t;return}Pt=t=a}while(t!==null);Nn=6,Pt=null}function Fg(t,n,a,o,u,d,y,C,H){t.cancelPendingCommit=null;do Ic();while(qn!==0);if((an&6)!==0)throw Error(s(327));if(n!==null){if(n===t.current)throw Error(s(177));if(d=n.lanes|n.childLanes,d|=hf,Qt(t,a,d,y,C,H),t===xn&&(Pt=xn=null,It=0),lo=n,Gr=t,cr=a,Sd=d,bd=u,Ag=o,(n.subtreeFlags&10256)!==0||(n.flags&10256)!==0?(t.callbackNode=null,t.callbackPriority=0,hS(Z,function(){return Vg(),null})):(t.callbackNode=null,t.callbackPriority=0),o=(n.flags&13878)!==0,(n.subtreeFlags&13878)!==0||o){o=B.T,B.T=null,u=V.p,V.p=2,y=an,an|=4;try{nS(t,n,a)}finally{an=y,V.p=u,B.T=o}}qn=1,Bg(),Ig(),Hg()}}function Bg(){if(qn===1){qn=0;var t=Gr,n=lo,a=(n.flags&13878)!==0;if((n.subtreeFlags&13878)!==0||a){a=B.T,B.T=null;var o=V.p;V.p=2;var u=an;an|=4;try{vg(n,t);var d=Fd,y=Em(t.containerInfo),C=d.focusedElem,H=d.selectionRange;if(y!==C&&C&&C.ownerDocument&&Mm(C.ownerDocument.documentElement,C)){if(H!==null&&lf(C)){var he=H.start,Me=H.end;if(Me===void 0&&(Me=he),"selectionStart"in C)C.selectionStart=he,C.selectionEnd=Math.min(Me,C.value.length);else{var Te=C.ownerDocument||document,me=Te&&Te.defaultView||window;if(me.getSelection){var ve=me.getSelection(),tt=C.textContent.length,ft=Math.min(H.start,tt),mn=H.end===void 0?ft:Math.min(H.end,tt);!ve.extend&&ft>mn&&(y=mn,mn=ft,ft=y);var $=bm(C,ft),Y=bm(C,mn);if($&&Y&&(ve.rangeCount!==1||ve.anchorNode!==$.node||ve.anchorOffset!==$.offset||ve.focusNode!==Y.node||ve.focusOffset!==Y.offset)){var de=Te.createRange();de.setStart($.node,$.offset),ve.removeAllRanges(),ft>mn?(ve.addRange(de),ve.extend(Y.node,Y.offset)):(de.setEnd(Y.node,Y.offset),ve.addRange(de))}}}}for(Te=[],ve=C;ve=ve.parentNode;)ve.nodeType===1&&Te.push({element:ve,left:ve.scrollLeft,top:ve.scrollTop});for(typeof C.focus=="function"&&C.focus(),C=0;C<Te.length;C++){var Ee=Te[C];Ee.element.scrollLeft=Ee.left,Ee.element.scrollTop=Ee.top}}Qc=!!zd,Fd=zd=null}finally{an=u,V.p=o,B.T=a}}t.current=n,qn=2}}function Ig(){if(qn===2){qn=0;var t=Gr,n=lo,a=(n.flags&8772)!==0;if((n.subtreeFlags&8772)!==0||a){a=B.T,B.T=null;var o=V.p;V.p=2;var u=an;an|=4;try{hg(t,n.alternate,n)}finally{an=u,V.p=o,B.T=a}}qn=3}}function Hg(){if(qn===4||qn===3){qn=0,j();var t=Gr,n=lo,a=cr,o=Ag;(n.subtreeFlags&10256)!==0||(n.flags&10256)!==0?qn=5:(qn=0,lo=Gr=null,Gg(t,t.pendingLanes));var u=t.pendingLanes;if(u===0&&(Hr=null),ls(a),n=n.stateNode,ye&&typeof ye.onCommitFiberRoot=="function")try{ye.onCommitFiberRoot(pe,n,void 0,(n.current.flags&128)===128)}catch{}if(o!==null){n=B.T,u=V.p,V.p=2,B.T=null;try{for(var d=t.onRecoverableError,y=0;y<o.length;y++){var C=o[y];d(C.value,{componentStack:C.stack})}}finally{B.T=n,V.p=u}}(cr&3)!==0&&Ic(),Fa(t),u=t.pendingLanes,(a&261930)!==0&&(u&42)!==0?t===Md?vl++:(vl=0,Md=t):vl=0,_l(0)}}function Gg(t,n){(t.pooledCacheLanes&=n)===0&&(n=t.pooledCache,n!=null&&(t.pooledCache=null,$o(n)))}function Ic(){return Bg(),Ig(),Hg(),Vg()}function Vg(){if(qn!==5)return!1;var t=Gr,n=Sd;Sd=0;var a=ls(cr),o=B.T,u=V.p;try{V.p=32>a?32:a,B.T=null,a=bd,bd=null;var d=Gr,y=cr;if(qn=0,lo=Gr=null,cr=0,(an&6)!==0)throw Error(s(331));var C=an;if(an|=4,Mg(d.current),yg(d,d.current,y,a),an=C,_l(0,!1),ye&&typeof ye.onPostCommitFiberRoot=="function")try{ye.onPostCommitFiberRoot(pe,d)}catch{}return!0}finally{V.p=u,B.T=o,Gg(t,n)}}function kg(t,n,a){n=na(a,n),n=td(t.stateNode,n,2),t=Or(t,n,2),t!==null&&(Je(t,2),Fa(t))}function ln(t,n,a){if(t.tag===3)kg(t,t,a);else for(;n!==null;){if(n.tag===3){kg(n,t,a);break}else if(n.tag===1){var o=n.stateNode;if(typeof n.type.getDerivedStateFromError=="function"||typeof o.componentDidCatch=="function"&&(Hr===null||!Hr.has(o))){t=na(a,t),a=X0(2),o=Or(n,a,2),o!==null&&(W0(a,o,n,t),Je(o,2),Fa(o));break}}n=n.return}}function Ad(t,n,a){var o=t.pingCache;if(o===null){o=t.pingCache=new rS;var u=new Set;o.set(n,u)}else u=o.get(n),u===void 0&&(u=new Set,o.set(n,u));u.has(a)||(vd=!0,u.add(a),t=uS.bind(null,t,n,a),n.then(t,t))}function uS(t,n,a){var o=t.pingCache;o!==null&&o.delete(n),t.pingedLanes|=t.suspendedLanes&a,t.warmLanes&=~a,xn===t&&(It&a)===a&&(Nn===4||Nn===3&&(It&62914560)===It&&300>Ft()-Lc?(an&2)===0&&co(t,0):_d|=a,oo===It&&(oo=0)),Fa(t)}function Xg(t,n){n===0&&(n=we()),t=fs(t,n),t!==null&&(Je(t,n),Fa(t))}function fS(t){var n=t.memoizedState,a=0;n!==null&&(a=n.retryLane),Xg(t,a)}function dS(t,n){var a=0;switch(t.tag){case 31:case 13:var o=t.stateNode,u=t.memoizedState;u!==null&&(a=u.retryLane);break;case 19:o=t.stateNode;break;case 22:o=t.stateNode._retryCache;break;default:throw Error(s(314))}o!==null&&o.delete(n),Xg(t,a)}function hS(t,n){return vn(t,n)}var Hc=null,fo=null,wd=!1,Gc=!1,Cd=!1,kr=0;function Fa(t){t!==fo&&t.next===null&&(fo===null?Hc=fo=t:fo=fo.next=t),Gc=!0,wd||(wd=!0,mS())}function _l(t,n){if(!Cd&&Gc){Cd=!0;do for(var a=!1,o=Hc;o!==null;){if(t!==0){var u=o.pendingLanes;if(u===0)var d=0;else{var y=o.suspendedLanes,C=o.pingedLanes;d=(1<<31-Ze(42|t)+1)-1,d&=u&~(y&~C),d=d&201326741?d&201326741|1:d?d|2:0}d!==0&&(a=!0,jg(o,d))}else d=It,d=be(o,o===xn?d:0,o.cancelPendingCommit!==null||o.timeoutHandle!==-1),(d&3)===0||Pe(o,d)||(a=!0,jg(o,d));o=o.next}while(a);Cd=!1}}function pS(){Wg()}function Wg(){Gc=wd=!1;var t=0;kr!==0&&TS()&&(t=kr);for(var n=Ft(),a=null,o=Hc;o!==null;){var u=o.next,d=qg(o,n);d===0?(o.next=null,a===null?Hc=u:a.next=u,u===null&&(fo=a)):(a=o,(t!==0||(d&3)!==0)&&(Gc=!0)),o=u}qn!==0&&qn!==5||_l(t),kr!==0&&(kr=0)}function qg(t,n){for(var a=t.suspendedLanes,o=t.pingedLanes,u=t.expirationTimes,d=t.pendingLanes&-62914561;0<d;){var y=31-Ze(d),C=1<<y,H=u[y];H===-1?((C&a)===0||(C&o)!==0)&&(u[y]=Ve(C,n)):H<=n&&(t.expiredLanes|=C),d&=~C}if(n=xn,a=It,a=be(t,t===n?a:0,t.cancelPendingCommit!==null||t.timeoutHandle!==-1),o=t.callbackNode,a===0||t===n&&(on===2||on===9)||t.cancelPendingCommit!==null)return o!==null&&o!==null&&Xt(o),t.callbackNode=null,t.callbackPriority=0;if((a&3)===0||Pe(t,a)){if(n=a&-a,n===t.callbackPriority)return n;switch(o!==null&&Xt(o),ls(a)){case 2:case 8:a=M;break;case 32:a=Z;break;case 268435456:a=xe;break;default:a=Z}return o=Yg.bind(null,t),a=vn(a,o),t.callbackPriority=n,t.callbackNode=a,n}return o!==null&&o!==null&&Xt(o),t.callbackPriority=2,t.callbackNode=null,2}function Yg(t,n){if(qn!==0&&qn!==5)return t.callbackNode=null,t.callbackPriority=0,null;var a=t.callbackNode;if(Ic()&&t.callbackNode!==a)return null;var o=It;return o=be(t,t===xn?o:0,t.cancelPendingCommit!==null||t.timeoutHandle!==-1),o===0?null:(Cg(t,o,n),qg(t,Ft()),t.callbackNode!=null&&t.callbackNode===a?Yg.bind(null,t):null)}function jg(t,n){if(Ic())return null;Cg(t,n,!0)}function mS(){wS(function(){(an&6)!==0?vn(P,pS):Wg()})}function Rd(){if(kr===0){var t=Ks;t===0&&(t=lt,lt<<=1,(lt&261888)===0&&(lt=256)),kr=t}return kr}function Zg(t){return t==null||typeof t=="symbol"||typeof t=="boolean"?null:typeof t=="function"?t:Fi(""+t)}function Kg(t,n){var a=n.ownerDocument.createElement("input");return a.name=n.name,a.value=n.value,t.id&&a.setAttribute("form",t.id),n.parentNode.insertBefore(a,n),t=new FormData(t),a.parentNode.removeChild(a),t}function gS(t,n,a,o,u){if(n==="submit"&&a&&a.stateNode===u){var d=Zg((u[In]||null).action),y=o.submitter;y&&(n=(n=y[In]||null)?Zg(n.formAction):y.getAttribute("formAction"),n!==null&&(d=n,y=null));var C=new An("action","action",null,o,u);t.push({event:C,listeners:[{instance:null,listener:function(){if(o.defaultPrevented){if(kr!==0){var H=y?Kg(u,y):new FormData(u);Zf(a,{pending:!0,data:H,method:u.method,action:d},null,H)}}else typeof d=="function"&&(C.preventDefault(),H=y?Kg(u,y):new FormData(u),Zf(a,{pending:!0,data:H,method:u.method,action:d},d,H))},currentTarget:u}]})}}for(var Ud=0;Ud<df.length;Ud++){var Dd=df[Ud],xS=Dd.toLowerCase(),vS=Dd[0].toUpperCase()+Dd.slice(1);va(xS,"on"+vS)}va(wm,"onAnimationEnd"),va(Cm,"onAnimationIteration"),va(Rm,"onAnimationStart"),va("dblclick","onDoubleClick"),va("focusin","onFocus"),va("focusout","onBlur"),va(Oy,"onTransitionRun"),va(Py,"onTransitionStart"),va(zy,"onTransitionCancel"),va(Um,"onTransitionEnd"),X("onMouseEnter",["mouseout","mouseover"]),X("onMouseLeave",["mouseout","mouseover"]),X("onPointerEnter",["pointerout","pointerover"]),X("onPointerLeave",["pointerout","pointerover"]),A("onChange","change click focusin focusout input keydown keyup selectionchange".split(" ")),A("onSelect","focusout contextmenu dragend focusin keydown keyup mousedown mouseup selectionchange".split(" ")),A("onBeforeInput",["compositionend","keypress","textInput","paste"]),A("onCompositionEnd","compositionend focusout keydown keypress keyup mousedown".split(" ")),A("onCompositionStart","compositionstart focusout keydown keypress keyup mousedown".split(" ")),A("onCompositionUpdate","compositionupdate focusout keydown keypress keyup mousedown".split(" "));var yl="abort canplay canplaythrough durationchange emptied encrypted ended error loadeddata loadedmetadata loadstart pause play playing progress ratechange resize seeked seeking stalled suspend timeupdate volumechange waiting".split(" "),_S=new Set("beforetoggle cancel close invalid load scroll scrollend toggle".split(" ").concat(yl));function Qg(t,n){n=(n&4)!==0;for(var a=0;a<t.length;a++){var o=t[a],u=o.event;o=o.listeners;e:{var d=void 0;if(n)for(var y=o.length-1;0<=y;y--){var C=o[y],H=C.instance,he=C.currentTarget;if(C=C.listener,H!==d&&u.isPropagationStopped())break e;d=C,u.currentTarget=he;try{d(u)}catch(Me){nc(Me)}u.currentTarget=null,d=H}else for(y=0;y<o.length;y++){if(C=o[y],H=C.instance,he=C.currentTarget,C=C.listener,H!==d&&u.isPropagationStopped())break e;d=C,u.currentTarget=he;try{d(u)}catch(Me){nc(Me)}u.currentTarget=null,d=H}}}}function zt(t,n){var a=n[Wt];a===void 0&&(a=n[Wt]=new Set);var o=t+"__bubble";a.has(o)||(Jg(n,t,2,!1),a.add(o))}function Nd(t,n,a){var o=0;n&&(o|=4),Jg(a,t,o,n)}var Vc="_reactListening"+Math.random().toString(36).slice(2);function Ld(t){if(!t[Vc]){t[Vc]=!0,Da.forEach(function(a){a!=="selectionchange"&&(_S.has(a)||Nd(a,!1,t),Nd(a,!0,t))});var n=t.nodeType===9?t:t.ownerDocument;n===null||n[Vc]||(n[Vc]=!0,Nd("selectionchange",!1,n))}}function Jg(t,n,a,o){switch(wx(n)){case 2:var u=YS;break;case 8:u=jS;break;default:u=jd}a=u.bind(null,n,a,t),u=void 0,!Qe||n!=="touchstart"&&n!=="touchmove"&&n!=="wheel"||(u=!0),o?u!==void 0?t.addEventListener(n,a,{capture:!0,passive:u}):t.addEventListener(n,a,!0):u!==void 0?t.addEventListener(n,a,{passive:u}):t.addEventListener(n,a,!1)}function Od(t,n,a,o,u){var d=o;if((n&1)===0&&(n&2)===0&&o!==null)e:for(;;){if(o===null)return;var y=o.tag;if(y===3||y===4){var C=o.stateNode.containerInfo;if(C===u)break;if(y===4)for(y=o.return;y!==null;){var H=y.tag;if((H===3||H===4)&&y.stateNode.containerInfo===u)return;y=y.return}for(;C!==null;){if(y=Pi(C),y===null)return;if(H=y.tag,H===5||H===6||H===26||H===27){o=d=y;continue e}C=C.parentNode}}o=o.return}te(function(){var he=d,Me=Hs(a),Te=[];e:{var me=Dm.get(t);if(me!==void 0){var ve=An,tt=t;switch(t){case"keypress":if(Yt(a)===0)break e;case"keydown":case"keyup":ve=dy;break;case"focusin":tt="focus",ve=$i;break;case"focusout":tt="blur",ve=$i;break;case"beforeblur":case"afterblur":ve=$i;break;case"click":if(a.button===2)break e;case"auxclick":case"dblclick":case"mousedown":case"mousemove":case"mouseup":case"mouseout":case"mouseover":case"contextmenu":ve=La;break;case"drag":case"dragend":case"dragenter":case"dragexit":case"dragleave":case"dragover":case"dragstart":case"drop":ve=nn;break;case"touchcancel":case"touchend":case"touchmove":case"touchstart":ve=my;break;case wm:case Cm:case Rm:ve=xa;break;case Um:ve=xy;break;case"scroll":case"scrollend":ve=ma;break;case"wheel":ve=_y;break;case"copy":case"cut":case"paste":ve=Za;break;case"gotpointercapture":case"lostpointercapture":case"pointercancel":case"pointerdown":case"pointermove":case"pointerout":case"pointerover":case"pointerup":ve=lm;break;case"toggle":case"beforetoggle":ve=Sy}var ft=(n&4)!==0,mn=!ft&&(t==="scroll"||t==="scrollend"),$=ft?me!==null?me+"Capture":null:me;ft=[];for(var Y=he,de;Y!==null;){var Ee=Y;if(de=Ee.stateNode,Ee=Ee.tag,Ee!==5&&Ee!==26&&Ee!==27||de===null||$===null||(Ee=Ue(Y,$),Ee!=null&&ft.push(Sl(Y,Ee,de))),mn)break;Y=Y.return}0<ft.length&&(me=new ve(me,tt,null,a,Me),Te.push({event:me,listeners:ft}))}}if((n&7)===0){e:{if(me=t==="mouseover"||t==="pointerover",ve=t==="mouseout"||t==="pointerout",me&&a!==Is&&(tt=a.relatedTarget||a.fromElement)&&(Pi(tt)||tt[Kn]))break e;if((ve||me)&&(me=Me.window===Me?Me:(me=Me.ownerDocument)?me.defaultView||me.parentWindow:window,ve?(tt=a.relatedTarget||a.toElement,ve=he,tt=tt?Pi(tt):null,tt!==null&&(mn=c(tt),ft=tt.tag,tt!==mn||ft!==5&&ft!==27&&ft!==6)&&(tt=null)):(ve=null,tt=he),ve!==tt)){if(ft=La,Ee="onMouseLeave",$="onMouseEnter",Y="mouse",(t==="pointerout"||t==="pointerover")&&(ft=lm,Ee="onPointerLeave",$="onPointerEnter",Y="pointer"),mn=ve==null?me:ha(ve),de=tt==null?me:ha(tt),me=new ft(Ee,Y+"leave",ve,a,Me),me.target=mn,me.relatedTarget=de,Ee=null,Pi(Me)===he&&(ft=new ft($,Y+"enter",tt,a,Me),ft.target=de,ft.relatedTarget=mn,Ee=ft),mn=Ee,ve&&tt)t:{for(ft=yS,$=ve,Y=tt,de=0,Ee=$;Ee;Ee=ft(Ee))de++;Ee=0;for(var ct=Y;ct;ct=ft(ct))Ee++;for(;0<de-Ee;)$=ft($),de--;for(;0<Ee-de;)Y=ft(Y),Ee--;for(;de--;){if($===Y||Y!==null&&$===Y.alternate){ft=$;break t}$=ft($),Y=ft(Y)}ft=null}else ft=null;ve!==null&&$g(Te,me,ve,ft,!1),tt!==null&&mn!==null&&$g(Te,mn,tt,ft,!0)}}e:{if(me=he?ha(he):window,ve=me.nodeName&&me.nodeName.toLowerCase(),ve==="select"||ve==="input"&&me.type==="file")var Jt=gm;else if(pm(me))if(xm)Jt=Dy;else{Jt=Ry;var ot=Cy}else ve=me.nodeName,!ve||ve.toLowerCase()!=="input"||me.type!=="checkbox"&&me.type!=="radio"?he&&Ai(he.elementType)&&(Jt=gm):Jt=Uy;if(Jt&&(Jt=Jt(t,he))){mm(Te,Jt,a,Me);break e}ot&&ot(t,me,he),t==="focusout"&&he&&me.type==="number"&&he.memoizedProps.value!=null&&Rn(me,"number",me.value)}switch(ot=he?ha(he):window,t){case"focusin":(pm(ot)||ot.contentEditable==="true")&&(Vs=ot,cf=he,Ko=null);break;case"focusout":Ko=cf=Vs=null;break;case"mousedown":uf=!0;break;case"contextmenu":case"mouseup":case"dragend":uf=!1,Tm(Te,a,Me);break;case"selectionchange":if(Ly)break;case"keydown":case"keyup":Tm(Te,a,Me)}var Ct;if(rf)e:{switch(t){case"compositionstart":var Ht="onCompositionStart";break e;case"compositionend":Ht="onCompositionEnd";break e;case"compositionupdate":Ht="onCompositionUpdate";break e}Ht=void 0}else Gs?dm(t,a)&&(Ht="onCompositionEnd"):t==="keydown"&&a.keyCode===229&&(Ht="onCompositionStart");Ht&&(cm&&a.locale!=="ko"&&(Gs||Ht!=="onCompositionStart"?Ht==="onCompositionEnd"&&Gs&&(Ct=Ot()):(Le=Me,st="value"in Le?Le.value:Le.textContent,Gs=!0)),ot=kc(he,Ht),0<ot.length&&(Ht=new Ci(Ht,t,null,a,Me),Te.push({event:Ht,listeners:ot}),Ct?Ht.data=Ct:(Ct=hm(a),Ct!==null&&(Ht.data=Ct)))),(Ct=My?Ey(t,a):Ty(t,a))&&(Ht=kc(he,"onBeforeInput"),0<Ht.length&&(ot=new Ci("onBeforeInput","beforeinput",null,a,Me),Te.push({event:ot,listeners:Ht}),ot.data=Ct)),gS(Te,t,he,a,Me)}Qg(Te,n)})}function Sl(t,n,a){return{instance:t,listener:n,currentTarget:a}}function kc(t,n){for(var a=n+"Capture",o=[];t!==null;){var u=t,d=u.stateNode;if(u=u.tag,u!==5&&u!==26&&u!==27||d===null||(u=Ue(t,a),u!=null&&o.unshift(Sl(t,u,d)),u=Ue(t,n),u!=null&&o.push(Sl(t,u,d))),t.tag===3)return o;t=t.return}return[]}function yS(t){if(t===null)return null;do t=t.return;while(t&&t.tag!==5&&t.tag!==27);return t||null}function $g(t,n,a,o,u){for(var d=n._reactName,y=[];a!==null&&a!==o;){var C=a,H=C.alternate,he=C.stateNode;if(C=C.tag,H!==null&&H===o)break;C!==5&&C!==26&&C!==27||he===null||(H=he,u?(he=Ue(a,d),he!=null&&y.unshift(Sl(a,he,H))):u||(he=Ue(a,d),he!=null&&y.push(Sl(a,he,H)))),a=a.return}y.length!==0&&t.push({event:n,listeners:y})}var SS=/\r\n?/g,bS=/\u0000|\uFFFD/g;function ex(t){return(typeof t=="string"?t:""+t).replace(SS,`
`).replace(bS,"")}function tx(t,n){return n=ex(n),ex(t)===n}function pn(t,n,a,o,u,d){switch(a){case"children":typeof o=="string"?n==="body"||n==="textarea"&&o===""||ni(t,o):(typeof o=="number"||typeof o=="bigint")&&n!=="body"&&ni(t,""+o);break;case"className":Ie(t,"class",o);break;case"tabIndex":Ie(t,"tabindex",o);break;case"dir":case"role":case"viewBox":case"width":case"height":Ie(t,a,o);break;case"style":gn(t,o,d);break;case"data":if(n!=="object"){Ie(t,"data",o);break}case"src":case"href":if(o===""&&(n!=="a"||a!=="href")){t.removeAttribute(a);break}if(o==null||typeof o=="function"||typeof o=="symbol"||typeof o=="boolean"){t.removeAttribute(a);break}o=Fi(""+o),t.setAttribute(a,o);break;case"action":case"formAction":if(typeof o=="function"){t.setAttribute(a,"javascript:throw new Error('A React form was unexpectedly submitted. If you called form.submit() manually, consider using form.requestSubmit() instead. If you\\'re trying to use event.stopPropagation() in a submit event handler, consider also calling event.preventDefault().')");break}else typeof d=="function"&&(a==="formAction"?(n!=="input"&&pn(t,n,"name",u.name,u,null),pn(t,n,"formEncType",u.formEncType,u,null),pn(t,n,"formMethod",u.formMethod,u,null),pn(t,n,"formTarget",u.formTarget,u,null)):(pn(t,n,"encType",u.encType,u,null),pn(t,n,"method",u.method,u,null),pn(t,n,"target",u.target,u,null)));if(o==null||typeof o=="symbol"||typeof o=="boolean"){t.removeAttribute(a);break}o=Fi(""+o),t.setAttribute(a,o);break;case"onClick":o!=null&&(t.onclick=yi);break;case"onScroll":o!=null&&zt("scroll",t);break;case"onScrollEnd":o!=null&&zt("scrollend",t);break;case"dangerouslySetInnerHTML":if(o!=null){if(typeof o!="object"||!("__html"in o))throw Error(s(61));if(a=o.__html,a!=null){if(u.children!=null)throw Error(s(60));t.innerHTML=a}}break;case"multiple":t.multiple=o&&typeof o!="function"&&typeof o!="symbol";break;case"muted":t.muted=o&&typeof o!="function"&&typeof o!="symbol";break;case"suppressContentEditableWarning":case"suppressHydrationWarning":case"defaultValue":case"defaultChecked":case"innerHTML":case"ref":break;case"autoFocus":break;case"xlinkHref":if(o==null||typeof o=="function"||typeof o=="boolean"||typeof o=="symbol"){t.removeAttribute("xlink:href");break}a=Fi(""+o),t.setAttributeNS("http://www.w3.org/1999/xlink","xlink:href",a);break;case"contentEditable":case"spellCheck":case"draggable":case"value":case"autoReverse":case"externalResourcesRequired":case"focusable":case"preserveAlpha":o!=null&&typeof o!="function"&&typeof o!="symbol"?t.setAttribute(a,""+o):t.removeAttribute(a);break;case"inert":case"allowFullScreen":case"async":case"autoPlay":case"controls":case"default":case"defer":case"disabled":case"disablePictureInPicture":case"disableRemotePlayback":case"formNoValidate":case"hidden":case"loop":case"noModule":case"noValidate":case"open":case"playsInline":case"readOnly":case"required":case"reversed":case"scoped":case"seamless":case"itemScope":o&&typeof o!="function"&&typeof o!="symbol"?t.setAttribute(a,""):t.removeAttribute(a);break;case"capture":case"download":o===!0?t.setAttribute(a,""):o!==!1&&o!=null&&typeof o!="function"&&typeof o!="symbol"?t.setAttribute(a,o):t.removeAttribute(a);break;case"cols":case"rows":case"size":case"span":o!=null&&typeof o!="function"&&typeof o!="symbol"&&!isNaN(o)&&1<=o?t.setAttribute(a,o):t.removeAttribute(a);break;case"rowSpan":case"start":o==null||typeof o=="function"||typeof o=="symbol"||isNaN(o)?t.removeAttribute(a):t.setAttribute(a,o);break;case"popover":zt("beforetoggle",t),zt("toggle",t),We(t,"popover",o);break;case"xlinkActuate":qe(t,"http://www.w3.org/1999/xlink","xlink:actuate",o);break;case"xlinkArcrole":qe(t,"http://www.w3.org/1999/xlink","xlink:arcrole",o);break;case"xlinkRole":qe(t,"http://www.w3.org/1999/xlink","xlink:role",o);break;case"xlinkShow":qe(t,"http://www.w3.org/1999/xlink","xlink:show",o);break;case"xlinkTitle":qe(t,"http://www.w3.org/1999/xlink","xlink:title",o);break;case"xlinkType":qe(t,"http://www.w3.org/1999/xlink","xlink:type",o);break;case"xmlBase":qe(t,"http://www.w3.org/XML/1998/namespace","xml:base",o);break;case"xmlLang":qe(t,"http://www.w3.org/XML/1998/namespace","xml:lang",o);break;case"xmlSpace":qe(t,"http://www.w3.org/XML/1998/namespace","xml:space",o);break;case"is":We(t,"is",o);break;case"innerText":case"textContent":break;default:(!(2<a.length)||a[0]!=="o"&&a[0]!=="O"||a[1]!=="n"&&a[1]!=="N")&&(a=en.get(a)||a,We(t,a,o))}}function Pd(t,n,a,o,u,d){switch(a){case"style":gn(t,o,d);break;case"dangerouslySetInnerHTML":if(o!=null){if(typeof o!="object"||!("__html"in o))throw Error(s(61));if(a=o.__html,a!=null){if(u.children!=null)throw Error(s(60));t.innerHTML=a}}break;case"children":typeof o=="string"?ni(t,o):(typeof o=="number"||typeof o=="bigint")&&ni(t,""+o);break;case"onScroll":o!=null&&zt("scroll",t);break;case"onScrollEnd":o!=null&&zt("scrollend",t);break;case"onClick":o!=null&&(t.onclick=yi);break;case"suppressContentEditableWarning":case"suppressHydrationWarning":case"innerHTML":case"ref":break;case"innerText":case"textContent":break;default:if(!_i.hasOwnProperty(a))e:{if(a[0]==="o"&&a[1]==="n"&&(u=a.endsWith("Capture"),n=a.slice(2,u?a.length-7:void 0),d=t[In]||null,d=d!=null?d[a]:null,typeof d=="function"&&t.removeEventListener(n,d,u),typeof o=="function")){typeof d!="function"&&d!==null&&(a in t?t[a]=null:t.hasAttribute(a)&&t.removeAttribute(a)),t.addEventListener(n,o,u);break e}a in t?t[a]=o:o===!0?t.setAttribute(a,""):We(t,a,o)}}}function oi(t,n,a){switch(n){case"div":case"span":case"svg":case"path":case"a":case"g":case"p":case"li":break;case"img":zt("error",t),zt("load",t);var o=!1,u=!1,d;for(d in a)if(a.hasOwnProperty(d)){var y=a[d];if(y!=null)switch(d){case"src":o=!0;break;case"srcSet":u=!0;break;case"children":case"dangerouslySetInnerHTML":throw Error(s(137,n));default:pn(t,n,d,y,a,null)}}u&&pn(t,n,"srcSet",a.srcSet,a,null),o&&pn(t,n,"src",a.src,a,null);return;case"input":zt("invalid",t);var C=d=y=u=null,H=null,he=null;for(o in a)if(a.hasOwnProperty(o)){var Me=a[o];if(Me!=null)switch(o){case"name":u=Me;break;case"type":y=Me;break;case"checked":H=Me;break;case"defaultChecked":he=Me;break;case"value":d=Me;break;case"defaultValue":C=Me;break;case"children":case"dangerouslySetInnerHTML":if(Me!=null)throw Error(s(137,n));break;default:pn(t,n,o,Me,a,null)}}Ke(t,d,C,H,he,y,u,!1);return;case"select":zt("invalid",t),o=y=d=null;for(u in a)if(a.hasOwnProperty(u)&&(C=a[u],C!=null))switch(u){case"value":d=C;break;case"defaultValue":y=C;break;case"multiple":o=C;default:pn(t,n,u,C,a,null)}n=d,a=y,t.multiple=!!o,n!=null?Et(t,!!o,n,!1):a!=null&&Et(t,!!o,a,!0);return;case"textarea":zt("invalid",t),d=u=o=null;for(y in a)if(a.hasOwnProperty(y)&&(C=a[y],C!=null))switch(y){case"value":o=C;break;case"defaultValue":u=C;break;case"children":d=C;break;case"dangerouslySetInnerHTML":if(C!=null)throw Error(s(91));break;default:pn(t,n,y,C,a,null)}ci(t,o,u,d);return;case"option":for(H in a)if(a.hasOwnProperty(H)&&(o=a[H],o!=null))switch(H){case"selected":t.selected=o&&typeof o!="function"&&typeof o!="symbol";break;default:pn(t,n,H,o,a,null)}return;case"dialog":zt("beforetoggle",t),zt("toggle",t),zt("cancel",t),zt("close",t);break;case"iframe":case"object":zt("load",t);break;case"video":case"audio":for(o=0;o<yl.length;o++)zt(yl[o],t);break;case"image":zt("error",t),zt("load",t);break;case"details":zt("toggle",t);break;case"embed":case"source":case"link":zt("error",t),zt("load",t);case"area":case"base":case"br":case"col":case"hr":case"keygen":case"meta":case"param":case"track":case"wbr":case"menuitem":for(he in a)if(a.hasOwnProperty(he)&&(o=a[he],o!=null))switch(he){case"children":case"dangerouslySetInnerHTML":throw Error(s(137,n));default:pn(t,n,he,o,a,null)}return;default:if(Ai(n)){for(Me in a)a.hasOwnProperty(Me)&&(o=a[Me],o!==void 0&&Pd(t,n,Me,o,a,void 0));return}}for(C in a)a.hasOwnProperty(C)&&(o=a[C],o!=null&&pn(t,n,C,o,a,null))}function MS(t,n,a,o){switch(n){case"div":case"span":case"svg":case"path":case"a":case"g":case"p":case"li":break;case"input":var u=null,d=null,y=null,C=null,H=null,he=null,Me=null;for(ve in a){var Te=a[ve];if(a.hasOwnProperty(ve)&&Te!=null)switch(ve){case"checked":break;case"value":break;case"defaultValue":H=Te;default:o.hasOwnProperty(ve)||pn(t,n,ve,null,o,Te)}}for(var me in o){var ve=o[me];if(Te=a[me],o.hasOwnProperty(me)&&(ve!=null||Te!=null))switch(me){case"type":d=ve;break;case"name":u=ve;break;case"checked":he=ve;break;case"defaultChecked":Me=ve;break;case"value":y=ve;break;case"defaultValue":C=ve;break;case"children":case"dangerouslySetInnerHTML":if(ve!=null)throw Error(s(137,n));break;default:ve!==Te&&pn(t,n,me,ve,o,Te)}}Tn(t,y,C,H,he,Me,d,u);return;case"select":ve=y=C=me=null;for(d in a)if(H=a[d],a.hasOwnProperty(d)&&H!=null)switch(d){case"value":break;case"multiple":ve=H;default:o.hasOwnProperty(d)||pn(t,n,d,null,o,H)}for(u in o)if(d=o[u],H=a[u],o.hasOwnProperty(u)&&(d!=null||H!=null))switch(u){case"value":me=d;break;case"defaultValue":C=d;break;case"multiple":y=d;default:d!==H&&pn(t,n,u,d,o,H)}n=C,a=y,o=ve,me!=null?Et(t,!!a,me,!1):!!o!=!!a&&(n!=null?Et(t,!!a,n,!0):Et(t,!!a,a?[]:"",!1));return;case"textarea":ve=me=null;for(C in a)if(u=a[C],a.hasOwnProperty(C)&&u!=null&&!o.hasOwnProperty(C))switch(C){case"value":break;case"children":break;default:pn(t,n,C,null,o,u)}for(y in o)if(u=o[y],d=a[y],o.hasOwnProperty(y)&&(u!=null||d!=null))switch(y){case"value":me=u;break;case"defaultValue":ve=u;break;case"children":break;case"dangerouslySetInnerHTML":if(u!=null)throw Error(s(91));break;default:u!==d&&pn(t,n,y,u,o,d)}Qn(t,me,ve);return;case"option":for(var tt in a)if(me=a[tt],a.hasOwnProperty(tt)&&me!=null&&!o.hasOwnProperty(tt))switch(tt){case"selected":t.selected=!1;break;default:pn(t,n,tt,null,o,me)}for(H in o)if(me=o[H],ve=a[H],o.hasOwnProperty(H)&&me!==ve&&(me!=null||ve!=null))switch(H){case"selected":t.selected=me&&typeof me!="function"&&typeof me!="symbol";break;default:pn(t,n,H,me,o,ve)}return;case"img":case"link":case"area":case"base":case"br":case"col":case"embed":case"hr":case"keygen":case"meta":case"param":case"source":case"track":case"wbr":case"menuitem":for(var ft in a)me=a[ft],a.hasOwnProperty(ft)&&me!=null&&!o.hasOwnProperty(ft)&&pn(t,n,ft,null,o,me);for(he in o)if(me=o[he],ve=a[he],o.hasOwnProperty(he)&&me!==ve&&(me!=null||ve!=null))switch(he){case"children":case"dangerouslySetInnerHTML":if(me!=null)throw Error(s(137,n));break;default:pn(t,n,he,me,o,ve)}return;default:if(Ai(n)){for(var mn in a)me=a[mn],a.hasOwnProperty(mn)&&me!==void 0&&!o.hasOwnProperty(mn)&&Pd(t,n,mn,void 0,o,me);for(Me in o)me=o[Me],ve=a[Me],!o.hasOwnProperty(Me)||me===ve||me===void 0&&ve===void 0||Pd(t,n,Me,me,o,ve);return}}for(var $ in a)me=a[$],a.hasOwnProperty($)&&me!=null&&!o.hasOwnProperty($)&&pn(t,n,$,null,o,me);for(Te in o)me=o[Te],ve=a[Te],!o.hasOwnProperty(Te)||me===ve||me==null&&ve==null||pn(t,n,Te,me,o,ve)}function nx(t){switch(t){case"css":case"script":case"font":case"img":case"image":case"input":case"link":return!0;default:return!1}}function ES(){if(typeof performance.getEntriesByType=="function"){for(var t=0,n=0,a=performance.getEntriesByType("resource"),o=0;o<a.length;o++){var u=a[o],d=u.transferSize,y=u.initiatorType,C=u.duration;if(d&&C&&nx(y)){for(y=0,C=u.responseEnd,o+=1;o<a.length;o++){var H=a[o],he=H.startTime;if(he>C)break;var Me=H.transferSize,Te=H.initiatorType;Me&&nx(Te)&&(H=H.responseEnd,y+=Me*(H<C?1:(C-he)/(H-he)))}if(--o,n+=8*(d+y)/(u.duration/1e3),t++,10<t)break}}if(0<t)return n/t/1e6}return navigator.connection&&(t=navigator.connection.downlink,typeof t=="number")?t:5}var zd=null,Fd=null;function Xc(t){return t.nodeType===9?t:t.ownerDocument}function ix(t){switch(t){case"http://www.w3.org/2000/svg":return 1;case"http://www.w3.org/1998/Math/MathML":return 2;default:return 0}}function ax(t,n){if(t===0)switch(n){case"svg":return 1;case"math":return 2;default:return 0}return t===1&&n==="foreignObject"?0:t}function Bd(t,n){return t==="textarea"||t==="noscript"||typeof n.children=="string"||typeof n.children=="number"||typeof n.children=="bigint"||typeof n.dangerouslySetInnerHTML=="object"&&n.dangerouslySetInnerHTML!==null&&n.dangerouslySetInnerHTML.__html!=null}var Id=null;function TS(){var t=window.event;return t&&t.type==="popstate"?t===Id?!1:(Id=t,!0):(Id=null,!1)}var rx=typeof setTimeout=="function"?setTimeout:void 0,AS=typeof clearTimeout=="function"?clearTimeout:void 0,sx=typeof Promise=="function"?Promise:void 0,wS=typeof queueMicrotask=="function"?queueMicrotask:typeof sx<"u"?function(t){return sx.resolve(null).then(t).catch(CS)}:rx;function CS(t){setTimeout(function(){throw t})}function Xr(t){return t==="head"}function ox(t,n){var a=n,o=0;do{var u=a.nextSibling;if(t.removeChild(a),u&&u.nodeType===8)if(a=u.data,a==="/$"||a==="/&"){if(o===0){t.removeChild(u),go(n);return}o--}else if(a==="$"||a==="$?"||a==="$~"||a==="$!"||a==="&")o++;else if(a==="html")bl(t.ownerDocument.documentElement);else if(a==="head"){a=t.ownerDocument.head,bl(a);for(var d=a.firstChild;d;){var y=d.nextSibling,C=d.nodeName;d[qt]||C==="SCRIPT"||C==="STYLE"||C==="LINK"&&d.rel.toLowerCase()==="stylesheet"||a.removeChild(d),d=y}}else a==="body"&&bl(t.ownerDocument.body);a=u}while(a);go(n)}function lx(t,n){var a=t;t=0;do{var o=a.nextSibling;if(a.nodeType===1?n?(a._stashedDisplay=a.style.display,a.style.display="none"):(a.style.display=a._stashedDisplay||"",a.getAttribute("style")===""&&a.removeAttribute("style")):a.nodeType===3&&(n?(a._stashedText=a.nodeValue,a.nodeValue=""):a.nodeValue=a._stashedText||""),o&&o.nodeType===8)if(a=o.data,a==="/$"){if(t===0)break;t--}else a!=="$"&&a!=="$?"&&a!=="$~"&&a!=="$!"||t++;a=o}while(a)}function Hd(t){var n=t.firstChild;for(n&&n.nodeType===10&&(n=n.nextSibling);n;){var a=n;switch(n=n.nextSibling,a.nodeName){case"HTML":case"HEAD":case"BODY":Hd(a),Ki(a);continue;case"SCRIPT":case"STYLE":continue;case"LINK":if(a.rel.toLowerCase()==="stylesheet")continue}t.removeChild(a)}}function RS(t,n,a,o){for(;t.nodeType===1;){var u=a;if(t.nodeName.toLowerCase()!==n.toLowerCase()){if(!o&&(t.nodeName!=="INPUT"||t.type!=="hidden"))break}else if(o){if(!t[qt])switch(n){case"meta":if(!t.hasAttribute("itemprop"))break;return t;case"link":if(d=t.getAttribute("rel"),d==="stylesheet"&&t.hasAttribute("data-precedence"))break;if(d!==u.rel||t.getAttribute("href")!==(u.href==null||u.href===""?null:u.href)||t.getAttribute("crossorigin")!==(u.crossOrigin==null?null:u.crossOrigin)||t.getAttribute("title")!==(u.title==null?null:u.title))break;return t;case"style":if(t.hasAttribute("data-precedence"))break;return t;case"script":if(d=t.getAttribute("src"),(d!==(u.src==null?null:u.src)||t.getAttribute("type")!==(u.type==null?null:u.type)||t.getAttribute("crossorigin")!==(u.crossOrigin==null?null:u.crossOrigin))&&d&&t.hasAttribute("async")&&!t.hasAttribute("itemprop"))break;return t;default:return t}}else if(n==="input"&&t.type==="hidden"){var d=u.name==null?null:""+u.name;if(u.type==="hidden"&&t.getAttribute("name")===d)return t}else return t;if(t=oa(t.nextSibling),t===null)break}return null}function US(t,n,a){if(n==="")return null;for(;t.nodeType!==3;)if((t.nodeType!==1||t.nodeName!=="INPUT"||t.type!=="hidden")&&!a||(t=oa(t.nextSibling),t===null))return null;return t}function cx(t,n){for(;t.nodeType!==8;)if((t.nodeType!==1||t.nodeName!=="INPUT"||t.type!=="hidden")&&!n||(t=oa(t.nextSibling),t===null))return null;return t}function Gd(t){return t.data==="$?"||t.data==="$~"}function Vd(t){return t.data==="$!"||t.data==="$?"&&t.ownerDocument.readyState!=="loading"}function DS(t,n){var a=t.ownerDocument;if(t.data==="$~")t._reactRetry=n;else if(t.data!=="$?"||a.readyState!=="loading")n();else{var o=function(){n(),a.removeEventListener("DOMContentLoaded",o)};a.addEventListener("DOMContentLoaded",o),t._reactRetry=o}}function oa(t){for(;t!=null;t=t.nextSibling){var n=t.nodeType;if(n===1||n===3)break;if(n===8){if(n=t.data,n==="$"||n==="$!"||n==="$?"||n==="$~"||n==="&"||n==="F!"||n==="F")break;if(n==="/$"||n==="/&")return null}}return t}var kd=null;function ux(t){t=t.nextSibling;for(var n=0;t;){if(t.nodeType===8){var a=t.data;if(a==="/$"||a==="/&"){if(n===0)return oa(t.nextSibling);n--}else a!=="$"&&a!=="$!"&&a!=="$?"&&a!=="$~"&&a!=="&"||n++}t=t.nextSibling}return null}function fx(t){t=t.previousSibling;for(var n=0;t;){if(t.nodeType===8){var a=t.data;if(a==="$"||a==="$!"||a==="$?"||a==="$~"||a==="&"){if(n===0)return t;n--}else a!=="/$"&&a!=="/&"||n++}t=t.previousSibling}return null}function dx(t,n,a){switch(n=Xc(a),t){case"html":if(t=n.documentElement,!t)throw Error(s(452));return t;case"head":if(t=n.head,!t)throw Error(s(453));return t;case"body":if(t=n.body,!t)throw Error(s(454));return t;default:throw Error(s(451))}}function bl(t){for(var n=t.attributes;n.length;)t.removeAttributeNode(n[0]);Ki(t)}var la=new Map,hx=new Set;function Wc(t){return typeof t.getRootNode=="function"?t.getRootNode():t.nodeType===9?t:t.ownerDocument}var ur=V.d;V.d={f:NS,r:LS,D:OS,C:PS,L:zS,m:FS,X:IS,S:BS,M:HS};function NS(){var t=ur.f(),n=zc();return t||n}function LS(t){var n=zi(t);n!==null&&n.tag===5&&n.type==="form"?U0(n):ur.r(t)}var ho=typeof document>"u"?null:document;function px(t,n,a){var o=ho;if(o&&typeof n=="string"&&n){var u=Mt(n);u='link[rel="'+t+'"][href="'+u+'"]',typeof a=="string"&&(u+='[crossorigin="'+a+'"]'),hx.has(u)||(hx.add(u),t={rel:t,crossOrigin:a,href:n},o.querySelector(u)===null&&(n=o.createElement("link"),oi(n,"link",t),sn(n),o.head.appendChild(n)))}}function OS(t){ur.D(t),px("dns-prefetch",t,null)}function PS(t,n){ur.C(t,n),px("preconnect",t,n)}function zS(t,n,a){ur.L(t,n,a);var o=ho;if(o&&t&&n){var u='link[rel="preload"][as="'+Mt(n)+'"]';n==="image"&&a&&a.imageSrcSet?(u+='[imagesrcset="'+Mt(a.imageSrcSet)+'"]',typeof a.imageSizes=="string"&&(u+='[imagesizes="'+Mt(a.imageSizes)+'"]')):u+='[href="'+Mt(t)+'"]';var d=u;switch(n){case"style":d=po(t);break;case"script":d=mo(t)}la.has(d)||(t=v({rel:"preload",href:n==="image"&&a&&a.imageSrcSet?void 0:t,as:n},a),la.set(d,t),o.querySelector(u)!==null||n==="style"&&o.querySelector(Ml(d))||n==="script"&&o.querySelector(El(d))||(n=o.createElement("link"),oi(n,"link",t),sn(n),o.head.appendChild(n)))}}function FS(t,n){ur.m(t,n);var a=ho;if(a&&t){var o=n&&typeof n.as=="string"?n.as:"script",u='link[rel="modulepreload"][as="'+Mt(o)+'"][href="'+Mt(t)+'"]',d=u;switch(o){case"audioworklet":case"paintworklet":case"serviceworker":case"sharedworker":case"worker":case"script":d=mo(t)}if(!la.has(d)&&(t=v({rel:"modulepreload",href:t},n),la.set(d,t),a.querySelector(u)===null)){switch(o){case"audioworklet":case"paintworklet":case"serviceworker":case"sharedworker":case"worker":case"script":if(a.querySelector(El(d)))return}o=a.createElement("link"),oi(o,"link",t),sn(o),a.head.appendChild(o)}}}function BS(t,n,a){ur.S(t,n,a);var o=ho;if(o&&t){var u=pa(o).hoistableStyles,d=po(t);n=n||"default";var y=u.get(d);if(!y){var C={loading:0,preload:null};if(y=o.querySelector(Ml(d)))C.loading=5;else{t=v({rel:"stylesheet",href:t,"data-precedence":n},a),(a=la.get(d))&&Xd(t,a);var H=y=o.createElement("link");sn(H),oi(H,"link",t),H._p=new Promise(function(he,Me){H.onload=he,H.onerror=Me}),H.addEventListener("load",function(){C.loading|=1}),H.addEventListener("error",function(){C.loading|=2}),C.loading|=4,qc(y,n,o)}y={type:"stylesheet",instance:y,count:1,state:C},u.set(d,y)}}}function IS(t,n){ur.X(t,n);var a=ho;if(a&&t){var o=pa(a).hoistableScripts,u=mo(t),d=o.get(u);d||(d=a.querySelector(El(u)),d||(t=v({src:t,async:!0},n),(n=la.get(u))&&Wd(t,n),d=a.createElement("script"),sn(d),oi(d,"link",t),a.head.appendChild(d)),d={type:"script",instance:d,count:1,state:null},o.set(u,d))}}function HS(t,n){ur.M(t,n);var a=ho;if(a&&t){var o=pa(a).hoistableScripts,u=mo(t),d=o.get(u);d||(d=a.querySelector(El(u)),d||(t=v({src:t,async:!0,type:"module"},n),(n=la.get(u))&&Wd(t,n),d=a.createElement("script"),sn(d),oi(d,"link",t),a.head.appendChild(d)),d={type:"script",instance:d,count:1,state:null},o.set(u,d))}}function mx(t,n,a,o){var u=(u=Xe.current)?Wc(u):null;if(!u)throw Error(s(446));switch(t){case"meta":case"title":return null;case"style":return typeof a.precedence=="string"&&typeof a.href=="string"?(n=po(a.href),a=pa(u).hoistableStyles,o=a.get(n),o||(o={type:"style",instance:null,count:0,state:null},a.set(n,o)),o):{type:"void",instance:null,count:0,state:null};case"link":if(a.rel==="stylesheet"&&typeof a.href=="string"&&typeof a.precedence=="string"){t=po(a.href);var d=pa(u).hoistableStyles,y=d.get(t);if(y||(u=u.ownerDocument||u,y={type:"stylesheet",instance:null,count:0,state:{loading:0,preload:null}},d.set(t,y),(d=u.querySelector(Ml(t)))&&!d._p&&(y.instance=d,y.state.loading=5),la.has(t)||(a={rel:"preload",as:"style",href:a.href,crossOrigin:a.crossOrigin,integrity:a.integrity,media:a.media,hrefLang:a.hrefLang,referrerPolicy:a.referrerPolicy},la.set(t,a),d||GS(u,t,a,y.state))),n&&o===null)throw Error(s(528,""));return y}if(n&&o!==null)throw Error(s(529,""));return null;case"script":return n=a.async,a=a.src,typeof a=="string"&&n&&typeof n!="function"&&typeof n!="symbol"?(n=mo(a),a=pa(u).hoistableScripts,o=a.get(n),o||(o={type:"script",instance:null,count:0,state:null},a.set(n,o)),o):{type:"void",instance:null,count:0,state:null};default:throw Error(s(444,t))}}function po(t){return'href="'+Mt(t)+'"'}function Ml(t){return'link[rel="stylesheet"]['+t+"]"}function gx(t){return v({},t,{"data-precedence":t.precedence,precedence:null})}function GS(t,n,a,o){t.querySelector('link[rel="preload"][as="style"]['+n+"]")?o.loading=1:(n=t.createElement("link"),o.preload=n,n.addEventListener("load",function(){return o.loading|=1}),n.addEventListener("error",function(){return o.loading|=2}),oi(n,"link",a),sn(n),t.head.appendChild(n))}function mo(t){return'[src="'+Mt(t)+'"]'}function El(t){return"script[async]"+t}function xx(t,n,a){if(n.count++,n.instance===null)switch(n.type){case"style":var o=t.querySelector('style[data-href~="'+Mt(a.href)+'"]');if(o)return n.instance=o,sn(o),o;var u=v({},a,{"data-href":a.href,"data-precedence":a.precedence,href:null,precedence:null});return o=(t.ownerDocument||t).createElement("style"),sn(o),oi(o,"style",u),qc(o,a.precedence,t),n.instance=o;case"stylesheet":u=po(a.href);var d=t.querySelector(Ml(u));if(d)return n.state.loading|=4,n.instance=d,sn(d),d;o=gx(a),(u=la.get(u))&&Xd(o,u),d=(t.ownerDocument||t).createElement("link"),sn(d);var y=d;return y._p=new Promise(function(C,H){y.onload=C,y.onerror=H}),oi(d,"link",o),n.state.loading|=4,qc(d,a.precedence,t),n.instance=d;case"script":return d=mo(a.src),(u=t.querySelector(El(d)))?(n.instance=u,sn(u),u):(o=a,(u=la.get(d))&&(o=v({},a),Wd(o,u)),t=t.ownerDocument||t,u=t.createElement("script"),sn(u),oi(u,"link",o),t.head.appendChild(u),n.instance=u);case"void":return null;default:throw Error(s(443,n.type))}else n.type==="stylesheet"&&(n.state.loading&4)===0&&(o=n.instance,n.state.loading|=4,qc(o,a.precedence,t));return n.instance}function qc(t,n,a){for(var o=a.querySelectorAll('link[rel="stylesheet"][data-precedence],style[data-precedence]'),u=o.length?o[o.length-1]:null,d=u,y=0;y<o.length;y++){var C=o[y];if(C.dataset.precedence===n)d=C;else if(d!==u)break}d?d.parentNode.insertBefore(t,d.nextSibling):(n=a.nodeType===9?a.head:a,n.insertBefore(t,n.firstChild))}function Xd(t,n){t.crossOrigin==null&&(t.crossOrigin=n.crossOrigin),t.referrerPolicy==null&&(t.referrerPolicy=n.referrerPolicy),t.title==null&&(t.title=n.title)}function Wd(t,n){t.crossOrigin==null&&(t.crossOrigin=n.crossOrigin),t.referrerPolicy==null&&(t.referrerPolicy=n.referrerPolicy),t.integrity==null&&(t.integrity=n.integrity)}var Yc=null;function vx(t,n,a){if(Yc===null){var o=new Map,u=Yc=new Map;u.set(a,o)}else u=Yc,o=u.get(a),o||(o=new Map,u.set(a,o));if(o.has(t))return o;for(o.set(t,null),a=a.getElementsByTagName(t),u=0;u<a.length;u++){var d=a[u];if(!(d[qt]||d[Sn]||t==="link"&&d.getAttribute("rel")==="stylesheet")&&d.namespaceURI!=="http://www.w3.org/2000/svg"){var y=d.getAttribute(n)||"";y=t+y;var C=o.get(y);C?C.push(d):o.set(y,[d])}}return o}function _x(t,n,a){t=t.ownerDocument||t,t.head.insertBefore(a,n==="title"?t.querySelector("head > title"):null)}function VS(t,n,a){if(a===1||n.itemProp!=null)return!1;switch(t){case"meta":case"title":return!0;case"style":if(typeof n.precedence!="string"||typeof n.href!="string"||n.href==="")break;return!0;case"link":if(typeof n.rel!="string"||typeof n.href!="string"||n.href===""||n.onLoad||n.onError)break;switch(n.rel){case"stylesheet":return t=n.disabled,typeof n.precedence=="string"&&t==null;default:return!0}case"script":if(n.async&&typeof n.async!="function"&&typeof n.async!="symbol"&&!n.onLoad&&!n.onError&&n.src&&typeof n.src=="string")return!0}return!1}function yx(t){return!(t.type==="stylesheet"&&(t.state.loading&3)===0)}function kS(t,n,a,o){if(a.type==="stylesheet"&&(typeof o.media!="string"||matchMedia(o.media).matches!==!1)&&(a.state.loading&4)===0){if(a.instance===null){var u=po(o.href),d=n.querySelector(Ml(u));if(d){n=d._p,n!==null&&typeof n=="object"&&typeof n.then=="function"&&(t.count++,t=jc.bind(t),n.then(t,t)),a.state.loading|=4,a.instance=d,sn(d);return}d=n.ownerDocument||n,o=gx(o),(u=la.get(u))&&Xd(o,u),d=d.createElement("link"),sn(d);var y=d;y._p=new Promise(function(C,H){y.onload=C,y.onerror=H}),oi(d,"link",o),a.instance=d}t.stylesheets===null&&(t.stylesheets=new Map),t.stylesheets.set(a,n),(n=a.state.preload)&&(a.state.loading&3)===0&&(t.count++,a=jc.bind(t),n.addEventListener("load",a),n.addEventListener("error",a))}}var qd=0;function XS(t,n){return t.stylesheets&&t.count===0&&Kc(t,t.stylesheets),0<t.count||0<t.imgCount?function(a){var o=setTimeout(function(){if(t.stylesheets&&Kc(t,t.stylesheets),t.unsuspend){var d=t.unsuspend;t.unsuspend=null,d()}},6e4+n);0<t.imgBytes&&qd===0&&(qd=62500*ES());var u=setTimeout(function(){if(t.waitingForImages=!1,t.count===0&&(t.stylesheets&&Kc(t,t.stylesheets),t.unsuspend)){var d=t.unsuspend;t.unsuspend=null,d()}},(t.imgBytes>qd?50:800)+n);return t.unsuspend=a,function(){t.unsuspend=null,clearTimeout(o),clearTimeout(u)}}:null}function jc(){if(this.count--,this.count===0&&(this.imgCount===0||!this.waitingForImages)){if(this.stylesheets)Kc(this,this.stylesheets);else if(this.unsuspend){var t=this.unsuspend;this.unsuspend=null,t()}}}var Zc=null;function Kc(t,n){t.stylesheets=null,t.unsuspend!==null&&(t.count++,Zc=new Map,n.forEach(WS,t),Zc=null,jc.call(t))}function WS(t,n){if(!(n.state.loading&4)){var a=Zc.get(t);if(a)var o=a.get(null);else{a=new Map,Zc.set(t,a);for(var u=t.querySelectorAll("link[data-precedence],style[data-precedence]"),d=0;d<u.length;d++){var y=u[d];(y.nodeName==="LINK"||y.getAttribute("media")!=="not all")&&(a.set(y.dataset.precedence,y),o=y)}o&&a.set(null,o)}u=n.instance,y=u.getAttribute("data-precedence"),d=a.get(y)||o,d===o&&a.set(null,u),a.set(y,u),this.count++,o=jc.bind(this),u.addEventListener("load",o),u.addEventListener("error",o),d?d.parentNode.insertBefore(u,d.nextSibling):(t=t.nodeType===9?t.head:t,t.insertBefore(u,t.firstChild)),n.state.loading|=4}}var Tl={$$typeof:G,Provider:null,Consumer:null,_currentValue:ee,_currentValue2:ee,_threadCount:0};function qS(t,n,a,o,u,d,y,C,H){this.tag=1,this.containerInfo=t,this.pingCache=this.current=this.pendingChildren=null,this.timeoutHandle=-1,this.callbackNode=this.next=this.pendingContext=this.context=this.cancelPendingCommit=null,this.callbackPriority=0,this.expirationTimes=et(-1),this.entangledLanes=this.shellSuspendCounter=this.errorRecoveryDisabledLanes=this.expiredLanes=this.warmLanes=this.pingedLanes=this.suspendedLanes=this.pendingLanes=0,this.entanglements=et(0),this.hiddenUpdates=et(null),this.identifierPrefix=o,this.onUncaughtError=u,this.onCaughtError=d,this.onRecoverableError=y,this.pooledCache=null,this.pooledCacheLanes=0,this.formState=H,this.incompleteTransitions=new Map}function Sx(t,n,a,o,u,d,y,C,H,he,Me,Te){return t=new qS(t,n,a,y,H,he,Me,Te,C),n=1,d===!0&&(n|=24),d=Ii(3,null,null,n),t.current=d,d.stateNode=t,n=Tf(),n.refCount++,t.pooledCache=n,n.refCount++,d.memoizedState={element:o,isDehydrated:a,cache:n},Rf(d),t}function bx(t){return t?(t=Ws,t):Ws}function Mx(t,n,a,o,u,d){u=bx(u),o.context===null?o.context=u:o.pendingContext=u,o=Lr(n),o.payload={element:a},d=d===void 0?null:d,d!==null&&(o.callback=d),a=Or(t,o,n),a!==null&&(Li(a,t,n),il(a,t,n))}function Ex(t,n){if(t=t.memoizedState,t!==null&&t.dehydrated!==null){var a=t.retryLane;t.retryLane=a!==0&&a<n?a:n}}function Yd(t,n){Ex(t,n),(t=t.alternate)&&Ex(t,n)}function Tx(t){if(t.tag===13||t.tag===31){var n=fs(t,67108864);n!==null&&Li(n,t,67108864),Yd(t,67108864)}}function Ax(t){if(t.tag===13||t.tag===31){var n=Xi();n=Zi(n);var a=fs(t,n);a!==null&&Li(a,t,n),Yd(t,n)}}var Qc=!0;function YS(t,n,a,o){var u=B.T;B.T=null;var d=V.p;try{V.p=2,jd(t,n,a,o)}finally{V.p=d,B.T=u}}function jS(t,n,a,o){var u=B.T;B.T=null;var d=V.p;try{V.p=8,jd(t,n,a,o)}finally{V.p=d,B.T=u}}function jd(t,n,a,o){if(Qc){var u=Zd(o);if(u===null)Od(t,n,o,Jc,a),Cx(t,o);else if(KS(u,t,n,a,o))o.stopPropagation();else if(Cx(t,o),n&4&&-1<ZS.indexOf(t)){for(;u!==null;){var d=zi(u);if(d!==null)switch(d.tag){case 3:if(d=d.stateNode,d.current.memoizedState.isDehydrated){var y=Oe(d.pendingLanes);if(y!==0){var C=d;for(C.pendingLanes|=2,C.entangledLanes|=2;y;){var H=1<<31-Ze(y);C.entanglements[1]|=H,y&=~H}Fa(d),(an&6)===0&&(Oc=Ft()+500,_l(0))}}break;case 31:case 13:C=fs(d,2),C!==null&&Li(C,d,2),zc(),Yd(d,2)}if(d=Zd(o),d===null&&Od(t,n,o,Jc,a),d===u)break;u=d}u!==null&&o.stopPropagation()}else Od(t,n,o,null,a)}}function Zd(t){return t=Hs(t),Kd(t)}var Jc=null;function Kd(t){if(Jc=null,t=Pi(t),t!==null){var n=c(t);if(n===null)t=null;else{var a=n.tag;if(a===13){if(t=f(n),t!==null)return t;t=null}else if(a===31){if(t=h(n),t!==null)return t;t=null}else if(a===3){if(n.stateNode.current.memoizedState.isDehydrated)return n.tag===3?n.stateNode.containerInfo:null;t=null}else n!==t&&(t=null)}}return Jc=t,null}function wx(t){switch(t){case"beforetoggle":case"cancel":case"click":case"close":case"contextmenu":case"copy":case"cut":case"auxclick":case"dblclick":case"dragend":case"dragstart":case"drop":case"focusin":case"focusout":case"input":case"invalid":case"keydown":case"keypress":case"keyup":case"mousedown":case"mouseup":case"paste":case"pause":case"play":case"pointercancel":case"pointerdown":case"pointerup":case"ratechange":case"reset":case"resize":case"seeked":case"submit":case"toggle":case"touchcancel":case"touchend":case"touchstart":case"volumechange":case"change":case"selectionchange":case"textInput":case"compositionstart":case"compositionend":case"compositionupdate":case"beforeblur":case"afterblur":case"beforeinput":case"blur":case"fullscreenchange":case"focus":case"hashchange":case"popstate":case"select":case"selectstart":return 2;case"drag":case"dragenter":case"dragexit":case"dragleave":case"dragover":case"mousemove":case"mouseout":case"mouseover":case"pointermove":case"pointerout":case"pointerover":case"scroll":case"touchmove":case"wheel":case"mouseenter":case"mouseleave":case"pointerenter":case"pointerleave":return 8;case"message":switch(Ut()){case P:return 2;case M:return 8;case Z:case ce:return 32;case xe:return 268435456;default:return 32}default:return 32}}var Qd=!1,Wr=null,qr=null,Yr=null,Al=new Map,wl=new Map,jr=[],ZS="mousedown mouseup touchcancel touchend touchstart auxclick dblclick pointercancel pointerdown pointerup dragend dragstart drop compositionend compositionstart keydown keypress keyup input textInput copy cut paste click change contextmenu reset".split(" ");function Cx(t,n){switch(t){case"focusin":case"focusout":Wr=null;break;case"dragenter":case"dragleave":qr=null;break;case"mouseover":case"mouseout":Yr=null;break;case"pointerover":case"pointerout":Al.delete(n.pointerId);break;case"gotpointercapture":case"lostpointercapture":wl.delete(n.pointerId)}}function Cl(t,n,a,o,u,d){return t===null||t.nativeEvent!==d?(t={blockedOn:n,domEventName:a,eventSystemFlags:o,nativeEvent:d,targetContainers:[u]},n!==null&&(n=zi(n),n!==null&&Tx(n)),t):(t.eventSystemFlags|=o,n=t.targetContainers,u!==null&&n.indexOf(u)===-1&&n.push(u),t)}function KS(t,n,a,o,u){switch(n){case"focusin":return Wr=Cl(Wr,t,n,a,o,u),!0;case"dragenter":return qr=Cl(qr,t,n,a,o,u),!0;case"mouseover":return Yr=Cl(Yr,t,n,a,o,u),!0;case"pointerover":var d=u.pointerId;return Al.set(d,Cl(Al.get(d)||null,t,n,a,o,u)),!0;case"gotpointercapture":return d=u.pointerId,wl.set(d,Cl(wl.get(d)||null,t,n,a,o,u)),!0}return!1}function Rx(t){var n=Pi(t.target);if(n!==null){var a=c(n);if(a!==null){if(n=a.tag,n===13){if(n=f(a),n!==null){t.blockedOn=n,da(t.priority,function(){Ax(a)});return}}else if(n===31){if(n=h(a),n!==null){t.blockedOn=n,da(t.priority,function(){Ax(a)});return}}else if(n===3&&a.stateNode.current.memoizedState.isDehydrated){t.blockedOn=a.tag===3?a.stateNode.containerInfo:null;return}}}t.blockedOn=null}function $c(t){if(t.blockedOn!==null)return!1;for(var n=t.targetContainers;0<n.length;){var a=Zd(t.nativeEvent);if(a===null){a=t.nativeEvent;var o=new a.constructor(a.type,a);Is=o,a.target.dispatchEvent(o),Is=null}else return n=zi(a),n!==null&&Tx(n),t.blockedOn=a,!1;n.shift()}return!0}function Ux(t,n,a){$c(t)&&a.delete(n)}function QS(){Qd=!1,Wr!==null&&$c(Wr)&&(Wr=null),qr!==null&&$c(qr)&&(qr=null),Yr!==null&&$c(Yr)&&(Yr=null),Al.forEach(Ux),wl.forEach(Ux)}function eu(t,n){t.blockedOn===n&&(t.blockedOn=null,Qd||(Qd=!0,r.unstable_scheduleCallback(r.unstable_NormalPriority,QS)))}var tu=null;function Dx(t){tu!==t&&(tu=t,r.unstable_scheduleCallback(r.unstable_NormalPriority,function(){tu===t&&(tu=null);for(var n=0;n<t.length;n+=3){var a=t[n],o=t[n+1],u=t[n+2];if(typeof o!="function"){if(Kd(o||a)===null)continue;break}var d=zi(a);d!==null&&(t.splice(n,3),n-=3,Zf(d,{pending:!0,data:u,method:a.method,action:o},o,u))}}))}function go(t){function n(H){return eu(H,t)}Wr!==null&&eu(Wr,t),qr!==null&&eu(qr,t),Yr!==null&&eu(Yr,t),Al.forEach(n),wl.forEach(n);for(var a=0;a<jr.length;a++){var o=jr[a];o.blockedOn===t&&(o.blockedOn=null)}for(;0<jr.length&&(a=jr[0],a.blockedOn===null);)Rx(a),a.blockedOn===null&&jr.shift();if(a=(t.ownerDocument||t).$$reactFormReplay,a!=null)for(o=0;o<a.length;o+=3){var u=a[o],d=a[o+1],y=u[In]||null;if(typeof d=="function")y||Dx(a);else if(y){var C=null;if(d&&d.hasAttribute("formAction")){if(u=d,y=d[In]||null)C=y.formAction;else if(Kd(u)!==null)continue}else C=y.action;typeof C=="function"?a[o+1]=C:(a.splice(o,3),o-=3),Dx(a)}}}function Nx(){function t(d){d.canIntercept&&d.info==="react-transition"&&d.intercept({handler:function(){return new Promise(function(y){return u=y})},focusReset:"manual",scroll:"manual"})}function n(){u!==null&&(u(),u=null),o||setTimeout(a,20)}function a(){if(!o&&!navigation.transition){var d=navigation.currentEntry;d&&d.url!=null&&navigation.navigate(d.url,{state:d.getState(),info:"react-transition",history:"replace"})}}if(typeof navigation=="object"){var o=!1,u=null;return navigation.addEventListener("navigate",t),navigation.addEventListener("navigatesuccess",n),navigation.addEventListener("navigateerror",n),setTimeout(a,100),function(){o=!0,navigation.removeEventListener("navigate",t),navigation.removeEventListener("navigatesuccess",n),navigation.removeEventListener("navigateerror",n),u!==null&&(u(),u=null)}}}function Jd(t){this._internalRoot=t}nu.prototype.render=Jd.prototype.render=function(t){var n=this._internalRoot;if(n===null)throw Error(s(409));var a=n.current,o=Xi();Mx(a,o,t,n,null,null)},nu.prototype.unmount=Jd.prototype.unmount=function(){var t=this._internalRoot;if(t!==null){this._internalRoot=null;var n=t.containerInfo;Mx(t.current,2,null,t,null,null),zc(),n[Kn]=null}};function nu(t){this._internalRoot=t}nu.prototype.unstable_scheduleHydration=function(t){if(t){var n=Ra();t={blockedOn:null,target:t,priority:n};for(var a=0;a<jr.length&&n!==0&&n<jr[a].priority;a++);jr.splice(a,0,t),a===0&&Rx(t)}};var Lx=e.version;if(Lx!=="19.2.0")throw Error(s(527,Lx,"19.2.0"));V.findDOMNode=function(t){var n=t._reactInternals;if(n===void 0)throw typeof t.render=="function"?Error(s(188)):(t=Object.keys(t).join(","),Error(s(268,t)));return t=p(n),t=t!==null?g(t):null,t=t===null?null:t.stateNode,t};var JS={bundleType:0,version:"19.2.0",rendererPackageName:"react-dom",currentDispatcherRef:B,reconcilerVersion:"19.2.0"};if(typeof __REACT_DEVTOOLS_GLOBAL_HOOK__<"u"){var iu=__REACT_DEVTOOLS_GLOBAL_HOOK__;if(!iu.isDisabled&&iu.supportsFiber)try{pe=iu.inject(JS),ye=iu}catch{}}return Ul.createRoot=function(t,n){if(!l(t))throw Error(s(299));var a=!1,o="",u=H0,d=G0,y=V0;return n!=null&&(n.unstable_strictMode===!0&&(a=!0),n.identifierPrefix!==void 0&&(o=n.identifierPrefix),n.onUncaughtError!==void 0&&(u=n.onUncaughtError),n.onCaughtError!==void 0&&(d=n.onCaughtError),n.onRecoverableError!==void 0&&(y=n.onRecoverableError)),n=Sx(t,1,!1,null,null,a,o,null,u,d,y,Nx),t[Kn]=n.current,Ld(t),new Jd(n)},Ul.hydrateRoot=function(t,n,a){if(!l(t))throw Error(s(299));var o=!1,u="",d=H0,y=G0,C=V0,H=null;return a!=null&&(a.unstable_strictMode===!0&&(o=!0),a.identifierPrefix!==void 0&&(u=a.identifierPrefix),a.onUncaughtError!==void 0&&(d=a.onUncaughtError),a.onCaughtError!==void 0&&(y=a.onCaughtError),a.onRecoverableError!==void 0&&(C=a.onRecoverableError),a.formState!==void 0&&(H=a.formState)),n=Sx(t,1,!0,n,a??null,o,u,H,d,y,C,Nx),n.context=bx(null),a=n.current,o=Xi(),o=Zi(o),u=Lr(o),u.callback=null,Or(a,u,o),a=o,n.current.lanes=a,Je(n,a),Fa(n),t[Kn]=n.current,Ld(t),new nu(n)},Ul.version="19.2.0",Ul}var Xx;function u1(){if(Xx)return th.exports;Xx=1;function r(){if(!(typeof __REACT_DEVTOOLS_GLOBAL_HOOK__>"u"||typeof __REACT_DEVTOOLS_GLOBAL_HOOK__.checkDCE!="function"))try{__REACT_DEVTOOLS_GLOBAL_HOOK__.checkDCE(r)}catch(e){console.error(e)}}return r(),th.exports=c1(),th.exports}var f1=u1();/**
 * @license @tabler/icons-react v3.49.0 - MIT
 *
 * This source code is licensed under the MIT license.
 * See the LICENSE file in the root directory of this source tree.
 */var d1={outline:{xmlns:"http://www.w3.org/2000/svg",width:24,height:24,viewBox:"0 0 24 24",fill:"none",stroke:"currentColor",strokeWidth:2,strokeLinecap:"round",strokeLinejoin:"round"},filled:{xmlns:"http://www.w3.org/2000/svg",width:24,height:24,viewBox:"0 0 24 24",fill:"currentColor",stroke:"none"}};/**
 * @license @tabler/icons-react v3.49.0 - MIT
 *
 * This source code is licensed under the MIT license.
 * See the LICENSE file in the root directory of this source tree.
 */const xi=(r,e,i,s)=>{const l=nt.forwardRef(({color:c="currentColor",size:f=24,stroke:h=2,title:m,className:p,children:g,...v},x)=>nt.createElement("svg",{ref:x,...d1[r],width:f,height:f,className:["tabler-icon",`tabler-icon-${e}`,p].filter(Boolean).join(" "),...r==="filled"?{fill:c}:{strokeWidth:h,stroke:c},...v},[m&&nt.createElement("title",{key:"svg-title"},m),...s.map(([_,E])=>nt.createElement(_,E)),...Array.isArray(g)?g:[g]]));return l.displayName=`${i}`,l};/**
 * @license @tabler/icons-react v3.49.0 - MIT
 *
 * This source code is licensed under the MIT license.
 * See the LICENSE file in the root directory of this source tree.
 */const h1=[["path",{d:"M12 6a2 2 0 1 0 4 0a2 2 0 1 0 -4 0",key:"svg-0"}],["path",{d:"M4 6l8 0",key:"svg-1"}],["path",{d:"M16 6l4 0",key:"svg-2"}],["path",{d:"M6 12a2 2 0 1 0 4 0a2 2 0 1 0 -4 0",key:"svg-3"}],["path",{d:"M4 12l2 0",key:"svg-4"}],["path",{d:"M10 12l10 0",key:"svg-5"}],["path",{d:"M15 18a2 2 0 1 0 4 0a2 2 0 1 0 -4 0",key:"svg-6"}],["path",{d:"M4 18l11 0",key:"svg-7"}],["path",{d:"M19 18l1 0",key:"svg-8"}]],p1=xi("outline","adjustments-horizontal","AdjustmentsHorizontal",h1);/**
 * @license @tabler/icons-react v3.49.0 - MIT
 *
 * This source code is licensed under the MIT license.
 * See the LICENSE file in the root directory of this source tree.
 */const m1=[["path",{d:"M7 7l10 10",key:"svg-0"}],["path",{d:"M17 8l0 9l-9 0",key:"svg-1"}]],g1=xi("outline","arrow-down-right","ArrowDownRight",m1);/**
 * @license @tabler/icons-react v3.49.0 - MIT
 *
 * This source code is licensed under the MIT license.
 * See the LICENSE file in the root directory of this source tree.
 */const x1=[["path",{d:"M17 7l-10 10",key:"svg-0"}],["path",{d:"M8 7l9 0l0 9",key:"svg-1"}]],v1=xi("outline","arrow-up-right","ArrowUpRight",x1);/**
 * @license @tabler/icons-react v3.49.0 - MIT
 *
 * This source code is licensed under the MIT license.
 * See the LICENSE file in the root directory of this source tree.
 */const _1=[["path",{d:"M3 12a9 9 0 1 0 18 0a9 9 0 0 0 -18 0",key:"svg-0"}],["path",{d:"M12 7v5l3 3",key:"svg-1"}]],Wx=xi("outline","clock","Clock",_1);/**
 * @license @tabler/icons-react v3.49.0 - MIT
 *
 * This source code is licensed under the MIT license.
 * See the LICENSE file in the root directory of this source tree.
 */const y1=[["path",{d:"M12 6h-6a2 2 0 0 0 -2 2v10a2 2 0 0 0 2 2h10a2 2 0 0 0 2 -2v-6",key:"svg-0"}],["path",{d:"M11 13l9 -9",key:"svg-1"}],["path",{d:"M15 4h5v5",key:"svg-2"}]],Xl=xi("outline","external-link","ExternalLink",y1);/**
 * @license @tabler/icons-react v3.49.0 - MIT
 *
 * This source code is licensed under the MIT license.
 * See the LICENSE file in the root directory of this source tree.
 */const S1=[["path",{d:"M3 12a9 9 0 1 0 18 0a9 9 0 0 0 -18 0",key:"svg-0"}],["path",{d:"M12 9h.01",key:"svg-1"}],["path",{d:"M11 12h1v4h1",key:"svg-2"}]],zp=xi("outline","info-circle","InfoCircle",S1);/**
 * @license @tabler/icons-react v3.49.0 - MIT
 *
 * This source code is licensed under the MIT license.
 * See the LICENSE file in the root directory of this source tree.
 */const b1=[["path",{d:"M9 15l6 -6",key:"svg-0"}],["path",{d:"M11 6l.463 -.536a5 5 0 0 1 7.071 7.072l-.534 .464",key:"svg-1"}],["path",{d:"M13 18l-.397 .534a5.068 5.068 0 0 1 -7.127 0a4.972 4.972 0 0 1 0 -7.071l.524 -.463",key:"svg-2"}]],Hu=xi("outline","link","Link",b1);/**
 * @license @tabler/icons-react v3.49.0 - MIT
 *
 * This source code is licensed under the MIT license.
 * See the LICENSE file in the root directory of this source tree.
 */const M1=[["path",{d:"M5 12l14 0",key:"svg-0"}]],E1=xi("outline","minus","Minus",M1);/**
 * @license @tabler/icons-react v3.49.0 - MIT
 *
 * This source code is licensed under the MIT license.
 * See the LICENSE file in the root directory of this source tree.
 */const T1=[["path",{d:"M16 6h3a1 1 0 0 1 1 1v11a2 2 0 0 1 -4 0v-13a1 1 0 0 0 -1 -1h-10a1 1 0 0 0 -1 1v12a3 3 0 0 0 3 3h11",key:"svg-0"}],["path",{d:"M8 8l4 0",key:"svg-1"}],["path",{d:"M8 12l4 0",key:"svg-2"}],["path",{d:"M8 16l4 0",key:"svg-3"}]],A1=xi("outline","news","News",T1);/**
 * @license @tabler/icons-react v3.49.0 - MIT
 *
 * This source code is licensed under the MIT license.
 * See the LICENSE file in the root directory of this source tree.
 */const w1=[["path",{d:"M6 6a1 1 0 0 1 1 -1h2a1 1 0 0 1 1 1v12a1 1 0 0 1 -1 1h-2a1 1 0 0 1 -1 -1l0 -12",key:"svg-0"}],["path",{d:"M14 6a1 1 0 0 1 1 -1h2a1 1 0 0 1 1 1v12a1 1 0 0 1 -1 1h-2a1 1 0 0 1 -1 -1l0 -12",key:"svg-1"}]],C1=xi("outline","player-pause","PlayerPause",w1);/**
 * @license @tabler/icons-react v3.49.0 - MIT
 *
 * This source code is licensed under the MIT license.
 * See the LICENSE file in the root directory of this source tree.
 */const R1=[["path",{d:"M7 4v16l13 -8l-13 -8",key:"svg-0"}]],U1=xi("outline","player-play","PlayerPlay",R1);/**
 * @license @tabler/icons-react v3.49.0 - MIT
 *
 * This source code is licensed under the MIT license.
 * See the LICENSE file in the root directory of this source tree.
 */const D1=[["path",{d:"M4.05 11a8 8 0 1 1 .5 4m-.5 5v-5h5",key:"svg-0"}]],N1=xi("outline","rotate-clockwise","RotateClockwise",D1);/**
 * @license @tabler/icons-react v3.49.0 - MIT
 *
 * This source code is licensed under the MIT license.
 * See the LICENSE file in the root directory of this source tree.
 */const L1=[["path",{d:"M3 10a7 7 0 1 0 14 0a7 7 0 1 0 -14 0",key:"svg-0"}],["path",{d:"M21 21l-6 -6",key:"svg-1"}]],O1=xi("outline","search","Search",L1);/**
 * @license @tabler/icons-react v3.49.0 - MIT
 *
 * This source code is licensed under the MIT license.
 * See the LICENSE file in the root directory of this source tree.
 */const P1=[["path",{d:"M5 7a4 4 0 1 0 8 0a4 4 0 1 0 -8 0",key:"svg-0"}],["path",{d:"M3 21v-2a4 4 0 0 1 4 -4h4a4 4 0 0 1 4 4v2",key:"svg-1"}],["path",{d:"M16 3.13a4 4 0 0 1 0 7.75",key:"svg-2"}],["path",{d:"M21 21v-2a4 4 0 0 0 -3 -3.85",key:"svg-3"}]],z1=xi("outline","users","Users",P1);/**
 * @license @tabler/icons-react v3.49.0 - MIT
 *
 * This source code is licensed under the MIT license.
 * See the LICENSE file in the root directory of this source tree.
 */const F1=[["path",{d:"M18 6l-12 12",key:"svg-0"}],["path",{d:"M6 6l12 12",key:"svg-1"}]],Wl=xi("outline","x","X",F1);/**
 * @license @tabler/icons-react v3.49.0 - MIT
 *
 * This source code is licensed under the MIT license.
 * See the LICENSE file in the root directory of this source tree.
 */const B1=[["path",{d:"M7 3.34a10 10 0 1 1 -4.995 8.984l-.005 -.324l.005 -.324a10 10 0 0 1 4.995 -8.336z",key:"svg-0"}]],qx=xi("filled","circle-filled","CircleFilled",B1);/**
 * @license
 * Copyright 2010-2026 Three.js Authors
 * SPDX-License-Identifier: MIT
 */const Fp="186",I1=0,Yx=1,H1=2,Nu=1,G1=2,Il=3,Ls=0,Oi=1,vr=2,Sr=0,zo=1,Aa=2,jx=3,Zx=4,V1=5,No=100,k1=101,X1=102,W1=103,q1=104,Y1=200,j1=201,Z1=202,K1=203,f_=204,d_=205,Q1=206,J1=207,$1=208,eb=209,tb=210,nb=211,ib=212,ab=213,rb=214,Xh=0,Wh=1,qh=2,ql=3,Yh=4,jh=5,Zh=6,Kh=7,h_=0,sb=1,ob=2,ka=0,p_=1,m_=2,g_=3,x_=4,v_=5,__=6,y_=7,S_=300,Os=301,Io=302,rh=303,sh=304,Ku=306,Qh=1e3,_r=1001,Jh=1002,li=1003,lb=1004,au=1005,mi=1006,oh=1007,Rs=1008,fa=1009,b_=1010,M_=1011,Yl=1012,Bp=1013,Xa=1014,Ga=1015,Wa=1016,Ip=1017,Hp=1018,jl=1020,E_=35902,T_=35899,A_=1021,w_=1022,Ta=1023,Mr=1026,Us=1027,C_=1028,Gp=1029,Ps=1030,Vp=1031,kp=1033,Lu=33776,Ou=33777,Pu=33778,zu=33779,$h=35840,ep=35841,tp=35842,np=35843,ip=36196,ap=37492,rp=37496,sp=37488,op=37489,Gu=37490,lp=37491,cp=37808,up=37809,fp=37810,dp=37811,hp=37812,pp=37813,mp=37814,gp=37815,xp=37816,vp=37817,_p=37818,yp=37819,Sp=37820,bp=37821,Mp=36492,Ep=36494,Tp=36495,Ap=36283,wp=36284,Vu=36285,Cp=36286,cb=3200,Kx=0,ub=1,ns="",Ei="srgb",ku="srgb-linear",Xu="linear",cn="srgb",lh=7680,fb=519,db=512,hb=513,pb=514,Xp=515,mb=516,gb=517,Wp=518,xb=519,vb=35044,ch=35048,Qx="300 es",Va=2e3,Wu=2001;function _b(r){for(let e=r.length-1;e>=0;--e)if(r[e]>=65535)return!0;return!1}function Zl(r){return document.createElementNS("http://www.w3.org/1999/xhtml",r)}function yb(){const r=Zl("canvas");return r.style.display="block",r}const Jx={};function $x(...r){const e="THREE."+r.shift();console.log(e,...r)}function R_(r){const e=r[0];if(typeof e=="string"&&e.startsWith("TSL:")){const i=r[1];i&&i.isStackTrace?r[0]+=" "+i.getLocation():r[1]='Stack trace not available. Enable "THREE.Node.captureStackTrace" to capture stack traces.'}return r}function ht(...r){r=R_(r);const e="THREE."+r.shift();{const i=r[0];i&&i.isStackTrace?console.warn(i.getError(e)):console.warn(e,...r)}}function Zt(...r){r=R_(r);const e="THREE."+r.shift();{const i=r[0];i&&i.isStackTrace?console.error(i.getError(e)):console.error(e,...r)}}function Fo(...r){const e=r.join(" ");e in Jx||(Jx[e]=!0,ht(...r))}function Sb(r,e,i){return new Promise(function(s,l){function c(){switch(r.clientWaitSync(e,r.SYNC_FLUSH_COMMANDS_BIT,0)){case r.WAIT_FAILED:l();break;case r.TIMEOUT_EXPIRED:setTimeout(c,i);break;default:s()}}setTimeout(c,i)})}const bb={[Xh]:Wh,[qh]:Zh,[Yh]:Kh,[ql]:jh,[Wh]:Xh,[Zh]:qh,[Kh]:Yh,[jh]:ql};class Fs{addEventListener(e,i){this._listeners===void 0&&(this._listeners={});const s=this._listeners;s[e]===void 0&&(s[e]=[]),s[e].indexOf(i)===-1&&s[e].push(i)}hasEventListener(e,i){const s=this._listeners;return s===void 0?!1:s[e]!==void 0&&s[e].indexOf(i)!==-1}removeEventListener(e,i){const s=this._listeners;if(s===void 0)return;const l=s[e];if(l!==void 0){const c=l.indexOf(i);c!==-1&&l.splice(c,1)}}dispatchEvent(e){const i=this._listeners;if(i===void 0)return;const s=i[e.type];if(s!==void 0){e.target=this;const l=s.slice(0);for(let c=0,f=l.length;c<f;c++)l[c].call(this,e);e.target=null}}}const di=["00","01","02","03","04","05","06","07","08","09","0a","0b","0c","0d","0e","0f","10","11","12","13","14","15","16","17","18","19","1a","1b","1c","1d","1e","1f","20","21","22","23","24","25","26","27","28","29","2a","2b","2c","2d","2e","2f","30","31","32","33","34","35","36","37","38","39","3a","3b","3c","3d","3e","3f","40","41","42","43","44","45","46","47","48","49","4a","4b","4c","4d","4e","4f","50","51","52","53","54","55","56","57","58","59","5a","5b","5c","5d","5e","5f","60","61","62","63","64","65","66","67","68","69","6a","6b","6c","6d","6e","6f","70","71","72","73","74","75","76","77","78","79","7a","7b","7c","7d","7e","7f","80","81","82","83","84","85","86","87","88","89","8a","8b","8c","8d","8e","8f","90","91","92","93","94","95","96","97","98","99","9a","9b","9c","9d","9e","9f","a0","a1","a2","a3","a4","a5","a6","a7","a8","a9","aa","ab","ac","ad","ae","af","b0","b1","b2","b3","b4","b5","b6","b7","b8","b9","ba","bb","bc","bd","be","bf","c0","c1","c2","c3","c4","c5","c6","c7","c8","c9","ca","cb","cc","cd","ce","cf","d0","d1","d2","d3","d4","d5","d6","d7","d8","d9","da","db","dc","dd","de","df","e0","e1","e2","e3","e4","e5","e6","e7","e8","e9","ea","eb","ec","ed","ee","ef","f0","f1","f2","f3","f4","f5","f6","f7","f8","f9","fa","fb","fc","fd","fe","ff"];let ev=1234567;const Gl=Math.PI/180,Kl=180/Math.PI;function Go(){const r=Math.random()*4294967295|0,e=Math.random()*4294967295|0,i=Math.random()*4294967295|0,s=Math.random()*4294967295|0;return(di[r&255]+di[r>>8&255]+di[r>>16&255]+di[r>>24&255]+"-"+di[e&255]+di[e>>8&255]+"-"+di[e>>16&15|64]+di[e>>24&255]+"-"+di[i&63|128]+di[i>>8&255]+"-"+di[i>>16&255]+di[i>>24&255]+di[s&255]+di[s>>8&255]+di[s>>16&255]+di[s>>24&255]).toLowerCase()}function Dt(r,e,i){return Math.max(e,Math.min(i,r))}function qp(r,e){return(r%e+e)%e}function Mb(r,e,i,s,l){return s+(r-e)*(l-s)/(i-e)}function Eb(r,e,i){return r!==e?(i-r)/(e-r):0}function Vl(r,e,i){return(1-i)*r+i*e}function Tb(r,e,i,s){return Vl(r,e,1-Math.exp(-i*s))}function Ab(r,e=1){return e-Math.abs(qp(r,e*2)-e)}function wb(r,e,i){return r<=e?0:r>=i?1:(r=(r-e)/(i-e),r*r*(3-2*r))}function Cb(r,e,i){return r<=e?0:r>=i?1:(r=(r-e)/(i-e),r*r*r*(r*(r*6-15)+10))}function Rb(r,e){return r+Math.floor(Math.random()*(e-r+1))}function Ub(r,e){return r+Math.random()*(e-r)}function Db(r){return r*(.5-Math.random())}function Nb(r){r!==void 0&&(ev=r);let e=ev+=1831565813;return e=Math.imul(e^e>>>15,e|1),e^=e+Math.imul(e^e>>>7,e|61),((e^e>>>14)>>>0)/4294967296}function Lb(r){return r*Gl}function Ob(r){return r*Kl}function Pb(r){return r>0&&Number.isInteger(r)&&2**Math.round(Math.log2(r))===r}function zb(r){return Math.pow(2,Math.ceil(Math.log(r)/Math.LN2))}function Fb(r){return Math.pow(2,Math.floor(Math.log(r)/Math.LN2))}function Bb(r,e,i,s,l){const c=Math.cos,f=Math.sin,h=c(i/2),m=f(i/2),p=c((e+s)/2),g=f((e+s)/2),v=c((e-s)/2),x=f((e-s)/2),_=c((s-e)/2),E=f((s-e)/2);switch(l){case"XYX":r.set(h*g,m*v,m*x,h*p);break;case"YZY":r.set(m*x,h*g,m*v,h*p);break;case"ZXZ":r.set(m*v,m*x,h*g,h*p);break;case"XZX":r.set(h*g,m*E,m*_,h*p);break;case"YXY":r.set(m*_,h*g,m*E,h*p);break;case"ZYZ":r.set(m*E,m*_,h*g,h*p);break;default:ht("MathUtils: .setQuaternionFromProperEuler() encountered an unknown order: "+l)}}function Lo(r,e){switch(e.constructor){case Float32Array:return r;case Uint32Array:return r/4294967295;case Uint16Array:return r/65535;case Uint8Array:case Uint8ClampedArray:return r/255;case Int32Array:return Math.max(r/2147483647,-1);case Int16Array:return Math.max(r/32767,-1);case Int8Array:return Math.max(r/127,-1);default:throw new Error("THREE.MathUtils: Invalid component type.")}}function bi(r,e){switch(e.constructor){case Float32Array:return r;case Uint32Array:return Math.round(r*4294967295);case Uint16Array:return Math.round(r*65535);case Uint8Array:case Uint8ClampedArray:return Math.round(r*255);case Int32Array:return Math.round(r*2147483647);case Int16Array:return Math.round(r*32767);case Int8Array:return Math.round(r*127);default:throw new Error("THREE.MathUtils: Invalid component type.")}}const xo={DEG2RAD:Gl,RAD2DEG:Kl,generateUUID:Go,clamp:Dt,euclideanModulo:qp,mapLinear:Mb,inverseLerp:Eb,lerp:Vl,damp:Tb,pingpong:Ab,smoothstep:wb,smootherstep:Cb,randInt:Rb,randFloat:Ub,randFloatSpread:Db,seededRandom:Nb,degToRad:Lb,radToDeg:Ob,isPowerOfTwo:Pb,ceilPowerOfTwo:zb,floorPowerOfTwo:Fb,setQuaternionFromProperEuler:Bb,normalize:bi,denormalize:Lo},im=class im{constructor(e=0,i=0){this.x=e,this.y=i}get width(){return this.x}set width(e){this.x=e}get height(){return this.y}set height(e){this.y=e}set(e,i){return this.x=e,this.y=i,this}setScalar(e){return this.x=e,this.y=e,this}setX(e){return this.x=e,this}setY(e){return this.y=e,this}setComponent(e,i){switch(e){case 0:this.x=i;break;case 1:this.y=i;break;default:throw new Error("THREE.Vector2: index is out of range: "+e)}return this}getComponent(e){switch(e){case 0:return this.x;case 1:return this.y;default:throw new Error("THREE.Vector2: index is out of range: "+e)}}clone(){return new this.constructor(this.x,this.y)}copy(e){return this.x=e.x,this.y=e.y,this}add(e){return this.x+=e.x,this.y+=e.y,this}addScalar(e){return this.x+=e,this.y+=e,this}addVectors(e,i){return this.x=e.x+i.x,this.y=e.y+i.y,this}addScaledVector(e,i){return this.x+=e.x*i,this.y+=e.y*i,this}sub(e){return this.x-=e.x,this.y-=e.y,this}subScalar(e){return this.x-=e,this.y-=e,this}subVectors(e,i){return this.x=e.x-i.x,this.y=e.y-i.y,this}multiply(e){return this.x*=e.x,this.y*=e.y,this}multiplyScalar(e){return this.x*=e,this.y*=e,this}divide(e){return this.x/=e.x,this.y/=e.y,this}divideScalar(e){return this.multiplyScalar(1/e)}applyMatrix3(e){const i=this.x,s=this.y,l=e.elements;return this.x=l[0]*i+l[3]*s+l[6],this.y=l[1]*i+l[4]*s+l[7],this}min(e){return this.x=Math.min(this.x,e.x),this.y=Math.min(this.y,e.y),this}max(e){return this.x=Math.max(this.x,e.x),this.y=Math.max(this.y,e.y),this}clamp(e,i){return this.x=Dt(this.x,e.x,i.x),this.y=Dt(this.y,e.y,i.y),this}clampScalar(e,i){return this.x=Dt(this.x,e,i),this.y=Dt(this.y,e,i),this}clampLength(e,i){const s=this.length();return this.divideScalar(s||1).multiplyScalar(Dt(s,e,i))}floor(){return this.x=Math.floor(this.x),this.y=Math.floor(this.y),this}ceil(){return this.x=Math.ceil(this.x),this.y=Math.ceil(this.y),this}round(){return this.x=Math.round(this.x),this.y=Math.round(this.y),this}roundToZero(){return this.x=Math.trunc(this.x),this.y=Math.trunc(this.y),this}negate(){return this.x=-this.x,this.y=-this.y,this}dot(e){return this.x*e.x+this.y*e.y}cross(e){return this.x*e.y-this.y*e.x}lengthSq(){return this.x*this.x+this.y*this.y}length(){return Math.sqrt(this.x*this.x+this.y*this.y)}manhattanLength(){return Math.abs(this.x)+Math.abs(this.y)}normalize(){return this.divideScalar(this.length()||1)}angle(){return Math.atan2(-this.y,-this.x)+Math.PI}angleTo(e){const i=Math.sqrt(this.lengthSq()*e.lengthSq());if(i===0)return Math.PI/2;const s=this.dot(e)/i;return Math.acos(Dt(s,-1,1))}distanceTo(e){return Math.sqrt(this.distanceToSquared(e))}distanceToSquared(e){const i=this.x-e.x,s=this.y-e.y;return i*i+s*s}manhattanDistanceTo(e){return Math.abs(this.x-e.x)+Math.abs(this.y-e.y)}setLength(e){return this.normalize().multiplyScalar(e)}lerp(e,i){return this.x+=(e.x-this.x)*i,this.y+=(e.y-this.y)*i,this}lerpVectors(e,i,s){return this.x=e.x+(i.x-e.x)*s,this.y=e.y+(i.y-e.y)*s,this}equals(e){return e.x===this.x&&e.y===this.y}fromArray(e,i=0){return this.x=e[i],this.y=e[i+1],this}toArray(e=[],i=0){return e[i]=this.x,e[i+1]=this.y,e}fromBufferAttribute(e,i){return this.x=e.getX(i),this.y=e.getY(i),this}rotateAround(e,i){const s=Math.cos(i),l=Math.sin(i),c=this.x-e.x,f=this.y-e.y;return this.x=c*s-f*l+e.x,this.y=c*l+f*s+e.y,this}random(){return this.x=Math.random(),this.y=Math.random(),this}*[Symbol.iterator](){yield this.x,yield this.y}};im.prototype.isVector2=!0;let Kt=im;class ss{constructor(e=0,i=0,s=0,l=1){this.isQuaternion=!0,this._x=e,this._y=i,this._z=s,this._w=l}static slerpFlat(e,i,s,l,c,f,h){let m=s[l+0],p=s[l+1],g=s[l+2],v=s[l+3],x=c[f+0],_=c[f+1],E=c[f+2],R=c[f+3];if(v!==R||m!==x||p!==_||g!==E){let b=m*x+p*_+g*E+v*R;b<0&&(x=-x,_=-_,E=-E,R=-R,b=-b);let S=1-h;if(b<.9995){const F=Math.acos(b),G=Math.sin(F);S=Math.sin(S*F)/G,h=Math.sin(h*F)/G,m=m*S+x*h,p=p*S+_*h,g=g*S+E*h,v=v*S+R*h}else{m=m*S+x*h,p=p*S+_*h,g=g*S+E*h,v=v*S+R*h;const F=1/Math.sqrt(m*m+p*p+g*g+v*v);m*=F,p*=F,g*=F,v*=F}}e[i]=m,e[i+1]=p,e[i+2]=g,e[i+3]=v}static multiplyQuaternionsFlat(e,i,s,l,c,f){const h=s[l],m=s[l+1],p=s[l+2],g=s[l+3],v=c[f],x=c[f+1],_=c[f+2],E=c[f+3];return e[i]=h*E+g*v+m*_-p*x,e[i+1]=m*E+g*x+p*v-h*_,e[i+2]=p*E+g*_+h*x-m*v,e[i+3]=g*E-h*v-m*x-p*_,e}get x(){return this._x}set x(e){this._x=e,this._onChangeCallback()}get y(){return this._y}set y(e){this._y=e,this._onChangeCallback()}get z(){return this._z}set z(e){this._z=e,this._onChangeCallback()}get w(){return this._w}set w(e){this._w=e,this._onChangeCallback()}set(e,i,s,l){return this._x=e,this._y=i,this._z=s,this._w=l,this._onChangeCallback(),this}clone(){return new this.constructor(this._x,this._y,this._z,this._w)}copy(e){return this._x=e.x,this._y=e.y,this._z=e.z,this._w=e.w,this._onChangeCallback(),this}setFromEuler(e,i=!0){const s=e._x,l=e._y,c=e._z,f=e._order,h=Math.cos,m=Math.sin,p=h(s/2),g=h(l/2),v=h(c/2),x=m(s/2),_=m(l/2),E=m(c/2);switch(f){case"XYZ":this._x=x*g*v+p*_*E,this._y=p*_*v-x*g*E,this._z=p*g*E+x*_*v,this._w=p*g*v-x*_*E;break;case"YXZ":this._x=x*g*v+p*_*E,this._y=p*_*v-x*g*E,this._z=p*g*E-x*_*v,this._w=p*g*v+x*_*E;break;case"ZXY":this._x=x*g*v-p*_*E,this._y=p*_*v+x*g*E,this._z=p*g*E+x*_*v,this._w=p*g*v-x*_*E;break;case"ZYX":this._x=x*g*v-p*_*E,this._y=p*_*v+x*g*E,this._z=p*g*E-x*_*v,this._w=p*g*v+x*_*E;break;case"YZX":this._x=x*g*v+p*_*E,this._y=p*_*v+x*g*E,this._z=p*g*E-x*_*v,this._w=p*g*v-x*_*E;break;case"XZY":this._x=x*g*v-p*_*E,this._y=p*_*v-x*g*E,this._z=p*g*E+x*_*v,this._w=p*g*v+x*_*E;break;default:ht("Quaternion: .setFromEuler() encountered an unknown order: "+f)}return i===!0&&this._onChangeCallback(),this}setFromAxisAngle(e,i){const s=i/2,l=Math.sin(s);return this._x=e.x*l,this._y=e.y*l,this._z=e.z*l,this._w=Math.cos(s),this._onChangeCallback(),this}setFromRotationMatrix(e){const i=e.elements,s=i[0],l=i[4],c=i[8],f=i[1],h=i[5],m=i[9],p=i[2],g=i[6],v=i[10],x=s+h+v;if(x>0){const _=.5/Math.sqrt(x+1);this._w=.25/_,this._x=(g-m)*_,this._y=(c-p)*_,this._z=(f-l)*_}else if(s>h&&s>v){const _=2*Math.sqrt(1+s-h-v);this._w=(g-m)/_,this._x=.25*_,this._y=(l+f)/_,this._z=(c+p)/_}else if(h>v){const _=2*Math.sqrt(1+h-s-v);this._w=(c-p)/_,this._x=(l+f)/_,this._y=.25*_,this._z=(m+g)/_}else{const _=2*Math.sqrt(1+v-s-h);this._w=(f-l)/_,this._x=(c+p)/_,this._y=(m+g)/_,this._z=.25*_}return this._onChangeCallback(),this}setFromUnitVectors(e,i){let s=e.dot(i)+1;return s<1e-8?(s=0,Math.abs(e.x)>Math.abs(e.z)?(this._x=-e.y,this._y=e.x,this._z=0,this._w=s):(this._x=0,this._y=-e.z,this._z=e.y,this._w=s)):(this._x=e.y*i.z-e.z*i.y,this._y=e.z*i.x-e.x*i.z,this._z=e.x*i.y-e.y*i.x,this._w=s),this.normalize()}angleTo(e){return 2*Math.acos(Math.abs(Dt(this.dot(e),-1,1)))}rotateTowards(e,i){const s=this.angleTo(e);if(s===0)return this;const l=Math.min(1,i/s);return this.slerp(e,l),this}identity(){return this.set(0,0,0,1)}invert(){return this.conjugate()}conjugate(){return this._x*=-1,this._y*=-1,this._z*=-1,this._onChangeCallback(),this}dot(e){return this._x*e._x+this._y*e._y+this._z*e._z+this._w*e._w}lengthSq(){return this._x*this._x+this._y*this._y+this._z*this._z+this._w*this._w}length(){return Math.sqrt(this._x*this._x+this._y*this._y+this._z*this._z+this._w*this._w)}normalize(){let e=this.length();return e===0?(this._x=0,this._y=0,this._z=0,this._w=1):(e=1/e,this._x=this._x*e,this._y=this._y*e,this._z=this._z*e,this._w=this._w*e),this._onChangeCallback(),this}multiply(e){return this.multiplyQuaternions(this,e)}premultiply(e){return this.multiplyQuaternions(e,this)}multiplyQuaternions(e,i){const s=e._x,l=e._y,c=e._z,f=e._w,h=i._x,m=i._y,p=i._z,g=i._w;return this._x=s*g+f*h+l*p-c*m,this._y=l*g+f*m+c*h-s*p,this._z=c*g+f*p+s*m-l*h,this._w=f*g-s*h-l*m-c*p,this._onChangeCallback(),this}slerp(e,i){let s=e._x,l=e._y,c=e._z,f=e._w,h=this.dot(e);h<0&&(s=-s,l=-l,c=-c,f=-f,h=-h);let m=1-i;if(h<.9995){const p=Math.acos(h),g=Math.sin(p);m=Math.sin(m*p)/g,i=Math.sin(i*p)/g,this._x=this._x*m+s*i,this._y=this._y*m+l*i,this._z=this._z*m+c*i,this._w=this._w*m+f*i,this._onChangeCallback()}else this._x=this._x*m+s*i,this._y=this._y*m+l*i,this._z=this._z*m+c*i,this._w=this._w*m+f*i,this.normalize();return this}slerpQuaternions(e,i,s){return this.copy(e).slerp(i,s)}random(){const e=2*Math.PI*Math.random(),i=2*Math.PI*Math.random(),s=Math.random(),l=Math.sqrt(1-s),c=Math.sqrt(s);return this.set(l*Math.sin(e),l*Math.cos(e),c*Math.sin(i),c*Math.cos(i))}equals(e){return e._x===this._x&&e._y===this._y&&e._z===this._z&&e._w===this._w}fromArray(e,i=0){return this._x=e[i],this._y=e[i+1],this._z=e[i+2],this._w=e[i+3],this._onChangeCallback(),this}toArray(e=[],i=0){return e[i]=this._x,e[i+1]=this._y,e[i+2]=this._z,e[i+3]=this._w,e}fromBufferAttribute(e,i){return this._x=e.getX(i),this._y=e.getY(i),this._z=e.getZ(i),this._w=e.getW(i),this._onChangeCallback(),this}toJSON(){return this.toArray()}_onChange(e){return this._onChangeCallback=e,this}_onChangeCallback(){}*[Symbol.iterator](){yield this._x,yield this._y,yield this._z,yield this._w}}const am=class am{constructor(e=0,i=0,s=0){this.x=e,this.y=i,this.z=s}set(e,i,s){return s===void 0&&(s=this.z),this.x=e,this.y=i,this.z=s,this}setScalar(e){return this.x=e,this.y=e,this.z=e,this}setX(e){return this.x=e,this}setY(e){return this.y=e,this}setZ(e){return this.z=e,this}setComponent(e,i){switch(e){case 0:this.x=i;break;case 1:this.y=i;break;case 2:this.z=i;break;default:throw new Error("THREE.Vector3: index is out of range: "+e)}return this}getComponent(e){switch(e){case 0:return this.x;case 1:return this.y;case 2:return this.z;default:throw new Error("THREE.Vector3: index is out of range: "+e)}}clone(){return new this.constructor(this.x,this.y,this.z)}copy(e){return this.x=e.x,this.y=e.y,this.z=e.z,this}add(e){return this.x+=e.x,this.y+=e.y,this.z+=e.z,this}addScalar(e){return this.x+=e,this.y+=e,this.z+=e,this}addVectors(e,i){return this.x=e.x+i.x,this.y=e.y+i.y,this.z=e.z+i.z,this}addScaledVector(e,i){return this.x+=e.x*i,this.y+=e.y*i,this.z+=e.z*i,this}sub(e){return this.x-=e.x,this.y-=e.y,this.z-=e.z,this}subScalar(e){return this.x-=e,this.y-=e,this.z-=e,this}subVectors(e,i){return this.x=e.x-i.x,this.y=e.y-i.y,this.z=e.z-i.z,this}multiply(e){return this.x*=e.x,this.y*=e.y,this.z*=e.z,this}multiplyScalar(e){return this.x*=e,this.y*=e,this.z*=e,this}multiplyVectors(e,i){return this.x=e.x*i.x,this.y=e.y*i.y,this.z=e.z*i.z,this}applyEuler(e){return this.applyQuaternion(tv.setFromEuler(e))}applyAxisAngle(e,i){return this.applyQuaternion(tv.setFromAxisAngle(e,i))}applyMatrix3(e){const i=this.x,s=this.y,l=this.z,c=e.elements;return this.x=c[0]*i+c[3]*s+c[6]*l,this.y=c[1]*i+c[4]*s+c[7]*l,this.z=c[2]*i+c[5]*s+c[8]*l,this}applyNormalMatrix(e){return this.applyMatrix3(e).normalize()}applyMatrix4(e){const i=this.x,s=this.y,l=this.z,c=e.elements,f=1/(c[3]*i+c[7]*s+c[11]*l+c[15]);return this.x=(c[0]*i+c[4]*s+c[8]*l+c[12])*f,this.y=(c[1]*i+c[5]*s+c[9]*l+c[13])*f,this.z=(c[2]*i+c[6]*s+c[10]*l+c[14])*f,this}applyQuaternion(e){const i=this.x,s=this.y,l=this.z,c=e.x,f=e.y,h=e.z,m=e.w,p=2*(f*l-h*s),g=2*(h*i-c*l),v=2*(c*s-f*i);return this.x=i+m*p+f*v-h*g,this.y=s+m*g+h*p-c*v,this.z=l+m*v+c*g-f*p,this}project(e){return this.applyMatrix4(e.matrixWorldInverse).applyMatrix4(e.projectionMatrix)}unproject(e){return this.applyMatrix4(e.projectionMatrixInverse).applyMatrix4(e.matrixWorld)}transformDirection(e){const i=this.x,s=this.y,l=this.z,c=e.elements;return this.x=c[0]*i+c[4]*s+c[8]*l,this.y=c[1]*i+c[5]*s+c[9]*l,this.z=c[2]*i+c[6]*s+c[10]*l,this.normalize()}divide(e){return this.x/=e.x,this.y/=e.y,this.z/=e.z,this}divideScalar(e){return this.multiplyScalar(1/e)}min(e){return this.x=Math.min(this.x,e.x),this.y=Math.min(this.y,e.y),this.z=Math.min(this.z,e.z),this}max(e){return this.x=Math.max(this.x,e.x),this.y=Math.max(this.y,e.y),this.z=Math.max(this.z,e.z),this}clamp(e,i){return this.x=Dt(this.x,e.x,i.x),this.y=Dt(this.y,e.y,i.y),this.z=Dt(this.z,e.z,i.z),this}clampScalar(e,i){return this.x=Dt(this.x,e,i),this.y=Dt(this.y,e,i),this.z=Dt(this.z,e,i),this}clampLength(e,i){const s=this.length();return this.divideScalar(s||1).multiplyScalar(Dt(s,e,i))}floor(){return this.x=Math.floor(this.x),this.y=Math.floor(this.y),this.z=Math.floor(this.z),this}ceil(){return this.x=Math.ceil(this.x),this.y=Math.ceil(this.y),this.z=Math.ceil(this.z),this}round(){return this.x=Math.round(this.x),this.y=Math.round(this.y),this.z=Math.round(this.z),this}roundToZero(){return this.x=Math.trunc(this.x),this.y=Math.trunc(this.y),this.z=Math.trunc(this.z),this}negate(){return this.x=-this.x,this.y=-this.y,this.z=-this.z,this}dot(e){return this.x*e.x+this.y*e.y+this.z*e.z}lengthSq(){return this.x*this.x+this.y*this.y+this.z*this.z}length(){return Math.sqrt(this.x*this.x+this.y*this.y+this.z*this.z)}manhattanLength(){return Math.abs(this.x)+Math.abs(this.y)+Math.abs(this.z)}normalize(){return this.divideScalar(this.length()||1)}setLength(e){return this.normalize().multiplyScalar(e)}lerp(e,i){return this.x+=(e.x-this.x)*i,this.y+=(e.y-this.y)*i,this.z+=(e.z-this.z)*i,this}lerpVectors(e,i,s){return this.x=e.x+(i.x-e.x)*s,this.y=e.y+(i.y-e.y)*s,this.z=e.z+(i.z-e.z)*s,this}cross(e){return this.crossVectors(this,e)}crossVectors(e,i){const s=e.x,l=e.y,c=e.z,f=i.x,h=i.y,m=i.z;return this.x=l*m-c*h,this.y=c*f-s*m,this.z=s*h-l*f,this}projectOnVector(e){const i=e.lengthSq();if(i===0)return this.set(0,0,0);const s=e.dot(this)/i;return this.copy(e).multiplyScalar(s)}projectOnPlane(e){return uh.copy(this).projectOnVector(e),this.sub(uh)}reflect(e){return this.sub(uh.copy(e).multiplyScalar(2*this.dot(e)))}angleTo(e){const i=Math.sqrt(this.lengthSq()*e.lengthSq());if(i===0)return Math.PI/2;const s=this.dot(e)/i;return Math.acos(Dt(s,-1,1))}distanceTo(e){return Math.sqrt(this.distanceToSquared(e))}distanceToSquared(e){const i=this.x-e.x,s=this.y-e.y,l=this.z-e.z;return i*i+s*s+l*l}manhattanDistanceTo(e){return Math.abs(this.x-e.x)+Math.abs(this.y-e.y)+Math.abs(this.z-e.z)}setFromSpherical(e){return this.setFromSphericalCoords(e.radius,e.phi,e.theta)}setFromSphericalCoords(e,i,s){const l=Math.sin(i)*e;return this.x=l*Math.sin(s),this.y=Math.cos(i)*e,this.z=l*Math.cos(s),this}setFromCylindrical(e){return this.setFromCylindricalCoords(e.radius,e.theta,e.y)}setFromCylindricalCoords(e,i,s){return this.x=e*Math.sin(i),this.y=s,this.z=e*Math.cos(i),this}setFromMatrixPosition(e){const i=e.elements;return this.x=i[12],this.y=i[13],this.z=i[14],this}setFromMatrixScale(e){const i=this.setFromMatrixColumn(e,0).length(),s=this.setFromMatrixColumn(e,1).length(),l=this.setFromMatrixColumn(e,2).length();return this.x=i,this.y=s,this.z=l,this}setFromMatrixColumn(e,i){return this.fromArray(e.elements,i*4)}setFromMatrix3Column(e,i){return this.fromArray(e.elements,i*3)}setFromEuler(e){return this.x=e._x,this.y=e._y,this.z=e._z,this}setFromColor(e){return this.x=e.r,this.y=e.g,this.z=e.b,this}equals(e){return e.x===this.x&&e.y===this.y&&e.z===this.z}fromArray(e,i=0){return this.x=e[i],this.y=e[i+1],this.z=e[i+2],this}toArray(e=[],i=0){return e[i]=this.x,e[i+1]=this.y,e[i+2]=this.z,e}fromBufferAttribute(e,i){return this.x=e.getX(i),this.y=e.getY(i),this.z=e.getZ(i),this}random(){return this.x=Math.random(),this.y=Math.random(),this.z=Math.random(),this}randomDirection(){const e=Math.random()*Math.PI*2,i=Math.random()*2-1,s=Math.sqrt(1-i*i);return this.x=s*Math.cos(e),this.y=i,this.z=s*Math.sin(e),this}*[Symbol.iterator](){yield this.x,yield this.y,yield this.z}};am.prototype.isVector3=!0;let Q=am;const uh=new Q,tv=new ss,rm=class rm{constructor(e,i,s,l,c,f,h,m,p){this.elements=[1,0,0,0,1,0,0,0,1],e!==void 0&&this.set(e,i,s,l,c,f,h,m,p)}set(e,i,s,l,c,f,h,m,p){const g=this.elements;return g[0]=e,g[1]=l,g[2]=h,g[3]=i,g[4]=c,g[5]=m,g[6]=s,g[7]=f,g[8]=p,this}identity(){return this.set(1,0,0,0,1,0,0,0,1),this}copy(e){const i=this.elements,s=e.elements;return i[0]=s[0],i[1]=s[1],i[2]=s[2],i[3]=s[3],i[4]=s[4],i[5]=s[5],i[6]=s[6],i[7]=s[7],i[8]=s[8],this}extractBasis(e,i,s){return e.setFromMatrix3Column(this,0),i.setFromMatrix3Column(this,1),s.setFromMatrix3Column(this,2),this}setFromMatrix4(e){const i=e.elements;return this.set(i[0],i[4],i[8],i[1],i[5],i[9],i[2],i[6],i[10]),this}multiply(e){return this.multiplyMatrices(this,e)}premultiply(e){return this.multiplyMatrices(e,this)}multiplyMatrices(e,i){const s=e.elements,l=i.elements,c=this.elements,f=s[0],h=s[3],m=s[6],p=s[1],g=s[4],v=s[7],x=s[2],_=s[5],E=s[8],R=l[0],b=l[3],S=l[6],F=l[1],G=l[4],w=l[7],N=l[2],L=l[5],z=l[8];return c[0]=f*R+h*F+m*N,c[3]=f*b+h*G+m*L,c[6]=f*S+h*w+m*z,c[1]=p*R+g*F+v*N,c[4]=p*b+g*G+v*L,c[7]=p*S+g*w+v*z,c[2]=x*R+_*F+E*N,c[5]=x*b+_*G+E*L,c[8]=x*S+_*w+E*z,this}multiplyScalar(e){const i=this.elements;return i[0]*=e,i[3]*=e,i[6]*=e,i[1]*=e,i[4]*=e,i[7]*=e,i[2]*=e,i[5]*=e,i[8]*=e,this}determinant(){const e=this.elements,i=e[0],s=e[1],l=e[2],c=e[3],f=e[4],h=e[5],m=e[6],p=e[7],g=e[8];return i*f*g-i*h*p-s*c*g+s*h*m+l*c*p-l*f*m}invert(){const e=this.elements,i=e[0],s=e[1],l=e[2],c=e[3],f=e[4],h=e[5],m=e[6],p=e[7],g=e[8],v=g*f-h*p,x=h*m-g*c,_=p*c-f*m,E=i*v+s*x+l*_;if(E===0)return this.set(0,0,0,0,0,0,0,0,0);const R=1/E;return e[0]=v*R,e[1]=(l*p-g*s)*R,e[2]=(h*s-l*f)*R,e[3]=x*R,e[4]=(g*i-l*m)*R,e[5]=(l*c-h*i)*R,e[6]=_*R,e[7]=(s*m-p*i)*R,e[8]=(f*i-s*c)*R,this}transpose(){let e;const i=this.elements;return e=i[1],i[1]=i[3],i[3]=e,e=i[2],i[2]=i[6],i[6]=e,e=i[5],i[5]=i[7],i[7]=e,this}getNormalMatrix(e){return this.setFromMatrix4(e).invert().transpose()}transposeIntoArray(e){const i=this.elements;return e[0]=i[0],e[1]=i[3],e[2]=i[6],e[3]=i[1],e[4]=i[4],e[5]=i[7],e[6]=i[2],e[7]=i[5],e[8]=i[8],this}setUvTransform(e,i,s,l,c,f,h){const m=Math.cos(c),p=Math.sin(c);return this.set(s*m,s*p,-s*(m*f+p*h)+f+e,-l*p,l*m,-l*(-p*f+m*h)+h+i,0,0,1),this}scale(e,i){return Fo("Matrix3: .scale() is deprecated. Use .makeScale() instead."),this.premultiply(fh.makeScale(e,i)),this}rotate(e){return Fo("Matrix3: .rotate() is deprecated. Use .makeRotation() instead."),this.premultiply(fh.makeRotation(-e)),this}translate(e,i){return Fo("Matrix3: .translate() is deprecated. Use .makeTranslation() instead."),this.premultiply(fh.makeTranslation(e,i)),this}makeTranslation(e,i){return e.isVector2?this.set(1,0,e.x,0,1,e.y,0,0,1):this.set(1,0,e,0,1,i,0,0,1),this}makeRotation(e){const i=Math.cos(e),s=Math.sin(e);return this.set(i,-s,0,s,i,0,0,0,1),this}makeScale(e,i){return this.set(e,0,0,0,i,0,0,0,1),this}equals(e){const i=this.elements,s=e.elements;for(let l=0;l<9;l++)if(i[l]!==s[l])return!1;return!0}fromArray(e,i=0){for(let s=0;s<9;s++)this.elements[s]=e[s+i];return this}toArray(e=[],i=0){const s=this.elements;return e[i]=s[0],e[i+1]=s[1],e[i+2]=s[2],e[i+3]=s[3],e[i+4]=s[4],e[i+5]=s[5],e[i+6]=s[6],e[i+7]=s[7],e[i+8]=s[8],e}clone(){return new this.constructor().fromArray(this.elements)}};rm.prototype.isMatrix3=!0;let St=rm;const fh=new St,nv=new St().set(.4123908,.3575843,.1804808,.212639,.7151687,.0721923,.0193308,.1191948,.9505322),iv=new St().set(3.2409699,-1.5373832,-.4986108,-.9692436,1.8759675,.0415551,.0556301,-.203977,1.0569715);function Ib(){const r={enabled:!0,workingColorSpace:ku,spaces:{},convert:function(l,c,f){return this.enabled===!1||c===f||!c||!f||(this.spaces[c].transfer===cn&&(l.r=br(l.r),l.g=br(l.g),l.b=br(l.b)),this.spaces[c].primaries!==this.spaces[f].primaries&&(l.applyMatrix3(this.spaces[c].toXYZ),l.applyMatrix3(this.spaces[f].fromXYZ)),this.spaces[f].transfer===cn&&(l.r=Bo(l.r),l.g=Bo(l.g),l.b=Bo(l.b))),l},workingToColorSpace:function(l,c){return this.convert(l,this.workingColorSpace,c)},colorSpaceToWorking:function(l,c){return this.convert(l,c,this.workingColorSpace)},getPrimaries:function(l){return this.spaces[l].primaries},getTransfer:function(l){return l===ns?Xu:this.spaces[l].transfer},getToneMappingMode:function(l){return this.spaces[l].outputColorSpaceConfig.toneMappingMode||"standard"},getLuminanceCoefficients:function(l,c=this.workingColorSpace){return l.fromArray(this.spaces[c].luminanceCoefficients)},define:function(l){Object.assign(this.spaces,l)},_getMatrix:function(l,c,f){return l.copy(this.spaces[c].toXYZ).multiply(this.spaces[f].fromXYZ)},_getDrawingBufferColorSpace:function(l){return this.spaces[l].outputColorSpaceConfig.drawingBufferColorSpace},_getUnpackColorSpace:function(l=this.workingColorSpace){return this.spaces[l].workingColorSpaceConfig.unpackColorSpace},fromWorkingColorSpace:function(l,c){return Fo("ColorManagement: .fromWorkingColorSpace() has been renamed to .workingToColorSpace()."),r.workingToColorSpace(l,c)},toWorkingColorSpace:function(l,c){return Fo("ColorManagement: .toWorkingColorSpace() has been renamed to .colorSpaceToWorking()."),r.colorSpaceToWorking(l,c)}},e=[.64,.33,.3,.6,.15,.06],i=[.2126,.7152,.0722],s=[.3127,.329];return r.define({[ku]:{primaries:e,whitePoint:s,transfer:Xu,toXYZ:nv,fromXYZ:iv,luminanceCoefficients:i,workingColorSpaceConfig:{unpackColorSpace:Ei},outputColorSpaceConfig:{drawingBufferColorSpace:Ei}},[Ei]:{primaries:e,whitePoint:s,transfer:cn,toXYZ:nv,fromXYZ:iv,luminanceCoefficients:i,outputColorSpaceConfig:{drawingBufferColorSpace:Ei}}}),r}const kt=Ib();function br(r){return r<.04045?r*.0773993808:Math.pow(r*.9478672986+.0521327014,2.4)}function Bo(r){return r<.0031308?r*12.92:1.055*Math.pow(r,.41666)-.055}let vo;class Hb{static getDataURL(e,i="image/png"){if(/^data:/i.test(e.src)||typeof HTMLCanvasElement>"u")return e.src;let s;if(e instanceof HTMLCanvasElement)s=e;else{vo===void 0&&(vo=Zl("canvas")),vo.width=e.width,vo.height=e.height;const l=vo.getContext("2d");e instanceof ImageData?l.putImageData(e,0,0):l.drawImage(e,0,0,e.width,e.height),s=vo}return s.toDataURL(i)}static sRGBToLinear(e){if(typeof HTMLImageElement<"u"&&e instanceof HTMLImageElement||typeof HTMLCanvasElement<"u"&&e instanceof HTMLCanvasElement||typeof ImageBitmap<"u"&&e instanceof ImageBitmap){const i=Zl("canvas");i.width=e.width,i.height=e.height;const s=i.getContext("2d");s.drawImage(e,0,0,e.width,e.height);const l=s.getImageData(0,0,e.width,e.height),c=l.data;for(let f=0;f<c.length;f++)c[f]=br(c[f]/255)*255;return s.putImageData(l,0,0),i}else if(e.data){const i=e.data.slice(0);for(let s=0;s<i.length;s++)i instanceof Uint8Array||i instanceof Uint8ClampedArray?i[s]=Math.floor(br(i[s]/255)*255):i[s]=br(i[s]);return{data:i,width:e.width,height:e.height}}else return ht("ImageUtils.sRGBToLinear(): Unsupported image type. No color space conversion applied."),e}}let Gb=0;class Yp{constructor(e=null){this.isTextureSource=!0,Object.defineProperty(this,"id",{value:Gb++}),this.uuid=Go(),this.data=e,this.dataReady=!0,this.version=0}getSize(e){const i=this.data;return typeof HTMLVideoElement<"u"&&i instanceof HTMLVideoElement?e.set(i.videoWidth,i.videoHeight,0):typeof VideoFrame<"u"&&i instanceof VideoFrame?e.set(i.displayWidth,i.displayHeight,0):i!==null?e.set(i.width,i.height,i.depth||0):e.set(0,0,0),e}set needsUpdate(e){e===!0&&this.version++}toJSON(e){const i=e===void 0||typeof e=="string";if(!i&&e.images[this.uuid]!==void 0)return e.images[this.uuid];const s={uuid:this.uuid,url:""},l=this.data;if(l!==null){let c;if(Array.isArray(l)){c=[];for(let f=0,h=l.length;f<h;f++)l[f].isDataTexture?c.push(dh(l[f].image)):c.push(dh(l[f]))}else c=dh(l);s.url=c}return i||(e.images[this.uuid]=s),s}}function dh(r){return typeof HTMLImageElement<"u"&&r instanceof HTMLImageElement||typeof HTMLCanvasElement<"u"&&r instanceof HTMLCanvasElement||typeof ImageBitmap<"u"&&r instanceof ImageBitmap?Hb.getDataURL(r):r.data?{data:Array.from(r.data),width:r.width,height:r.height,type:r.data.constructor.name}:(ht("Texture: Unable to serialize Texture."),{})}let Vb=0;const hh=new Q;class gi extends Fs{constructor(e=gi.DEFAULT_IMAGE,i=gi.DEFAULT_MAPPING,s=_r,l=_r,c=mi,f=Rs,h=Ta,m=fa,p=gi.DEFAULT_ANISOTROPY,g=ns){super(),this.isTexture=!0,Object.defineProperty(this,"id",{value:Vb++}),this.uuid=Go(),this.name="",this.source=new Yp(e),this.mipmaps=[],this.mapping=i,this.channel=0,this.wrapS=s,this.wrapT=l,this.magFilter=c,this.minFilter=f,this.anisotropy=p,this.format=h,this.internalFormat=null,this.type=m,this.offset=new Kt(0,0),this.repeat=new Kt(1,1),this.center=new Kt(0,0),this.rotation=0,this.matrixAutoUpdate=!0,this.matrix=new St,this.generateMipmaps=!0,this.premultiplyAlpha=!1,this.flipY=!0,this.unpackAlignment=4,this.colorSpace=g,this.userData={},this.updateRanges=[],this.version=0,this.onUpdate=null,this.renderTarget=null,this.isRenderTargetTexture=!1,this.isArrayTexture=!!(e&&e.depth&&e.depth>1),this.pmremVersion=0,this.normalized=!1}get width(){return this.source.getSize(hh).x}get height(){return this.source.getSize(hh).y}get depth(){return this.source.getSize(hh).z}get image(){return this.source.data}set image(e){this.source.data=e}updateMatrix(){this.matrix.setUvTransform(this.offset.x,this.offset.y,this.repeat.x,this.repeat.y,this.rotation,this.center.x,this.center.y)}addUpdateRange(e,i){this.updateRanges.push({start:e,count:i})}clearUpdateRanges(){this.updateRanges.length=0}clone(){return new this.constructor().copy(this)}copy(e){return this.name=e.name,this.source=e.source,this.mipmaps=e.mipmaps.slice(0),this.mapping=e.mapping,this.channel=e.channel,this.wrapS=e.wrapS,this.wrapT=e.wrapT,this.magFilter=e.magFilter,this.minFilter=e.minFilter,this.anisotropy=e.anisotropy,this.format=e.format,this.internalFormat=e.internalFormat,this.type=e.type,this.normalized=e.normalized,this.offset.copy(e.offset),this.repeat.copy(e.repeat),this.center.copy(e.center),this.rotation=e.rotation,this.matrixAutoUpdate=e.matrixAutoUpdate,this.matrix.copy(e.matrix),this.generateMipmaps=e.generateMipmaps,this.premultiplyAlpha=e.premultiplyAlpha,this.flipY=e.flipY,this.unpackAlignment=e.unpackAlignment,this.colorSpace=e.colorSpace,this.renderTarget=e.renderTarget,this.isRenderTargetTexture=e.isRenderTargetTexture,this.isArrayTexture=e.isArrayTexture,this.userData=JSON.parse(JSON.stringify(e.userData)),this.needsUpdate=!0,this}setValues(e){for(const i in e){const s=e[i];if(s===void 0){ht(`Texture.setValues(): parameter '${i}' has value of undefined.`);continue}const l=this[i];if(l===void 0){ht(`Texture.setValues(): property '${i}' does not exist.`);continue}l&&s&&l.isVector2&&s.isVector2||l&&s&&l.isVector3&&s.isVector3||l&&s&&l.isMatrix3&&s.isMatrix3?l.copy(s):this[i]=s}}toJSON(e){const i=e===void 0||typeof e=="string";if(!i&&e.textures[this.uuid]!==void 0)return e.textures[this.uuid];const s={metadata:{version:4.7,type:"Texture",generator:"Texture.toJSON"},uuid:this.uuid,name:this.name,image:this.source.toJSON(e).uuid,mapping:this.mapping,channel:this.channel,repeat:[this.repeat.x,this.repeat.y],offset:[this.offset.x,this.offset.y],center:[this.center.x,this.center.y],rotation:this.rotation,wrap:[this.wrapS,this.wrapT],format:this.format,internalFormat:this.internalFormat,type:this.type,normalized:this.normalized,colorSpace:this.colorSpace,minFilter:this.minFilter,magFilter:this.magFilter,anisotropy:this.anisotropy,flipY:this.flipY,generateMipmaps:this.generateMipmaps,premultiplyAlpha:this.premultiplyAlpha,unpackAlignment:this.unpackAlignment};return Object.keys(this.userData).length>0&&(s.userData=this.userData),i||(e.textures[this.uuid]=s),s}dispose(){this.dispatchEvent({type:"dispose"})}transformUv(e){if(this.mapping!==S_)return e;if(e.applyMatrix3(this.matrix),e.x<0||e.x>1)switch(this.wrapS){case Qh:e.x=e.x-Math.floor(e.x);break;case _r:e.x=e.x<0?0:1;break;case Jh:Math.abs(Math.floor(e.x)%2)===1?e.x=Math.ceil(e.x)-e.x:e.x=e.x-Math.floor(e.x);break}if(e.y<0||e.y>1)switch(this.wrapT){case Qh:e.y=e.y-Math.floor(e.y);break;case _r:e.y=e.y<0?0:1;break;case Jh:Math.abs(Math.floor(e.y)%2)===1?e.y=Math.ceil(e.y)-e.y:e.y=e.y-Math.floor(e.y);break}return this.flipY&&(e.y=1-e.y),e}set needsUpdate(e){e===!0&&(this.version++,this.source.needsUpdate=!0)}set needsPMREMUpdate(e){e===!0&&this.pmremVersion++}}gi.DEFAULT_IMAGE=null;gi.DEFAULT_MAPPING=S_;gi.DEFAULT_ANISOTROPY=1;const sm=class sm{constructor(e=0,i=0,s=0,l=1){this.x=e,this.y=i,this.z=s,this.w=l}get width(){return this.z}set width(e){this.z=e}get height(){return this.w}set height(e){this.w=e}set(e,i,s,l){return this.x=e,this.y=i,this.z=s,this.w=l,this}setScalar(e){return this.x=e,this.y=e,this.z=e,this.w=e,this}setX(e){return this.x=e,this}setY(e){return this.y=e,this}setZ(e){return this.z=e,this}setW(e){return this.w=e,this}setComponent(e,i){switch(e){case 0:this.x=i;break;case 1:this.y=i;break;case 2:this.z=i;break;case 3:this.w=i;break;default:throw new Error("THREE.Vector4: index is out of range: "+e)}return this}getComponent(e){switch(e){case 0:return this.x;case 1:return this.y;case 2:return this.z;case 3:return this.w;default:throw new Error("THREE.Vector4: index is out of range: "+e)}}clone(){return new this.constructor(this.x,this.y,this.z,this.w)}copy(e){return this.x=e.x,this.y=e.y,this.z=e.z,this.w=e.w!==void 0?e.w:1,this}add(e){return this.x+=e.x,this.y+=e.y,this.z+=e.z,this.w+=e.w,this}addScalar(e){return this.x+=e,this.y+=e,this.z+=e,this.w+=e,this}addVectors(e,i){return this.x=e.x+i.x,this.y=e.y+i.y,this.z=e.z+i.z,this.w=e.w+i.w,this}addScaledVector(e,i){return this.x+=e.x*i,this.y+=e.y*i,this.z+=e.z*i,this.w+=e.w*i,this}sub(e){return this.x-=e.x,this.y-=e.y,this.z-=e.z,this.w-=e.w,this}subScalar(e){return this.x-=e,this.y-=e,this.z-=e,this.w-=e,this}subVectors(e,i){return this.x=e.x-i.x,this.y=e.y-i.y,this.z=e.z-i.z,this.w=e.w-i.w,this}multiply(e){return this.x*=e.x,this.y*=e.y,this.z*=e.z,this.w*=e.w,this}multiplyScalar(e){return this.x*=e,this.y*=e,this.z*=e,this.w*=e,this}applyMatrix4(e){const i=this.x,s=this.y,l=this.z,c=this.w,f=e.elements;return this.x=f[0]*i+f[4]*s+f[8]*l+f[12]*c,this.y=f[1]*i+f[5]*s+f[9]*l+f[13]*c,this.z=f[2]*i+f[6]*s+f[10]*l+f[14]*c,this.w=f[3]*i+f[7]*s+f[11]*l+f[15]*c,this}divide(e){return this.x/=e.x,this.y/=e.y,this.z/=e.z,this.w/=e.w,this}divideScalar(e){return this.multiplyScalar(1/e)}setAxisAngleFromQuaternion(e){this.w=2*Math.acos(e.w);const i=Math.sqrt(1-e.w*e.w);return i<1e-4?(this.x=1,this.y=0,this.z=0):(this.x=e.x/i,this.y=e.y/i,this.z=e.z/i),this}setAxisAngleFromRotationMatrix(e){let i,s,l,c;const m=e.elements,p=m[0],g=m[4],v=m[8],x=m[1],_=m[5],E=m[9],R=m[2],b=m[6],S=m[10];if(Math.abs(g-x)<.01&&Math.abs(v-R)<.01&&Math.abs(E-b)<.01){if(Math.abs(g+x)<.1&&Math.abs(v+R)<.1&&Math.abs(E+b)<.1&&Math.abs(p+_+S-3)<.1)return this.set(1,0,0,0),this;i=Math.PI;const G=(p+1)/2,w=(_+1)/2,N=(S+1)/2,L=(g+x)/4,z=(v+R)/4,T=(E+b)/4;return G>w&&G>N?G<.01?(s=0,l=.707106781,c=.707106781):(s=Math.sqrt(G),l=L/s,c=z/s):w>N?w<.01?(s=.707106781,l=0,c=.707106781):(l=Math.sqrt(w),s=L/l,c=T/l):N<.01?(s=.707106781,l=.707106781,c=0):(c=Math.sqrt(N),s=z/c,l=T/c),this.set(s,l,c,i),this}let F=Math.sqrt((b-E)*(b-E)+(v-R)*(v-R)+(x-g)*(x-g));return Math.abs(F)<.001&&(F=1),this.x=(b-E)/F,this.y=(v-R)/F,this.z=(x-g)/F,this.w=Math.acos((p+_+S-1)/2),this}setFromMatrixPosition(e){const i=e.elements;return this.x=i[12],this.y=i[13],this.z=i[14],this.w=i[15],this}min(e){return this.x=Math.min(this.x,e.x),this.y=Math.min(this.y,e.y),this.z=Math.min(this.z,e.z),this.w=Math.min(this.w,e.w),this}max(e){return this.x=Math.max(this.x,e.x),this.y=Math.max(this.y,e.y),this.z=Math.max(this.z,e.z),this.w=Math.max(this.w,e.w),this}clamp(e,i){return this.x=Dt(this.x,e.x,i.x),this.y=Dt(this.y,e.y,i.y),this.z=Dt(this.z,e.z,i.z),this.w=Dt(this.w,e.w,i.w),this}clampScalar(e,i){return this.x=Dt(this.x,e,i),this.y=Dt(this.y,e,i),this.z=Dt(this.z,e,i),this.w=Dt(this.w,e,i),this}clampLength(e,i){const s=this.length();return this.divideScalar(s||1).multiplyScalar(Dt(s,e,i))}floor(){return this.x=Math.floor(this.x),this.y=Math.floor(this.y),this.z=Math.floor(this.z),this.w=Math.floor(this.w),this}ceil(){return this.x=Math.ceil(this.x),this.y=Math.ceil(this.y),this.z=Math.ceil(this.z),this.w=Math.ceil(this.w),this}round(){return this.x=Math.round(this.x),this.y=Math.round(this.y),this.z=Math.round(this.z),this.w=Math.round(this.w),this}roundToZero(){return this.x=Math.trunc(this.x),this.y=Math.trunc(this.y),this.z=Math.trunc(this.z),this.w=Math.trunc(this.w),this}negate(){return this.x=-this.x,this.y=-this.y,this.z=-this.z,this.w=-this.w,this}dot(e){return this.x*e.x+this.y*e.y+this.z*e.z+this.w*e.w}lengthSq(){return this.x*this.x+this.y*this.y+this.z*this.z+this.w*this.w}length(){return Math.sqrt(this.x*this.x+this.y*this.y+this.z*this.z+this.w*this.w)}manhattanLength(){return Math.abs(this.x)+Math.abs(this.y)+Math.abs(this.z)+Math.abs(this.w)}normalize(){return this.divideScalar(this.length()||1)}setLength(e){return this.normalize().multiplyScalar(e)}lerp(e,i){return this.x+=(e.x-this.x)*i,this.y+=(e.y-this.y)*i,this.z+=(e.z-this.z)*i,this.w+=(e.w-this.w)*i,this}lerpVectors(e,i,s){return this.x=e.x+(i.x-e.x)*s,this.y=e.y+(i.y-e.y)*s,this.z=e.z+(i.z-e.z)*s,this.w=e.w+(i.w-e.w)*s,this}equals(e){return e.x===this.x&&e.y===this.y&&e.z===this.z&&e.w===this.w}fromArray(e,i=0){return this.x=e[i],this.y=e[i+1],this.z=e[i+2],this.w=e[i+3],this}toArray(e=[],i=0){return e[i]=this.x,e[i+1]=this.y,e[i+2]=this.z,e[i+3]=this.w,e}fromBufferAttribute(e,i){return this.x=e.getX(i),this.y=e.getY(i),this.z=e.getZ(i),this.w=e.getW(i),this}random(){return this.x=Math.random(),this.y=Math.random(),this.z=Math.random(),this.w=Math.random(),this}*[Symbol.iterator](){yield this.x,yield this.y,yield this.z,yield this.w}};sm.prototype.isVector4=!0;let Ln=sm;class kb extends Fs{constructor(e=1,i=1,s={}){super(),s=Object.assign({generateMipmaps:!1,internalFormat:null,minFilter:mi,depthBuffer:!0,stencilBuffer:!1,resolveColorBuffer:!0,resolveDepthBuffer:!0,resolveStencilBuffer:!0,storeMultisampledColorBuffer:!0,storeMultisampledDepthBuffer:!0,storeMultisampledStencilBuffer:!0,depthTexture:null,samples:0,count:1,depth:1,multiview:!1,useArrayDepthTexture:!1},s),this.isRenderTarget=!0,this.width=e,this.height=i,this.depth=s.depth,this.scissor=new Ln(0,0,e,i),this.scissorTest=!1,this.viewport=new Ln(0,0,e,i),this.textures=[];const l={width:e,height:i,depth:s.depth},c=new gi(l),f=s.count;for(let h=0;h<f;h++)this.textures[h]=c.clone(),this.textures[h].isRenderTargetTexture=!0,this.textures[h].renderTarget=this;this._setTextureOptions(s),this.depthBuffer=s.depthBuffer,this.stencilBuffer=s.stencilBuffer,this.resolveColorBuffer=s.resolveColorBuffer,this.resolveDepthBuffer=s.resolveDepthBuffer,this.resolveStencilBuffer=s.resolveStencilBuffer,this.storeMultisampledColorBuffer=s.storeMultisampledColorBuffer,this.storeMultisampledDepthBuffer=s.storeMultisampledDepthBuffer,this.storeMultisampledStencilBuffer=s.storeMultisampledStencilBuffer,this._depthTexture=null,this.depthTexture=s.depthTexture,this.samples=s.samples,this.multiview=s.multiview,this.useArrayDepthTexture=s.useArrayDepthTexture}_setTextureOptions(e={}){const i={minFilter:mi,generateMipmaps:!1,flipY:!1,internalFormat:null};e.mapping!==void 0&&(i.mapping=e.mapping),e.wrapS!==void 0&&(i.wrapS=e.wrapS),e.wrapT!==void 0&&(i.wrapT=e.wrapT),e.wrapR!==void 0&&(i.wrapR=e.wrapR),e.magFilter!==void 0&&(i.magFilter=e.magFilter),e.minFilter!==void 0&&(i.minFilter=e.minFilter),e.format!==void 0&&(i.format=e.format),e.type!==void 0&&(i.type=e.type),e.anisotropy!==void 0&&(i.anisotropy=e.anisotropy),e.colorSpace!==void 0&&(i.colorSpace=e.colorSpace),e.flipY!==void 0&&(i.flipY=e.flipY),e.generateMipmaps!==void 0&&(i.generateMipmaps=e.generateMipmaps),e.internalFormat!==void 0&&(i.internalFormat=e.internalFormat);for(let s=0;s<this.textures.length;s++)this.textures[s].setValues(i)}get texture(){return this.textures[0]}set texture(e){this.textures[0]=e}set depthTexture(e){this._depthTexture!==null&&this._depthTexture.renderTarget===this&&(this._depthTexture.renderTarget=null),e!==null&&e.renderTarget===null&&(e.renderTarget=this),this._depthTexture=e}get depthTexture(){return this._depthTexture}setSize(e,i,s=1){if(this.width!==e||this.height!==i||this.depth!==s){this.width=e,this.height=i,this.depth=s;for(let l=0,c=this.textures.length;l<c;l++)this.textures[l].image.width=e,this.textures[l].image.height=i,this.textures[l].image.depth=s,this.textures[l].isData3DTexture!==!0&&(this.textures[l].isArrayTexture=this.textures[l].image.depth>1);this.dispose()}this.viewport.set(0,0,e,i),this.scissor.set(0,0,e,i)}clone(){return new this.constructor().copy(this)}copy(e){this.width=e.width,this.height=e.height,this.depth=e.depth,this.scissor.copy(e.scissor),this.scissorTest=e.scissorTest,this.viewport.copy(e.viewport),this.textures.length=0;for(let i=0,s=e.textures.length;i<s;i++){this.textures[i]=e.textures[i].clone(),this.textures[i].isRenderTargetTexture=!0,this.textures[i].renderTarget=this;const l=Object.assign({},e.textures[i].image);this.textures[i].source=new Yp(l)}if(this.depthBuffer=e.depthBuffer,this.stencilBuffer=e.stencilBuffer,this.resolveColorBuffer=e.resolveColorBuffer,this.resolveDepthBuffer=e.resolveDepthBuffer,this.resolveStencilBuffer=e.resolveStencilBuffer,this.storeMultisampledColorBuffer=e.storeMultisampledColorBuffer,this.storeMultisampledDepthBuffer=e.storeMultisampledDepthBuffer,this.storeMultisampledStencilBuffer=e.storeMultisampledStencilBuffer,e.depthTexture!==null)if(e.depthTexture.renderTarget===e){const i=e.depthTexture.clone();i.renderTarget=null,this.depthTexture=i}else this.depthTexture=e.depthTexture;return this.samples=e.samples,this.multiview=e.multiview,this.useArrayDepthTexture=e.useArrayDepthTexture,this}dispose(){this.dispatchEvent({type:"dispose"})}}class wa extends kb{constructor(e=1,i=1,s={}){super(e,i,s),this.isWebGLRenderTarget=!0}}class U_ extends gi{constructor(e=null,i=1,s=1,l=1){super(null),this.isDataArrayTexture=!0,this.image={data:e,width:i,height:s,depth:l},this.magFilter=li,this.minFilter=li,this.wrapR=_r,this.generateMipmaps=!1,this.flipY=!1,this.unpackAlignment=1,this.layerUpdates=new Set}copy(e){return super.copy(e),this.wrapR=e.wrapR,this}addLayerUpdate(e){this.layerUpdates.add(e)}clearLayerUpdates(){this.layerUpdates.clear()}}class Xb extends gi{constructor(e=null,i=1,s=1,l=1){super(null),this.isData3DTexture=!0,this.image={data:e,width:i,height:s,depth:l},this.magFilter=li,this.minFilter=li,this.wrapR=_r,this.generateMipmaps=!1,this.flipY=!1,this.unpackAlignment=1}copy(e){return super.copy(e),this.wrapR=e.wrapR,this}}const Zu=class Zu{constructor(e,i,s,l,c,f,h,m,p,g,v,x,_,E,R,b){this.elements=[1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1],e!==void 0&&this.set(e,i,s,l,c,f,h,m,p,g,v,x,_,E,R,b)}set(e,i,s,l,c,f,h,m,p,g,v,x,_,E,R,b){const S=this.elements;return S[0]=e,S[4]=i,S[8]=s,S[12]=l,S[1]=c,S[5]=f,S[9]=h,S[13]=m,S[2]=p,S[6]=g,S[10]=v,S[14]=x,S[3]=_,S[7]=E,S[11]=R,S[15]=b,this}identity(){return this.set(1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1),this}clone(){return new Zu().fromArray(this.elements)}copy(e){const i=this.elements,s=e.elements;return i[0]=s[0],i[1]=s[1],i[2]=s[2],i[3]=s[3],i[4]=s[4],i[5]=s[5],i[6]=s[6],i[7]=s[7],i[8]=s[8],i[9]=s[9],i[10]=s[10],i[11]=s[11],i[12]=s[12],i[13]=s[13],i[14]=s[14],i[15]=s[15],this}copyPosition(e){const i=this.elements,s=e.elements;return i[12]=s[12],i[13]=s[13],i[14]=s[14],this}setFromMatrix3(e){const i=e.elements;return this.set(i[0],i[3],i[6],0,i[1],i[4],i[7],0,i[2],i[5],i[8],0,0,0,0,1),this}extractBasis(e,i,s){return this.determinantAffine()===0?(e.set(1,0,0),i.set(0,1,0),s.set(0,0,1),this):(e.setFromMatrixColumn(this,0),i.setFromMatrixColumn(this,1),s.setFromMatrixColumn(this,2),this)}makeBasis(e,i,s){return this.set(e.x,i.x,s.x,0,e.y,i.y,s.y,0,e.z,i.z,s.z,0,0,0,0,1),this}extractRotation(e){if(e.determinantAffine()===0)return this.identity();const i=this.elements,s=e.elements,l=1/_o.setFromMatrixColumn(e,0).length(),c=1/_o.setFromMatrixColumn(e,1).length(),f=1/_o.setFromMatrixColumn(e,2).length();return i[0]=s[0]*l,i[1]=s[1]*l,i[2]=s[2]*l,i[3]=0,i[4]=s[4]*c,i[5]=s[5]*c,i[6]=s[6]*c,i[7]=0,i[8]=s[8]*f,i[9]=s[9]*f,i[10]=s[10]*f,i[11]=0,i[12]=0,i[13]=0,i[14]=0,i[15]=1,this}makeRotationFromEuler(e){const i=this.elements,s=e.x,l=e.y,c=e.z,f=Math.cos(s),h=Math.sin(s),m=Math.cos(l),p=Math.sin(l),g=Math.cos(c),v=Math.sin(c);if(e.order==="XYZ"){const x=f*g,_=f*v,E=h*g,R=h*v;i[0]=m*g,i[4]=-m*v,i[8]=p,i[1]=_+E*p,i[5]=x-R*p,i[9]=-h*m,i[2]=R-x*p,i[6]=E+_*p,i[10]=f*m}else if(e.order==="YXZ"){const x=m*g,_=m*v,E=p*g,R=p*v;i[0]=x+R*h,i[4]=E*h-_,i[8]=f*p,i[1]=f*v,i[5]=f*g,i[9]=-h,i[2]=_*h-E,i[6]=R+x*h,i[10]=f*m}else if(e.order==="ZXY"){const x=m*g,_=m*v,E=p*g,R=p*v;i[0]=x-R*h,i[4]=-f*v,i[8]=E+_*h,i[1]=_+E*h,i[5]=f*g,i[9]=R-x*h,i[2]=-f*p,i[6]=h,i[10]=f*m}else if(e.order==="ZYX"){const x=f*g,_=f*v,E=h*g,R=h*v;i[0]=m*g,i[4]=E*p-_,i[8]=x*p+R,i[1]=m*v,i[5]=R*p+x,i[9]=_*p-E,i[2]=-p,i[6]=h*m,i[10]=f*m}else if(e.order==="YZX"){const x=f*m,_=f*p,E=h*m,R=h*p;i[0]=m*g,i[4]=R-x*v,i[8]=E*v+_,i[1]=v,i[5]=f*g,i[9]=-h*g,i[2]=-p*g,i[6]=_*v+E,i[10]=x-R*v}else if(e.order==="XZY"){const x=f*m,_=f*p,E=h*m,R=h*p;i[0]=m*g,i[4]=-v,i[8]=p*g,i[1]=x*v+R,i[5]=f*g,i[9]=_*v-E,i[2]=E*v-_,i[6]=h*g,i[10]=R*v+x}return i[3]=0,i[7]=0,i[11]=0,i[12]=0,i[13]=0,i[14]=0,i[15]=1,this}makeRotationFromQuaternion(e){return this.compose(Wb,e,qb)}lookAt(e,i,s){const l=this.elements;return Wi.subVectors(e,i),Wi.lengthSq()===0&&(Wi.z=1),Wi.normalize(),Kr.crossVectors(s,Wi),Kr.lengthSq()===0&&(Math.abs(s.z)===1?Wi.x+=1e-4:Wi.z+=1e-4,Wi.normalize(),Kr.crossVectors(s,Wi)),Kr.normalize(),ru.crossVectors(Wi,Kr),l[0]=Kr.x,l[4]=ru.x,l[8]=Wi.x,l[1]=Kr.y,l[5]=ru.y,l[9]=Wi.y,l[2]=Kr.z,l[6]=ru.z,l[10]=Wi.z,this}multiply(e){return this.multiplyMatrices(this,e)}premultiply(e){return this.multiplyMatrices(e,this)}multiplyMatrices(e,i){const s=e.elements,l=i.elements,c=this.elements,f=s[0],h=s[4],m=s[8],p=s[12],g=s[1],v=s[5],x=s[9],_=s[13],E=s[2],R=s[6],b=s[10],S=s[14],F=s[3],G=s[7],w=s[11],N=s[15],L=l[0],z=l[4],T=l[8],O=l[12],I=l[1],W=l[5],J=l[9],re=l[13],k=l[2],K=l[6],B=l[10],V=l[14],ee=l[3],oe=l[7],fe=l[11],D=l[15];return c[0]=f*L+h*I+m*k+p*ee,c[4]=f*z+h*W+m*K+p*oe,c[8]=f*T+h*J+m*B+p*fe,c[12]=f*O+h*re+m*V+p*D,c[1]=g*L+v*I+x*k+_*ee,c[5]=g*z+v*W+x*K+_*oe,c[9]=g*T+v*J+x*B+_*fe,c[13]=g*O+v*re+x*V+_*D,c[2]=E*L+R*I+b*k+S*ee,c[6]=E*z+R*W+b*K+S*oe,c[10]=E*T+R*J+b*B+S*fe,c[14]=E*O+R*re+b*V+S*D,c[3]=F*L+G*I+w*k+N*ee,c[7]=F*z+G*W+w*K+N*oe,c[11]=F*T+G*J+w*B+N*fe,c[15]=F*O+G*re+w*V+N*D,this}multiplyScalar(e){const i=this.elements;return i[0]*=e,i[4]*=e,i[8]*=e,i[12]*=e,i[1]*=e,i[5]*=e,i[9]*=e,i[13]*=e,i[2]*=e,i[6]*=e,i[10]*=e,i[14]*=e,i[3]*=e,i[7]*=e,i[11]*=e,i[15]*=e,this}determinant(){const e=this.elements,i=e[0],s=e[4],l=e[8],c=e[12],f=e[1],h=e[5],m=e[9],p=e[13],g=e[2],v=e[6],x=e[10],_=e[14],E=e[3],R=e[7],b=e[11],S=e[15],F=m*_-p*x,G=h*_-p*v,w=h*x-m*v,N=f*_-p*g,L=f*x-m*g,z=f*v-h*g;return i*(R*F-b*G+S*w)-s*(E*F-b*N+S*L)+l*(E*G-R*N+S*z)-c*(E*w-R*L+b*z)}determinantAffine(){const e=this.elements,i=e[0],s=e[4],l=e[8],c=e[1],f=e[5],h=e[9],m=e[2],p=e[6],g=e[10];return i*(f*g-h*p)-s*(c*g-h*m)+l*(c*p-f*m)}transpose(){const e=this.elements;let i;return i=e[1],e[1]=e[4],e[4]=i,i=e[2],e[2]=e[8],e[8]=i,i=e[6],e[6]=e[9],e[9]=i,i=e[3],e[3]=e[12],e[12]=i,i=e[7],e[7]=e[13],e[13]=i,i=e[11],e[11]=e[14],e[14]=i,this}setPosition(e,i,s){const l=this.elements;return e.isVector3?(l[12]=e.x,l[13]=e.y,l[14]=e.z):(l[12]=e,l[13]=i,l[14]=s),this}invert(){const e=this.elements,i=e[0],s=e[1],l=e[2],c=e[3],f=e[4],h=e[5],m=e[6],p=e[7],g=e[8],v=e[9],x=e[10],_=e[11],E=e[12],R=e[13],b=e[14],S=e[15],F=i*h-s*f,G=i*m-l*f,w=i*p-c*f,N=s*m-l*h,L=s*p-c*h,z=l*p-c*m,T=g*R-v*E,O=g*b-x*E,I=g*S-_*E,W=v*b-x*R,J=v*S-_*R,re=x*S-_*b,k=F*re-G*J+w*W+N*I-L*O+z*T;if(k===0)return this.set(0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0);const K=1/k;return e[0]=(h*re-m*J+p*W)*K,e[1]=(l*J-s*re-c*W)*K,e[2]=(R*z-b*L+S*N)*K,e[3]=(x*L-v*z-_*N)*K,e[4]=(m*I-f*re-p*O)*K,e[5]=(i*re-l*I+c*O)*K,e[6]=(b*w-E*z-S*G)*K,e[7]=(g*z-x*w+_*G)*K,e[8]=(f*J-h*I+p*T)*K,e[9]=(s*I-i*J-c*T)*K,e[10]=(E*L-R*w+S*F)*K,e[11]=(v*w-g*L-_*F)*K,e[12]=(h*O-f*W-m*T)*K,e[13]=(i*W-s*O+l*T)*K,e[14]=(R*G-E*N-b*F)*K,e[15]=(g*N-v*G+x*F)*K,this}scale(e){const i=this.elements,s=e.x,l=e.y,c=e.z;return i[0]*=s,i[4]*=l,i[8]*=c,i[1]*=s,i[5]*=l,i[9]*=c,i[2]*=s,i[6]*=l,i[10]*=c,i[3]*=s,i[7]*=l,i[11]*=c,this}getMaxScaleOnAxis(){const e=this.elements,i=e[0]*e[0]+e[1]*e[1]+e[2]*e[2],s=e[4]*e[4]+e[5]*e[5]+e[6]*e[6],l=e[8]*e[8]+e[9]*e[9]+e[10]*e[10];return Math.sqrt(Math.max(i,s,l))}makeTranslation(e,i,s){return e.isVector3?this.set(1,0,0,e.x,0,1,0,e.y,0,0,1,e.z,0,0,0,1):this.set(1,0,0,e,0,1,0,i,0,0,1,s,0,0,0,1),this}makeRotationX(e){const i=Math.cos(e),s=Math.sin(e);return this.set(1,0,0,0,0,i,-s,0,0,s,i,0,0,0,0,1),this}makeRotationY(e){const i=Math.cos(e),s=Math.sin(e);return this.set(i,0,s,0,0,1,0,0,-s,0,i,0,0,0,0,1),this}makeRotationZ(e){const i=Math.cos(e),s=Math.sin(e);return this.set(i,-s,0,0,s,i,0,0,0,0,1,0,0,0,0,1),this}makeRotationAxis(e,i){const s=Math.cos(i),l=Math.sin(i),c=1-s,f=e.x,h=e.y,m=e.z,p=c*f,g=c*h;return this.set(p*f+s,p*h-l*m,p*m+l*h,0,p*h+l*m,g*h+s,g*m-l*f,0,p*m-l*h,g*m+l*f,c*m*m+s,0,0,0,0,1),this}makeScale(e,i,s){return this.set(e,0,0,0,0,i,0,0,0,0,s,0,0,0,0,1),this}makeShear(e,i,s,l,c,f){return this.set(1,s,c,0,e,1,f,0,i,l,1,0,0,0,0,1),this}compose(e,i,s){const l=this.elements,c=i._x,f=i._y,h=i._z,m=i._w,p=c+c,g=f+f,v=h+h,x=c*p,_=c*g,E=c*v,R=f*g,b=f*v,S=h*v,F=m*p,G=m*g,w=m*v,N=s.x,L=s.y,z=s.z;return l[0]=(1-(R+S))*N,l[1]=(_+w)*N,l[2]=(E-G)*N,l[3]=0,l[4]=(_-w)*L,l[5]=(1-(x+S))*L,l[6]=(b+F)*L,l[7]=0,l[8]=(E+G)*z,l[9]=(b-F)*z,l[10]=(1-(x+R))*z,l[11]=0,l[12]=e.x,l[13]=e.y,l[14]=e.z,l[15]=1,this}decompose(e,i,s){const l=this.elements;e.x=l[12],e.y=l[13],e.z=l[14];const c=this.determinantAffine();if(c===0)return s.set(1,1,1),i.identity(),this;let f=_o.set(l[0],l[1],l[2]).length();const h=_o.set(l[4],l[5],l[6]).length(),m=_o.set(l[8],l[9],l[10]).length();c<0&&(f=-f),Sa.copy(this);const p=1/f,g=1/h,v=1/m;return Sa.elements[0]*=p,Sa.elements[1]*=p,Sa.elements[2]*=p,Sa.elements[4]*=g,Sa.elements[5]*=g,Sa.elements[6]*=g,Sa.elements[8]*=v,Sa.elements[9]*=v,Sa.elements[10]*=v,i.setFromRotationMatrix(Sa),s.x=f,s.y=h,s.z=m,this}makePerspective(e,i,s,l,c,f,h=Va,m=!1){const p=this.elements,g=2*c/(i-e),v=2*c/(s-l),x=(i+e)/(i-e),_=(s+l)/(s-l);let E,R;if(m)E=c/(f-c),R=f*c/(f-c);else if(h===Va)E=-(f+c)/(f-c),R=-2*f*c/(f-c);else if(h===Wu)E=-f/(f-c),R=-f*c/(f-c);else throw new Error("THREE.Matrix4.makePerspective(): Invalid coordinate system: "+h);return p[0]=g,p[4]=0,p[8]=x,p[12]=0,p[1]=0,p[5]=v,p[9]=_,p[13]=0,p[2]=0,p[6]=0,p[10]=E,p[14]=R,p[3]=0,p[7]=0,p[11]=-1,p[15]=0,this}makeOrthographic(e,i,s,l,c,f,h=Va,m=!1){const p=this.elements,g=2/(i-e),v=2/(s-l),x=-(i+e)/(i-e),_=-(s+l)/(s-l);let E,R;if(m)E=1/(f-c),R=f/(f-c);else if(h===Va)E=-2/(f-c),R=-(f+c)/(f-c);else if(h===Wu)E=-1/(f-c),R=-c/(f-c);else throw new Error("THREE.Matrix4.makeOrthographic(): Invalid coordinate system: "+h);return p[0]=g,p[4]=0,p[8]=0,p[12]=x,p[1]=0,p[5]=v,p[9]=0,p[13]=_,p[2]=0,p[6]=0,p[10]=E,p[14]=R,p[3]=0,p[7]=0,p[11]=0,p[15]=1,this}equals(e){const i=this.elements,s=e.elements;for(let l=0;l<16;l++)if(i[l]!==s[l])return!1;return!0}fromArray(e,i=0){for(let s=0;s<16;s++)this.elements[s]=e[s+i];return this}toArray(e=[],i=0){const s=this.elements;return e[i]=s[0],e[i+1]=s[1],e[i+2]=s[2],e[i+3]=s[3],e[i+4]=s[4],e[i+5]=s[5],e[i+6]=s[6],e[i+7]=s[7],e[i+8]=s[8],e[i+9]=s[9],e[i+10]=s[10],e[i+11]=s[11],e[i+12]=s[12],e[i+13]=s[13],e[i+14]=s[14],e[i+15]=s[15],e}};Zu.prototype.isMatrix4=!0;let En=Zu;const _o=new Q,Sa=new En,Wb=new Q(0,0,0),qb=new Q(1,1,1),Kr=new Q,ru=new Q,Wi=new Q,av=new En,rv=new ss;class zs{constructor(e=0,i=0,s=0,l=zs.DEFAULT_ORDER){this.isEuler=!0,this._x=e,this._y=i,this._z=s,this._order=l}get x(){return this._x}set x(e){this._x=e,this._onChangeCallback()}get y(){return this._y}set y(e){this._y=e,this._onChangeCallback()}get z(){return this._z}set z(e){this._z=e,this._onChangeCallback()}get order(){return this._order}set order(e){this._order=e,this._onChangeCallback()}set(e,i,s,l=this._order){return this._x=e,this._y=i,this._z=s,this._order=l,this._onChangeCallback(),this}clone(){return new this.constructor(this._x,this._y,this._z,this._order)}copy(e){return this._x=e._x,this._y=e._y,this._z=e._z,this._order=e._order,this._onChangeCallback(),this}setFromRotationMatrix(e,i=this._order,s=!0){const l=e.elements,c=l[0],f=l[4],h=l[8],m=l[1],p=l[5],g=l[9],v=l[2],x=l[6],_=l[10];switch(i){case"XYZ":this._y=Math.asin(Dt(h,-1,1)),Math.abs(h)<.9999999?(this._x=Math.atan2(-g,_),this._z=Math.atan2(-f,c)):(this._x=Math.atan2(x,p),this._z=0);break;case"YXZ":this._x=Math.asin(-Dt(g,-1,1)),Math.abs(g)<.9999999?(this._y=Math.atan2(h,_),this._z=Math.atan2(m,p)):(this._y=Math.atan2(-v,c),this._z=0);break;case"ZXY":this._x=Math.asin(Dt(x,-1,1)),Math.abs(x)<.9999999?(this._y=Math.atan2(-v,_),this._z=Math.atan2(-f,p)):(this._y=0,this._z=Math.atan2(m,c));break;case"ZYX":this._y=Math.asin(-Dt(v,-1,1)),Math.abs(v)<.9999999?(this._x=Math.atan2(x,_),this._z=Math.atan2(m,c)):(this._x=0,this._z=Math.atan2(-f,p));break;case"YZX":this._z=Math.asin(Dt(m,-1,1)),Math.abs(m)<.9999999?(this._x=Math.atan2(-g,p),this._y=Math.atan2(-v,c)):(this._x=0,this._y=Math.atan2(h,_));break;case"XZY":this._z=Math.asin(-Dt(f,-1,1)),Math.abs(f)<.9999999?(this._x=Math.atan2(x,p),this._y=Math.atan2(h,c)):(this._x=Math.atan2(-g,_),this._y=0);break;default:ht("Euler: .setFromRotationMatrix() encountered an unknown order: "+i)}return this._order=i,s===!0&&this._onChangeCallback(),this}setFromQuaternion(e,i,s){return av.makeRotationFromQuaternion(e),this.setFromRotationMatrix(av,i,s)}setFromVector3(e,i=this._order){return this.set(e.x,e.y,e.z,i)}reorder(e){return rv.setFromEuler(this),this.setFromQuaternion(rv,e)}equals(e){return e._x===this._x&&e._y===this._y&&e._z===this._z&&e._order===this._order}fromArray(e){return this._x=e[0],this._y=e[1],this._z=e[2],e[3]!==void 0&&(this._order=e[3]),this._onChangeCallback(),this}toArray(e=[],i=0){return e[i]=this._x,e[i+1]=this._y,e[i+2]=this._z,e[i+3]=this._order,e}_onChange(e){return this._onChangeCallback=e,this}_onChangeCallback(){}*[Symbol.iterator](){yield this._x,yield this._y,yield this._z,yield this._order}}zs.DEFAULT_ORDER="XYZ";class jp{constructor(){this.mask=1}set(e){this.mask=(1<<e|0)>>>0}enable(e){this.mask|=1<<e|0}enableAll(){this.mask=-1}toggle(e){this.mask^=1<<e|0}disable(e){this.mask&=~(1<<e|0)}disableAll(){this.mask=0}test(e){return(this.mask&e.mask)!==0}isEnabled(e){return(this.mask&(1<<e|0))!==0}}let Yb=0;const sv=new Q,yo=new ss,fr=new En,su=new Q,Dl=new Q,jb=new Q,Zb=new ss,ov=new Q(1,0,0),lv=new Q(0,1,0),cv=new Q(0,0,1),uv={type:"added"},Kb={type:"removed"},So={type:"childadded",child:null},ph={type:"childremoved",child:null};class Ti extends Fs{constructor(){super(),this.isObject3D=!0,Object.defineProperty(this,"id",{value:Yb++}),this.uuid=Go(),this.name="",this.type="Object3D",this.parent=null,this.children=[],this.up=Ti.DEFAULT_UP.clone();const e=new Q,i=new zs,s=new ss,l=new Q(1,1,1);function c(){s.setFromEuler(i,!1)}function f(){i.setFromQuaternion(s,void 0,!1)}i._onChange(c),s._onChange(f),Object.defineProperties(this,{position:{configurable:!0,enumerable:!0,value:e},rotation:{configurable:!0,enumerable:!0,value:i},quaternion:{configurable:!0,enumerable:!0,value:s},scale:{configurable:!0,enumerable:!0,value:l},modelViewMatrix:{value:new En},normalMatrix:{value:new St}}),this.matrix=new En,this.matrixWorld=new En,this.matrixAutoUpdate=Ti.DEFAULT_MATRIX_AUTO_UPDATE,this.matrixWorldAutoUpdate=Ti.DEFAULT_MATRIX_WORLD_AUTO_UPDATE,this.matrixWorldNeedsUpdate=!1,this.layers=new jp,this.visible=!0,this.castShadow=!1,this.receiveShadow=!1,this.frustumCulled=!0,this.renderOrder=0,this.animations=[],this.customDepthMaterial=void 0,this.customDistanceMaterial=void 0,this.static=!1,this.userData={},this.pivot=null}onBeforeShadow(){}onAfterShadow(){}onBeforeRender(){}onAfterRender(){}applyMatrix4(e){this.matrixAutoUpdate&&this.updateMatrix(),this.matrix.premultiply(e),this.matrix.decompose(this.position,this.quaternion,this.scale)}applyQuaternion(e){return this.quaternion.premultiply(e),this}setRotationFromAxisAngle(e,i){this.quaternion.setFromAxisAngle(e,i)}setRotationFromEuler(e){this.quaternion.setFromEuler(e,!0)}setRotationFromMatrix(e){this.quaternion.setFromRotationMatrix(e)}setRotationFromQuaternion(e){this.quaternion.copy(e)}rotateOnAxis(e,i){return yo.setFromAxisAngle(e,i),this.quaternion.multiply(yo),this}rotateOnWorldAxis(e,i){return yo.setFromAxisAngle(e,i),this.quaternion.premultiply(yo),this}rotateX(e){return this.rotateOnAxis(ov,e)}rotateY(e){return this.rotateOnAxis(lv,e)}rotateZ(e){return this.rotateOnAxis(cv,e)}translateOnAxis(e,i){return sv.copy(e).applyQuaternion(this.quaternion),this.position.add(sv.multiplyScalar(i)),this}translateX(e){return this.translateOnAxis(ov,e)}translateY(e){return this.translateOnAxis(lv,e)}translateZ(e){return this.translateOnAxis(cv,e)}localToWorld(e){return this.updateWorldMatrix(!0,!1),e.applyMatrix4(this.matrixWorld)}worldToLocal(e){return this.updateWorldMatrix(!0,!1),e.applyMatrix4(fr.copy(this.matrixWorld).invert())}lookAt(e,i,s){e.isVector3?su.copy(e):su.set(e,i,s);const l=this.parent;this.updateWorldMatrix(!0,!1),Dl.setFromMatrixPosition(this.matrixWorld),this.isCamera||this.isLight?fr.lookAt(Dl,su,this.up):fr.lookAt(su,Dl,this.up),this.quaternion.setFromRotationMatrix(fr),l&&(fr.extractRotation(l.matrixWorld),yo.setFromRotationMatrix(fr),this.quaternion.premultiply(yo.invert()))}add(e){if(arguments.length>1){for(let i=0;i<arguments.length;i++)this.add(arguments[i]);return this}return e===this?(Zt("Object3D.add: object can't be added as a child of itself.",e),this):(e&&e.isObject3D?(e.removeFromParent(),e.parent=this,this.children.push(e),e.dispatchEvent(uv),So.child=e,this.dispatchEvent(So),So.child=null):Zt("Object3D.add: object not an instance of THREE.Object3D.",e),this)}remove(e){if(arguments.length>1){for(let s=0;s<arguments.length;s++)this.remove(arguments[s]);return this}const i=this.children.indexOf(e);return i!==-1&&(e.parent=null,this.children.splice(i,1),e.dispatchEvent(Kb),ph.child=e,this.dispatchEvent(ph),ph.child=null),this}removeFromParent(){const e=this.parent;return e!==null&&e.remove(this),this}clear(){return this.remove(...this.children)}attach(e){return this.updateWorldMatrix(!0,!1),fr.copy(this.matrixWorld).invert(),e.parent!==null&&(e.parent.updateWorldMatrix(!0,!1),fr.multiply(e.parent.matrixWorld)),e.applyMatrix4(fr),e.removeFromParent(),e.parent=this,this.children.push(e),e.updateWorldMatrix(!1,!0),e.dispatchEvent(uv),So.child=e,this.dispatchEvent(So),So.child=null,this}getObjectById(e){return this.getObjectByProperty("id",e)}getObjectByName(e){return this.getObjectByProperty("name",e)}getObjectByProperty(e,i){if(this[e]===i)return this;for(let s=0,l=this.children.length;s<l;s++){const f=this.children[s].getObjectByProperty(e,i);if(f!==void 0)return f}}getObjectsByProperty(e,i,s=[]){this[e]===i&&s.push(this);const l=this.children;for(let c=0,f=l.length;c<f;c++)l[c].getObjectsByProperty(e,i,s);return s}getWorldPosition(e){return this.updateWorldMatrix(!0,!1),e.setFromMatrixPosition(this.matrixWorld)}getWorldQuaternion(e){return this.updateWorldMatrix(!0,!1),this.matrixWorld.decompose(Dl,e,jb),e}getWorldScale(e){return this.updateWorldMatrix(!0,!1),this.matrixWorld.decompose(Dl,Zb,e),e}getWorldDirection(e){this.updateWorldMatrix(!0,!1);const i=this.matrixWorld.elements;return e.set(i[8],i[9],i[10]).normalize()}raycast(){}intersectsFrustum(){}traverse(e){e(this);const i=this.children;for(let s=0,l=i.length;s<l;s++)i[s].traverse(e)}traverseVisible(e){if(this.visible===!1)return;e(this);const i=this.children;for(let s=0,l=i.length;s<l;s++)i[s].traverseVisible(e)}traverseAncestors(e){const i=this.parent;i!==null&&(e(i),i.traverseAncestors(e))}updateMatrix(){this.matrix.compose(this.position,this.quaternion,this.scale);const e=this.pivot;if(e!==null){const i=e.x,s=e.y,l=e.z,c=this.matrix.elements;c[12]+=i-c[0]*i-c[4]*s-c[8]*l,c[13]+=s-c[1]*i-c[5]*s-c[9]*l,c[14]+=l-c[2]*i-c[6]*s-c[10]*l}this.matrixWorldNeedsUpdate=!0}updateMatrixWorld(e){this.matrixAutoUpdate&&this.updateMatrix(),(this.matrixWorldNeedsUpdate||e)&&(this.matrixWorldAutoUpdate===!0&&(this.parent===null?this.matrixWorld.copy(this.matrix):this.matrixWorld.multiplyMatrices(this.parent.matrixWorld,this.matrix)),this.matrixWorldNeedsUpdate=!1,e=!0);const i=this.children;for(let s=0,l=i.length;s<l;s++)i[s].updateMatrixWorld(e)}updateWorldMatrix(e,i,s=!1){const l=this.parent;if(e===!0&&l!==null&&l.updateWorldMatrix(!0,!1),this.matrixAutoUpdate&&this.updateMatrix(),(this.matrixWorldNeedsUpdate||s)&&(this.matrixWorldAutoUpdate===!0&&(this.parent===null?this.matrixWorld.copy(this.matrix):this.matrixWorld.multiplyMatrices(this.parent.matrixWorld,this.matrix)),this.matrixWorldNeedsUpdate=!1,s=!0),i===!0){const c=this.children;for(let f=0,h=c.length;f<h;f++)c[f].updateWorldMatrix(!1,!0,s)}}toJSON(e){const i=e===void 0||typeof e=="string",s={};i&&(e={geometries:{},materials:{},textures:{},images:{},shapes:{},skeletons:{},animations:{},nodes:{}},s.metadata={version:4.7,type:"Object",generator:"Object3D.toJSON"});const l={};l.uuid=this.uuid,l.type=this.type,l.name=this.name,l.castShadow=this.castShadow,l.receiveShadow=this.receiveShadow,l.visible=this.visible,l.frustumCulled=this.frustumCulled,l.renderOrder=this.renderOrder,l.static=this.static,l.matrixAutoUpdate=this.matrixAutoUpdate,Object.keys(this.userData).length>0&&(l.userData=this.userData),l.layers=this.layers.mask,l.matrix=this.matrix.toArray(),l.up=this.up.toArray(),this.pivot!==null&&(l.pivot=this.pivot.toArray()),this.morphTargetDictionary!==void 0&&(l.morphTargetDictionary=Object.assign({},this.morphTargetDictionary)),this.morphTargetInfluences!==void 0&&(l.morphTargetInfluences=this.morphTargetInfluences.slice()),this.isInstancedMesh&&(l.type="InstancedMesh",l.count=this.count,l.instanceMatrix=this.instanceMatrix.toJSON(),this.instanceColor!==null&&(l.instanceColor=this.instanceColor.toJSON())),this.isBatchedMesh&&(l.type="BatchedMesh",l.perObjectFrustumCulled=this.perObjectFrustumCulled,l.sortObjects=this.sortObjects,l.drawRanges=this._drawRanges,l.reservedRanges=this._reservedRanges,l.geometryInfo=this._geometryInfo.map(h=>({...h,boundingBox:h.boundingBox?h.boundingBox.toJSON():void 0,boundingSphere:h.boundingSphere?h.boundingSphere.toJSON():void 0})),l.instanceInfo=this._instanceInfo.map(h=>({...h})),l.availableInstanceIds=this._availableInstanceIds.slice(),l.availableGeometryIds=this._availableGeometryIds.slice(),l.nextIndexStart=this._nextIndexStart,l.nextVertexStart=this._nextVertexStart,l.geometryCount=this._geometryCount,l.maxInstanceCount=this._maxInstanceCount,l.maxVertexCount=this._maxVertexCount,l.maxIndexCount=this._maxIndexCount,l.geometryInitialized=this._geometryInitialized,l.matricesTexture=this._matricesTexture.toJSON(e),l.indirectTexture=this._indirectTexture.toJSON(e),this._colorsTexture!==null&&(l.colorsTexture=this._colorsTexture.toJSON(e)),this.boundingSphere!==null&&(l.boundingSphere=this.boundingSphere.toJSON()),this.boundingBox!==null&&(l.boundingBox=this.boundingBox.toJSON()));function c(h,m){return h[m.uuid]===void 0&&(h[m.uuid]=m.toJSON(e)),m.uuid}if(this.isScene)this.background&&(this.background.isColor?l.background=this.background.toJSON():this.background.isTexture&&(l.background=this.background.toJSON(e).uuid)),this.environment&&this.environment.isTexture&&this.environment.isRenderTargetTexture!==!0&&(l.environment=this.environment.toJSON(e).uuid);else if(this.isMesh||this.isLine||this.isPoints){l.geometry=c(e.geometries,this.geometry);const h=this.geometry.parameters;if(h!==void 0&&h.shapes!==void 0){const m=h.shapes;if(Array.isArray(m))for(let p=0,g=m.length;p<g;p++){const v=m[p];c(e.shapes,v)}else c(e.shapes,m)}}if(this.isSkinnedMesh&&(l.bindMode=this.bindMode,l.bindMatrix=this.bindMatrix.toArray(),this.skeleton!==void 0&&(c(e.skeletons,this.skeleton),l.skeleton=this.skeleton.uuid)),this.material!==void 0)if(Array.isArray(this.material)){const h=[];for(let m=0,p=this.material.length;m<p;m++)h.push(c(e.materials,this.material[m]));l.material=h}else l.material=c(e.materials,this.material);if(this.children.length>0){l.children=[];for(let h=0;h<this.children.length;h++)l.children.push(this.children[h].toJSON(e).object)}if(this.animations.length>0){l.animations=[];for(let h=0;h<this.animations.length;h++){const m=this.animations[h];l.animations.push(c(e.animations,m))}}if(i){const h=f(e.geometries),m=f(e.materials),p=f(e.textures),g=f(e.images),v=f(e.shapes),x=f(e.skeletons),_=f(e.animations),E=f(e.nodes);h.length>0&&(s.geometries=h),m.length>0&&(s.materials=m),p.length>0&&(s.textures=p),g.length>0&&(s.images=g),v.length>0&&(s.shapes=v),x.length>0&&(s.skeletons=x),_.length>0&&(s.animations=_),E.length>0&&(s.nodes=E)}return s.object=l,s;function f(h){const m=[];for(const p in h){const g=h[p];delete g.metadata,m.push(g)}return m}}clone(e){return new this.constructor().copy(this,e)}copy(e,i=!0){if(this.name=e.name,this.up.copy(e.up),this.position.copy(e.position),this.rotation.order=e.rotation.order,this.quaternion.copy(e.quaternion),this.scale.copy(e.scale),this.pivot=e.pivot!==null?e.pivot.clone():null,this.matrix.copy(e.matrix),this.matrixWorld.copy(e.matrixWorld),this.matrixAutoUpdate=e.matrixAutoUpdate,this.matrixWorldAutoUpdate=e.matrixWorldAutoUpdate,this.matrixWorldNeedsUpdate=e.matrixWorldNeedsUpdate,this.layers.mask=e.layers.mask,this.visible=e.visible,this.castShadow=e.castShadow,this.receiveShadow=e.receiveShadow,this.frustumCulled=e.frustumCulled,this.renderOrder=e.renderOrder,this.static=e.static,this.animations=e.animations.slice(),this.userData=JSON.parse(JSON.stringify(e.userData)),i===!0)for(let s=0;s<e.children.length;s++){const l=e.children[s];this.add(l.clone())}return this}dispose(){this.dispatchEvent({type:"dispose"})}}Ti.DEFAULT_UP=new Q(0,1,0);Ti.DEFAULT_MATRIX_AUTO_UPDATE=!0;Ti.DEFAULT_MATRIX_WORLD_AUTO_UPDATE=!0;class ua extends Ti{constructor(){super(),this.isGroup=!0,this.type="Group"}}const Qb={type:"move"};class mh{constructor(){this._targetRay=null,this._grip=null,this._hand=null}getHandSpace(){return this._hand===null&&(this._hand=new ua,this._hand.matrixAutoUpdate=!1,this._hand.visible=!1,this._hand.joints={},this._hand.inputState={pinching:!1}),this._hand}getTargetRaySpace(){return this._targetRay===null&&(this._targetRay=new ua,this._targetRay.matrixAutoUpdate=!1,this._targetRay.visible=!1,this._targetRay.hasLinearVelocity=!1,this._targetRay.linearVelocity=new Q,this._targetRay.hasAngularVelocity=!1,this._targetRay.angularVelocity=new Q),this._targetRay}getGripSpace(){return this._grip===null&&(this._grip=new ua,this._grip.matrixAutoUpdate=!1,this._grip.visible=!1,this._grip.hasLinearVelocity=!1,this._grip.linearVelocity=new Q,this._grip.hasAngularVelocity=!1,this._grip.angularVelocity=new Q,this._grip.eventsEnabled=!1),this._grip}dispatchEvent(e){return this._targetRay!==null&&this._targetRay.dispatchEvent(e),this._grip!==null&&this._grip.dispatchEvent(e),this._hand!==null&&this._hand.dispatchEvent(e),this}connect(e){if(e&&e.hand){const i=this._hand;if(i)for(const s of e.hand.values())this._getHandJoint(i,s)}return this.dispatchEvent({type:"connected",data:e}),this}disconnect(e){return this.dispatchEvent({type:"disconnected",data:e}),this._targetRay!==null&&(this._targetRay.visible=!1),this._grip!==null&&(this._grip.visible=!1),this._hand!==null&&(this._hand.visible=!1),this}update(e,i,s){let l=null,c=null,f=null;const h=this._targetRay,m=this._grip,p=this._hand;if(e&&i.session.visibilityState!=="visible-blurred"){if(p&&e.hand){f=!0;for(const R of e.hand.values()){const b=i.getJointPose(R,s),S=this._getHandJoint(p,R);b!==null&&(S.matrix.fromArray(b.transform.matrix),S.matrix.decompose(S.position,S.rotation,S.scale),S.matrixWorldNeedsUpdate=!0,S.jointRadius=b.radius),S.visible=b!==null}const g=p.joints["index-finger-tip"],v=p.joints["thumb-tip"],x=g.position.distanceTo(v.position),_=.02,E=.005;p.inputState.pinching&&x>_+E?(p.inputState.pinching=!1,this.dispatchEvent({type:"pinchend",handedness:e.handedness,target:this})):!p.inputState.pinching&&x<=_-E&&(p.inputState.pinching=!0,this.dispatchEvent({type:"pinchstart",handedness:e.handedness,target:this}))}else m!==null&&e.gripSpace&&(c=i.getPose(e.gripSpace,s),c!==null&&(m.matrix.fromArray(c.transform.matrix),m.matrix.decompose(m.position,m.rotation,m.scale),m.matrixWorldNeedsUpdate=!0,c.linearVelocity?(m.hasLinearVelocity=!0,m.linearVelocity.copy(c.linearVelocity)):m.hasLinearVelocity=!1,c.angularVelocity?(m.hasAngularVelocity=!0,m.angularVelocity.copy(c.angularVelocity)):m.hasAngularVelocity=!1,m.eventsEnabled&&m.dispatchEvent({type:"gripUpdated",data:e,target:this})));h!==null&&(l=i.getPose(e.targetRaySpace,s),l===null&&c!==null&&(l=c),l!==null&&(h.matrix.fromArray(l.transform.matrix),h.matrix.decompose(h.position,h.rotation,h.scale),h.matrixWorldNeedsUpdate=!0,l.linearVelocity?(h.hasLinearVelocity=!0,h.linearVelocity.copy(l.linearVelocity)):h.hasLinearVelocity=!1,l.angularVelocity?(h.hasAngularVelocity=!0,h.angularVelocity.copy(l.angularVelocity)):h.hasAngularVelocity=!1,this.dispatchEvent(Qb)))}return h!==null&&(h.visible=l!==null),m!==null&&(m.visible=c!==null),p!==null&&(p.visible=f!==null),this}_getHandJoint(e,i){if(e.joints[i.jointName]===void 0){const s=new ua;s.matrixAutoUpdate=!1,s.visible=!1,e.joints[i.jointName]=s,e.add(s)}return e.joints[i.jointName]}}const D_={aliceblue:15792383,antiquewhite:16444375,aqua:65535,aquamarine:8388564,azure:15794175,beige:16119260,bisque:16770244,black:0,blanchedalmond:16772045,blue:255,blueviolet:9055202,brown:10824234,burlywood:14596231,cadetblue:6266528,chartreuse:8388352,chocolate:13789470,coral:16744272,cornflowerblue:6591981,cornsilk:16775388,crimson:14423100,cyan:65535,darkblue:139,darkcyan:35723,darkgoldenrod:12092939,darkgray:11119017,darkgreen:25600,darkgrey:11119017,darkkhaki:12433259,darkmagenta:9109643,darkolivegreen:5597999,darkorange:16747520,darkorchid:10040012,darkred:9109504,darksalmon:15308410,darkseagreen:9419919,darkslateblue:4734347,darkslategray:3100495,darkslategrey:3100495,darkturquoise:52945,darkviolet:9699539,deeppink:16716947,deepskyblue:49151,dimgray:6908265,dimgrey:6908265,dodgerblue:2003199,firebrick:11674146,floralwhite:16775920,forestgreen:2263842,fuchsia:16711935,gainsboro:14474460,ghostwhite:16316671,gold:16766720,goldenrod:14329120,gray:8421504,green:32768,greenyellow:11403055,grey:8421504,honeydew:15794160,hotpink:16738740,indianred:13458524,indigo:4915330,ivory:16777200,khaki:15787660,lavender:15132410,lavenderblush:16773365,lawngreen:8190976,lemonchiffon:16775885,lightblue:11393254,lightcoral:15761536,lightcyan:14745599,lightgoldenrodyellow:16448210,lightgray:13882323,lightgreen:9498256,lightgrey:13882323,lightpink:16758465,lightsalmon:16752762,lightseagreen:2142890,lightskyblue:8900346,lightslategray:7833753,lightslategrey:7833753,lightsteelblue:11584734,lightyellow:16777184,lime:65280,limegreen:3329330,linen:16445670,magenta:16711935,maroon:8388608,mediumaquamarine:6737322,mediumblue:205,mediumorchid:12211667,mediumpurple:9662683,mediumseagreen:3978097,mediumslateblue:8087790,mediumspringgreen:64154,mediumturquoise:4772300,mediumvioletred:13047173,midnightblue:1644912,mintcream:16121850,mistyrose:16770273,moccasin:16770229,navajowhite:16768685,navy:128,oldlace:16643558,olive:8421376,olivedrab:7048739,orange:16753920,orangered:16729344,orchid:14315734,palegoldenrod:15657130,palegreen:10025880,paleturquoise:11529966,palevioletred:14381203,papayawhip:16773077,peachpuff:16767673,peru:13468991,pink:16761035,plum:14524637,powderblue:11591910,purple:8388736,rebeccapurple:6697881,red:16711680,rosybrown:12357519,royalblue:4286945,saddlebrown:9127187,salmon:16416882,sandybrown:16032864,seagreen:3050327,seashell:16774638,sienna:10506797,silver:12632256,skyblue:8900331,slateblue:6970061,slategray:7372944,slategrey:7372944,snow:16775930,springgreen:65407,steelblue:4620980,tan:13808780,teal:32896,thistle:14204888,tomato:16737095,turquoise:4251856,violet:15631086,wheat:16113331,white:16777215,whitesmoke:16119285,yellow:16776960,yellowgreen:10145074},Qr={h:0,s:0,l:0},ou={h:0,s:0,l:0};function gh(r,e,i){return i<0&&(i+=1),i>1&&(i-=1),i<1/6?r+(e-r)*6*i:i<1/2?e:i<2/3?r+(e-r)*6*(2/3-i):r}class wt{constructor(e,i,s){return this.isColor=!0,this.r=1,this.g=1,this.b=1,this.set(e,i,s)}set(e,i,s){if(i===void 0&&s===void 0){const l=e;l&&l.isColor?this.copy(l):typeof l=="number"?this.setHex(l):typeof l=="string"&&this.setStyle(l)}else this.setRGB(e,i,s);return this}setScalar(e){return this.r=e,this.g=e,this.b=e,this}setHex(e,i=Ei){return e=Math.floor(e),this.r=(e>>16&255)/255,this.g=(e>>8&255)/255,this.b=(e&255)/255,kt.colorSpaceToWorking(this,i),this}setRGB(e,i,s,l=kt.workingColorSpace){return this.r=e,this.g=i,this.b=s,kt.colorSpaceToWorking(this,l),this}setHSL(e,i,s,l=kt.workingColorSpace){if(e=qp(e,1),i=Dt(i,0,1),s=Dt(s,0,1),i===0)this.r=this.g=this.b=s;else{const c=s<=.5?s*(1+i):s+i-s*i,f=2*s-c;this.r=gh(f,c,e+1/3),this.g=gh(f,c,e),this.b=gh(f,c,e-1/3)}return kt.colorSpaceToWorking(this,l),this}setStyle(e,i=Ei){function s(c){c!==void 0&&parseFloat(c)<1&&ht("Color: Alpha component of "+e+" will be ignored.")}let l;if(l=/^(\w+)\(([^\)]*)\)/.exec(e)){let c;const f=l[1],h=l[2];switch(f){case"rgb":case"rgba":if(c=/^\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*(?:,\s*(\d*\.?\d+)\s*)?$/.exec(h))return s(c[4]),this.setRGB(Math.min(255,parseInt(c[1],10))/255,Math.min(255,parseInt(c[2],10))/255,Math.min(255,parseInt(c[3],10))/255,i);if(c=/^\s*(\d+)\%\s*,\s*(\d+)\%\s*,\s*(\d+)\%\s*(?:,\s*(\d*\.?\d+)\s*)?$/.exec(h))return s(c[4]),this.setRGB(Math.min(100,parseInt(c[1],10))/100,Math.min(100,parseInt(c[2],10))/100,Math.min(100,parseInt(c[3],10))/100,i);break;case"hsl":case"hsla":if(c=/^\s*(\d*\.?\d+)\s*,\s*(\d*\.?\d+)\%\s*,\s*(\d*\.?\d+)\%\s*(?:,\s*(\d*\.?\d+)\s*)?$/.exec(h))return s(c[4]),this.setHSL(parseFloat(c[1])/360,parseFloat(c[2])/100,parseFloat(c[3])/100,i);break;default:ht("Color: Unknown color model "+e)}}else if(l=/^\#([A-Fa-f\d]+)$/.exec(e)){const c=l[1],f=c.length;if(f===3)return this.setRGB(parseInt(c.charAt(0),16)/15,parseInt(c.charAt(1),16)/15,parseInt(c.charAt(2),16)/15,i);if(f===6)return this.setHex(parseInt(c,16),i);ht("Color: Invalid hex color "+e)}else if(e&&e.length>0)return this.setColorName(e,i);return this}setColorName(e,i=Ei){const s=D_[e.toLowerCase()];return s!==void 0?this.setHex(s,i):ht("Color: Unknown color "+e),this}clone(){return new this.constructor(this.r,this.g,this.b)}copy(e){return this.r=e.r,this.g=e.g,this.b=e.b,this}copySRGBToLinear(e){return this.r=br(e.r),this.g=br(e.g),this.b=br(e.b),this}copyLinearToSRGB(e){return this.r=Bo(e.r),this.g=Bo(e.g),this.b=Bo(e.b),this}convertSRGBToLinear(){return this.copySRGBToLinear(this),this}convertLinearToSRGB(){return this.copyLinearToSRGB(this),this}getHex(e=Ei){return kt.workingToColorSpace(hi.copy(this),e),Math.round(Dt(hi.r*255,0,255))*65536+Math.round(Dt(hi.g*255,0,255))*256+Math.round(Dt(hi.b*255,0,255))}getHexString(e=Ei){return("000000"+this.getHex(e).toString(16)).slice(-6)}getHSL(e,i=kt.workingColorSpace){kt.workingToColorSpace(hi.copy(this),i);const s=hi.r,l=hi.g,c=hi.b,f=Math.max(s,l,c),h=Math.min(s,l,c);let m,p;const g=(h+f)/2;if(h===f)m=0,p=0;else{const v=f-h;switch(p=g<=.5?v/(f+h):v/(2-f-h),f){case s:m=(l-c)/v+(l<c?6:0);break;case l:m=(c-s)/v+2;break;case c:m=(s-l)/v+4;break}m/=6}return e.h=m,e.s=p,e.l=g,e}getRGB(e,i=kt.workingColorSpace){return kt.workingToColorSpace(hi.copy(this),i),e.r=hi.r,e.g=hi.g,e.b=hi.b,e}getStyle(e=Ei){kt.workingToColorSpace(hi.copy(this),e);const i=hi.r,s=hi.g,l=hi.b;return e!==Ei?`color(${e} ${i.toFixed(3)} ${s.toFixed(3)} ${l.toFixed(3)})`:`rgb(${Math.round(i*255)},${Math.round(s*255)},${Math.round(l*255)})`}offsetHSL(e,i,s){return this.getHSL(Qr),this.setHSL(Qr.h+e,Qr.s+i,Qr.l+s)}add(e){return this.r+=e.r,this.g+=e.g,this.b+=e.b,this}addColors(e,i){return this.r=e.r+i.r,this.g=e.g+i.g,this.b=e.b+i.b,this}addScalar(e){return this.r+=e,this.g+=e,this.b+=e,this}sub(e){return this.r=Math.max(0,this.r-e.r),this.g=Math.max(0,this.g-e.g),this.b=Math.max(0,this.b-e.b),this}multiply(e){return this.r*=e.r,this.g*=e.g,this.b*=e.b,this}multiplyScalar(e){return this.r*=e,this.g*=e,this.b*=e,this}lerp(e,i){return this.r+=(e.r-this.r)*i,this.g+=(e.g-this.g)*i,this.b+=(e.b-this.b)*i,this}lerpColors(e,i,s){return this.r=e.r+(i.r-e.r)*s,this.g=e.g+(i.g-e.g)*s,this.b=e.b+(i.b-e.b)*s,this}lerpHSL(e,i){this.getHSL(Qr),e.getHSL(ou);const s=Vl(Qr.h,ou.h,i),l=Vl(Qr.s,ou.s,i),c=Vl(Qr.l,ou.l,i);return this.setHSL(s,l,c),this}setFromVector3(e){return this.r=e.x,this.g=e.y,this.b=e.z,this}applyMatrix3(e){const i=this.r,s=this.g,l=this.b,c=e.elements;return this.r=c[0]*i+c[3]*s+c[6]*l,this.g=c[1]*i+c[4]*s+c[7]*l,this.b=c[2]*i+c[5]*s+c[8]*l,this}equals(e){return e.r===this.r&&e.g===this.g&&e.b===this.b}fromArray(e,i=0){return this.r=e[i],this.g=e[i+1],this.b=e[i+2],this}toArray(e=[],i=0){return e[i]=this.r,e[i+1]=this.g,e[i+2]=this.b,e}fromBufferAttribute(e,i){return this.r=e.getX(i),this.g=e.getY(i),this.b=e.getZ(i),this}toJSON(){return this.getHex()}*[Symbol.iterator](){yield this.r,yield this.g,yield this.b}}const hi=new wt;wt.NAMES=D_;class N_ extends Ti{constructor(){super(),this.isScene=!0,this.type="Scene",this.background=null,this.environment=null,this.fog=null,this.backgroundBlurriness=0,this.backgroundIntensity=1,this.backgroundRotation=new zs,this.environmentIntensity=1,this.environmentRotation=new zs,this.overrideMaterial=null,typeof __THREE_DEVTOOLS__<"u"&&__THREE_DEVTOOLS__.dispatchEvent(new CustomEvent("observe",{detail:this}))}copy(e,i){return super.copy(e,i),e.background!==null&&(this.background=e.background.clone()),e.environment!==null&&(this.environment=e.environment.clone()),e.fog!==null&&(this.fog=e.fog.clone()),this.backgroundBlurriness=e.backgroundBlurriness,this.backgroundIntensity=e.backgroundIntensity,this.backgroundRotation.copy(e.backgroundRotation),this.environmentIntensity=e.environmentIntensity,this.environmentRotation.copy(e.environmentRotation),e.overrideMaterial!==null&&(this.overrideMaterial=e.overrideMaterial.clone()),this.matrixAutoUpdate=e.matrixAutoUpdate,this}toJSON(e){const i=super.toJSON(e);return this.fog!==null&&(i.object.fog=this.fog.toJSON()),i.object.backgroundBlurriness=this.backgroundBlurriness,i.object.backgroundIntensity=this.backgroundIntensity,i.object.backgroundRotation=this.backgroundRotation.toArray(),i.object.environmentIntensity=this.environmentIntensity,i.object.environmentRotation=this.environmentRotation.toArray(),i}}const ba=new Q,dr=new Q,xh=new Q,hr=new Q,bo=new Q,Mo=new Q,fv=new Q,vh=new Q,_h=new Q,yh=new Q,Sh=new Ln,bh=new Ln,Mh=new Ln;class Ea{constructor(e=new Q,i=new Q,s=new Q){this.a=e,this.b=i,this.c=s}static getNormal(e,i,s,l){l.subVectors(s,i),ba.subVectors(e,i),l.cross(ba);const c=l.lengthSq();return c>0?l.multiplyScalar(1/Math.sqrt(c)):l.set(0,0,0)}static getBarycoord(e,i,s,l,c){ba.subVectors(l,i),dr.subVectors(s,i),xh.subVectors(e,i);const f=ba.dot(ba),h=ba.dot(dr),m=ba.dot(xh),p=dr.dot(dr),g=dr.dot(xh),v=f*p-h*h;if(v===0)return c.set(0,0,0),null;const x=1/v,_=(p*m-h*g)*x,E=(f*g-h*m)*x;return c.set(1-_-E,E,_)}static containsPoint(e,i,s,l){return this.getBarycoord(e,i,s,l,hr)===null?!1:hr.x>=0&&hr.y>=0&&hr.x+hr.y<=1}static getInterpolation(e,i,s,l,c,f,h,m){return this.getBarycoord(e,i,s,l,hr)===null?(m.x=0,m.y=0,"z"in m&&(m.z=0),"w"in m&&(m.w=0),null):(m.setScalar(0),m.addScaledVector(c,hr.x),m.addScaledVector(f,hr.y),m.addScaledVector(h,hr.z),m)}static getInterpolatedAttribute(e,i,s,l,c,f){return Sh.setScalar(0),bh.setScalar(0),Mh.setScalar(0),Sh.fromBufferAttribute(e,i),bh.fromBufferAttribute(e,s),Mh.fromBufferAttribute(e,l),f.setScalar(0),f.addScaledVector(Sh,c.x),f.addScaledVector(bh,c.y),f.addScaledVector(Mh,c.z),f}static isFrontFacing(e,i,s,l){return ba.subVectors(s,i),dr.subVectors(e,i),ba.cross(dr).dot(l)<0}set(e,i,s){return this.a.copy(e),this.b.copy(i),this.c.copy(s),this}setFromPointsAndIndices(e,i,s,l){return this.a.copy(e[i]),this.b.copy(e[s]),this.c.copy(e[l]),this}setFromAttributeAndIndices(e,i,s,l){return this.a.fromBufferAttribute(e,i),this.b.fromBufferAttribute(e,s),this.c.fromBufferAttribute(e,l),this}clone(){return new this.constructor().copy(this)}copy(e){return this.a.copy(e.a),this.b.copy(e.b),this.c.copy(e.c),this}getArea(){return ba.subVectors(this.c,this.b),dr.subVectors(this.a,this.b),ba.cross(dr).length()*.5}getMidpoint(e){return e.addVectors(this.a,this.b).add(this.c).multiplyScalar(1/3)}getNormal(e){return Ea.getNormal(this.a,this.b,this.c,e)}getPlane(e){return e.setFromCoplanarPoints(this.a,this.b,this.c)}getBarycoord(e,i){return Ea.getBarycoord(e,this.a,this.b,this.c,i)}getInterpolation(e,i,s,l,c){return Ea.getInterpolation(e,this.a,this.b,this.c,i,s,l,c)}containsPoint(e){return Ea.containsPoint(e,this.a,this.b,this.c)}isFrontFacing(e){return Ea.isFrontFacing(this.a,this.b,this.c,e)}intersectsBox(e){return e.intersectsTriangle(this)}closestPointToPoint(e,i){const s=this.a,l=this.b,c=this.c;let f,h;bo.subVectors(l,s),Mo.subVectors(c,s),vh.subVectors(e,s);const m=bo.dot(vh),p=Mo.dot(vh);if(m<=0&&p<=0)return i.copy(s);_h.subVectors(e,l);const g=bo.dot(_h),v=Mo.dot(_h);if(g>=0&&v<=g)return i.copy(l);const x=m*v-g*p;if(x<=0&&m>=0&&g<=0)return f=m/(m-g),i.copy(s).addScaledVector(bo,f);yh.subVectors(e,c);const _=bo.dot(yh),E=Mo.dot(yh);if(E>=0&&_<=E)return i.copy(c);const R=_*p-m*E;if(R<=0&&p>=0&&E<=0)return h=p/(p-E),i.copy(s).addScaledVector(Mo,h);const b=g*E-_*v;if(b<=0&&v-g>=0&&_-E>=0)return fv.subVectors(c,l),h=(v-g)/(v-g+(_-E)),i.copy(l).addScaledVector(fv,h);const S=1/(b+R+x);return f=R*S,h=x*S,i.copy(s).addScaledVector(bo,f).addScaledVector(Mo,h)}equals(e){return e.a.equals(this.a)&&e.b.equals(this.b)&&e.c.equals(this.c)}}class Vo{constructor(e=new Q(1/0,1/0,1/0),i=new Q(-1/0,-1/0,-1/0)){this.isBox3=!0,this.min=e,this.max=i}set(e,i){return this.min.copy(e),this.max.copy(i),this}setFromArray(e){this.makeEmpty();for(let i=0,s=e.length;i<s;i+=3)this.expandByPoint(Ma.fromArray(e,i));return this}setFromBufferAttribute(e){this.makeEmpty();for(let i=0,s=e.count;i<s;i++)this.expandByPoint(Ma.fromBufferAttribute(e,i));return this}setFromPoints(e){this.makeEmpty();for(let i=0,s=e.length;i<s;i++)this.expandByPoint(e[i]);return this}setFromCenterAndSize(e,i){const s=Ma.copy(i).multiplyScalar(.5);return this.min.copy(e).sub(s),this.max.copy(e).add(s),this}setFromObject(e,i=!1){return this.makeEmpty(),this.expandByObject(e,i)}clone(){return new this.constructor().copy(this)}copy(e){return this.min.copy(e.min),this.max.copy(e.max),this}makeEmpty(){return this.min.x=this.min.y=this.min.z=1/0,this.max.x=this.max.y=this.max.z=-1/0,this}isEmpty(){return this.max.x<this.min.x||this.max.y<this.min.y||this.max.z<this.min.z}getCenter(e){return this.isEmpty()?e.set(0,0,0):e.addVectors(this.min,this.max).multiplyScalar(.5)}getSize(e){return this.isEmpty()?e.set(0,0,0):e.subVectors(this.max,this.min)}expandByPoint(e){return this.min.min(e),this.max.max(e),this}expandByVector(e){return this.min.sub(e),this.max.add(e),this}expandByScalar(e){return this.min.addScalar(-e),this.max.addScalar(e),this}expandByObject(e,i=!1){e.updateWorldMatrix(!1,!1);const s=e.geometry;if(s!==void 0){const c=s.getAttribute("position");if(i===!0&&c!==void 0&&e.isInstancedMesh!==!0)for(let f=0,h=c.count;f<h;f++)e.isMesh===!0?e.getVertexPosition(f,Ma):Ma.fromBufferAttribute(c,f),Ma.applyMatrix4(e.matrixWorld),this.expandByPoint(Ma);else e.boundingBox!==void 0?(e.boundingBox===null&&e.computeBoundingBox(),lu.copy(e.boundingBox)):(s.boundingBox===null&&s.computeBoundingBox(),lu.copy(s.boundingBox)),lu.applyMatrix4(e.matrixWorld),this.union(lu)}const l=e.children;for(let c=0,f=l.length;c<f;c++)this.expandByObject(l[c],i);return this}containsPoint(e){return e.x>=this.min.x&&e.x<=this.max.x&&e.y>=this.min.y&&e.y<=this.max.y&&e.z>=this.min.z&&e.z<=this.max.z}containsBox(e){return this.min.x<=e.min.x&&e.max.x<=this.max.x&&this.min.y<=e.min.y&&e.max.y<=this.max.y&&this.min.z<=e.min.z&&e.max.z<=this.max.z}getParameter(e,i){return i.set((e.x-this.min.x)/(this.max.x-this.min.x),(e.y-this.min.y)/(this.max.y-this.min.y),(e.z-this.min.z)/(this.max.z-this.min.z))}intersectsBox(e){return e.max.x>=this.min.x&&e.min.x<=this.max.x&&e.max.y>=this.min.y&&e.min.y<=this.max.y&&e.max.z>=this.min.z&&e.min.z<=this.max.z}intersectsSphere(e){return this.clampPoint(e.center,Ma),Ma.distanceToSquared(e.center)<=e.radius*e.radius}intersectsPlane(e){let i,s;return e.normal.x>0?(i=e.normal.x*this.min.x,s=e.normal.x*this.max.x):(i=e.normal.x*this.max.x,s=e.normal.x*this.min.x),e.normal.y>0?(i+=e.normal.y*this.min.y,s+=e.normal.y*this.max.y):(i+=e.normal.y*this.max.y,s+=e.normal.y*this.min.y),e.normal.z>0?(i+=e.normal.z*this.min.z,s+=e.normal.z*this.max.z):(i+=e.normal.z*this.max.z,s+=e.normal.z*this.min.z),i<=-e.constant&&s>=-e.constant}intersectsTriangle(e){if(this.isEmpty())return!1;this.getCenter(Nl),cu.subVectors(this.max,Nl),Eo.subVectors(e.a,Nl),To.subVectors(e.b,Nl),Ao.subVectors(e.c,Nl),Jr.subVectors(To,Eo),$r.subVectors(Ao,To),Es.subVectors(Eo,Ao);let i=[0,-Jr.z,Jr.y,0,-$r.z,$r.y,0,-Es.z,Es.y,Jr.z,0,-Jr.x,$r.z,0,-$r.x,Es.z,0,-Es.x,-Jr.y,Jr.x,0,-$r.y,$r.x,0,-Es.y,Es.x,0];return!Eh(i,Eo,To,Ao,cu)||(i=[1,0,0,0,1,0,0,0,1],!Eh(i,Eo,To,Ao,cu))?!1:(uu.crossVectors(Jr,$r),i=[uu.x,uu.y,uu.z],Eh(i,Eo,To,Ao,cu))}clampPoint(e,i){return i.copy(e).clamp(this.min,this.max)}distanceToPoint(e){return this.clampPoint(e,Ma).distanceTo(e)}getBoundingSphere(e){return this.isEmpty()?e.makeEmpty():(this.getCenter(e.center),e.radius=this.getSize(Ma).length()*.5),e}intersect(e){return this.min.max(e.min),this.max.min(e.max),this.isEmpty()&&this.makeEmpty(),this}union(e){return this.min.min(e.min),this.max.max(e.max),this}applyMatrix4(e){return this.isEmpty()?this:(pr[0].set(this.min.x,this.min.y,this.min.z).applyMatrix4(e),pr[1].set(this.min.x,this.min.y,this.max.z).applyMatrix4(e),pr[2].set(this.min.x,this.max.y,this.min.z).applyMatrix4(e),pr[3].set(this.min.x,this.max.y,this.max.z).applyMatrix4(e),pr[4].set(this.max.x,this.min.y,this.min.z).applyMatrix4(e),pr[5].set(this.max.x,this.min.y,this.max.z).applyMatrix4(e),pr[6].set(this.max.x,this.max.y,this.min.z).applyMatrix4(e),pr[7].set(this.max.x,this.max.y,this.max.z).applyMatrix4(e),this.setFromPoints(pr),this)}translate(e){return this.min.add(e),this.max.add(e),this}equals(e){return e.min.equals(this.min)&&e.max.equals(this.max)}toJSON(){return{min:this.min.toArray(),max:this.max.toArray()}}fromJSON(e){return this.min.fromArray(e.min),this.max.fromArray(e.max),this}}const pr=[new Q,new Q,new Q,new Q,new Q,new Q,new Q,new Q],Ma=new Q,lu=new Vo,Eo=new Q,To=new Q,Ao=new Q,Jr=new Q,$r=new Q,Es=new Q,Nl=new Q,cu=new Q,uu=new Q,Ts=new Q;function Eh(r,e,i,s,l){for(let c=0,f=r.length-3;c<=f;c+=3){Ts.fromArray(r,c);const h=l.x*Math.abs(Ts.x)+l.y*Math.abs(Ts.y)+l.z*Math.abs(Ts.z),m=e.dot(Ts),p=i.dot(Ts),g=s.dot(Ts);if(Math.max(-Math.max(m,p,g),Math.min(m,p,g))>h)return!1}return!0}const Xn=new Q,fu=new Kt;let Jb=0;class Fn extends Fs{constructor(e,i,s=!1){if(super(),Array.isArray(e))throw new TypeError("THREE.BufferAttribute: array should be a Typed Array.");this.isBufferAttribute=!0,Object.defineProperty(this,"id",{value:Jb++}),this.name="",this.array=e,this.itemSize=i,this.count=e!==void 0?e.length/i:0,this.normalized=s,this.usage=vb,this.updateRanges=[],this.gpuType=Ga,this.version=0}onUploadCallback(){}set needsUpdate(e){e===!0&&this.version++}setUsage(e){return this.usage=e,this}addUpdateRange(e,i){this.updateRanges.push({start:e,count:i})}clearUpdateRanges(){this.updateRanges.length=0}copy(e){return this.name=e.name,this.array=new e.array.constructor(e.array),this.itemSize=e.itemSize,this.count=e.count,this.normalized=e.normalized,this.usage=e.usage,this.gpuType=e.gpuType,this}copyAt(e,i,s){e*=this.itemSize,s*=i.itemSize;for(let l=0,c=this.itemSize;l<c;l++)this.array[e+l]=i.array[s+l];return this}copyArray(e){return this.array.set(e),this}applyMatrix3(e){if(this.itemSize===2)for(let i=0,s=this.count;i<s;i++)fu.fromBufferAttribute(this,i),fu.applyMatrix3(e),this.setXY(i,fu.x,fu.y);else if(this.itemSize===3)for(let i=0,s=this.count;i<s;i++)Xn.fromBufferAttribute(this,i),Xn.applyMatrix3(e),this.setXYZ(i,Xn.x,Xn.y,Xn.z);return this}applyMatrix4(e){for(let i=0,s=this.count;i<s;i++)Xn.fromBufferAttribute(this,i),Xn.applyMatrix4(e),this.setXYZ(i,Xn.x,Xn.y,Xn.z);return this}applyNormalMatrix(e){for(let i=0,s=this.count;i<s;i++)Xn.fromBufferAttribute(this,i),Xn.applyNormalMatrix(e),this.setXYZ(i,Xn.x,Xn.y,Xn.z);return this}transformDirection(e){for(let i=0,s=this.count;i<s;i++)Xn.fromBufferAttribute(this,i),Xn.transformDirection(e),this.setXYZ(i,Xn.x,Xn.y,Xn.z);return this}set(e,i=0){return this.array.set(e,i),this}getComponent(e,i){let s=this.array[e*this.itemSize+i];return this.normalized&&(s=Lo(s,this.array)),s}setComponent(e,i,s){return this.normalized&&(s=bi(s,this.array)),this.array[e*this.itemSize+i]=s,this}getX(e){let i=this.array[e*this.itemSize];return this.normalized&&(i=Lo(i,this.array)),i}setX(e,i){return this.normalized&&(i=bi(i,this.array)),this.array[e*this.itemSize]=i,this}getY(e){let i=this.array[e*this.itemSize+1];return this.normalized&&(i=Lo(i,this.array)),i}setY(e,i){return this.normalized&&(i=bi(i,this.array)),this.array[e*this.itemSize+1]=i,this}getZ(e){let i=this.array[e*this.itemSize+2];return this.normalized&&(i=Lo(i,this.array)),i}setZ(e,i){return this.normalized&&(i=bi(i,this.array)),this.array[e*this.itemSize+2]=i,this}getW(e){let i=this.array[e*this.itemSize+3];return this.normalized&&(i=Lo(i,this.array)),i}setW(e,i){return this.normalized&&(i=bi(i,this.array)),this.array[e*this.itemSize+3]=i,this}setXY(e,i,s){return e*=this.itemSize,this.normalized&&(i=bi(i,this.array),s=bi(s,this.array)),this.array[e+0]=i,this.array[e+1]=s,this}setXYZ(e,i,s,l){return e*=this.itemSize,this.normalized&&(i=bi(i,this.array),s=bi(s,this.array),l=bi(l,this.array)),this.array[e+0]=i,this.array[e+1]=s,this.array[e+2]=l,this}setXYZW(e,i,s,l,c){return e*=this.itemSize,this.normalized&&(i=bi(i,this.array),s=bi(s,this.array),l=bi(l,this.array),c=bi(c,this.array)),this.array[e+0]=i,this.array[e+1]=s,this.array[e+2]=l,this.array[e+3]=c,this}onUpload(e){return this.onUploadCallback=e,this}clone(){return new this.constructor(this.array,this.itemSize).copy(this)}toJSON(){const e={itemSize:this.itemSize,type:this.array.constructor.name,array:Array.from(this.array),normalized:this.normalized};return e.name=this.name,e.usage=this.usage,e.gpuType=this.gpuType,e}dispose(){this.dispatchEvent({type:"dispose"})}}class L_ extends Fn{constructor(e,i,s){super(new Uint16Array(e),i,s)}}class O_ extends Fn{constructor(e,i,s){super(new Uint32Array(e),i,s)}}class Cn extends Fn{constructor(e,i,s){super(new Float32Array(e),i,s)}}const $b=new Vo,Ll=new Q,Th=new Q;class Bs{constructor(e=new Q,i=-1){this.isSphere=!0,this.center=e,this.radius=i}set(e,i){return this.center.copy(e),this.radius=i,this}setFromPoints(e,i){const s=this.center;i!==void 0?s.copy(i):$b.setFromPoints(e).getCenter(s);let l=0;for(let c=0,f=e.length;c<f;c++)l=Math.max(l,s.distanceToSquared(e[c]));return this.radius=Math.sqrt(l),this}copy(e){return this.center.copy(e.center),this.radius=e.radius,this}isEmpty(){return this.radius<0}makeEmpty(){return this.center.set(0,0,0),this.radius=-1,this}containsPoint(e){return e.distanceToSquared(this.center)<=this.radius*this.radius}distanceToPoint(e){return e.distanceTo(this.center)-this.radius}intersectsSphere(e){const i=this.radius+e.radius;return e.center.distanceToSquared(this.center)<=i*i}intersectsBox(e){return e.intersectsSphere(this)}intersectsPlane(e){return Math.abs(e.distanceToPoint(this.center))<=this.radius}clampPoint(e,i){const s=this.center.distanceToSquared(e);return i.copy(e),s>this.radius*this.radius&&(i.sub(this.center).normalize(),i.multiplyScalar(this.radius).add(this.center)),i}getBoundingBox(e){return this.isEmpty()?(e.makeEmpty(),e):(e.set(this.center,this.center),e.expandByScalar(this.radius),e)}applyMatrix4(e){return this.center.applyMatrix4(e),this.radius=this.radius*e.getMaxScaleOnAxis(),this}translate(e){return this.center.add(e),this}expandByPoint(e){if(this.isEmpty())return this.center.copy(e),this.radius=0,this;Ll.subVectors(e,this.center);const i=Ll.lengthSq();if(i>this.radius*this.radius){const s=Math.sqrt(i),l=(s-this.radius)*.5;this.center.addScaledVector(Ll,l/s),this.radius+=l}return this}union(e){return e.isEmpty()?this:this.isEmpty()?(this.copy(e),this):(this.center.equals(e.center)===!0?this.radius=Math.max(this.radius,e.radius):(Th.subVectors(e.center,this.center).setLength(e.radius),this.expandByPoint(Ll.copy(e.center).add(Th)),this.expandByPoint(Ll.copy(e.center).sub(Th))),this)}equals(e){return e.center.equals(this.center)&&e.radius===this.radius}clone(){return new this.constructor().copy(this)}toJSON(){return{radius:this.radius,center:this.center.toArray()}}fromJSON(e){return this.radius=e.radius,this.center.fromArray(e.center),this}}let eM=0;const ca=new En,Ah=new Ti,wo=new Q,qi=new Vo,Ol=new Vo,$n=new Q;class Bn extends Fs{constructor(){super(),this.isBufferGeometry=!0,Object.defineProperty(this,"id",{value:eM++}),this.uuid=Go(),this.name="",this.type="BufferGeometry",this.index=null,this.indirect=null,this.indirectOffset=0,this.attributes={},this.morphAttributes={},this.morphTargetsRelative=!1,this.groups=[],this.boundingBox=null,this.boundingSphere=null,this.drawRange={start:0,count:1/0},this.userData={},this._transformed=!1}getIndex(){return this.index}setIndex(e){return Array.isArray(e)?this.index=new(_b(e)?O_:L_)(e,1):this.index=e,this}setIndirect(e,i=0){return this.indirect=e,this.indirectOffset=i,this}getIndirect(){return this.indirect}getAttribute(e){return this.attributes[e]}setAttribute(e,i){return this.attributes[e]=i,this}deleteAttribute(e){return delete this.attributes[e],this}hasAttribute(e){return this.attributes[e]!==void 0}addGroup(e,i,s=0){this.groups.push({start:e,count:i,materialIndex:s})}clearGroups(){this.groups=[]}setDrawRange(e,i){this.drawRange.start=e,this.drawRange.count=i}applyMatrix4(e){const i=this.attributes.position;i!==void 0&&(i.applyMatrix4(e),i.needsUpdate=!0);const s=this.attributes.normal;if(s!==void 0){const c=new St().getNormalMatrix(e);s.applyNormalMatrix(c),s.needsUpdate=!0}const l=this.attributes.tangent;return l!==void 0&&(l.transformDirection(e),l.needsUpdate=!0),this.boundingBox!==null&&this.computeBoundingBox(),this.boundingSphere!==null&&this.computeBoundingSphere(),this._transformed=!0,this}applyQuaternion(e){return ca.makeRotationFromQuaternion(e),this.applyMatrix4(ca),this}rotateX(e){return ca.makeRotationX(e),this.applyMatrix4(ca),this}rotateY(e){return ca.makeRotationY(e),this.applyMatrix4(ca),this}rotateZ(e){return ca.makeRotationZ(e),this.applyMatrix4(ca),this}translate(e,i,s){return ca.makeTranslation(e,i,s),this.applyMatrix4(ca),this}scale(e,i,s){return ca.makeScale(e,i,s),this.applyMatrix4(ca),this}lookAt(e){return Ah.lookAt(e),Ah.updateMatrix(),this.applyMatrix4(Ah.matrix),this}center(){return this.computeBoundingBox(),this.boundingBox.getCenter(wo).negate(),this.translate(wo.x,wo.y,wo.z),this}setFromPoints(e){const i=this.getAttribute("position");if(i===void 0){const s=[];for(let l=0,c=e.length;l<c;l++){const f=e[l];s.push(f.x,f.y,f.z||0)}this.setAttribute("position",new Cn(s,3))}else{const s=Math.min(e.length,i.count);for(let l=0;l<s;l++){const c=e[l];i.setXYZ(l,c.x,c.y,c.z||0)}e.length>i.count&&ht("BufferGeometry: Buffer size too small for points data. Use .dispose() and create a new geometry."),i.needsUpdate=!0}return this}computeBoundingBox(){this.boundingBox===null&&(this.boundingBox=new Vo);const e=this.attributes.position,i=this.morphAttributes.position;if(e&&e.isGLBufferAttribute){Zt("BufferGeometry.computeBoundingBox(): GLBufferAttribute requires a manual bounding box.",this),this.boundingBox.set(new Q(-1/0,-1/0,-1/0),new Q(1/0,1/0,1/0));return}if(e!==void 0){if(this.boundingBox.setFromBufferAttribute(e),i)for(let s=0,l=i.length;s<l;s++){const c=i[s];qi.setFromBufferAttribute(c),this.morphTargetsRelative?($n.addVectors(this.boundingBox.min,qi.min),this.boundingBox.expandByPoint($n),$n.addVectors(this.boundingBox.max,qi.max),this.boundingBox.expandByPoint($n)):(this.boundingBox.expandByPoint(qi.min),this.boundingBox.expandByPoint(qi.max))}}else this.boundingBox.makeEmpty();(isNaN(this.boundingBox.min.x)||isNaN(this.boundingBox.min.y)||isNaN(this.boundingBox.min.z))&&Zt('BufferGeometry.computeBoundingBox(): Computed min/max have NaN values. The "position" attribute is likely to have NaN values.',this)}computeBoundingSphere(){this.boundingSphere===null&&(this.boundingSphere=new Bs);const e=this.attributes.position,i=this.morphAttributes.position;if(e&&e.isGLBufferAttribute){Zt("BufferGeometry.computeBoundingSphere(): GLBufferAttribute requires a manual bounding sphere.",this),this.boundingSphere.set(new Q,1/0);return}if(e){const s=this.boundingSphere.center;if(qi.setFromBufferAttribute(e),i)for(let c=0,f=i.length;c<f;c++){const h=i[c];Ol.setFromBufferAttribute(h),this.morphTargetsRelative?($n.addVectors(qi.min,Ol.min),qi.expandByPoint($n),$n.addVectors(qi.max,Ol.max),qi.expandByPoint($n)):(qi.expandByPoint(Ol.min),qi.expandByPoint(Ol.max))}qi.getCenter(s);let l=0;for(let c=0,f=e.count;c<f;c++)$n.fromBufferAttribute(e,c),l=Math.max(l,s.distanceToSquared($n));if(i)for(let c=0,f=i.length;c<f;c++){const h=i[c],m=this.morphTargetsRelative;for(let p=0,g=h.count;p<g;p++)$n.fromBufferAttribute(h,p),m&&(wo.fromBufferAttribute(e,p),$n.add(wo)),l=Math.max(l,s.distanceToSquared($n))}this.boundingSphere.radius=Math.sqrt(l),isNaN(this.boundingSphere.radius)&&Zt('BufferGeometry.computeBoundingSphere(): Computed radius is NaN. The "position" attribute is likely to have NaN values.',this)}}computeTangents(){const e=this.index,i=this.attributes;if(e===null||i.position===void 0||i.normal===void 0||i.uv===void 0){Zt("BufferGeometry: .computeTangents() failed. Missing required attributes (index, position, normal or uv)");return}const s=i.position,l=i.normal,c=i.uv;let f=this.getAttribute("tangent");(f===void 0||f.count!==s.count)&&(f=new Fn(new Float32Array(4*s.count),4),this.setAttribute("tangent",f));const h=[],m=[];for(let T=0;T<s.count;T++)h[T]=new Q,m[T]=new Q;const p=new Q,g=new Q,v=new Q,x=new Kt,_=new Kt,E=new Kt,R=new Q,b=new Q;function S(T,O,I){p.fromBufferAttribute(s,T),g.fromBufferAttribute(s,O),v.fromBufferAttribute(s,I),x.fromBufferAttribute(c,T),_.fromBufferAttribute(c,O),E.fromBufferAttribute(c,I),g.sub(p),v.sub(p),_.sub(x),E.sub(x);const W=1/(_.x*E.y-E.x*_.y);isFinite(W)&&(R.copy(g).multiplyScalar(E.y).addScaledVector(v,-_.y).multiplyScalar(W),b.copy(v).multiplyScalar(_.x).addScaledVector(g,-E.x).multiplyScalar(W),h[T].add(R),h[O].add(R),h[I].add(R),m[T].add(b),m[O].add(b),m[I].add(b))}let F=this.groups;F.length===0&&(F=[{start:0,count:e.count}]);for(let T=0,O=F.length;T<O;++T){const I=F[T],W=I.start,J=I.count;for(let re=W,k=W+J;re<k;re+=3)S(e.getX(re+0),e.getX(re+1),e.getX(re+2))}const G=new Q,w=new Q,N=new Q,L=new Q;function z(T){N.fromBufferAttribute(l,T),L.copy(N);const O=h[T];G.copy(O),G.sub(N.multiplyScalar(N.dot(O))).normalize(),w.crossVectors(L,O);const W=w.dot(m[T])<0?-1:1;f.setXYZW(T,G.x,G.y,G.z,W)}for(let T=0,O=F.length;T<O;++T){const I=F[T],W=I.start,J=I.count;for(let re=W,k=W+J;re<k;re+=3)z(e.getX(re+0)),z(e.getX(re+1)),z(e.getX(re+2))}this._transformed=!0}computeVertexNormals(){const e=this.index,i=this.getAttribute("position");if(i!==void 0){let s=this.getAttribute("normal");if(s===void 0||s.count!==i.count)s=new Fn(new Float32Array(i.count*3),3),this.setAttribute("normal",s);else for(let x=0,_=s.count;x<_;x++)s.setXYZ(x,0,0,0);const l=new Q,c=new Q,f=new Q,h=new Q,m=new Q,p=new Q,g=new Q,v=new Q;if(e)for(let x=0,_=e.count;x<_;x+=3){const E=e.getX(x+0),R=e.getX(x+1),b=e.getX(x+2);l.fromBufferAttribute(i,E),c.fromBufferAttribute(i,R),f.fromBufferAttribute(i,b),g.subVectors(f,c),v.subVectors(l,c),g.cross(v),h.fromBufferAttribute(s,E),m.fromBufferAttribute(s,R),p.fromBufferAttribute(s,b),h.add(g),m.add(g),p.add(g),s.setXYZ(E,h.x,h.y,h.z),s.setXYZ(R,m.x,m.y,m.z),s.setXYZ(b,p.x,p.y,p.z)}else for(let x=0,_=i.count;x<_;x+=3)l.fromBufferAttribute(i,x+0),c.fromBufferAttribute(i,x+1),f.fromBufferAttribute(i,x+2),g.subVectors(f,c),v.subVectors(l,c),g.cross(v),s.setXYZ(x+0,g.x,g.y,g.z),s.setXYZ(x+1,g.x,g.y,g.z),s.setXYZ(x+2,g.x,g.y,g.z);this.normalizeNormals(),s.needsUpdate=!0}}normalizeNormals(){const e=this.attributes.normal;for(let i=0,s=e.count;i<s;i++)$n.fromBufferAttribute(e,i),$n.normalize(),e.setXYZ(i,$n.x,$n.y,$n.z)}toNonIndexed(){function e(h,m){const p=h.array,g=h.itemSize,v=h.normalized,x=new p.constructor(m.length*g);let _=0,E=0;for(let R=0,b=m.length;R<b;R++){h.isInterleavedBufferAttribute?_=m[R]*h.data.stride+h.offset:_=m[R]*g;for(let S=0;S<g;S++)x[E++]=p[_++]}return new Fn(x,g,v)}if(this.index===null)return ht("BufferGeometry.toNonIndexed(): BufferGeometry is already non-indexed."),this;const i=new Bn,s=this.index.array,l=this.attributes;for(const h in l){const m=l[h],p=e(m,s);i.setAttribute(h,p)}const c=this.morphAttributes;for(const h in c){const m=[],p=c[h];for(let g=0,v=p.length;g<v;g++){const x=p[g],_=e(x,s);m.push(_)}i.morphAttributes[h]=m}i.morphTargetsRelative=this.morphTargetsRelative;const f=this.groups;for(let h=0,m=f.length;h<m;h++){const p=f[h];i.addGroup(p.start,p.count,p.materialIndex)}return i}toJSON(){const e={metadata:{version:4.7,type:"BufferGeometry",generator:"BufferGeometry.toJSON"}};if(e.uuid=this.uuid,e.type=this.parameters!==void 0&&this._transformed===!0?"BufferGeometry":this.type,e.name=this.name,Object.keys(this.userData).length>0&&(e.userData=this.userData),this.parameters!==void 0&&this._transformed!==!0){const m=this.parameters;for(const p in m)m[p]!==void 0&&(e[p]=m[p]);return e}e.data={attributes:{}};const i=this.index;i!==null&&(e.data.index={type:i.array.constructor.name,array:Array.prototype.slice.call(i.array)});const s=this.attributes;for(const m in s){const p=s[m];e.data.attributes[m]=p.toJSON(e.data)}const l={};let c=!1;for(const m in this.morphAttributes){const p=this.morphAttributes[m],g=[];for(let v=0,x=p.length;v<x;v++){const _=p[v];g.push(_.toJSON(e.data))}g.length>0&&(l[m]=g,c=!0)}c&&(e.data.morphAttributes=l,e.data.morphTargetsRelative=this.morphTargetsRelative);const f=this.groups;f.length>0&&(e.data.groups=JSON.parse(JSON.stringify(f)));const h=this.boundingSphere;return h!==null&&(e.data.boundingSphere=h.toJSON()),e}clone(){return new this.constructor().copy(this)}copy(e){this.index=null,this.attributes={},this.morphAttributes={},this.groups=[],this.boundingBox=null,this.boundingSphere=null;const i={};this.name=e.name;const s=e.index;s!==null&&this.setIndex(s.clone());const l=e.attributes;for(const p in l){const g=l[p];this.setAttribute(p,g.clone(i))}const c=e.morphAttributes;for(const p in c){const g=[],v=c[p];for(let x=0,_=v.length;x<_;x++)g.push(v[x].clone(i));this.morphAttributes[p]=g}this.morphTargetsRelative=e.morphTargetsRelative;const f=e.groups;for(let p=0,g=f.length;p<g;p++){const v=f[p];this.addGroup(v.start,v.count,v.materialIndex)}const h=e.boundingBox;h!==null&&(this.boundingBox=h.clone());const m=e.boundingSphere;return m!==null&&(this.boundingSphere=m.clone()),this.drawRange.start=e.drawRange.start,this.drawRange.count=e.drawRange.count,this.userData=e.userData,this._transformed=e._transformed,this}dispose(){this.dispatchEvent({type:"dispose"})}}const wh=new Q,tM=new Q,nM=new St;class ts{constructor(e=new Q(1,0,0),i=0){this.isPlane=!0,this.normal=e,this.constant=i}set(e,i){return this.normal.copy(e),this.constant=i,this}setComponents(e,i,s,l){return this.normal.set(e,i,s),this.constant=l,this}setFromNormalAndCoplanarPoint(e,i){return this.normal.copy(e),this.constant=-i.dot(this.normal),this}setFromCoplanarPoints(e,i,s){const l=wh.subVectors(s,i).cross(tM.subVectors(e,i)).normalize();return this.setFromNormalAndCoplanarPoint(l,e),this}copy(e){return this.normal.copy(e.normal),this.constant=e.constant,this}normalize(){const e=1/this.normal.length();return this.normal.multiplyScalar(e),this.constant*=e,this}negate(){return this.constant*=-1,this.normal.negate(),this}distanceToPoint(e){return this.normal.dot(e)+this.constant}distanceToSphere(e){return this.distanceToPoint(e.center)-e.radius}projectPoint(e,i){return i.copy(e).addScaledVector(this.normal,-this.distanceToPoint(e))}intersectLine(e,i,s=!0){const l=e.delta(wh),c=this.normal.dot(l);if(c===0)return this.distanceToPoint(e.start)===0?i.copy(e.start):null;const f=-(e.start.dot(this.normal)+this.constant)/c;return s===!0&&(f<0||f>1)?null:i.copy(e.start).addScaledVector(l,f)}intersectsLine(e){const i=this.distanceToPoint(e.start),s=this.distanceToPoint(e.end);return i<0&&s>0||s<0&&i>0}intersectsBox(e){return e.intersectsPlane(this)}intersectsSphere(e){return e.intersectsPlane(this)}coplanarPoint(e){return e.copy(this.normal).multiplyScalar(-this.constant)}applyMatrix4(e,i){const s=i||nM.getNormalMatrix(e),l=this.coplanarPoint(wh).applyMatrix4(e),c=this.normal.applyMatrix3(s).normalize();return this.constant=-l.dot(c),this}translate(e){return this.constant-=e.dot(this.normal),this}equals(e){return e.normal.equals(this.normal)&&e.constant===this.constant}clone(){return new this.constructor().copy(this)}toJSON(){return{normal:this.normal.toArray(),constant:this.constant}}fromJSON(e){return this.normal.fromArray(e.normal),this.constant=e.constant,this}}let iM=0;class ko extends Fs{constructor(){super(),this.isMaterial=!0,Object.defineProperty(this,"id",{value:iM++}),this.uuid=Go(),this.name="",this.type="Material",this.blending=zo,this.side=Ls,this.vertexColors=!1,this.opacity=1,this.transparent=!1,this.alphaHash=!1,this.blendSrc=f_,this.blendDst=d_,this.blendEquation=No,this.blendSrcAlpha=null,this.blendDstAlpha=null,this.blendEquationAlpha=null,this.blendColor=new wt(0,0,0),this.blendAlpha=0,this.depthFunc=ql,this.depthTest=!0,this.depthWrite=!0,this.stencilWriteMask=255,this.stencilFunc=fb,this.stencilRef=0,this.stencilFuncMask=255,this.stencilFail=lh,this.stencilZFail=lh,this.stencilZPass=lh,this.stencilWrite=!1,this.clippingPlanes=null,this.clipIntersection=!1,this.clipShadows=!1,this.shadowSide=null,this.colorWrite=!0,this.precision=null,this.polygonOffset=!1,this.polygonOffsetFactor=0,this.polygonOffsetUnits=0,this.dithering=!1,this.alphaToCoverage=!1,this.premultipliedAlpha=!1,this.forceSinglePass=!1,this.allowOverride=!0,this.visible=!0,this.toneMapped=!0,this.userData={},this.version=0,this._alphaTest=0}get alphaTest(){return this._alphaTest}set alphaTest(e){this._alphaTest>0!=e>0&&this.version++,this._alphaTest=e}onBeforeRender(){}onBeforeCompile(){}customProgramCacheKey(){return this.onBeforeCompile.toString()}setValues(e){if(e!==void 0)for(const i in e){const s=e[i];if(s===void 0){ht(`Material: parameter '${i}' has value of undefined.`);continue}const l=this[i];if(l===void 0){ht(`Material: '${i}' is not a property of THREE.${this.type}.`);continue}l&&l.isColor?l.set(s):l&&l.isVector2&&s&&s.isVector2||l&&l.isEuler&&s&&s.isEuler||l&&l.isVector3&&s&&s.isVector3?l.copy(s):this[i]=s}}toJSON(e){const i=e===void 0||typeof e=="string";i&&(e={textures:{},images:{}});const s={metadata:{version:4.7,type:"Material",generator:"Material.toJSON"}};s.uuid=this.uuid,s.type=this.type,s.blending=this.blending,s.side=this.side,s.shadowSide=this.shadowSide,s.vertexColors=this.vertexColors,s.opacity=this.opacity,s.transparent=this.transparent,s.blendSrc=this.blendSrc,s.blendDst=this.blendDst,s.blendEquation=this.blendEquation,s.blendSrcAlpha=this.blendSrcAlpha,s.blendDstAlpha=this.blendDstAlpha,s.blendEquationAlpha=this.blendEquationAlpha,s.blendColor=this.blendColor.getHex(),s.blendAlpha=this.blendAlpha,s.depthFunc=this.depthFunc,s.depthTest=this.depthTest,s.depthWrite=this.depthWrite,s.colorWrite=this.colorWrite,s.clipIntersection=this.clipIntersection,s.clipShadows=this.clipShadows,s.stencilWriteMask=this.stencilWriteMask,s.stencilFunc=this.stencilFunc,s.stencilRef=this.stencilRef,s.stencilFuncMask=this.stencilFuncMask,s.stencilFail=this.stencilFail,s.stencilZFail=this.stencilZFail,s.stencilZPass=this.stencilZPass,s.stencilWrite=this.stencilWrite,s.polygonOffset=this.polygonOffset,s.polygonOffsetFactor=this.polygonOffsetFactor,s.polygonOffsetUnits=this.polygonOffsetUnits,s.dithering=this.dithering,s.alphaTest=this.alphaTest,s.alphaHash=this.alphaHash,s.alphaToCoverage=this.alphaToCoverage,s.premultipliedAlpha=this.premultipliedAlpha,s.forceSinglePass=this.forceSinglePass,s.allowOverride=this.allowOverride,s.visible=this.visible,s.toneMapped=this.toneMapped,s.name=this.name,this.color&&this.color.isColor&&(s.color=this.color.getHex()),this.roughness!==void 0&&(s.roughness=this.roughness),this.metalness!==void 0&&(s.metalness=this.metalness),this.sheen!==void 0&&(s.sheen=this.sheen),this.sheenColor&&this.sheenColor.isColor&&(s.sheenColor=this.sheenColor.getHex()),this.sheenRoughness!==void 0&&(s.sheenRoughness=this.sheenRoughness),this.emissive&&this.emissive.isColor&&(s.emissive=this.emissive.getHex()),this.emissiveIntensity!==void 0&&(s.emissiveIntensity=this.emissiveIntensity),this.specular&&this.specular.isColor&&(s.specular=this.specular.getHex()),this.specularIntensity!==void 0&&(s.specularIntensity=this.specularIntensity),this.specularColor&&this.specularColor.isColor&&(s.specularColor=this.specularColor.getHex()),this.shininess!==void 0&&(s.shininess=this.shininess),this.clearcoat!==void 0&&(s.clearcoat=this.clearcoat),this.clearcoatRoughness!==void 0&&(s.clearcoatRoughness=this.clearcoatRoughness),this.clearcoatMap&&this.clearcoatMap.isTexture&&(s.clearcoatMap=this.clearcoatMap.toJSON(e).uuid),this.clearcoatRoughnessMap&&this.clearcoatRoughnessMap.isTexture&&(s.clearcoatRoughnessMap=this.clearcoatRoughnessMap.toJSON(e).uuid),this.clearcoatNormalMap&&this.clearcoatNormalMap.isTexture&&(s.clearcoatNormalMap=this.clearcoatNormalMap.toJSON(e).uuid,s.clearcoatNormalScale=this.clearcoatNormalScale.toArray()),this.sheenColorMap&&this.sheenColorMap.isTexture&&(s.sheenColorMap=this.sheenColorMap.toJSON(e).uuid),this.sheenRoughnessMap&&this.sheenRoughnessMap.isTexture&&(s.sheenRoughnessMap=this.sheenRoughnessMap.toJSON(e).uuid),this.dispersion!==void 0&&(s.dispersion=this.dispersion),this.retroreflectivity!==void 0&&(s.retroreflectivity=this.retroreflectivity),this.iridescence!==void 0&&(s.iridescence=this.iridescence),this.iridescenceIOR!==void 0&&(s.iridescenceIOR=this.iridescenceIOR),this.iridescenceThicknessRange!==void 0&&(s.iridescenceThicknessRange=this.iridescenceThicknessRange),this.iridescenceMap&&this.iridescenceMap.isTexture&&(s.iridescenceMap=this.iridescenceMap.toJSON(e).uuid),this.iridescenceThicknessMap&&this.iridescenceThicknessMap.isTexture&&(s.iridescenceThicknessMap=this.iridescenceThicknessMap.toJSON(e).uuid),this.anisotropy!==void 0&&(s.anisotropy=this.anisotropy),this.anisotropyRotation!==void 0&&(s.anisotropyRotation=this.anisotropyRotation),this.anisotropyMap&&this.anisotropyMap.isTexture&&(s.anisotropyMap=this.anisotropyMap.toJSON(e).uuid),this.map&&this.map.isTexture&&(s.map=this.map.toJSON(e).uuid),this.matcap&&this.matcap.isTexture&&(s.matcap=this.matcap.toJSON(e).uuid),this.alphaMap&&this.alphaMap.isTexture&&(s.alphaMap=this.alphaMap.toJSON(e).uuid),this.lightMap&&this.lightMap.isTexture&&(s.lightMap=this.lightMap.toJSON(e).uuid,s.lightMapIntensity=this.lightMapIntensity),this.aoMap&&this.aoMap.isTexture&&(s.aoMap=this.aoMap.toJSON(e).uuid,s.aoMapIntensity=this.aoMapIntensity),this.bumpMap&&this.bumpMap.isTexture&&(s.bumpMap=this.bumpMap.toJSON(e).uuid,s.bumpScale=this.bumpScale),this.normalMap&&this.normalMap.isTexture&&(s.normalMap=this.normalMap.toJSON(e).uuid,s.normalMapType=this.normalMapType,s.normalScale=this.normalScale.toArray()),this.displacementMap&&this.displacementMap.isTexture&&(s.displacementMap=this.displacementMap.toJSON(e).uuid,s.displacementScale=this.displacementScale,s.displacementBias=this.displacementBias),this.roughnessMap&&this.roughnessMap.isTexture&&(s.roughnessMap=this.roughnessMap.toJSON(e).uuid),this.metalnessMap&&this.metalnessMap.isTexture&&(s.metalnessMap=this.metalnessMap.toJSON(e).uuid),this.emissiveMap&&this.emissiveMap.isTexture&&(s.emissiveMap=this.emissiveMap.toJSON(e).uuid),this.specularMap&&this.specularMap.isTexture&&(s.specularMap=this.specularMap.toJSON(e).uuid),this.specularIntensityMap&&this.specularIntensityMap.isTexture&&(s.specularIntensityMap=this.specularIntensityMap.toJSON(e).uuid),this.specularColorMap&&this.specularColorMap.isTexture&&(s.specularColorMap=this.specularColorMap.toJSON(e).uuid),this.envMap&&this.envMap.isTexture&&(s.envMap=this.envMap.toJSON(e).uuid,this.combine!==void 0&&(s.combine=this.combine)),this.envMapRotation!==void 0&&(s.envMapRotation=this.envMapRotation.toArray()),this.envMapIntensity!==void 0&&(s.envMapIntensity=this.envMapIntensity),this.reflectivity!==void 0&&(s.reflectivity=this.reflectivity),this.refractionRatio!==void 0&&(s.refractionRatio=this.refractionRatio),this.gradientMap&&this.gradientMap.isTexture&&(s.gradientMap=this.gradientMap.toJSON(e).uuid),this.transmission!==void 0&&(s.transmission=this.transmission),this.transmissionMap&&this.transmissionMap.isTexture&&(s.transmissionMap=this.transmissionMap.toJSON(e).uuid),this.thickness!==void 0&&(s.thickness=this.thickness),this.thicknessMap&&this.thicknessMap.isTexture&&(s.thicknessMap=this.thicknessMap.toJSON(e).uuid),this.attenuationDistance!==void 0&&(s.attenuationDistance=this.attenuationDistance),this.attenuationColor!==void 0&&(s.attenuationColor=this.attenuationColor.getHex()),this.size!==void 0&&(s.size=this.size),this.sizeAttenuation!==void 0&&(s.sizeAttenuation=this.sizeAttenuation),Array.isArray(this.clippingPlanes)&&this.clippingPlanes.length>0&&(s.clippingPlanes=this.clippingPlanes.map(c=>c.toJSON())),this.rotation!==void 0&&(s.rotation=this.rotation),this.depthPacking!==void 0&&(s.depthPacking=this.depthPacking),this.linewidth!==void 0&&(s.linewidth=this.linewidth),this.linecap!==void 0&&(s.linecap=this.linecap),this.linejoin!==void 0&&(s.linejoin=this.linejoin),this.dashSize!==void 0&&(s.dashSize=this.dashSize),this.gapSize!==void 0&&(s.gapSize=this.gapSize),this.scale!==void 0&&(s.scale=this.scale),this.wireframe!==void 0&&(s.wireframe=this.wireframe),this.wireframeLinewidth!==void 0&&(s.wireframeLinewidth=this.wireframeLinewidth),this.wireframeLinecap!==void 0&&(s.wireframeLinecap=this.wireframeLinecap),this.wireframeLinejoin!==void 0&&(s.wireframeLinejoin=this.wireframeLinejoin),this.flatShading!==void 0&&(s.flatShading=this.flatShading),this.fog!==void 0&&(s.fog=this.fog),Object.keys(this.userData).length>0&&(s.userData=this.userData);function l(c){const f=[];for(const h in c){const m=c[h];delete m.metadata,f.push(m)}return f}if(i){const c=l(e.textures),f=l(e.images);c.length>0&&(s.textures=c),f.length>0&&(s.images=f)}return s}fromJSON(e,i){if(e.uuid!==void 0&&(this.uuid=e.uuid),e.name!==void 0&&(this.name=e.name),e.color!==void 0&&this.color!==void 0&&this.color.setHex(e.color),e.roughness!==void 0&&(this.roughness=e.roughness),e.metalness!==void 0&&(this.metalness=e.metalness),e.sheen!==void 0&&(this.sheen=e.sheen),e.sheenColor!==void 0&&(this.sheenColor=new wt().setHex(e.sheenColor)),e.sheenRoughness!==void 0&&(this.sheenRoughness=e.sheenRoughness),e.emissive!==void 0&&this.emissive!==void 0&&this.emissive.setHex(e.emissive),e.specular!==void 0&&this.specular!==void 0&&this.specular.setHex(e.specular),e.specularIntensity!==void 0&&(this.specularIntensity=e.specularIntensity),e.specularColor!==void 0&&this.specularColor!==void 0&&this.specularColor.setHex(e.specularColor),e.shininess!==void 0&&(this.shininess=e.shininess),e.clearcoat!==void 0&&(this.clearcoat=e.clearcoat),e.clearcoatRoughness!==void 0&&(this.clearcoatRoughness=e.clearcoatRoughness),e.dispersion!==void 0&&(this.dispersion=e.dispersion),e.retroreflectivity!==void 0&&(this.retroreflectivity=e.retroreflectivity),e.iridescence!==void 0&&(this.iridescence=e.iridescence),e.iridescenceIOR!==void 0&&(this.iridescenceIOR=e.iridescenceIOR),e.iridescenceThicknessRange!==void 0&&(this.iridescenceThicknessRange=e.iridescenceThicknessRange),e.transmission!==void 0&&(this.transmission=e.transmission),e.thickness!==void 0&&(this.thickness=e.thickness),e.attenuationDistance!==void 0&&(this.attenuationDistance=e.attenuationDistance),e.attenuationColor!==void 0&&this.attenuationColor!==void 0&&this.attenuationColor.setHex(e.attenuationColor),e.anisotropy!==void 0&&(this.anisotropy=e.anisotropy),e.anisotropyRotation!==void 0&&(this.anisotropyRotation=e.anisotropyRotation),e.fog!==void 0&&(this.fog=e.fog),e.flatShading!==void 0&&(this.flatShading=e.flatShading),e.blending!==void 0&&(this.blending=e.blending),e.combine!==void 0&&(this.combine=e.combine),e.side!==void 0&&(this.side=e.side),e.shadowSide!==void 0&&(this.shadowSide=e.shadowSide),e.opacity!==void 0&&(this.opacity=e.opacity),e.transparent!==void 0&&(this.transparent=e.transparent),e.alphaTest!==void 0&&(this.alphaTest=e.alphaTest),e.alphaHash!==void 0&&(this.alphaHash=e.alphaHash),e.depthFunc!==void 0&&(this.depthFunc=e.depthFunc),e.depthTest!==void 0&&(this.depthTest=e.depthTest),e.depthWrite!==void 0&&(this.depthWrite=e.depthWrite),e.colorWrite!==void 0&&(this.colorWrite=e.colorWrite),e.clippingPlanes!==void 0&&(this.clippingPlanes=e.clippingPlanes.map(s=>new ts().fromJSON(s))),e.clipIntersection!==void 0&&(this.clipIntersection=e.clipIntersection),e.clipShadows!==void 0&&(this.clipShadows=e.clipShadows),e.depthPacking!==void 0&&(this.depthPacking=e.depthPacking),e.blendSrc!==void 0&&(this.blendSrc=e.blendSrc),e.blendDst!==void 0&&(this.blendDst=e.blendDst),e.blendEquation!==void 0&&(this.blendEquation=e.blendEquation),e.blendSrcAlpha!==void 0&&(this.blendSrcAlpha=e.blendSrcAlpha),e.blendDstAlpha!==void 0&&(this.blendDstAlpha=e.blendDstAlpha),e.blendEquationAlpha!==void 0&&(this.blendEquationAlpha=e.blendEquationAlpha),e.blendColor!==void 0&&this.blendColor!==void 0&&this.blendColor.setHex(e.blendColor),e.blendAlpha!==void 0&&(this.blendAlpha=e.blendAlpha),e.stencilWriteMask!==void 0&&(this.stencilWriteMask=e.stencilWriteMask),e.stencilFunc!==void 0&&(this.stencilFunc=e.stencilFunc),e.stencilRef!==void 0&&(this.stencilRef=e.stencilRef),e.stencilFuncMask!==void 0&&(this.stencilFuncMask=e.stencilFuncMask),e.stencilFail!==void 0&&(this.stencilFail=e.stencilFail),e.stencilZFail!==void 0&&(this.stencilZFail=e.stencilZFail),e.stencilZPass!==void 0&&(this.stencilZPass=e.stencilZPass),e.stencilWrite!==void 0&&(this.stencilWrite=e.stencilWrite),e.wireframe!==void 0&&(this.wireframe=e.wireframe),e.wireframeLinewidth!==void 0&&(this.wireframeLinewidth=e.wireframeLinewidth),e.wireframeLinecap!==void 0&&(this.wireframeLinecap=e.wireframeLinecap),e.wireframeLinejoin!==void 0&&(this.wireframeLinejoin=e.wireframeLinejoin),e.rotation!==void 0&&(this.rotation=e.rotation),e.linewidth!==void 0&&(this.linewidth=e.linewidth),e.linecap!==void 0&&(this.linecap=e.linecap),e.linejoin!==void 0&&(this.linejoin=e.linejoin),e.dashSize!==void 0&&(this.dashSize=e.dashSize),e.gapSize!==void 0&&(this.gapSize=e.gapSize),e.scale!==void 0&&(this.scale=e.scale),e.polygonOffset!==void 0&&(this.polygonOffset=e.polygonOffset),e.polygonOffsetFactor!==void 0&&(this.polygonOffsetFactor=e.polygonOffsetFactor),e.polygonOffsetUnits!==void 0&&(this.polygonOffsetUnits=e.polygonOffsetUnits),e.dithering!==void 0&&(this.dithering=e.dithering),e.alphaToCoverage!==void 0&&(this.alphaToCoverage=e.alphaToCoverage),e.premultipliedAlpha!==void 0&&(this.premultipliedAlpha=e.premultipliedAlpha),e.forceSinglePass!==void 0&&(this.forceSinglePass=e.forceSinglePass),e.allowOverride!==void 0&&(this.allowOverride=e.allowOverride),e.visible!==void 0&&(this.visible=e.visible),e.toneMapped!==void 0&&(this.toneMapped=e.toneMapped),e.userData!==void 0&&(this.userData=e.userData),e.vertexColors!==void 0&&(typeof e.vertexColors=="number"?this.vertexColors=e.vertexColors>0:this.vertexColors=e.vertexColors),e.size!==void 0&&(this.size=e.size),e.sizeAttenuation!==void 0&&(this.sizeAttenuation=e.sizeAttenuation),e.map!==void 0&&(this.map=i[e.map]||null),e.matcap!==void 0&&(this.matcap=i[e.matcap]||null),e.alphaMap!==void 0&&(this.alphaMap=i[e.alphaMap]||null),e.bumpMap!==void 0&&(this.bumpMap=i[e.bumpMap]||null),e.bumpScale!==void 0&&(this.bumpScale=e.bumpScale),e.normalMap!==void 0&&(this.normalMap=i[e.normalMap]||null),e.normalMapType!==void 0&&(this.normalMapType=e.normalMapType),e.normalScale!==void 0){let s=e.normalScale;Array.isArray(s)===!1&&(s=[s,s]),this.normalScale=new Kt().fromArray(s)}return e.displacementMap!==void 0&&(this.displacementMap=i[e.displacementMap]||null),e.displacementScale!==void 0&&(this.displacementScale=e.displacementScale),e.displacementBias!==void 0&&(this.displacementBias=e.displacementBias),e.roughnessMap!==void 0&&(this.roughnessMap=i[e.roughnessMap]||null),e.metalnessMap!==void 0&&(this.metalnessMap=i[e.metalnessMap]||null),e.emissiveMap!==void 0&&(this.emissiveMap=i[e.emissiveMap]||null),e.emissiveIntensity!==void 0&&(this.emissiveIntensity=e.emissiveIntensity),e.specularMap!==void 0&&(this.specularMap=i[e.specularMap]||null),e.specularIntensityMap!==void 0&&(this.specularIntensityMap=i[e.specularIntensityMap]||null),e.specularColorMap!==void 0&&(this.specularColorMap=i[e.specularColorMap]||null),e.envMap!==void 0&&(this.envMap=i[e.envMap]||null),e.envMapRotation!==void 0&&this.envMapRotation.fromArray(e.envMapRotation),e.envMapIntensity!==void 0&&(this.envMapIntensity=e.envMapIntensity),e.reflectivity!==void 0&&(this.reflectivity=e.reflectivity),e.refractionRatio!==void 0&&(this.refractionRatio=e.refractionRatio),e.lightMap!==void 0&&(this.lightMap=i[e.lightMap]||null),e.lightMapIntensity!==void 0&&(this.lightMapIntensity=e.lightMapIntensity),e.aoMap!==void 0&&(this.aoMap=i[e.aoMap]||null),e.aoMapIntensity!==void 0&&(this.aoMapIntensity=e.aoMapIntensity),e.gradientMap!==void 0&&(this.gradientMap=i[e.gradientMap]||null),e.clearcoatMap!==void 0&&(this.clearcoatMap=i[e.clearcoatMap]||null),e.clearcoatRoughnessMap!==void 0&&(this.clearcoatRoughnessMap=i[e.clearcoatRoughnessMap]||null),e.clearcoatNormalMap!==void 0&&(this.clearcoatNormalMap=i[e.clearcoatNormalMap]||null),e.clearcoatNormalScale!==void 0&&(this.clearcoatNormalScale=new Kt().fromArray(e.clearcoatNormalScale)),e.iridescenceMap!==void 0&&(this.iridescenceMap=i[e.iridescenceMap]||null),e.iridescenceThicknessMap!==void 0&&(this.iridescenceThicknessMap=i[e.iridescenceThicknessMap]||null),e.transmissionMap!==void 0&&(this.transmissionMap=i[e.transmissionMap]||null),e.thicknessMap!==void 0&&(this.thicknessMap=i[e.thicknessMap]||null),e.anisotropyMap!==void 0&&(this.anisotropyMap=i[e.anisotropyMap]||null),e.sheenColorMap!==void 0&&(this.sheenColorMap=i[e.sheenColorMap]||null),e.sheenRoughnessMap!==void 0&&(this.sheenRoughnessMap=i[e.sheenRoughnessMap]||null),this}clone(){return new this.constructor().copy(this)}copy(e){this.name=e.name,this.blending=e.blending,this.side=e.side,this.vertexColors=e.vertexColors,this.opacity=e.opacity,this.transparent=e.transparent,this.blendSrc=e.blendSrc,this.blendDst=e.blendDst,this.blendEquation=e.blendEquation,this.blendSrcAlpha=e.blendSrcAlpha,this.blendDstAlpha=e.blendDstAlpha,this.blendEquationAlpha=e.blendEquationAlpha,this.blendColor.copy(e.blendColor),this.blendAlpha=e.blendAlpha,this.depthFunc=e.depthFunc,this.depthTest=e.depthTest,this.depthWrite=e.depthWrite,this.stencilWriteMask=e.stencilWriteMask,this.stencilFunc=e.stencilFunc,this.stencilRef=e.stencilRef,this.stencilFuncMask=e.stencilFuncMask,this.stencilFail=e.stencilFail,this.stencilZFail=e.stencilZFail,this.stencilZPass=e.stencilZPass,this.stencilWrite=e.stencilWrite;const i=e.clippingPlanes;let s=null;if(i!==null){const l=i.length;s=new Array(l);for(let c=0;c!==l;++c)s[c]=i[c].clone()}return this.clippingPlanes=s,this.clipIntersection=e.clipIntersection,this.clipShadows=e.clipShadows,this.shadowSide=e.shadowSide,this.colorWrite=e.colorWrite,this.precision=e.precision,this.polygonOffset=e.polygonOffset,this.polygonOffsetFactor=e.polygonOffsetFactor,this.polygonOffsetUnits=e.polygonOffsetUnits,this.dithering=e.dithering,this.alphaTest=e.alphaTest,this.alphaHash=e.alphaHash,this.alphaToCoverage=e.alphaToCoverage,this.premultipliedAlpha=e.premultipliedAlpha,this.forceSinglePass=e.forceSinglePass,this.allowOverride=e.allowOverride,this.visible=e.visible,this.toneMapped=e.toneMapped,this.userData=JSON.parse(JSON.stringify(e.userData)),this}dispose(){this.dispatchEvent({type:"dispose"})}set needsUpdate(e){e===!0&&this.version++}}const mr=new Q,Ch=new Q,du=new Q,hu=new Q;class Qu{constructor(e=new Q,i=new Q(0,0,-1)){this.origin=e,this.direction=i}set(e,i){return this.origin.copy(e),this.direction.copy(i),this}copy(e){return this.origin.copy(e.origin),this.direction.copy(e.direction),this}at(e,i){return i.copy(this.origin).addScaledVector(this.direction,e)}lookAt(e){return this.direction.copy(e).sub(this.origin).normalize(),this}recast(e){return this.origin.copy(this.at(e,mr)),this}closestPointToPoint(e,i){i.subVectors(e,this.origin);const s=i.dot(this.direction);return s<0?i.copy(this.origin):i.copy(this.origin).addScaledVector(this.direction,s)}distanceToPoint(e){return Math.sqrt(this.distanceSqToPoint(e))}distanceSqToPoint(e){const i=mr.subVectors(e,this.origin).dot(this.direction);return i<0?this.origin.distanceToSquared(e):(mr.copy(this.origin).addScaledVector(this.direction,i),mr.distanceToSquared(e))}distanceSqToSegment(e,i,s,l){Ch.copy(e).add(i).multiplyScalar(.5),du.copy(i).sub(e).normalize(),hu.copy(this.origin).sub(Ch);const c=e.distanceTo(i)*.5,f=-this.direction.dot(du),h=hu.dot(this.direction),m=-hu.dot(du),p=hu.lengthSq(),g=Math.abs(1-f*f);let v,x,_,E;if(g>0)if(v=f*m-h,x=f*h-m,E=c*g,v>=0)if(x>=-E)if(x<=E){const R=1/g;v*=R,x*=R,_=v*(v+f*x+2*h)+x*(f*v+x+2*m)+p}else x=c,v=Math.max(0,-(f*x+h)),_=-v*v+x*(x+2*m)+p;else x=-c,v=Math.max(0,-(f*x+h)),_=-v*v+x*(x+2*m)+p;else x<=-E?(v=Math.max(0,-(-f*c+h)),x=v>0?-c:Math.min(Math.max(-c,-m),c),_=-v*v+x*(x+2*m)+p):x<=E?(v=0,x=Math.min(Math.max(-c,-m),c),_=x*(x+2*m)+p):(v=Math.max(0,-(f*c+h)),x=v>0?c:Math.min(Math.max(-c,-m),c),_=-v*v+x*(x+2*m)+p);else x=f>0?-c:c,v=Math.max(0,-(f*x+h)),_=-v*v+x*(x+2*m)+p;return s&&s.copy(this.origin).addScaledVector(this.direction,v),l&&l.copy(Ch).addScaledVector(du,x),_}intersectSphere(e,i){if(e.radius<0)return null;mr.subVectors(e.center,this.origin);const s=mr.dot(this.direction),l=mr.dot(mr)-s*s,c=e.radius*e.radius;if(l>c)return null;const f=Math.sqrt(c-l),h=s-f,m=s+f;return m<0?null:h<0?this.at(m,i):this.at(h,i)}intersectsSphere(e){return e.radius<0?!1:this.distanceSqToPoint(e.center)<=e.radius*e.radius}distanceToPlane(e){const i=e.normal.dot(this.direction);if(i===0)return e.distanceToPoint(this.origin)===0?0:null;const s=-(this.origin.dot(e.normal)+e.constant)/i;return s>=0?s:null}intersectPlane(e,i){const s=this.distanceToPlane(e);return s===null?null:this.at(s,i)}intersectsPlane(e){const i=e.distanceToPoint(this.origin);return i===0||e.normal.dot(this.direction)*i<0}intersectBox(e,i){let s,l,c,f,h,m;const p=1/this.direction.x,g=1/this.direction.y,v=1/this.direction.z,x=this.origin;return p>=0?(s=(e.min.x-x.x)*p,l=(e.max.x-x.x)*p):(s=(e.max.x-x.x)*p,l=(e.min.x-x.x)*p),g>=0?(c=(e.min.y-x.y)*g,f=(e.max.y-x.y)*g):(c=(e.max.y-x.y)*g,f=(e.min.y-x.y)*g),s>f||c>l||((c>s||isNaN(s))&&(s=c),(f<l||isNaN(l))&&(l=f),v>=0?(h=(e.min.z-x.z)*v,m=(e.max.z-x.z)*v):(h=(e.max.z-x.z)*v,m=(e.min.z-x.z)*v),s>m||h>l)||((h>s||s!==s)&&(s=h),(m<l||l!==l)&&(l=m),l<0)?null:this.at(s>=0?s:l,i)}intersectsBox(e){return this.intersectBox(e,mr)!==null}intersectTriangle(e,i,s,l,c){const f=this.origin,h=this.direction,m=h.x,p=h.y,g=h.z,v=e.x-f.x,x=e.y-f.y,_=e.z-f.z,E=i.x-f.x,R=i.y-f.y,b=i.z-f.z,S=s.x-f.x,F=s.y-f.y,G=s.z-f.z,w=Math.abs(m),N=Math.abs(p),L=Math.abs(g);let z,T,O,I,W,J,re,k,K,B,V,ee;if(w>=N&&w>=L?(O=m,J=v,K=E,ee=S,m>=0?(z=p,T=g,I=x,W=_,re=R,k=b,B=F,V=G):(z=g,T=p,I=_,W=x,re=b,k=R,B=G,V=F)):N>=L?(O=p,J=x,K=R,ee=F,p>=0?(z=g,T=m,I=_,W=v,re=b,k=E,B=G,V=S):(z=m,T=g,I=v,W=_,re=E,k=b,B=S,V=G)):(O=g,J=_,K=b,ee=G,g>=0?(z=m,T=p,I=v,W=x,re=E,k=R,B=S,V=F):(z=p,T=m,I=x,W=v,re=R,k=E,B=F,V=S)),O===0)return null;const oe=z/O,fe=T/O,D=1/O,se=I-oe*J,_e=W-fe*J,De=re-oe*K,ze=k-fe*K,Xe=B-oe*ee,ue=V-fe*ee,Se=Xe*ze-ue*De,Re=se*ue-_e*Xe,at=De*_e-ze*se;if(l){if(Se<0||Re<0||at<0)return null}else if((Se<0||Re<0||at<0)&&(Se>0||Re>0||at>0))return null;const Ge=Se+Re+at;if(Ge===0)return null;const mt=D*(Se*J+Re*K+at*ee);return(Ge>0?mt<0:mt>0)?null:this.at(mt/Ge,c)}applyMatrix4(e){return this.origin.applyMatrix4(e),this.direction.transformDirection(e),this}equals(e){return e.origin.equals(this.origin)&&e.direction.equals(this.direction)}clone(){return new this.constructor().copy(this)}}class Ju extends ko{constructor(e){super(),this.isMeshBasicMaterial=!0,this.type="MeshBasicMaterial",this.color=new wt(16777215),this.map=null,this.lightMap=null,this.lightMapIntensity=1,this.aoMap=null,this.aoMapIntensity=1,this.specularMap=null,this.alphaMap=null,this.envMap=null,this.envMapRotation=new zs,this.combine=h_,this.reflectivity=1,this.refractionRatio=.98,this.wireframe=!1,this.wireframeLinewidth=1,this.wireframeLinecap="round",this.wireframeLinejoin="round",this.fog=!0,this.setValues(e)}copy(e){return super.copy(e),this.color.copy(e.color),this.map=e.map,this.lightMap=e.lightMap,this.lightMapIntensity=e.lightMapIntensity,this.aoMap=e.aoMap,this.aoMapIntensity=e.aoMapIntensity,this.specularMap=e.specularMap,this.alphaMap=e.alphaMap,this.envMap=e.envMap,this.envMapRotation.copy(e.envMapRotation),this.combine=e.combine,this.reflectivity=e.reflectivity,this.refractionRatio=e.refractionRatio,this.wireframe=e.wireframe,this.wireframeLinewidth=e.wireframeLinewidth,this.wireframeLinecap=e.wireframeLinecap,this.wireframeLinejoin=e.wireframeLinejoin,this.fog=e.fog,this}}const dv=new En,As=new Qu,pu=new Bs,hv=new Q,mu=new Q,gu=new Q,xu=new Q,Rh=new Q,vu=new Q,pv=new Q,_u=new Q;class ji extends Ti{constructor(e=new Bn,i=new Ju){super(),this.isMesh=!0,this.type="Mesh",this.geometry=e,this.material=i,this.morphTargetDictionary=void 0,this.morphTargetInfluences=void 0,this.count=1,this.updateMorphTargets()}copy(e,i){return super.copy(e,i),e.morphTargetInfluences!==void 0&&(this.morphTargetInfluences=e.morphTargetInfluences.slice()),e.morphTargetDictionary!==void 0&&(this.morphTargetDictionary=Object.assign({},e.morphTargetDictionary)),this.material=Array.isArray(e.material)?e.material.slice():e.material,this.geometry=e.geometry,this}updateMorphTargets(){const i=this.geometry.morphAttributes,s=Object.keys(i);if(s.length>0){const l=i[s[0]];if(l!==void 0){this.morphTargetInfluences=[],this.morphTargetDictionary={};for(let c=0,f=l.length;c<f;c++){const h=l[c].name||String(c);this.morphTargetInfluences.push(0),this.morphTargetDictionary[h]=c}}}}getVertexPosition(e,i){const s=this.geometry,l=s.attributes.position,c=s.morphAttributes.position,f=s.morphTargetsRelative;i.fromBufferAttribute(l,e);const h=this.morphTargetInfluences;if(c&&h){vu.set(0,0,0);for(let m=0,p=c.length;m<p;m++){const g=h[m],v=c[m];g!==0&&(Rh.fromBufferAttribute(v,e),f?vu.addScaledVector(Rh,g):vu.addScaledVector(Rh.sub(i),g))}i.add(vu)}return i}intersectsFrustum(e){return e.intersectsObject(this)}raycast(e,i){const s=this.geometry,l=this.material,c=this.matrixWorld;l!==void 0&&(s.boundingSphere===null&&s.computeBoundingSphere(),pu.copy(s.boundingSphere),pu.applyMatrix4(c),As.copy(e.ray).recast(e.near),!(pu.containsPoint(As.origin)===!1&&(As.intersectSphere(pu,hv)===null||As.origin.distanceToSquared(hv)>(e.far-e.near)**2))&&(dv.copy(c).invert(),As.copy(e.ray).applyMatrix4(dv),!(s.boundingBox!==null&&As.intersectsBox(s.boundingBox)===!1)&&this._computeIntersections(e,i,As)))}_computeIntersections(e,i,s){let l;const c=this.geometry,f=this.material,h=c.index,m=c.attributes.position,p=c.attributes.uv,g=c.attributes.uv1,v=c.attributes.normal,x=c.groups,_=c.drawRange;if(h!==null)if(Array.isArray(f))for(let E=0,R=x.length;E<R;E++){const b=x[E],S=f[b.materialIndex],F=Math.max(b.start,_.start),G=Math.min(h.count,Math.min(b.start+b.count,_.start+_.count));for(let w=F,N=G;w<N;w+=3){const L=h.getX(w),z=h.getX(w+1),T=h.getX(w+2);l=yu(this,S,e,s,p,g,v,L,z,T),l&&(l.faceIndex=Math.floor(w/3),l.face.materialIndex=b.materialIndex,i.push(l))}}else{const E=Math.max(0,_.start),R=Math.min(h.count,_.start+_.count);for(let b=E,S=R;b<S;b+=3){const F=h.getX(b),G=h.getX(b+1),w=h.getX(b+2);l=yu(this,f,e,s,p,g,v,F,G,w),l&&(l.faceIndex=Math.floor(b/3),i.push(l))}}else if(m!==void 0)if(Array.isArray(f))for(let E=0,R=x.length;E<R;E++){const b=x[E],S=f[b.materialIndex],F=Math.max(b.start,_.start),G=Math.min(m.count,Math.min(b.start+b.count,_.start+_.count));for(let w=F,N=G;w<N;w+=3){const L=w,z=w+1,T=w+2;l=yu(this,S,e,s,p,g,v,L,z,T),l&&(l.faceIndex=Math.floor(w/3),l.face.materialIndex=b.materialIndex,i.push(l))}}else{const E=Math.max(0,_.start),R=Math.min(m.count,_.start+_.count);for(let b=E,S=R;b<S;b+=3){const F=b,G=b+1,w=b+2;l=yu(this,f,e,s,p,g,v,F,G,w),l&&(l.faceIndex=Math.floor(b/3),i.push(l))}}}}function aM(r,e,i,s,l,c,f,h){let m;if(e.side===Oi?m=s.intersectTriangle(f,c,l,!0,h):m=s.intersectTriangle(l,c,f,e.side===Ls,h),m===null)return null;_u.copy(h),_u.applyMatrix4(r.matrixWorld);const p=i.ray.origin.distanceTo(_u);return p<i.near||p>i.far?null:{distance:p,point:_u.clone(),object:r}}function yu(r,e,i,s,l,c,f,h,m,p){r.getVertexPosition(h,mu),r.getVertexPosition(m,gu),r.getVertexPosition(p,xu);const g=aM(r,e,i,s,mu,gu,xu,pv);if(g){const v=new Q;Ea.getBarycoord(pv,mu,gu,xu,v),l&&(g.uv=Ea.getInterpolatedAttribute(l,h,m,p,v,new Kt)),c&&(g.uv1=Ea.getInterpolatedAttribute(c,h,m,p,v,new Kt)),f&&(g.normal=Ea.getInterpolatedAttribute(f,h,m,p,v,new Q),g.normal.dot(s.direction)>0&&g.normal.multiplyScalar(-1));const x={a:h,b:m,c:p,normal:new Q,materialIndex:0};Ea.getNormal(mu,gu,xu,x.normal),g.face=x,g.barycoord=v}return g}class rM extends gi{constructor(e=null,i=1,s=1,l,c,f,h,m,p=li,g=li,v,x){super(null,f,h,m,p,g,l,c,v,x),this.isDataTexture=!0,this.image={data:e,width:i,height:s},this.generateMipmaps=!1,this.flipY=!1,this.unpackAlignment=1}}const ws=new Bs,sM=new Kt(.5,.5),Su=new Q;class P_{constructor(e=new ts,i=new ts,s=new ts,l=new ts,c=new ts,f=new ts){this.planes=[e,i,s,l,c,f]}set(e,i,s,l,c,f){const h=this.planes;return h[0].copy(e),h[1].copy(i),h[2].copy(s),h[3].copy(l),h[4].copy(c),h[5].copy(f),this}copy(e){const i=this.planes;for(let s=0;s<6;s++)i[s].copy(e.planes[s]);return this}setFromProjectionMatrix(e,i=Va,s=!1){const l=this.planes,c=e.elements,f=c[0],h=c[1],m=c[2],p=c[3],g=c[4],v=c[5],x=c[6],_=c[7],E=c[8],R=c[9],b=c[10],S=c[11],F=c[12],G=c[13],w=c[14],N=c[15];if(l[0].setComponents(p-f,_-g,S-E,N-F).normalize(),l[1].setComponents(p+f,_+g,S+E,N+F).normalize(),l[2].setComponents(p+h,_+v,S+R,N+G).normalize(),l[3].setComponents(p-h,_-v,S-R,N-G).normalize(),s)l[4].setComponents(m,x,b,w).normalize(),l[5].setComponents(p-m,_-x,S-b,N-w).normalize();else if(l[4].setComponents(p-m,_-x,S-b,N-w).normalize(),i===Va)l[5].setComponents(p+m,_+x,S+b,N+w).normalize();else if(i===Wu)l[5].setComponents(m,x,b,w).normalize();else throw new Error("THREE.Frustum.setFromProjectionMatrix(): Invalid coordinate system: "+i);return this}intersectsObject(e){if(e.boundingSphere!==void 0)e.boundingSphere===null&&e.computeBoundingSphere(),ws.copy(e.boundingSphere).applyMatrix4(e.matrixWorld);else{const i=e.geometry;i.boundingSphere===null&&i.computeBoundingSphere(),ws.copy(i.boundingSphere).applyMatrix4(e.matrixWorld)}return this.intersectsSphere(ws)}intersectsSprite(e){ws.center.set(0,0,0);const i=sM.distanceTo(e.center);return ws.radius=.7071067811865476+i,ws.applyMatrix4(e.matrixWorld),this.intersectsSphere(ws)}intersectsSphere(e){const i=this.planes,s=e.center,l=-e.radius;for(let c=0;c<6;c++)if(i[c].distanceToPoint(s)<l)return!1;return!0}intersectsBox(e){const i=this.planes;for(let s=0;s<6;s++){const l=i[s];if(Su.x=l.normal.x>0?e.max.x:e.min.x,Su.y=l.normal.y>0?e.max.y:e.min.y,Su.z=l.normal.z>0?e.max.z:e.min.z,l.distanceToPoint(Su)<0)return!1}return!0}containsPoint(e){const i=this.planes;for(let s=0;s<6;s++)if(i[s].distanceToPoint(e)<0)return!1;return!0}clone(){return new this.constructor().copy(this)}}class Zp extends ko{constructor(e){super(),this.isLineBasicMaterial=!0,this.type="LineBasicMaterial",this.color=new wt(16777215),this.map=null,this.linewidth=1,this.linecap="round",this.linejoin="round",this.fog=!0,this.setValues(e)}copy(e){return super.copy(e),this.color.copy(e.color),this.map=e.map,this.linewidth=e.linewidth,this.linecap=e.linecap,this.linejoin=e.linejoin,this.fog=e.fog,this}}const qu=new Q,Yu=new Q,mv=new En,Pl=new Qu,bu=new Bs,Uh=new Q,gv=new Q;class Kp extends Ti{constructor(e=new Bn,i=new Zp){super(),this.isLine=!0,this.type="Line",this.geometry=e,this.material=i,this.morphTargetDictionary=void 0,this.morphTargetInfluences=void 0,this.updateMorphTargets()}copy(e,i){return super.copy(e,i),this.material=Array.isArray(e.material)?e.material.slice():e.material,this.geometry=e.geometry,this}computeLineDistances(){const e=this.geometry;if(e.index===null){const i=e.attributes.position,s=[0];for(let l=1,c=i.count;l<c;l++)qu.fromBufferAttribute(i,l-1),Yu.fromBufferAttribute(i,l),s[l]=s[l-1],s[l]+=qu.distanceTo(Yu);e.setAttribute("lineDistance",new Cn(s,1))}else ht("Line.computeLineDistances(): Computation only possible with non-indexed BufferGeometry.");return this}intersectsFrustum(e){return e.intersectsObject(this)}raycast(e,i){const s=this.geometry,l=this.matrixWorld,c=e.params.Line.threshold,f=s.drawRange;if(s.boundingSphere===null&&s.computeBoundingSphere(),bu.copy(s.boundingSphere),bu.applyMatrix4(l),bu.radius+=c,e.ray.intersectsSphere(bu)===!1)return;mv.copy(l).invert(),Pl.copy(e.ray).applyMatrix4(mv);const h=c/((this.scale.x+this.scale.y+this.scale.z)/3),m=h*h,p=this.isLineSegments?2:1,g=s.index,x=s.attributes.position;if(g!==null){const _=Math.max(0,f.start),E=Math.min(g.count,f.start+f.count);for(let R=_,b=E-1;R<b;R+=p){const S=g.getX(R),F=g.getX(R+1),G=Mu(this,e,Pl,m,S,F,R);G&&i.push(G)}if(this.isLineLoop){const R=g.getX(E-1),b=g.getX(_),S=Mu(this,e,Pl,m,R,b,E-1);S&&i.push(S)}}else{const _=Math.max(0,f.start),E=Math.min(x.count,f.start+f.count);for(let R=_,b=E-1;R<b;R+=p){const S=Mu(this,e,Pl,m,R,R+1,R);S&&i.push(S)}if(this.isLineLoop){const R=Mu(this,e,Pl,m,E-1,_,E-1);R&&i.push(R)}}}updateMorphTargets(){const i=this.geometry.morphAttributes,s=Object.keys(i);if(s.length>0){const l=i[s[0]];if(l!==void 0){this.morphTargetInfluences=[],this.morphTargetDictionary={};for(let c=0,f=l.length;c<f;c++){const h=l[c].name||String(c);this.morphTargetInfluences.push(0),this.morphTargetDictionary[h]=c}}}}}function Mu(r,e,i,s,l,c,f){const h=r.geometry.attributes.position;if(qu.fromBufferAttribute(h,l),Yu.fromBufferAttribute(h,c),i.distanceSqToSegment(qu,Yu,Uh,gv)>s)return;Uh.applyMatrix4(r.matrixWorld);const p=e.ray.origin.distanceTo(Uh);if(!(p<e.near||p>e.far))return{distance:p,point:gv.clone().applyMatrix4(r.matrixWorld),index:f,face:null,faceIndex:null,barycoord:null,object:r}}const xv=new Q,vv=new Q;class oM extends Kp{constructor(e,i){super(e,i),this.isLineSegments=!0,this.type="LineSegments"}computeLineDistances(){const e=this.geometry;if(e.index===null){const i=e.attributes.position,s=[];for(let l=0,c=i.count;l<c;l+=2)xv.fromBufferAttribute(i,l),vv.fromBufferAttribute(i,l+1),s[l]=l===0?0:s[l-1],s[l+1]=s[l]+xv.distanceTo(vv);e.setAttribute("lineDistance",new Cn(s,1))}else ht("LineSegments.computeLineDistances(): Computation only possible with non-indexed BufferGeometry.");return this}}class lM extends ko{constructor(e){super(),this.isPointsMaterial=!0,this.type="PointsMaterial",this.color=new wt(16777215),this.map=null,this.alphaMap=null,this.size=1,this.sizeAttenuation=!0,this.fog=!0,this.setValues(e)}copy(e){return super.copy(e),this.color.copy(e.color),this.map=e.map,this.alphaMap=e.alphaMap,this.size=e.size,this.sizeAttenuation=e.sizeAttenuation,this.fog=e.fog,this}}const _v=new En,Rp=new Qu,Eu=new Bs,Tu=new Q;class Ds extends Ti{constructor(e=new Bn,i=new lM){super(),this.isPoints=!0,this.type="Points",this.geometry=e,this.material=i,this.morphTargetDictionary=void 0,this.morphTargetInfluences=void 0,this.updateMorphTargets()}copy(e,i){return super.copy(e,i),this.material=Array.isArray(e.material)?e.material.slice():e.material,this.geometry=e.geometry,this}intersectsFrustum(e){return e.intersectsObject(this)}raycast(e,i){const s=this.geometry,l=this.matrixWorld,c=e.params.Points.threshold,f=s.drawRange;if(s.boundingSphere===null&&s.computeBoundingSphere(),Eu.copy(s.boundingSphere),Eu.applyMatrix4(l),Eu.radius+=c,e.ray.intersectsSphere(Eu)===!1)return;_v.copy(l).invert(),Rp.copy(e.ray).applyMatrix4(_v);const h=c/((this.scale.x+this.scale.y+this.scale.z)/3),m=h*h,p=s.index,v=s.attributes.position;if(p!==null){const x=Math.max(0,f.start),_=Math.min(p.count,f.start+f.count);for(let E=x,R=_;E<R;E++){const b=p.getX(E);Tu.fromBufferAttribute(v,b),yv(Tu,b,m,l,e,i,this)}}else{const x=Math.max(0,f.start),_=Math.min(v.count,f.start+f.count);for(let E=x,R=_;E<R;E++)Tu.fromBufferAttribute(v,E),yv(Tu,E,m,l,e,i,this)}}updateMorphTargets(){const i=this.geometry.morphAttributes,s=Object.keys(i);if(s.length>0){const l=i[s[0]];if(l!==void 0){this.morphTargetInfluences=[],this.morphTargetDictionary={};for(let c=0,f=l.length;c<f;c++){const h=l[c].name||String(c);this.morphTargetInfluences.push(0),this.morphTargetDictionary[h]=c}}}}}function yv(r,e,i,s,l,c,f){const h=Rp.distanceSqToPoint(r);if(h<i){const m=new Q;Rp.closestPointToPoint(r,m),m.applyMatrix4(s);const p=l.ray.origin.distanceTo(m);if(p<l.near||p>l.far)return;c.push({distance:p,distanceToRay:Math.sqrt(h),point:m,index:e,face:null,faceIndex:null,barycoord:null,object:f})}}class z_ extends gi{constructor(e=[],i=Os,s,l,c,f,h,m,p,g){super(e,i,s,l,c,f,h,m,p,g),this.isCubeTexture=!0,this.flipY=!1}get images(){return this.image}set images(e){this.image=e}}class Ql extends gi{constructor(e,i,s=Xa,l,c,f,h=li,m=li,p,g=Mr,v=1){if(g!==Mr&&g!==Us)throw new Error("THREE.DepthTexture: format must be either THREE.DepthFormat or THREE.DepthStencilFormat");const x={width:e,height:i,depth:v};super(x,l,c,f,h,m,g,s,p),this.isDepthTexture=!0,this.flipY=!1,this.generateMipmaps=!1,this.compareFunction=null}copy(e){return super.copy(e),this.source=new Yp(Object.assign({},e.image)),this.compareFunction=e.compareFunction,this}toJSON(e){const i=super.toJSON(e);return i.compareFunction=this.compareFunction,i}}class cM extends Ql{constructor(e,i=Xa,s=Os,l,c,f=li,h=li,m,p=Mr){const g={width:e,height:e,depth:1},v=[g,g,g,g,g,g];super(e,e,i,s,l,c,f,h,m,p),this.image=v,this.isCubeDepthTexture=!0,this.isCubeTexture=!0}get images(){return this.image}set images(e){this.image=e}}class F_ extends gi{constructor(e=null){super(),this.sourceTexture=e,this.isExternalTexture=!0}copy(e){return super.copy(e),this.sourceTexture=e.sourceTexture,this}}class $l extends Bn{constructor(e=1,i=1,s=1,l=1,c=1,f=1){super(),this.type="BoxGeometry",this.parameters={width:e,height:i,depth:s,widthSegments:l,heightSegments:c,depthSegments:f};const h=this;l=Math.floor(l),c=Math.floor(c),f=Math.floor(f);const m=[],p=[],g=[],v=[];let x=0,_=0;E("z","y","x",-1,-1,s,i,e,f,c,0),E("z","y","x",1,-1,s,i,-e,f,c,1),E("x","z","y",1,1,e,s,i,l,f,2),E("x","z","y",1,-1,e,s,-i,l,f,3),E("x","y","z",1,-1,e,i,s,l,c,4),E("x","y","z",-1,-1,e,i,-s,l,c,5),this.setIndex(m),this.setAttribute("position",new Cn(p,3)),this.setAttribute("normal",new Cn(g,3)),this.setAttribute("uv",new Cn(v,2));function E(R,b,S,F,G,w,N,L,z,T,O){const I=w/z,W=N/T,J=w/2,re=N/2,k=L/2,K=z+1,B=T+1;let V=0,ee=0;const oe=new Q;for(let fe=0;fe<B;fe++){const D=fe*W-re;for(let se=0;se<K;se++){const _e=se*I-J;oe[R]=_e*F,oe[b]=D*G,oe[S]=k,p.push(oe.x,oe.y,oe.z),oe[R]=0,oe[b]=0,oe[S]=L>0?1:-1,g.push(oe.x,oe.y,oe.z),v.push(se/z),v.push(1-fe/T),V+=1}}for(let fe=0;fe<T;fe++)for(let D=0;D<z;D++){const se=x+D+K*fe,_e=x+D+K*(fe+1),De=x+(D+1)+K*(fe+1),ze=x+(D+1)+K*fe;m.push(se,_e,ze),m.push(_e,De,ze),ee+=6}h.addGroup(_,ee,O),_+=ee,x+=V}}copy(e){return super.copy(e),this.parameters=Object.assign({},e.parameters),this}static fromJSON(e){return new $l(e.width,e.height,e.depth,e.widthSegments,e.heightSegments,e.depthSegments)}}class B_{constructor(){this.type="Curve",this.arcLengthDivisions=200,this.needsUpdate=!1,this.cacheArcLengths=null}getPoint(){ht("Curve: .getPoint() not implemented.")}getPointAt(e,i){const s=this.getUtoTmapping(e);return this.getPoint(s,i)}getPoints(e=5){const i=[];for(let s=0;s<=e;s++)i.push(this.getPoint(s/e));return i}getSpacedPoints(e=5){const i=[];for(let s=0;s<=e;s++)i.push(this.getPointAt(s/e));return i}getLength(){const e=this.getLengths();return e[e.length-1]}getLengths(e=this.arcLengthDivisions){if(this.cacheArcLengths&&this.cacheArcLengths.length===e+1&&!this.needsUpdate)return this.cacheArcLengths;this.needsUpdate=!1;const i=[];let s,l=this.getPoint(0),c=0;i.push(0);for(let f=1;f<=e;f++)s=this.getPoint(f/e),c+=s.distanceTo(l),i.push(c),l=s;return this.cacheArcLengths=i,i}updateArcLengths(){this.needsUpdate=!0,this.getLengths()}getUtoTmapping(e,i=null){const s=this.getLengths();let l=0;const c=s.length;let f;i?f=i:f=e*s[c-1];let h=0,m=c-1,p;for(;h<=m;)if(l=Math.floor(h+(m-h)/2),p=s[l]-f,p<0)h=l+1;else if(p>0)m=l-1;else{m=l;break}if(l=m,s[l]===f)return l/(c-1);const g=s[l],x=s[l+1]-g,_=(f-g)/x;return(l+_)/(c-1)}getTangent(e,i){let l=e-1e-4,c=e+1e-4;l<0&&(l=0),c>1&&(c=1);const f=this.getPoint(l),h=this.getPoint(c),m=i||(f.isVector2?new Kt:new Q);return m.copy(h).sub(f).normalize(),m}getTangentAt(e,i){const s=this.getUtoTmapping(e);return this.getTangent(s,i)}computeFrenetFrames(e,i=!1){const s=new Q,l=[],c=[],f=[],h=new Q,m=new En;for(let _=0;_<=e;_++){const E=_/e;l[_]=this.getTangentAt(E,new Q)}c[0]=new Q,f[0]=new Q;let p=Number.MAX_VALUE;const g=Math.abs(l[0].x),v=Math.abs(l[0].y),x=Math.abs(l[0].z);g<=p&&(p=g,s.set(1,0,0)),v<=p&&(p=v,s.set(0,1,0)),x<=p&&s.set(0,0,1),h.crossVectors(l[0],s).normalize(),c[0].crossVectors(l[0],h),f[0].crossVectors(l[0],c[0]);for(let _=1;_<=e;_++){if(c[_]=c[_-1].clone(),f[_]=f[_-1].clone(),h.crossVectors(l[_-1],l[_]),h.length()>Number.EPSILON){h.normalize();const E=Math.acos(Dt(l[_-1].dot(l[_]),-1,1));c[_].applyMatrix4(m.makeRotationAxis(h,E))}f[_].crossVectors(l[_],c[_])}if(i===!0){let _=Math.acos(Dt(c[0].dot(c[e]),-1,1));_/=e,l[0].dot(h.crossVectors(c[0],c[e]))>0&&(_=-_);for(let E=1;E<=e;E++)c[E].applyMatrix4(m.makeRotationAxis(l[E],_*E)),f[E].crossVectors(l[E],c[E])}return{tangents:l,normals:c,binormals:f}}clone(){return new this.constructor().copy(this)}copy(e){return this.arcLengthDivisions=e.arcLengthDivisions,this}toJSON(){const e={metadata:{version:4.7,type:"Curve",generator:"Curve.toJSON"}};return e.arcLengthDivisions=this.arcLengthDivisions,e.type=this.type,e}fromJSON(e){return this.arcLengthDivisions=e.arcLengthDivisions,this}}function Qp(){let r=0,e=0,i=0,s=0;function l(c,f,h,m){r=c,e=h,i=-3*c+3*f-2*h-m,s=2*c-2*f+h+m}return{initCatmullRom:function(c,f,h,m,p){l(f,h,p*(h-c),p*(m-f))},initNonuniformCatmullRom:function(c,f,h,m,p,g,v){let x=(f-c)/p-(h-c)/(p+g)+(h-f)/g,_=(h-f)/g-(m-f)/(g+v)+(m-h)/v;x*=g,_*=g,l(f,h,x,_)},calc:function(c){const f=c*c,h=f*c;return r+e*c+i*f+s*h}}}const Sv=new Q,bv=new Q,Dh=new Qp,Nh=new Qp,Lh=new Qp;class uM extends B_{constructor(e=[],i=!1,s="centripetal",l=.5){super(),this.isCatmullRomCurve3=!0,this.type="CatmullRomCurve3",this.points=e,this.closed=i,this.curveType=s,this.tension=l}getPoint(e,i=new Q){const s=i,l=this.points,c=l.length,f=(c-(this.closed?0:1))*e;let h=Math.floor(f),m=f-h;this.closed?h+=h>0?0:(Math.floor(Math.abs(h)/c)+1)*c:m===0&&h===c-1&&(h=c-2,m=1);let p,g;this.closed||h>0?p=l[(h-1)%c]:(bv.subVectors(l[0],l[1]).add(l[0]),p=bv);const v=l[h%c],x=l[(h+1)%c];if(this.closed||h+2<c?g=l[(h+2)%c]:(Sv.subVectors(l[c-1],l[c-2]).add(l[c-1]),g=Sv),this.curveType==="centripetal"||this.curveType==="chordal"){const _=this.curveType==="chordal"?.5:.25;let E=Math.pow(p.distanceToSquared(v),_),R=Math.pow(v.distanceToSquared(x),_),b=Math.pow(x.distanceToSquared(g),_);R<1e-4&&(R=1),E<1e-4&&(E=R),b<1e-4&&(b=R),Dh.initNonuniformCatmullRom(p.x,v.x,x.x,g.x,E,R,b),Nh.initNonuniformCatmullRom(p.y,v.y,x.y,g.y,E,R,b),Lh.initNonuniformCatmullRom(p.z,v.z,x.z,g.z,E,R,b)}else this.curveType==="catmullrom"&&(Dh.initCatmullRom(p.x,v.x,x.x,g.x,this.tension),Nh.initCatmullRom(p.y,v.y,x.y,g.y,this.tension),Lh.initCatmullRom(p.z,v.z,x.z,g.z,this.tension));return s.set(Dh.calc(m),Nh.calc(m),Lh.calc(m)),s}copy(e){super.copy(e),this.points=[];for(let i=0,s=e.points.length;i<s;i++){const l=e.points[i];this.points.push(l.clone())}return this.closed=e.closed,this.curveType=e.curveType,this.tension=e.tension,this}toJSON(){const e=super.toJSON();e.points=[];for(let i=0,s=this.points.length;i<s;i++){const l=this.points[i];e.points.push(l.toArray())}return e.closed=this.closed,e.curveType=this.curveType,e.tension=this.tension,e}fromJSON(e){super.fromJSON(e),this.points=[];for(let i=0,s=e.points.length;i<s;i++){const l=e.points[i];this.points.push(new Q().fromArray(l))}return this.closed=e.closed,this.curveType=e.curveType,this.tension=e.tension,this}}function fM(r,e){const i=1-r;return i*i*e}function dM(r,e){return 2*(1-r)*r*e}function hM(r,e){return r*r*e}function Oh(r,e,i,s){return fM(r,e)+dM(r,i)+hM(r,s)}class pM extends B_{constructor(e=new Q,i=new Q,s=new Q){super(),this.isQuadraticBezierCurve3=!0,this.type="QuadraticBezierCurve3",this.v0=e,this.v1=i,this.v2=s}getPoint(e,i=new Q){const s=i,l=this.v0,c=this.v1,f=this.v2;return s.set(Oh(e,l.x,c.x,f.x),Oh(e,l.y,c.y,f.y),Oh(e,l.z,c.z,f.z)),s}copy(e){return super.copy(e),this.v0.copy(e.v0),this.v1.copy(e.v1),this.v2.copy(e.v2),this}toJSON(){const e=super.toJSON();return e.v0=this.v0.toArray(),e.v1=this.v1.toArray(),e.v2=this.v2.toArray(),e}fromJSON(e){return super.fromJSON(e),this.v0.fromArray(e.v0),this.v1.fromArray(e.v1),this.v2.fromArray(e.v2),this}}class ec extends Bn{constructor(e=1,i=1,s=1,l=1){super(),this.type="PlaneGeometry",this.parameters={width:e,height:i,widthSegments:s,heightSegments:l};const c=e/2,f=i/2,h=Math.floor(s),m=Math.floor(l),p=h+1,g=m+1,v=e/h,x=i/m,_=[],E=[],R=[],b=[];for(let S=0;S<g;S++){const F=S*x-f;for(let G=0;G<p;G++){const w=G*v-c;E.push(w,-F,0),R.push(0,0,1),b.push(G/h),b.push(1-S/m)}}for(let S=0;S<m;S++)for(let F=0;F<h;F++){const G=F+p*S,w=F+p*(S+1),N=F+1+p*(S+1),L=F+1+p*S;_.push(G,w,L),_.push(w,N,L)}this.setIndex(_),this.setAttribute("position",new Cn(E,3)),this.setAttribute("normal",new Cn(R,3)),this.setAttribute("uv",new Cn(b,2))}copy(e){return super.copy(e),this.parameters=Object.assign({},e.parameters),this}static fromJSON(e){return new ec(e.width,e.height,e.widthSegments,e.heightSegments)}}class Jl extends Bn{constructor(e=1,i=32,s=16,l=0,c=Math.PI*2,f=0,h=Math.PI){super(),this.type="SphereGeometry",this.parameters={radius:e,widthSegments:i,heightSegments:s,phiStart:l,phiLength:c,thetaStart:f,thetaLength:h},i=Math.max(3,Math.floor(i)),s=Math.max(2,Math.floor(s));const m=Math.min(f+h,Math.PI);let p=0;const g=[],v=new Q,x=new Q,_=[],E=[],R=[],b=[];for(let S=0;S<=s;S++){const F=[],G=S/s,w=f+G*h,N=e*Math.cos(w),L=Math.sqrt(e*e-N*N);let z=0;S===0&&f===0?z=.5/i:S===s&&m===Math.PI&&(z=-.5/i);for(let T=0;T<=i;T++){const O=T/i,I=l+O*c;v.x=-L*Math.cos(I),v.y=N,v.z=L*Math.sin(I),E.push(v.x,v.y,v.z),x.copy(v).normalize(),R.push(x.x,x.y,x.z),b.push(O+z,1-G),F.push(p++)}g.push(F)}for(let S=0;S<s;S++)for(let F=0;F<i;F++){const G=g[S][F+1],w=g[S][F],N=g[S+1][F],L=g[S+1][F+1];(S!==0||f>0)&&_.push(G,w,L),(S!==s-1||m<Math.PI)&&_.push(w,N,L)}this.setIndex(_),this.setAttribute("position",new Cn(E,3)),this.setAttribute("normal",new Cn(R,3)),this.setAttribute("uv",new Cn(b,2))}copy(e){return super.copy(e),this.parameters=Object.assign({},e.parameters),this}static fromJSON(e){return new Jl(e.radius,e.widthSegments,e.heightSegments,e.phiStart,e.phiLength,e.thetaStart,e.thetaLength)}}function Ho(r){const e={};for(const i in r){e[i]={};for(const s in r[i]){const l=r[i][s];if(Mv(l))l.isRenderTargetTexture?(ht("UniformsUtils: Textures of render targets cannot be cloned via cloneUniforms() or mergeUniforms()."),e[i][s]=null):e[i][s]=l.clone();else if(Array.isArray(l))if(Mv(l[0])){const c=[];for(let f=0,h=l.length;f<h;f++)c[f]=l[f].clone();e[i][s]=c}else e[i][s]=l.slice();else e[i][s]=l}}return e}function Mi(r){const e={};for(let i=0;i<r.length;i++){const s=Ho(r[i]);for(const l in s)e[l]=s[l]}return e}function Mv(r){return r&&(r.isColor||r.isMatrix3||r.isMatrix4||r.isVector2||r.isVector3||r.isVector4||r.isTexture||r.isQuaternion)}function mM(r){const e=[];for(let i=0;i<r.length;i++)e.push(r[i].clone());return e}function I_(r){const e=r.getRenderTarget();return e===null?r.outputColorSpace:e.isXRRenderTarget===!0?e.texture.colorSpace:kt.workingColorSpace}const gM={clone:Ho,merge:Mi};var xM=`void main() {
	gl_Position = projectionMatrix * modelViewMatrix * vec4( position, 1.0 );
}`,vM=`void main() {
	gl_FragColor = vec4( 1.0, 0.0, 0.0, 1.0 );
}`;class Yn extends ko{constructor(e){super(),this.isShaderMaterial=!0,this.type="ShaderMaterial",this.defines={},this.uniforms={},this.uniformsGroups=[],this.vertexShader=xM,this.fragmentShader=vM,this.linewidth=1,this.wireframe=!1,this.wireframeLinewidth=1,this.fog=!1,this.lights=!1,this.clipping=!1,this.forceSinglePass=!0,this.extensions={clipCullDistance:!1,multiDraw:!1},this.defaultAttributeValues={color:[1,1,1],uv:[0,0],uv1:[0,0]},this.index0AttributeName=void 0,this.uniformsNeedUpdate=!1,this.glslVersion=null,e!==void 0&&this.setValues(e)}copy(e){return super.copy(e),this.fragmentShader=e.fragmentShader,this.vertexShader=e.vertexShader,this.uniforms=Ho(e.uniforms),this.uniformsGroups=mM(e.uniformsGroups),this.defines=Object.assign({},e.defines),this.wireframe=e.wireframe,this.wireframeLinewidth=e.wireframeLinewidth,this.fog=e.fog,this.lights=e.lights,this.clipping=e.clipping,this.extensions=Object.assign({},e.extensions),this.glslVersion=e.glslVersion,this.defaultAttributeValues=Object.assign({},e.defaultAttributeValues),this.index0AttributeName=e.index0AttributeName,this.uniformsNeedUpdate=e.uniformsNeedUpdate,this}toJSON(e){const i=super.toJSON(e);i.glslVersion=this.glslVersion,i.uniforms={};for(const l in this.uniforms){const f=this.uniforms[l].value;f&&f.isTexture?i.uniforms[l]={type:"t",value:f.toJSON(e).uuid}:f&&f.isColor?i.uniforms[l]={type:"c",value:f.getHex()}:f&&f.isVector2?i.uniforms[l]={type:"v2",value:f.toArray()}:f&&f.isVector3?i.uniforms[l]={type:"v3",value:f.toArray()}:f&&f.isVector4?i.uniforms[l]={type:"v4",value:f.toArray()}:f&&f.isMatrix3?i.uniforms[l]={type:"m3",value:f.toArray()}:f&&f.isMatrix4?i.uniforms[l]={type:"m4",value:f.toArray()}:i.uniforms[l]={value:f}}Object.keys(this.defines).length>0&&(i.defines=this.defines),i.vertexShader=this.vertexShader,i.fragmentShader=this.fragmentShader,i.lights=this.lights,i.clipping=this.clipping;const s={};for(const l in this.extensions)this.extensions[l]===!0&&(s[l]=!0);return Object.keys(s).length>0&&(i.extensions=s),i}fromJSON(e,i){if(super.fromJSON(e,i),e.uniforms!==void 0)for(const s in e.uniforms){const l=e.uniforms[s];switch(this.uniforms[s]={},l.type){case"t":this.uniforms[s].value=i[l.value]||null;break;case"c":this.uniforms[s].value=new wt().setHex(l.value);break;case"v2":this.uniforms[s].value=new Kt().fromArray(l.value);break;case"v3":this.uniforms[s].value=new Q().fromArray(l.value);break;case"v4":this.uniforms[s].value=new Ln().fromArray(l.value);break;case"m3":this.uniforms[s].value=new St().fromArray(l.value);break;case"m4":this.uniforms[s].value=new En().fromArray(l.value);break;default:this.uniforms[s].value=l.value}}if(e.defines!==void 0&&(this.defines=e.defines),e.vertexShader!==void 0&&(this.vertexShader=e.vertexShader),e.fragmentShader!==void 0&&(this.fragmentShader=e.fragmentShader),e.glslVersion!==void 0&&(this.glslVersion=e.glslVersion),e.extensions!==void 0)for(const s in e.extensions)this.extensions[s]=e.extensions[s];return e.lights!==void 0&&(this.lights=e.lights),e.clipping!==void 0&&(this.clipping=e.clipping),this}}class _M extends Yn{constructor(e){super(e),this.isRawShaderMaterial=!0,this.type="RawShaderMaterial"}}class yM extends ko{constructor(e){super(),this.isMeshDepthMaterial=!0,this.type="MeshDepthMaterial",this.depthPacking=cb,this.map=null,this.alphaMap=null,this.displacementMap=null,this.displacementScale=1,this.displacementBias=0,this.wireframe=!1,this.wireframeLinewidth=1,this.setValues(e)}copy(e){return super.copy(e),this.depthPacking=e.depthPacking,this.map=e.map,this.alphaMap=e.alphaMap,this.displacementMap=e.displacementMap,this.displacementScale=e.displacementScale,this.displacementBias=e.displacementBias,this.wireframe=e.wireframe,this.wireframeLinewidth=e.wireframeLinewidth,this}}class SM extends ko{constructor(e){super(),this.isMeshDistanceMaterial=!0,this.type="MeshDistanceMaterial",this.map=null,this.alphaMap=null,this.displacementMap=null,this.displacementScale=1,this.displacementBias=0,this.setValues(e)}copy(e){return super.copy(e),this.map=e.map,this.alphaMap=e.alphaMap,this.displacementMap=e.displacementMap,this.displacementScale=e.displacementScale,this.displacementBias=e.displacementBias,this}}const Ph={enabled:!1,files:{},add:function(r,e){this.enabled!==!1&&(Ev(r)||(this.files[r]=e))},get:function(r){if(this.enabled!==!1&&!Ev(r))return this.files[r]},remove:function(r){delete this.files[r]},clear:function(){this.files={}}};function Ev(r){try{const e=r.slice(r.indexOf(":")+1);return new URL(e).protocol==="blob:"}catch{return!1}}class bM{constructor(e,i,s){const l=this;let c=!1,f=0,h=0,m;const p=[];this.onStart=void 0,this.onLoad=e,this.onProgress=i,this.onError=s,this._abortController=null,this.itemStart=function(g){h++,c===!1&&l.onStart!==void 0&&l.onStart(g,f,h),c=!0},this.itemEnd=function(g){f++,l.onProgress!==void 0&&l.onProgress(g,f,h),f===h&&(c=!1,l.onLoad!==void 0&&l.onLoad())},this.itemError=function(g){l.onError!==void 0&&l.onError(g)},this.resolveURL=function(g){return g=g.normalize("NFC"),m?m(g):g},this.setURLModifier=function(g){return m=g,this},this.addHandler=function(g,v){return p.push(g,v),this},this.removeHandler=function(g){const v=p.indexOf(g);return v!==-1&&p.splice(v,2),this},this.getHandler=function(g){for(let v=0,x=p.length;v<x;v+=2){const _=p[v],E=p[v+1];if(_.global&&(_.lastIndex=0),_.test(g))return E}return null},this.abort=function(){return this.abortController.abort(),this._abortController=null,this}}get abortController(){return this._abortController||(this._abortController=new AbortController),this._abortController}}const MM=new bM;class Jp{constructor(e){this.manager=e!==void 0?e:MM,this.crossOrigin="anonymous",this.withCredentials=!1,this.path="",this.resourcePath="",this.requestHeader={},typeof __THREE_DEVTOOLS__<"u"&&__THREE_DEVTOOLS__.dispatchEvent(new CustomEvent("observe",{detail:this}))}load(){}loadAsync(e,i){const s=this;return new Promise(function(l,c){s.load(e,l,i,c)})}parse(){}setCrossOrigin(e){return this.crossOrigin=e,this}setWithCredentials(e){return this.withCredentials=e,this}setPath(e){return this.path=e,this}setResourcePath(e){return this.resourcePath=e,this}setRequestHeader(e){return this.requestHeader=e,this}abort(){return this}}Jp.DEFAULT_MATERIAL_NAME="__DEFAULT";const Co=new WeakMap;class EM extends Jp{constructor(e){super(e)}load(e,i,s,l){this.path!==void 0&&(e=this.path+e),e=this.manager.resolveURL(e);const c=this,f=Ph.get(`image:${e}`);if(f!==void 0){if(f.complete===!0)c.manager.itemStart(e),setTimeout(function(){i&&i(f),c.manager.itemEnd(e)},0);else{let v=Co.get(f);v===void 0&&(v=[],Co.set(f,v)),v.push({onLoad:i,onError:l})}return f}const h=Zl("img");function m(){g(),i&&i(this);const v=Co.get(this)||[];for(let x=0;x<v.length;x++){const _=v[x];_.onLoad&&_.onLoad(this)}Co.delete(this),c.manager.itemEnd(e)}function p(v){g(),l&&l(v),Ph.remove(`image:${e}`);const x=Co.get(this)||[];for(let _=0;_<x.length;_++){const E=x[_];E.onError&&E.onError(v)}Co.delete(this),c.manager.itemError(e),c.manager.itemEnd(e)}function g(){h.removeEventListener("load",m,!1),h.removeEventListener("error",p,!1)}return h.addEventListener("load",m,!1),h.addEventListener("error",p,!1),e.slice(0,5)!=="data:"&&this.crossOrigin!==void 0&&(h.crossOrigin=this.crossOrigin),Ph.add(`image:${e}`,h),c.manager.itemStart(e),h.src=e,h}}class TM extends Jp{constructor(e){super(e)}load(e,i,s,l){const c=new gi,f=new EM(this.manager);return f.setCrossOrigin(this.crossOrigin),f.setPath(this.path),f.load(e,function(h){c.image=h,c.needsUpdate=!0,i!==void 0&&i(c)},s,l),c}}const Au=new Q,wu=new ss,Ba=new Q;class H_ extends Ti{constructor(){super(),this.isCamera=!0,this.type="Camera",this.matrixWorldInverse=new En,this.projectionMatrix=new En,this.projectionMatrixInverse=new En,this.coordinateSystem=Va,this._reversedDepth=!1}get reversedDepth(){return this._reversedDepth}copy(e,i){return super.copy(e,i),this.matrixWorldInverse.copy(e.matrixWorldInverse),this.projectionMatrix.copy(e.projectionMatrix),this.projectionMatrixInverse.copy(e.projectionMatrixInverse),this.coordinateSystem=e.coordinateSystem,this}getWorldDirection(e){return super.getWorldDirection(e).negate()}updateMatrixWorld(e){super.updateMatrixWorld(e),this.matrixWorld.decompose(Au,wu,Ba),Ba.x===1&&Ba.y===1&&Ba.z===1?this.matrixWorldInverse.copy(this.matrixWorld).invert():this.matrixWorldInverse.compose(Au,wu,Ba.set(1,1,1)).invert()}updateWorldMatrix(e,i,s=!1){super.updateWorldMatrix(e,i,s),this.matrixWorld.decompose(Au,wu,Ba),Ba.x===1&&Ba.y===1&&Ba.z===1?this.matrixWorldInverse.copy(this.matrixWorld).invert():this.matrixWorldInverse.compose(Au,wu,Ba.set(1,1,1)).invert()}clone(){return new this.constructor().copy(this)}}const es=new Q,Tv=new Kt,Av=new Kt;class Yi extends H_{constructor(e=50,i=1,s=.1,l=2e3){super(),this.isPerspectiveCamera=!0,this.type="PerspectiveCamera",this.fov=e,this.zoom=1,this.near=s,this.far=l,this.focus=10,this.aspect=i,this.view=null,this.filmGauge=35,this.filmOffset=0,this.updateProjectionMatrix()}copy(e,i){return super.copy(e,i),this.fov=e.fov,this.zoom=e.zoom,this.near=e.near,this.far=e.far,this.focus=e.focus,this.aspect=e.aspect,this.view=e.view===null?null:Object.assign({},e.view),this.filmGauge=e.filmGauge,this.filmOffset=e.filmOffset,this}setFocalLength(e){const i=.5*this.getFilmHeight()/e;this.fov=Kl*2*Math.atan(i),this.updateProjectionMatrix()}getFocalLength(){const e=Math.tan(Gl*.5*this.fov);return .5*this.getFilmHeight()/e}getEffectiveFOV(){return Kl*2*Math.atan(Math.tan(Gl*.5*this.fov)/this.zoom)}getFilmWidth(){return this.filmGauge*Math.min(this.aspect,1)}getFilmHeight(){return this.filmGauge/Math.max(this.aspect,1)}getViewBounds(e,i,s){es.set(-1,-1,.5).applyMatrix4(this.projectionMatrixInverse),i.set(es.x,es.y).multiplyScalar(-e/es.z),es.set(1,1,.5).applyMatrix4(this.projectionMatrixInverse),s.set(es.x,es.y).multiplyScalar(-e/es.z)}getViewSize(e,i){return this.getViewBounds(e,Tv,Av),i.subVectors(Av,Tv)}setViewOffset(e,i,s,l,c,f){this.aspect=e/i,this.view===null&&(this.view={enabled:!0,fullWidth:1,fullHeight:1,offsetX:0,offsetY:0,width:1,height:1}),this.view.enabled=!0,this.view.fullWidth=e,this.view.fullHeight=i,this.view.offsetX=s,this.view.offsetY=l,this.view.width=c,this.view.height=f,this.updateProjectionMatrix()}clearViewOffset(){this.view!==null&&(this.view.enabled=!1),this.updateProjectionMatrix()}updateProjectionMatrix(){const e=this.near;let i=e*Math.tan(Gl*.5*this.fov)/this.zoom,s=2*i,l=this.aspect*s,c=-.5*l;const f=this.view;if(this.view!==null&&this.view.enabled){const m=f.fullWidth,p=f.fullHeight;c+=f.offsetX*l/m,i-=f.offsetY*s/p,l*=f.width/m,s*=f.height/p}const h=this.filmOffset;h!==0&&(c+=e*h/this.getFilmWidth()),this.projectionMatrix.makePerspective(c,c+l,i,i-s,e,this.far,this.coordinateSystem,this.reversedDepth),this.projectionMatrixInverse.copy(this.projectionMatrix).invert()}toJSON(e){const i=super.toJSON(e);return i.object.fov=this.fov,i.object.zoom=this.zoom,i.object.near=this.near,i.object.far=this.far,i.object.focus=this.focus,i.object.aspect=this.aspect,this.view!==null&&(i.object.view=Object.assign({},this.view)),i.object.filmGauge=this.filmGauge,i.object.filmOffset=this.filmOffset,i}}class G_ extends H_{constructor(e=-1,i=1,s=1,l=-1,c=.1,f=2e3){super(),this.isOrthographicCamera=!0,this.type="OrthographicCamera",this.zoom=1,this.view=null,this.left=e,this.right=i,this.top=s,this.bottom=l,this.near=c,this.far=f,this.updateProjectionMatrix()}copy(e,i){return super.copy(e,i),this.left=e.left,this.right=e.right,this.top=e.top,this.bottom=e.bottom,this.near=e.near,this.far=e.far,this.zoom=e.zoom,this.view=e.view===null?null:Object.assign({},e.view),this}setViewOffset(e,i,s,l,c,f){this.view===null&&(this.view={enabled:!0,fullWidth:1,fullHeight:1,offsetX:0,offsetY:0,width:1,height:1}),this.view.enabled=!0,this.view.fullWidth=e,this.view.fullHeight=i,this.view.offsetX=s,this.view.offsetY=l,this.view.width=c,this.view.height=f,this.updateProjectionMatrix()}clearViewOffset(){this.view!==null&&(this.view.enabled=!1),this.updateProjectionMatrix()}updateProjectionMatrix(){const e=(this.right-this.left)/(2*this.zoom),i=(this.top-this.bottom)/(2*this.zoom),s=(this.right+this.left)/2,l=(this.top+this.bottom)/2;let c=s-e,f=s+e,h=l+i,m=l-i;if(this.view!==null&&this.view.enabled){const p=(this.right-this.left)/this.view.fullWidth/this.zoom,g=(this.top-this.bottom)/this.view.fullHeight/this.zoom;c+=p*this.view.offsetX,f=c+p*this.view.width,h-=g*this.view.offsetY,m=h-g*this.view.height}this.projectionMatrix.makeOrthographic(c,f,h,m,this.near,this.far,this.coordinateSystem,this.reversedDepth),this.projectionMatrixInverse.copy(this.projectionMatrix).invert()}toJSON(e){const i=super.toJSON(e);return i.object.zoom=this.zoom,i.object.left=this.left,i.object.right=this.right,i.object.top=this.top,i.object.bottom=this.bottom,i.object.near=this.near,i.object.far=this.far,this.view!==null&&(i.object.view=Object.assign({},this.view)),i}}const Ro=-90,Uo=1;class AM extends Ti{constructor(e,i,s){super(),this.type="CubeCamera",this.renderTarget=s,this.coordinateSystem=null,this.activeMipmapLevel=0;const l=new Yi(Ro,Uo,e,i);l.layers=this.layers,this.add(l);const c=new Yi(Ro,Uo,e,i);c.layers=this.layers,this.add(c);const f=new Yi(Ro,Uo,e,i);f.layers=this.layers,this.add(f);const h=new Yi(Ro,Uo,e,i);h.layers=this.layers,this.add(h);const m=new Yi(Ro,Uo,e,i);m.layers=this.layers,this.add(m);const p=new Yi(Ro,Uo,e,i);p.layers=this.layers,this.add(p)}updateCoordinateSystem(){const e=this.coordinateSystem,i=this.children.concat(),[s,l,c,f,h,m]=i;for(const p of i)this.remove(p);if(e===Va)s.up.set(0,1,0),s.lookAt(1,0,0),l.up.set(0,1,0),l.lookAt(-1,0,0),c.up.set(0,0,-1),c.lookAt(0,1,0),f.up.set(0,0,1),f.lookAt(0,-1,0),h.up.set(0,1,0),h.lookAt(0,0,1),m.up.set(0,1,0),m.lookAt(0,0,-1);else if(e===Wu)s.up.set(0,-1,0),s.lookAt(-1,0,0),l.up.set(0,-1,0),l.lookAt(1,0,0),c.up.set(0,0,1),c.lookAt(0,1,0),f.up.set(0,0,-1),f.lookAt(0,-1,0),h.up.set(0,-1,0),h.lookAt(0,0,1),m.up.set(0,-1,0),m.lookAt(0,0,-1);else throw new Error("THREE.CubeCamera.updateCoordinateSystem(): Invalid coordinate system: "+e);for(const p of i)this.add(p),p.updateMatrixWorld()}update(e,i){this.parent===null&&this.updateMatrixWorld();const{renderTarget:s,activeMipmapLevel:l}=this;this.coordinateSystem!==e.coordinateSystem&&(this.coordinateSystem=e.coordinateSystem,this.updateCoordinateSystem());const[c,f,h,m,p,g]=this.children,v=e.getRenderTarget(),x=e.getActiveCubeFace(),_=e.getActiveMipmapLevel(),E=e.xr.enabled;e.xr.enabled=!1;const R=s.texture.generateMipmaps;s.texture.generateMipmaps=!1;let b=!1;e.isWebGLRenderer===!0?b=e.state.buffers.depth.getReversed():b=e.reversedDepthBuffer,e.setRenderTarget(s,0,l),b&&e.autoClear===!1&&e.clearDepth(),e.render(i,c),e.setRenderTarget(s,1,l),b&&e.autoClear===!1&&e.clearDepth(),e.render(i,f),e.setRenderTarget(s,2,l),b&&e.autoClear===!1&&e.clearDepth(),e.render(i,h),e.setRenderTarget(s,3,l),b&&e.autoClear===!1&&e.clearDepth(),e.render(i,m),e.setRenderTarget(s,4,l),b&&e.autoClear===!1&&e.clearDepth(),e.render(i,p),s.texture.generateMipmaps=R,e.setRenderTarget(s,5,l),b&&e.autoClear===!1&&e.clearDepth(),e.render(i,g),e.setRenderTarget(v,x,_),e.xr.enabled=E,s.texture.needsPMREMUpdate=!0}}class wM extends Yi{constructor(e=[]){super(),this.isArrayCamera=!0,this.isMultiViewCamera=!1,this.cameras=e}}const wv=new En;class CM{constructor(e,i,s=0,l=1/0){this.ray=new Qu(e,i),this.near=s,this.far=l,this.camera=null,this.layers=new jp,this.params={Mesh:{},Line:{threshold:1},LOD:{},Points:{threshold:1},Sprite:{}}}set(e,i){this.ray.set(e,i)}setFromCamera(e,i){i.isPerspectiveCamera?(this.ray.origin.setFromMatrixPosition(i.matrixWorld),this.ray.direction.set(e.x,e.y,.5).unproject(i).sub(this.ray.origin).normalize(),this.camera=i):i.isOrthographicCamera?(this.ray.origin.set(e.x,e.y,i.projectionMatrix.elements[14]).unproject(i),this.ray.direction.set(0,0,-1).transformDirection(i.matrixWorld),this.camera=i):Zt("Raycaster: Unsupported camera type: "+i.type)}setFromXRController(e){return wv.identity().extractRotation(e.matrixWorld),this.ray.origin.setFromMatrixPosition(e.matrixWorld),this.ray.direction.set(0,0,-1).applyMatrix4(wv),this}intersectObject(e,i=!0,s=[]){return Up(e,this,s,i),s.sort(Cv),s}intersectObjects(e,i=!0,s=[]){for(let l=0,c=e.length;l<c;l++)Up(e[l],this,s,i);return s.sort(Cv),s}}function Cv(r,e){return r.distance-e.distance}function Up(r,e,i,s){let l=!0;if(r.layers.test(e.layers)&&r.raycast(e,i)===!1&&(l=!1),l===!0&&s===!0){const c=r.children;for(let f=0,h=c.length;f<h;f++)Up(c[f],e,i,!0)}}const om=class om{constructor(e,i,s,l){this.elements=[1,0,0,1],e!==void 0&&this.set(e,i,s,l)}identity(){return this.set(1,0,0,1),this}fromArray(e,i=0){for(let s=0;s<4;s++)this.elements[s]=e[s+i];return this}set(e,i,s,l){const c=this.elements;return c[0]=e,c[2]=i,c[1]=s,c[3]=l,this}};om.prototype.isMatrix2=!0;let Rv=om;function Uv(r,e,i,s){const l=RM(s);switch(i){case A_:return r*e;case C_:return r*e/l.components*l.byteLength;case Gp:return r*e/l.components*l.byteLength;case Ps:return r*e*2/l.components*l.byteLength;case Vp:return r*e*2/l.components*l.byteLength;case w_:return r*e*3/l.components*l.byteLength;case Ta:return r*e*4/l.components*l.byteLength;case kp:return r*e*4/l.components*l.byteLength;case Lu:case Ou:return Math.floor((r+3)/4)*Math.floor((e+3)/4)*8;case Pu:case zu:return Math.floor((r+3)/4)*Math.floor((e+3)/4)*16;case ep:case np:return Math.max(r,16)*Math.max(e,8)/4;case $h:case tp:return Math.max(r,8)*Math.max(e,8)/2;case ip:case ap:case sp:case op:return Math.floor((r+3)/4)*Math.floor((e+3)/4)*8;case rp:case Gu:case lp:return Math.floor((r+3)/4)*Math.floor((e+3)/4)*16;case cp:return Math.floor((r+3)/4)*Math.floor((e+3)/4)*16;case up:return Math.floor((r+4)/5)*Math.floor((e+3)/4)*16;case fp:return Math.floor((r+4)/5)*Math.floor((e+4)/5)*16;case dp:return Math.floor((r+5)/6)*Math.floor((e+4)/5)*16;case hp:return Math.floor((r+5)/6)*Math.floor((e+5)/6)*16;case pp:return Math.floor((r+7)/8)*Math.floor((e+4)/5)*16;case mp:return Math.floor((r+7)/8)*Math.floor((e+5)/6)*16;case gp:return Math.floor((r+7)/8)*Math.floor((e+7)/8)*16;case xp:return Math.floor((r+9)/10)*Math.floor((e+4)/5)*16;case vp:return Math.floor((r+9)/10)*Math.floor((e+5)/6)*16;case _p:return Math.floor((r+9)/10)*Math.floor((e+7)/8)*16;case yp:return Math.floor((r+9)/10)*Math.floor((e+9)/10)*16;case Sp:return Math.floor((r+11)/12)*Math.floor((e+9)/10)*16;case bp:return Math.floor((r+11)/12)*Math.floor((e+11)/12)*16;case Mp:case Ep:case Tp:return Math.ceil(r/4)*Math.ceil(e/4)*16;case Ap:case wp:return Math.ceil(r/4)*Math.ceil(e/4)*8;case Vu:case Cp:return Math.ceil(r/4)*Math.ceil(e/4)*16}throw new Error(`Unable to determine texture byte length for ${i} format.`)}function RM(r){switch(r){case fa:case b_:return{byteLength:1,components:1};case Yl:case M_:case Wa:return{byteLength:2,components:1};case Ip:case Hp:return{byteLength:2,components:4};case Xa:case Bp:case Ga:return{byteLength:4,components:1};case E_:case T_:return{byteLength:4,components:3}}throw new Error(`THREE.TextureUtils: Unknown texture type ${r}.`)}typeof __THREE_DEVTOOLS__<"u"&&__THREE_DEVTOOLS__.dispatchEvent(new CustomEvent("register",{detail:{revision:Fp}}));typeof window<"u"&&(window.__THREE__?ht("WARNING: Multiple instances of Three.js being imported."):window.__THREE__=Fp);/**
 * @license
 * Copyright 2010-2026 Three.js Authors
 * SPDX-License-Identifier: MIT
 */function V_(){let r=null,e=!1,i=null,s=null;function l(c,f){s=r.requestAnimationFrame(l),i(c,f)}return{start:function(){e!==!0&&i!==null&&r!==null&&(s=r.requestAnimationFrame(l),e=!0)},stop:function(){r!==null&&r.cancelAnimationFrame(s),e=!1},setAnimationLoop:function(c){i=c},setContext:function(c){r=c}}}function UM(r){const e=new WeakMap;function i(h,m){const p=h.array,g=h.usage,v=p.byteLength,x=r.createBuffer();r.bindBuffer(m,x),r.bufferData(m,p,g),h.onUploadCallback();let _;if(p instanceof Float32Array)_=r.FLOAT;else if(typeof Float16Array<"u"&&p instanceof Float16Array)_=r.HALF_FLOAT;else if(p instanceof Uint16Array)h.isFloat16BufferAttribute?_=r.HALF_FLOAT:_=r.UNSIGNED_SHORT;else if(p instanceof Int16Array)_=r.SHORT;else if(p instanceof Uint32Array)_=r.UNSIGNED_INT;else if(p instanceof Int32Array)_=r.INT;else if(p instanceof Int8Array)_=r.BYTE;else if(p instanceof Uint8Array)_=r.UNSIGNED_BYTE;else if(p instanceof Uint8ClampedArray)_=r.UNSIGNED_BYTE;else throw new Error("THREE.WebGLAttributes: Unsupported buffer data format: "+p);return{buffer:x,type:_,bytesPerElement:p.BYTES_PER_ELEMENT,version:h.version,size:v}}function s(h,m,p){const g=m.array,v=m.updateRanges;if(r.bindBuffer(p,h),v.length===0)r.bufferSubData(p,0,g);else{v.sort((_,E)=>_.start-E.start);let x=0;for(let _=1;_<v.length;_++){const E=v[x],R=v[_];R.start<=E.start+E.count+1?E.count=Math.max(E.count,R.start+R.count-E.start):(++x,v[x]=R)}v.length=x+1;for(let _=0,E=v.length;_<E;_++){const R=v[_];r.bufferSubData(p,R.start*g.BYTES_PER_ELEMENT,g,R.start,R.count)}m.clearUpdateRanges()}m.onUploadCallback()}function l(h){return h.isInterleavedBufferAttribute&&(h=h.data),e.get(h)}function c(h){h.isInterleavedBufferAttribute&&(h=h.data);const m=e.get(h);m&&(r.deleteBuffer(m.buffer),e.delete(h))}function f(h,m){if(h.isInterleavedBufferAttribute&&(h=h.data),h.isGLBufferAttribute){const g=e.get(h);(!g||g.version<h.version)&&e.set(h,{buffer:h.buffer,type:h.type,bytesPerElement:h.elementSize,version:h.version});return}const p=e.get(h);if(p===void 0)e.set(h,i(h,m));else if(p.version<h.version){if(p.size!==h.array.byteLength)throw new Error("THREE.WebGLAttributes: The size of the buffer attribute's array buffer does not match the original size. Resizing buffer attributes is not supported.");s(p.buffer,h,m),p.version=h.version}}return{get:l,remove:c,update:f}}var DM=`#ifdef USE_ALPHAHASH
	if ( diffuseColor.a < getAlphaHashThreshold( vPosition ) ) discard;
#endif`,NM=`#ifdef USE_ALPHAHASH
	const float ALPHA_HASH_SCALE = 0.05;
	float hash2D( vec2 value ) {
		return fract( 1.0e4 * sin( 17.0 * value.x + 0.1 * value.y ) * ( 0.1 + abs( sin( 13.0 * value.y + value.x ) ) ) );
	}
	float hash3D( vec3 value ) {
		return hash2D( vec2( hash2D( value.xy ), value.z ) );
	}
	float getAlphaHashThreshold( vec3 position ) {
		float maxDeriv = max(
			length( dFdx( position.xyz ) ),
			length( dFdy( position.xyz ) )
		);
		float pixScale = 1.0 / ( ALPHA_HASH_SCALE * maxDeriv );
		vec2 pixScales = vec2(
			exp2( floor( log2( pixScale ) ) ),
			exp2( ceil( log2( pixScale ) ) )
		);
		vec2 alpha = vec2(
			hash3D( floor( pixScales.x * position.xyz ) ),
			hash3D( floor( pixScales.y * position.xyz ) )
		);
		float lerpFactor = fract( log2( pixScale ) );
		float x = ( 1.0 - lerpFactor ) * alpha.x + lerpFactor * alpha.y;
		float a = min( lerpFactor, 1.0 - lerpFactor );
		vec3 cases = vec3(
			x * x / ( 2.0 * a * ( 1.0 - a ) ),
			( x - 0.5 * a ) / ( 1.0 - a ),
			1.0 - ( ( 1.0 - x ) * ( 1.0 - x ) / ( 2.0 * a * ( 1.0 - a ) ) )
		);
		float threshold = ( x < ( 1.0 - a ) )
			? ( ( x < a ) ? cases.x : cases.y )
			: cases.z;
		return clamp( threshold , 1.0e-6, 1.0 );
	}
#endif`,LM=`#ifdef USE_ALPHAMAP
	diffuseColor.a *= texture2D( alphaMap, vAlphaMapUv ).g;
#endif`,OM=`#ifdef USE_ALPHAMAP
	uniform sampler2D alphaMap;
#endif`,PM=`#ifdef USE_ALPHATEST
	#ifdef ALPHA_TO_COVERAGE
	diffuseColor.a = smoothstep( alphaTest, alphaTest + fwidth( diffuseColor.a ), diffuseColor.a );
	if ( diffuseColor.a == 0.0 ) discard;
	#else
	if ( diffuseColor.a < alphaTest ) discard;
	#endif
#endif`,zM=`#ifdef USE_ALPHATEST
	uniform float alphaTest;
#endif`,FM=`#ifdef USE_AOMAP
	float ambientOcclusion = ( texture2D( aoMap, vAoMapUv ).r - 1.0 ) * aoMapIntensity + 1.0;
	reflectedLight.indirectDiffuse *= ambientOcclusion;
	#if defined( USE_CLEARCOAT ) 
		clearcoatSpecularIndirect *= ambientOcclusion;
	#endif
	#if defined( USE_SHEEN ) 
		sheenSpecularIndirect *= ambientOcclusion;
	#endif
	#if defined( USE_ENVMAP ) && defined( STANDARD )
		float dotNV = saturate( dot( geometryNormal, geometryViewDir ) );
		reflectedLight.indirectSpecular *= computeSpecularOcclusion( dotNV, ambientOcclusion, material.roughness );
	#endif
#endif`,BM=`#ifdef USE_AOMAP
	uniform sampler2D aoMap;
	uniform float aoMapIntensity;
#endif`,IM=`#ifdef USE_BATCHING
	#if ! defined( GL_ANGLE_multi_draw )
	#define gl_DrawID _gl_DrawID
	uniform int _gl_DrawID;
	#endif
	uniform highp sampler2D batchingTexture;
	uniform highp usampler2D batchingIdTexture;
	mat4 getBatchingMatrix( const in float i ) {
		int size = textureSize( batchingTexture, 0 ).x;
		int j = int( i ) * 4;
		int x = j % size;
		int y = j / size;
		vec4 v1 = texelFetch( batchingTexture, ivec2( x, y ), 0 );
		vec4 v2 = texelFetch( batchingTexture, ivec2( x + 1, y ), 0 );
		vec4 v3 = texelFetch( batchingTexture, ivec2( x + 2, y ), 0 );
		vec4 v4 = texelFetch( batchingTexture, ivec2( x + 3, y ), 0 );
		return mat4( v1, v2, v3, v4 );
	}
	float getIndirectIndex( const in int i ) {
		int size = textureSize( batchingIdTexture, 0 ).x;
		int x = i % size;
		int y = i / size;
		return float( texelFetch( batchingIdTexture, ivec2( x, y ), 0 ).r );
	}
#endif
#ifdef USE_BATCHING_COLOR
	uniform sampler2D batchingColorTexture;
	vec4 getBatchingColor( const in float i ) {
		int size = textureSize( batchingColorTexture, 0 ).x;
		int j = int( i );
		int x = j % size;
		int y = j / size;
		return texelFetch( batchingColorTexture, ivec2( x, y ), 0 );
	}
#endif`,HM=`#ifdef USE_BATCHING
	mat4 batchingMatrix = getBatchingMatrix( getIndirectIndex( gl_DrawID ) );
#endif`,GM=`vec3 transformed = vec3( position );
#ifdef USE_ALPHAHASH
	vPosition = vec3( position );
#endif`,VM=`vec3 objectNormal = vec3( normal );
#ifdef USE_TANGENT
	vec3 objectTangent = vec3( tangent.xyz );
#endif`,kM=`float G_BlinnPhong_Implicit( ) {
	return 0.25;
}
float D_BlinnPhong( const in float shininess, const in float dotNH ) {
	return RECIPROCAL_PI * ( shininess * 0.5 + 1.0 ) * pow( dotNH, shininess );
}
vec3 BRDF_BlinnPhong( const in vec3 lightDir, const in vec3 viewDir, const in vec3 normal, const in vec3 specularColor, const in float shininess ) {
	vec3 halfDir = normalize( lightDir + viewDir );
	float dotNH = saturate( dot( normal, halfDir ) );
	float dotVH = saturate( dot( viewDir, halfDir ) );
	vec3 F = F_Schlick( specularColor, 1.0, dotVH );
	float G = G_BlinnPhong_Implicit( );
	float D = D_BlinnPhong( shininess, dotNH );
	return F * ( G * D );
} // validated`,XM=`#ifdef USE_IRIDESCENCE
	const mat3 XYZ_TO_REC709 = mat3(
		 3.2404542, -0.9692660,  0.0556434,
		-1.5371385,  1.8760108, -0.2040259,
		-0.4985314,  0.0415560,  1.0572252
	);
	vec3 Fresnel0ToIor( vec3 fresnel0 ) {
		vec3 sqrtF0 = sqrt( fresnel0 );
		return ( vec3( 1.0 ) + sqrtF0 ) / ( vec3( 1.0 ) - sqrtF0 );
	}
	vec3 IorToFresnel0( vec3 transmittedIor, float incidentIor ) {
		return pow2( ( transmittedIor - vec3( incidentIor ) ) / ( transmittedIor + vec3( incidentIor ) ) );
	}
	float IorToFresnel0( float transmittedIor, float incidentIor ) {
		return pow2( ( transmittedIor - incidentIor ) / ( transmittedIor + incidentIor ));
	}
	vec3 evalSensitivity( float OPD, vec3 shift ) {
		float phase = 2.0 * PI * OPD * 1.0e-9;
		vec3 val = vec3( 5.4856e-13, 4.4201e-13, 5.2481e-13 );
		vec3 pos = vec3( 1.6810e+06, 1.7953e+06, 2.2084e+06 );
		vec3 var = vec3( 4.3278e+09, 9.3046e+09, 6.6121e+09 );
		vec3 xyz = val * sqrt( 2.0 * PI * var ) * cos( pos * phase + shift ) * exp( - pow2( phase ) * var );
		xyz.x += 9.7470e-14 * sqrt( 2.0 * PI * 4.5282e+09 ) * cos( 2.2399e+06 * phase + shift[ 0 ] ) * exp( - 4.5282e+09 * pow2( phase ) );
		xyz /= 1.0685e-7;
		vec3 rgb = XYZ_TO_REC709 * xyz;
		return rgb;
	}
	vec3 evalIridescence( float outsideIOR, float eta2, float cosTheta1, float thinFilmThickness, vec3 baseF0 ) {
		vec3 I;
		float iridescenceIOR = mix( outsideIOR, eta2, smoothstep( 0.0, 0.03, thinFilmThickness ) );
		float sinTheta2Sq = pow2( outsideIOR / iridescenceIOR ) * ( 1.0 - pow2( cosTheta1 ) );
		float cosTheta2Sq = 1.0 - sinTheta2Sq;
		if ( cosTheta2Sq < 0.0 ) {
			return vec3( 1.0 );
		}
		float cosTheta2 = sqrt( cosTheta2Sq );
		float R0 = IorToFresnel0( iridescenceIOR, outsideIOR );
		float R12 = F_Schlick( R0, 1.0, cosTheta1 );
		float T121 = 1.0 - R12;
		float phi12 = 0.0;
		if ( iridescenceIOR < outsideIOR ) phi12 = PI;
		float phi21 = PI - phi12;
		vec3 baseIOR = Fresnel0ToIor( clamp( baseF0, 0.0, 0.9999 ) );		vec3 R1 = IorToFresnel0( baseIOR, iridescenceIOR );
		vec3 R23 = F_Schlick( R1, 1.0, cosTheta2 );
		vec3 phi23 = vec3( 0.0 );
		if ( baseIOR[ 0 ] < iridescenceIOR ) phi23[ 0 ] = PI;
		if ( baseIOR[ 1 ] < iridescenceIOR ) phi23[ 1 ] = PI;
		if ( baseIOR[ 2 ] < iridescenceIOR ) phi23[ 2 ] = PI;
		float OPD = 2.0 * iridescenceIOR * thinFilmThickness * cosTheta2;
		vec3 phi = vec3( phi21 ) + phi23;
		vec3 R123 = clamp( R12 * R23, 1e-5, 0.9999 );
		vec3 r123 = sqrt( R123 );
		vec3 Rs = pow2( T121 ) * R23 / ( vec3( 1.0 ) - R123 );
		vec3 C0 = R12 + Rs;
		I = C0;
		vec3 Cm = Rs - T121;
		for ( int m = 1; m <= 2; ++ m ) {
			Cm *= r123;
			vec3 Sm = 2.0 * evalSensitivity( float( m ) * OPD, float( m ) * phi );
			I += Cm * Sm;
		}
		return max( I, vec3( 0.0 ) );
	}
#endif`,WM=`#ifdef USE_BUMPMAP
	uniform sampler2D bumpMap;
	uniform float bumpScale;
	vec2 dHdxy_fwd() {
		vec2 dSTdx = dFdx( vBumpMapUv );
		vec2 dSTdy = dFdy( vBumpMapUv );
		float Hll = bumpScale * texture2D( bumpMap, vBumpMapUv ).x;
		float dBx = bumpScale * texture2D( bumpMap, vBumpMapUv + dSTdx ).x - Hll;
		float dBy = bumpScale * texture2D( bumpMap, vBumpMapUv + dSTdy ).x - Hll;
		return vec2( dBx, dBy );
	}
	vec3 perturbNormalArb( vec3 surf_pos, vec3 surf_norm, vec2 dHdxy, float faceDirection ) {
		vec3 vSigmaX = normalize( dFdx( surf_pos.xyz ) );
		vec3 vSigmaY = normalize( dFdy( surf_pos.xyz ) );
		vec3 vN = surf_norm;
		vec3 R1 = cross( vSigmaY, vN );
		vec3 R2 = cross( vN, vSigmaX );
		float fDet = dot( vSigmaX, R1 ) * faceDirection;
		vec3 vGrad = sign( fDet ) * ( dHdxy.x * R1 + dHdxy.y * R2 );
		return normalize( abs( fDet ) * surf_norm - vGrad );
	}
#endif`,qM=`#if NUM_CLIPPING_PLANES > 0
	vec4 plane;
	#ifdef ALPHA_TO_COVERAGE
		float distanceToPlane, distanceGradient;
		float clipOpacity = 1.0;
		#pragma unroll_loop_start
		for ( int i = 0; i < UNION_CLIPPING_PLANES; i ++ ) {
			plane = clippingPlanes[ i ];
			distanceToPlane = - dot( vClipPosition, plane.xyz ) + plane.w;
			distanceGradient = fwidth( distanceToPlane ) / 2.0;
			clipOpacity *= smoothstep( - distanceGradient, distanceGradient, distanceToPlane );
			if ( clipOpacity == 0.0 ) discard;
		}
		#pragma unroll_loop_end
		#if UNION_CLIPPING_PLANES < NUM_CLIPPING_PLANES
			float unionClipOpacity = 1.0;
			#pragma unroll_loop_start
			for ( int i = UNION_CLIPPING_PLANES; i < NUM_CLIPPING_PLANES; i ++ ) {
				plane = clippingPlanes[ i ];
				distanceToPlane = - dot( vClipPosition, plane.xyz ) + plane.w;
				distanceGradient = fwidth( distanceToPlane ) / 2.0;
				unionClipOpacity *= 1.0 - smoothstep( - distanceGradient, distanceGradient, distanceToPlane );
			}
			#pragma unroll_loop_end
			clipOpacity *= 1.0 - unionClipOpacity;
		#endif
		diffuseColor.a *= clipOpacity;
		if ( diffuseColor.a == 0.0 ) discard;
	#else
		#pragma unroll_loop_start
		for ( int i = 0; i < UNION_CLIPPING_PLANES; i ++ ) {
			plane = clippingPlanes[ i ];
			if ( dot( vClipPosition, plane.xyz ) > plane.w ) discard;
		}
		#pragma unroll_loop_end
		#if UNION_CLIPPING_PLANES < NUM_CLIPPING_PLANES
			bool clipped = true;
			#pragma unroll_loop_start
			for ( int i = UNION_CLIPPING_PLANES; i < NUM_CLIPPING_PLANES; i ++ ) {
				plane = clippingPlanes[ i ];
				clipped = ( dot( vClipPosition, plane.xyz ) > plane.w ) && clipped;
			}
			#pragma unroll_loop_end
			if ( clipped ) discard;
		#endif
	#endif
#endif`,YM=`#if NUM_CLIPPING_PLANES > 0
	varying vec3 vClipPosition;
	uniform vec4 clippingPlanes[ NUM_CLIPPING_PLANES ];
#endif`,jM=`#if NUM_CLIPPING_PLANES > 0
	varying vec3 vClipPosition;
#endif`,ZM=`#if NUM_CLIPPING_PLANES > 0
	vClipPosition = - mvPosition.xyz;
#endif`,KM=`#if defined( USE_COLOR ) || defined( USE_COLOR_ALPHA )
	diffuseColor *= vColor;
#endif`,QM=`#if defined( USE_COLOR ) || defined( USE_COLOR_ALPHA )
	varying vec4 vColor;
#endif`,JM=`#if defined( USE_COLOR ) || defined( USE_COLOR_ALPHA ) || defined( USE_INSTANCING_COLOR ) || defined( USE_BATCHING_COLOR )
	varying vec4 vColor;
#endif`,$M=`#if defined( USE_COLOR ) || defined( USE_COLOR_ALPHA ) || defined( USE_INSTANCING_COLOR ) || defined( USE_BATCHING_COLOR )
	vColor = vec4( 1.0 );
#endif
#ifdef USE_COLOR_ALPHA
	vColor *= color;
#elif defined( USE_COLOR )
	vColor.rgb *= color;
#endif
#ifdef USE_INSTANCING_COLOR
	vColor.rgb *= instanceColor.rgb;
#endif
#ifdef USE_BATCHING_COLOR
	vColor *= getBatchingColor( getIndirectIndex( gl_DrawID ) );
#endif`,eE=`#define PI 3.141592653589793
#define PI2 6.283185307179586
#define PI_HALF 1.5707963267948966
#define RECIPROCAL_PI 0.3183098861837907
#define RECIPROCAL_PI2 0.15915494309189535
#define EPSILON 1e-6
#ifndef saturate
#define saturate( a ) clamp( a, 0.0, 1.0 )
#endif
#define whiteComplement( a ) ( 1.0 - saturate( a ) )
float pow2( const in float x ) { return x*x; }
vec3 pow2( const in vec3 x ) { return x*x; }
float pow3( const in float x ) { return x*x*x; }
float pow4( const in float x ) { float x2 = x*x; return x2*x2; }
float max3( const in vec3 v ) { return max( max( v.x, v.y ), v.z ); }
float average( const in vec3 v ) { return dot( v, vec3( 0.3333333 ) ); }
highp float rand( const in vec2 uv ) {
	const highp float a = 12.9898, b = 78.233, c = 43758.5453;
	highp float dt = dot( uv.xy, vec2( a,b ) ), sn = mod( dt, PI );
	return fract( sin( sn ) * c );
}
#ifdef HIGH_PRECISION
	float precisionSafeLength( vec3 v ) { return length( v ); }
#else
	float precisionSafeLength( vec3 v ) {
		float maxComponent = max3( abs( v ) );
		return length( v / maxComponent ) * maxComponent;
	}
#endif
struct IncidentLight {
	vec3 color;
	vec3 direction;
	bool visible;
};
struct ReflectedLight {
	vec3 directDiffuse;
	vec3 directSpecular;
	vec3 indirectDiffuse;
	vec3 indirectSpecular;
};
#ifdef USE_ALPHAHASH
	varying vec3 vPosition;
#endif
vec3 transformDirection( in vec3 dir, in mat4 matrix ) {
	return normalize( ( matrix * vec4( dir, 0.0 ) ).xyz );
}
#define inverseTransformDirection transformDirectionByInverseViewMatrix
vec3 transformNormalByInverseViewMatrix( in vec3 normal, in mat4 viewMatrix ) {
	return normalize( ( vec4( normal, 0.0 ) * viewMatrix ).xyz );
}
vec3 transformDirectionByInverseViewMatrix( in vec3 dir, in mat4 viewMatrix ) {
	return normalize( ( vec4( dir, 0.0 ) * viewMatrix ).xyz );
}
bool isPerspectiveMatrix( mat4 m ) {
	return m[ 2 ][ 3 ] == - 1.0;
}
vec2 equirectUv( in vec3 dir ) {
	float u = atan( dir.z, dir.x ) * RECIPROCAL_PI2 + 0.5;
	float v = asin( clamp( dir.y, - 1.0, 1.0 ) ) * RECIPROCAL_PI + 0.5;
	return vec2( u, v );
}
vec3 BRDF_Lambert( const in vec3 diffuseColor ) {
	return RECIPROCAL_PI * diffuseColor;
}
vec3 F_Schlick( const in vec3 f0, const in float f90, const in float dotVH ) {
	float fresnel = exp2( ( - 5.55473 * dotVH - 6.98316 ) * dotVH );
	return f0 * ( 1.0 - fresnel ) + ( f90 * fresnel );
}
float F_Schlick( const in float f0, const in float f90, const in float dotVH ) {
	float fresnel = exp2( ( - 5.55473 * dotVH - 6.98316 ) * dotVH );
	return f0 * ( 1.0 - fresnel ) + ( f90 * fresnel );
} // validated`,tE=`#ifdef ENVMAP_TYPE_CUBE_UV
	#define cubeUV_minMipLevel 4.0
	#define cubeUV_minTileSize 16.0
	float getFace( vec3 direction ) {
		vec3 absDirection = abs( direction );
		float face = - 1.0;
		if ( absDirection.x > absDirection.z ) {
			if ( absDirection.x > absDirection.y )
				face = direction.x > 0.0 ? 0.0 : 3.0;
			else
				face = direction.y > 0.0 ? 1.0 : 4.0;
		} else {
			if ( absDirection.z > absDirection.y )
				face = direction.z > 0.0 ? 2.0 : 5.0;
			else
				face = direction.y > 0.0 ? 1.0 : 4.0;
		}
		return face;
	}
	vec2 getUV( vec3 direction, float face ) {
		vec2 uv;
		if ( face == 0.0 ) {
			uv = vec2( direction.z, direction.y ) / abs( direction.x );
		} else if ( face == 1.0 ) {
			uv = vec2( - direction.x, - direction.z ) / abs( direction.y );
		} else if ( face == 2.0 ) {
			uv = vec2( - direction.x, direction.y ) / abs( direction.z );
		} else if ( face == 3.0 ) {
			uv = vec2( - direction.z, direction.y ) / abs( direction.x );
		} else if ( face == 4.0 ) {
			uv = vec2( - direction.x, direction.z ) / abs( direction.y );
		} else {
			uv = vec2( direction.x, direction.y ) / abs( direction.z );
		}
		return 0.5 * ( uv + 1.0 );
	}
	vec3 bilinearCubeUV( sampler2D envMap, vec3 direction, float mipInt ) {
		float face = getFace( direction );
		float filterInt = max( cubeUV_minMipLevel - mipInt, 0.0 );
		mipInt = max( mipInt, cubeUV_minMipLevel );
		float faceSize = exp2( mipInt );
		highp vec2 uv = getUV( direction, face ) * ( faceSize - 2.0 ) + 1.0;
		if ( face > 2.0 ) {
			uv.y += faceSize;
			face -= 3.0;
		}
		uv.x += face * faceSize;
		uv.x += filterInt * 3.0 * cubeUV_minTileSize;
		uv.y += 4.0 * ( exp2( CUBEUV_MAX_MIP ) - faceSize );
		uv.x *= CUBEUV_TEXEL_WIDTH;
		uv.y *= CUBEUV_TEXEL_HEIGHT;
		#ifdef texture2DGradEXT
			return texture2DGradEXT( envMap, uv, vec2( 0.0 ), vec2( 0.0 ) ).rgb;
		#else
			return texture2D( envMap, uv ).rgb;
		#endif
	}
	#define cubeUV_r0 1.0
	#define cubeUV_m0 - 2.0
	#define cubeUV_r1 0.8
	#define cubeUV_m1 - 1.0
	#define cubeUV_r4 0.4
	#define cubeUV_m4 2.0
	#define cubeUV_r5 0.305
	#define cubeUV_m5 3.0
	#define cubeUV_r6 0.21
	#define cubeUV_m6 4.0
	float roughnessToMip( float roughness ) {
		float mip = 0.0;
		if ( roughness >= cubeUV_r1 ) {
			mip = ( cubeUV_r0 - roughness ) * ( cubeUV_m1 - cubeUV_m0 ) / ( cubeUV_r0 - cubeUV_r1 ) + cubeUV_m0;
		} else if ( roughness >= cubeUV_r4 ) {
			mip = ( cubeUV_r1 - roughness ) * ( cubeUV_m4 - cubeUV_m1 ) / ( cubeUV_r1 - cubeUV_r4 ) + cubeUV_m1;
		} else if ( roughness >= cubeUV_r5 ) {
			mip = ( cubeUV_r4 - roughness ) * ( cubeUV_m5 - cubeUV_m4 ) / ( cubeUV_r4 - cubeUV_r5 ) + cubeUV_m4;
		} else if ( roughness >= cubeUV_r6 ) {
			mip = ( cubeUV_r5 - roughness ) * ( cubeUV_m6 - cubeUV_m5 ) / ( cubeUV_r5 - cubeUV_r6 ) + cubeUV_m5;
		} else {
			mip = - 2.0 * log2( 1.16 * roughness );		}
		return mip;
	}
	vec4 textureCubeUV( sampler2D envMap, vec3 sampleDir, float roughness ) {
		float mip = clamp( roughnessToMip( roughness ), cubeUV_m0, CUBEUV_MAX_MIP );
		float mipF = fract( mip );
		float mipInt = floor( mip );
		vec3 color0 = bilinearCubeUV( envMap, sampleDir, mipInt );
		if ( mipF == 0.0 ) {
			return vec4( color0, 1.0 );
		} else {
			vec3 color1 = bilinearCubeUV( envMap, sampleDir, mipInt + 1.0 );
			return vec4( mix( color0, color1, mipF ), 1.0 );
		}
	}
#endif`,nE=`vec3 transformedNormal = objectNormal;
#ifdef USE_TANGENT
	vec3 transformedTangent = objectTangent;
#endif
#ifdef USE_BATCHING
	mat3 bm = mat3( batchingMatrix );
	transformedNormal /= vec3( dot( bm[ 0 ], bm[ 0 ] ), dot( bm[ 1 ], bm[ 1 ] ), dot( bm[ 2 ], bm[ 2 ] ) );
	transformedNormal = bm * transformedNormal;
	#ifdef USE_TANGENT
		transformedTangent = bm * transformedTangent;
	#endif
#endif
#ifdef USE_INSTANCING
	mat3 im = mat3( instanceMatrix );
	transformedNormal /= vec3( dot( im[ 0 ], im[ 0 ] ), dot( im[ 1 ], im[ 1 ] ), dot( im[ 2 ], im[ 2 ] ) );
	transformedNormal = im * transformedNormal;
	#ifdef USE_TANGENT
		transformedTangent = im * transformedTangent;
	#endif
#endif
transformedNormal = normalMatrix * transformedNormal;
#ifdef FLIP_SIDED
	transformedNormal = - transformedNormal;
#endif
#ifdef USE_TANGENT
	transformedTangent = ( modelViewMatrix * vec4( transformedTangent, 0.0 ) ).xyz;
#endif`,iE=`#ifdef USE_DISPLACEMENTMAP
	uniform sampler2D displacementMap;
	uniform float displacementScale;
	uniform float displacementBias;
#endif`,aE=`#ifdef USE_DISPLACEMENTMAP
	transformed += normalize( objectNormal ) * ( texture2D( displacementMap, vDisplacementMapUv ).x * displacementScale + displacementBias );
#endif`,rE=`#ifdef USE_EMISSIVEMAP
	vec4 emissiveColor = texture2D( emissiveMap, vEmissiveMapUv );
	#ifdef DECODE_VIDEO_TEXTURE_EMISSIVE
		emissiveColor = sRGBTransferEOTF( emissiveColor );
	#endif
	totalEmissiveRadiance *= emissiveColor.rgb;
#endif`,sE=`#ifdef USE_EMISSIVEMAP
	uniform sampler2D emissiveMap;
#endif`,oE="gl_FragColor = linearToOutputTexel( gl_FragColor );",lE=`vec4 LinearTransferOETF( in vec4 value ) {
	return value;
}
vec4 sRGBTransferEOTF( in vec4 value ) {
	return vec4( mix( pow( value.rgb * 0.9478672986 + vec3( 0.0521327014 ), vec3( 2.4 ) ), value.rgb * 0.0773993808, vec3( lessThanEqual( value.rgb, vec3( 0.04045 ) ) ) ), value.a );
}
vec4 sRGBTransferOETF( in vec4 value ) {
	return vec4( mix( pow( value.rgb, vec3( 0.41666 ) ) * 1.055 - vec3( 0.055 ), value.rgb * 12.92, vec3( lessThanEqual( value.rgb, vec3( 0.0031308 ) ) ) ), value.a );
}`,cE=`#ifdef USE_ENVMAP
	#ifdef ENV_WORLDPOS
		vec3 cameraToFrag;
		if ( isOrthographic ) {
			cameraToFrag = normalize( vec3( - viewMatrix[ 0 ][ 2 ], - viewMatrix[ 1 ][ 2 ], - viewMatrix[ 2 ][ 2 ] ) );
		} else {
			cameraToFrag = normalize( vWorldPosition - cameraPosition );
		}
		vec3 worldNormal = transformNormalByInverseViewMatrix( normal, viewMatrix );
		#ifdef ENVMAP_MODE_REFLECTION
			vec3 reflectVec = reflect( cameraToFrag, worldNormal );
		#else
			vec3 reflectVec = refract( cameraToFrag, worldNormal, refractionRatio );
		#endif
	#else
		vec3 reflectVec = vReflect;
	#endif
	#ifdef ENVMAP_TYPE_CUBE
		vec4 envColor = textureCube( envMap, envMapRotation * reflectVec );
		#ifdef ENVMAP_BLENDING_MULTIPLY
			outgoingLight = mix( outgoingLight, outgoingLight * envColor.xyz, specularStrength * reflectivity );
		#elif defined( ENVMAP_BLENDING_MIX )
			outgoingLight = mix( outgoingLight, envColor.xyz, specularStrength * reflectivity );
		#elif defined( ENVMAP_BLENDING_ADD )
			outgoingLight += envColor.xyz * specularStrength * reflectivity;
		#endif
	#endif
#endif`,uE=`#ifdef USE_ENVMAP
	uniform float envMapIntensity;
	uniform mat3 envMapRotation;
	#ifdef ENVMAP_TYPE_CUBE
		uniform samplerCube envMap;
	#else
		uniform sampler2D envMap;
	#endif
#endif`,fE=`#ifdef USE_ENVMAP
	uniform float reflectivity;
	#if defined( USE_BUMPMAP ) || defined( USE_NORMALMAP ) || defined( PHONG ) || defined( LAMBERT )
		#define ENV_WORLDPOS
	#endif
	#ifdef ENV_WORLDPOS
		varying vec3 vWorldPosition;
		uniform float refractionRatio;
	#else
		varying vec3 vReflect;
	#endif
#endif`,dE=`#ifdef USE_ENVMAP
	#if defined( USE_BUMPMAP ) || defined( USE_NORMALMAP ) || defined( PHONG ) || defined( LAMBERT )
		#define ENV_WORLDPOS
	#endif
	#ifdef ENV_WORLDPOS
		
		varying vec3 vWorldPosition;
	#else
		varying vec3 vReflect;
		uniform float refractionRatio;
	#endif
#endif`,hE=`#ifdef USE_ENVMAP
	#ifdef ENV_WORLDPOS
		vWorldPosition = worldPosition.xyz;
	#else
		vec3 cameraToVertex;
		if ( isOrthographic ) {
			cameraToVertex = normalize( vec3( - viewMatrix[ 0 ][ 2 ], - viewMatrix[ 1 ][ 2 ], - viewMatrix[ 2 ][ 2 ] ) );
		} else {
			cameraToVertex = normalize( worldPosition.xyz - cameraPosition );
		}
		vec3 worldNormal = transformNormalByInverseViewMatrix( transformedNormal, viewMatrix );
		#ifdef ENVMAP_MODE_REFLECTION
			vReflect = reflect( cameraToVertex, worldNormal );
		#else
			vReflect = refract( cameraToVertex, worldNormal, refractionRatio );
		#endif
	#endif
#endif`,pE=`#ifdef USE_FOG
	vFogDepth = - mvPosition.z;
#endif`,mE=`#ifdef USE_FOG
	varying float vFogDepth;
#endif`,gE=`#ifdef USE_FOG
	#ifdef FOG_EXP2
		float fogFactor = 1.0 - exp( - fogDensity * fogDensity * vFogDepth * vFogDepth );
	#else
		float fogFactor = smoothstep( fogNear, fogFar, vFogDepth );
	#endif
	gl_FragColor.rgb = mix( gl_FragColor.rgb, fogColor, fogFactor );
#endif`,xE=`#ifdef USE_FOG
	uniform vec3 fogColor;
	varying float vFogDepth;
	#ifdef FOG_EXP2
		uniform float fogDensity;
	#else
		uniform float fogNear;
		uniform float fogFar;
	#endif
#endif`,vE=`#ifdef USE_GRADIENTMAP
	uniform sampler2D gradientMap;
#endif
vec3 getGradientIrradiance( vec3 normal, vec3 lightDirection ) {
	float dotNL = dot( normal, lightDirection );
	vec2 coord = vec2( dotNL * 0.5 + 0.5, 0.0 );
	#ifdef USE_GRADIENTMAP
		return vec3( texture2D( gradientMap, coord ).r );
	#else
		vec2 fw = fwidth( coord ) * 0.5;
		return mix( vec3( 0.7 ), vec3( 1.0 ), smoothstep( 0.7 - fw.x, 0.7 + fw.x, coord.x ) );
	#endif
}`,_E=`#ifdef USE_LIGHTMAP
	uniform sampler2D lightMap;
	uniform float lightMapIntensity;
#endif`,yE=`LambertMaterial material;
material.diffuseColor = diffuseColor.rgb;
material.specularStrength = specularStrength;`,SE=`varying vec3 vViewPosition;
struct LambertMaterial {
	vec3 diffuseColor;
	float specularStrength;
};
void RE_Direct_Lambert( const in IncidentLight directLight, const in vec3 geometryPosition, const in vec3 geometryNormal, const in vec3 geometryViewDir, const in vec3 geometryClearcoatNormal, const in LambertMaterial material, inout ReflectedLight reflectedLight ) {
	float dotNL = saturate( dot( geometryNormal, directLight.direction ) );
	vec3 irradiance = dotNL * directLight.color;
	reflectedLight.directDiffuse += irradiance * BRDF_Lambert( material.diffuseColor );
}
void RE_IndirectDiffuse_Lambert( const in vec3 irradiance, const in vec3 geometryPosition, const in vec3 geometryNormal, const in vec3 geometryViewDir, const in vec3 geometryClearcoatNormal, const in LambertMaterial material, inout ReflectedLight reflectedLight ) {
	reflectedLight.indirectDiffuse += irradiance * BRDF_Lambert( material.diffuseColor );
}
#define RE_Direct				RE_Direct_Lambert
#define RE_IndirectDiffuse		RE_IndirectDiffuse_Lambert`,bE=`uniform bool receiveShadow;
uniform vec3 ambientLightColor;
#if defined( USE_LIGHT_PROBES )
	uniform vec3 lightProbe[ 9 ];
#endif
vec3 shGetIrradianceAt( in vec3 normal, in vec3 shCoefficients[ 9 ] ) {
	float x = normal.x, y = normal.y, z = normal.z;
	vec3 result = shCoefficients[ 0 ] * 0.886227;
	result += shCoefficients[ 1 ] * 2.0 * 0.511664 * y;
	result += shCoefficients[ 2 ] * 2.0 * 0.511664 * z;
	result += shCoefficients[ 3 ] * 2.0 * 0.511664 * x;
	result += shCoefficients[ 4 ] * 2.0 * 0.429043 * x * y;
	result += shCoefficients[ 5 ] * 2.0 * 0.429043 * y * z;
	result += shCoefficients[ 6 ] * ( 0.743125 * z * z - 0.247708 );
	result += shCoefficients[ 7 ] * 2.0 * 0.429043 * x * z;
	result += shCoefficients[ 8 ] * 0.429043 * ( x * x - y * y );
	return result;
}
vec3 getLightProbeIrradiance( const in vec3 lightProbe[ 9 ], const in vec3 normal ) {
	vec3 worldNormal = transformNormalByInverseViewMatrix( normal, viewMatrix );
	vec3 irradiance = shGetIrradianceAt( worldNormal, lightProbe );
	return irradiance;
}
vec3 getAmbientLightIrradiance( const in vec3 ambientLightColor ) {
	vec3 irradiance = ambientLightColor;
	return irradiance;
}
float getDistanceAttenuation( const in float lightDistance, const in float cutoffDistance, const in float decayExponent ) {
	float distanceFalloff = 1.0 / max( pow( lightDistance, decayExponent ), 0.01 );
	if ( cutoffDistance > 0.0 ) {
		distanceFalloff *= pow2( saturate( 1.0 - pow4( lightDistance / cutoffDistance ) ) );
	}
	return distanceFalloff;
}
float getSpotAttenuation( const in float coneCosine, const in float penumbraCosine, const in float angleCosine ) {
	return smoothstep( coneCosine, penumbraCosine, angleCosine );
}
#if NUM_SUN_LIGHTS > 0
	struct SunLight {
		vec3 direction;
		vec3 color;
	};
	uniform SunLight sunLights[ NUM_SUN_LIGHTS ];
	void getSunLightInfo( const in SunLight sunLight, out IncidentLight light ) {
		light.color = sunLight.color;
		light.direction = sunLight.direction;
		light.visible = true;
	}
#endif
#if NUM_DIR_LIGHTS > 0
	struct DirectionalLight {
		vec3 direction;
		vec3 color;
	};
	uniform DirectionalLight directionalLights[ NUM_DIR_LIGHTS ];
	void getDirectionalLightInfo( const in DirectionalLight directionalLight, out IncidentLight light ) {
		light.color = directionalLight.color;
		light.direction = directionalLight.direction;
		light.visible = true;
	}
#endif
#if NUM_POINT_LIGHTS > 0
	struct PointLight {
		vec3 position;
		vec3 color;
		float distance;
		float decay;
	};
	uniform PointLight pointLights[ NUM_POINT_LIGHTS ];
	void getPointLightInfo( const in PointLight pointLight, const in vec3 geometryPosition, out IncidentLight light ) {
		vec3 lVector = pointLight.position - geometryPosition;
		light.direction = normalize( lVector );
		float lightDistance = length( lVector );
		light.color = pointLight.color;
		light.color *= getDistanceAttenuation( lightDistance, pointLight.distance, pointLight.decay );
		light.visible = ( light.color != vec3( 0.0 ) );
	}
#endif
#if NUM_SPOT_LIGHTS > 0
	struct SpotLight {
		vec3 position;
		vec3 direction;
		vec3 color;
		float distance;
		float decay;
		float coneCos;
		float penumbraCos;
	};
	uniform SpotLight spotLights[ NUM_SPOT_LIGHTS ];
	void getSpotLightInfo( const in SpotLight spotLight, const in vec3 geometryPosition, out IncidentLight light ) {
		vec3 lVector = spotLight.position - geometryPosition;
		light.direction = normalize( lVector );
		float angleCos = dot( light.direction, spotLight.direction );
		float spotAttenuation = getSpotAttenuation( spotLight.coneCos, spotLight.penumbraCos, angleCos );
		if ( spotAttenuation > 0.0 ) {
			float lightDistance = length( lVector );
			light.color = spotLight.color * spotAttenuation;
			light.color *= getDistanceAttenuation( lightDistance, spotLight.distance, spotLight.decay );
			light.visible = ( light.color != vec3( 0.0 ) );
		} else {
			light.color = vec3( 0.0 );
			light.visible = false;
		}
	}
#endif
#if NUM_RECT_AREA_LIGHTS > 0
	struct RectAreaLight {
		vec3 color;
		vec3 position;
		vec3 halfWidth;
		vec3 halfHeight;
	};
	uniform sampler2D ltc_1;	uniform sampler2D ltc_2;
	uniform RectAreaLight rectAreaLights[ NUM_RECT_AREA_LIGHTS ];
#endif
#if NUM_HEMI_LIGHTS > 0
	struct HemisphereLight {
		vec3 direction;
		vec3 skyColor;
		vec3 groundColor;
	};
	uniform HemisphereLight hemisphereLights[ NUM_HEMI_LIGHTS ];
	vec3 getHemisphereLightIrradiance( const in HemisphereLight hemiLight, const in vec3 normal ) {
		float dotNL = dot( normal, hemiLight.direction );
		float hemiDiffuseWeight = 0.5 * dotNL + 0.5;
		vec3 irradiance = mix( hemiLight.groundColor, hemiLight.skyColor, hemiDiffuseWeight );
		return irradiance;
	}
#endif
#include <lightprobes_pars_fragment>`,ME=`#ifdef USE_ENVMAP
	vec3 getIBLIrradiance( const in vec3 normal ) {
		#ifdef ENVMAP_TYPE_CUBE_UV
			vec3 worldNormal = transformNormalByInverseViewMatrix( normal, viewMatrix );
			vec4 envMapColor = textureCubeUV( envMap, envMapRotation * worldNormal, 1.0 );
			return PI * envMapColor.rgb * envMapIntensity;
		#else
			return vec3( 0.0 );
		#endif
	}
	vec3 getIBLRadiance( const in vec3 viewDir, const in vec3 normal, const in float roughness ) {
		#ifdef ENVMAP_TYPE_CUBE_UV
			vec3 reflectVec = reflect( - viewDir, normal );
			reflectVec = normalize( mix( reflectVec, normal, pow4( roughness ) ) );
			reflectVec = transformDirectionByInverseViewMatrix( reflectVec, viewMatrix );
			vec4 envMapColor = textureCubeUV( envMap, envMapRotation * reflectVec, roughness );
			return envMapColor.rgb * envMapIntensity;
		#else
			return vec3( 0.0 );
		#endif
	}
	#ifdef USE_RETROREFLECTION
		vec3 getIBLRetroRadiance( const in vec3 viewDir, const in vec3 normal, const in float roughness ) {
			#ifdef ENVMAP_TYPE_CUBE_UV
				vec3 retroVec = normalize( mix( viewDir, normal, pow4( roughness ) ) );
				retroVec = transformDirectionByInverseViewMatrix( retroVec, viewMatrix );
				vec4 envMapColor = textureCubeUV( envMap, envMapRotation * retroVec, roughness );
				return envMapColor.rgb * envMapIntensity;
			#else
				return vec3( 0.0 );
			#endif
		}
	#endif
	#ifdef USE_ANISOTROPY
		vec3 getIBLAnisotropyRadiance( const in vec3 viewDir, const in vec3 normal, const in float roughness, const in vec3 bitangent, const in float anisotropy ) {
			#ifdef ENVMAP_TYPE_CUBE_UV
				vec3 bentNormal = cross( bitangent, viewDir );
				bentNormal = normalize( cross( bentNormal, bitangent ) );
				bentNormal = normalize( mix( bentNormal, normal, pow2( pow2( 1.0 - anisotropy * ( 1.0 - roughness ) ) ) ) );
				return getIBLRadiance( viewDir, bentNormal, roughness );
			#else
				return vec3( 0.0 );
			#endif
		}
		#ifdef USE_RETROREFLECTION
			vec3 getIBLAnisotropyRetroRadiance( const in vec3 viewDir, const in vec3 normal, const in float roughness, const in vec3 bitangent, const in float anisotropy ) {
				#ifdef ENVMAP_TYPE_CUBE_UV
					vec3 bentNormal = cross( bitangent, viewDir );
					bentNormal = normalize( cross( bentNormal, bitangent ) );
					bentNormal = normalize( mix( bentNormal, normal, pow2( pow2( 1.0 - anisotropy * ( 1.0 - roughness ) ) ) ) );
					return getIBLRetroRadiance( viewDir, bentNormal, roughness );
				#else
					return vec3( 0.0 );
				#endif
			}
		#endif
	#endif
#endif`,EE=`ToonMaterial material;
material.diffuseColor = diffuseColor.rgb;`,TE=`varying vec3 vViewPosition;
struct ToonMaterial {
	vec3 diffuseColor;
};
void RE_Direct_Toon( const in IncidentLight directLight, const in vec3 geometryPosition, const in vec3 geometryNormal, const in vec3 geometryViewDir, const in vec3 geometryClearcoatNormal, const in ToonMaterial material, inout ReflectedLight reflectedLight ) {
	vec3 irradiance = getGradientIrradiance( geometryNormal, directLight.direction ) * directLight.color;
	reflectedLight.directDiffuse += irradiance * BRDF_Lambert( material.diffuseColor );
}
void RE_IndirectDiffuse_Toon( const in vec3 irradiance, const in vec3 geometryPosition, const in vec3 geometryNormal, const in vec3 geometryViewDir, const in vec3 geometryClearcoatNormal, const in ToonMaterial material, inout ReflectedLight reflectedLight ) {
	reflectedLight.indirectDiffuse += irradiance * BRDF_Lambert( material.diffuseColor );
}
#define RE_Direct				RE_Direct_Toon
#define RE_IndirectDiffuse		RE_IndirectDiffuse_Toon`,AE=`BlinnPhongMaterial material;
material.diffuseColor = diffuseColor.rgb;
material.specularColor = specular;
material.specularShininess = shininess;
material.specularStrength = specularStrength;`,wE=`varying vec3 vViewPosition;
struct BlinnPhongMaterial {
	vec3 diffuseColor;
	vec3 specularColor;
	float specularShininess;
	float specularStrength;
};
void RE_Direct_BlinnPhong( const in IncidentLight directLight, const in vec3 geometryPosition, const in vec3 geometryNormal, const in vec3 geometryViewDir, const in vec3 geometryClearcoatNormal, const in BlinnPhongMaterial material, inout ReflectedLight reflectedLight ) {
	float dotNL = saturate( dot( geometryNormal, directLight.direction ) );
	vec3 irradiance = dotNL * directLight.color;
	reflectedLight.directDiffuse += irradiance * BRDF_Lambert( material.diffuseColor );
	reflectedLight.directSpecular += irradiance * BRDF_BlinnPhong( directLight.direction, geometryViewDir, geometryNormal, material.specularColor, material.specularShininess ) * material.specularStrength;
}
void RE_IndirectDiffuse_BlinnPhong( const in vec3 irradiance, const in vec3 geometryPosition, const in vec3 geometryNormal, const in vec3 geometryViewDir, const in vec3 geometryClearcoatNormal, const in BlinnPhongMaterial material, inout ReflectedLight reflectedLight ) {
	reflectedLight.indirectDiffuse += irradiance * BRDF_Lambert( material.diffuseColor );
}
#define RE_Direct				RE_Direct_BlinnPhong
#define RE_IndirectDiffuse		RE_IndirectDiffuse_BlinnPhong`,CE=`PhysicalMaterial material;
material.diffuseColor = diffuseColor.rgb;
material.diffuseContribution = diffuseColor.rgb * ( 1.0 - metalnessFactor );
material.metalness = metalnessFactor;
vec3 dxy = max( abs( dFdx( nonPerturbedNormal ) ), abs( dFdy( nonPerturbedNormal ) ) );
float geometryRoughness = max( max( dxy.x, dxy.y ), dxy.z );
material.roughness = max( roughnessFactor, 0.0525 );material.roughness += geometryRoughness;
material.roughness = min( material.roughness, 1.0 );
#ifdef IOR
	material.ior = ior;
	#ifdef USE_SPECULAR
		float specularIntensityFactor = specularIntensity;
		vec3 specularColorFactor = specularColor;
		#ifdef USE_SPECULAR_COLORMAP
			specularColorFactor *= texture2D( specularColorMap, vSpecularColorMapUv ).rgb;
		#endif
		#ifdef USE_SPECULAR_INTENSITYMAP
			specularIntensityFactor *= texture2D( specularIntensityMap, vSpecularIntensityMapUv ).a;
		#endif
		material.specularF90 = mix( specularIntensityFactor, 1.0, metalnessFactor );
	#else
		float specularIntensityFactor = 1.0;
		vec3 specularColorFactor = vec3( 1.0 );
		material.specularF90 = 1.0;
	#endif
	material.specularColor = min( pow2( ( material.ior - 1.0 ) / ( material.ior + 1.0 ) ) * specularColorFactor, vec3( 1.0 ) ) * specularIntensityFactor;
	material.specularColorBlended = mix( material.specularColor, diffuseColor.rgb, metalnessFactor );
#else
	material.specularColor = vec3( 0.04 );
	material.specularColorBlended = mix( material.specularColor, diffuseColor.rgb, metalnessFactor );
	material.specularF90 = 1.0;
#endif
#ifdef USE_CLEARCOAT
	material.clearcoat = clearcoat;
	material.clearcoatRoughness = clearcoatRoughness;
	material.clearcoatF0 = vec3( 0.04 );
	material.clearcoatF90 = 1.0;
	#ifdef USE_CLEARCOATMAP
		material.clearcoat *= texture2D( clearcoatMap, vClearcoatMapUv ).x;
	#endif
	#ifdef USE_CLEARCOAT_ROUGHNESSMAP
		material.clearcoatRoughness *= texture2D( clearcoatRoughnessMap, vClearcoatRoughnessMapUv ).y;
	#endif
	material.clearcoat = saturate( material.clearcoat );	material.clearcoatRoughness = max( material.clearcoatRoughness, 0.0525 );
	material.clearcoatRoughness += geometryRoughness;
	material.clearcoatRoughness = min( material.clearcoatRoughness, 1.0 );
#endif
#ifdef USE_DISPERSION
	material.dispersion = dispersion;
#endif
#ifdef USE_RETROREFLECTION
	material.retroreflectivity = retroreflectivity;
#endif
#ifdef USE_IRIDESCENCE
	material.iridescence = iridescence;
	material.iridescenceIOR = iridescenceIOR;
	#ifdef USE_IRIDESCENCEMAP
		material.iridescence *= texture2D( iridescenceMap, vIridescenceMapUv ).r;
	#endif
	#ifdef USE_IRIDESCENCE_THICKNESSMAP
		material.iridescenceThickness = (iridescenceThicknessMaximum - iridescenceThicknessMinimum) * texture2D( iridescenceThicknessMap, vIridescenceThicknessMapUv ).g + iridescenceThicknessMinimum;
	#else
		material.iridescenceThickness = iridescenceThicknessMaximum;
	#endif
#endif
#ifdef USE_SHEEN
	material.sheenColor = sheenColor;
	#ifdef USE_SHEEN_COLORMAP
		material.sheenColor *= texture2D( sheenColorMap, vSheenColorMapUv ).rgb;
	#endif
	material.sheenRoughness = clamp( sheenRoughness, 0.0001, 1.0 );
	#ifdef USE_SHEEN_ROUGHNESSMAP
		material.sheenRoughness *= texture2D( sheenRoughnessMap, vSheenRoughnessMapUv ).a;
	#endif
#endif
#ifdef USE_ANISOTROPY
	#ifdef USE_ANISOTROPYMAP
		mat2 anisotropyMat = mat2( anisotropyVector.x, anisotropyVector.y, - anisotropyVector.y, anisotropyVector.x );
		vec3 anisotropyPolar = texture2D( anisotropyMap, vAnisotropyMapUv ).rgb;
		vec2 anisotropyV = anisotropyMat * normalize( 2.0 * anisotropyPolar.rg - vec2( 1.0 ) ) * anisotropyPolar.b;
	#else
		vec2 anisotropyV = anisotropyVector;
	#endif
	material.anisotropy = length( anisotropyV );
	if( material.anisotropy == 0.0 ) {
		anisotropyV = vec2( 1.0, 0.0 );
	} else {
		anisotropyV /= material.anisotropy;
		material.anisotropy = saturate( material.anisotropy );
	}
	material.alphaT = mix( pow2( material.roughness ), 1.0, pow2( material.anisotropy ) );
	material.anisotropyT = tbn[ 0 ] * anisotropyV.x + tbn[ 1 ] * anisotropyV.y;
	material.anisotropyB = tbn[ 1 ] * anisotropyV.x - tbn[ 0 ] * anisotropyV.y;
#endif`,RE=`uniform sampler2D dfgLUT;
struct PhysicalMaterial {
	vec3 diffuseColor;
	vec3 diffuseContribution;
	vec3 specularColor;
	vec3 specularColorBlended;
	float roughness;
	float metalness;
	float specularF90;
	float dispersion;
	vec2 dfg;
	vec3 multiScatteringCompensation;
	#ifdef USE_RETROREFLECTION
		float retroreflectivity;
	#endif
	#ifdef USE_CLEARCOAT
		float clearcoat;
		float clearcoatRoughness;
		vec3 clearcoatF0;
		float clearcoatF90;
	#endif
	#ifdef USE_IRIDESCENCE
		float iridescence;
		float iridescenceIOR;
		float iridescenceThickness;
		vec3 iridescenceFresnel;
		vec3 iridescenceF0Dielectric;
		vec3 iridescenceF0Metallic;
	#endif
	#ifdef USE_SHEEN
		vec3 sheenColor;
		float sheenRoughness;
	#endif
	#ifdef IOR
		float ior;
	#endif
	#ifdef USE_TRANSMISSION
		float transmission;
		float transmissionAlpha;
		float thickness;
		float attenuationDistance;
		vec3 attenuationColor;
	#endif
	#ifdef USE_ANISOTROPY
		float anisotropy;
		float alphaT;
		vec3 anisotropyT;
		vec3 anisotropyB;
	#endif
};
vec3 clearcoatSpecularDirect = vec3( 0.0 );
vec3 clearcoatSpecularIndirect = vec3( 0.0 );
vec3 sheenSpecularDirect = vec3( 0.0 );
vec3 sheenSpecularIndirect = vec3(0.0 );
vec3 Schlick_to_F0( const in vec3 f, const in float f90, const in float dotVH ) {
    float x = clamp( 1.0 - dotVH, 0.0, 1.0 );
    float x2 = x * x;
    float x5 = clamp( x * x2 * x2, 0.0, 0.9999 );
    return ( f - vec3( f90 ) * x5 ) / ( 1.0 - x5 );
}
float V_GGX_SmithCorrelated( const in float alpha, const in float dotNL, const in float dotNV ) {
	float a2 = pow2( alpha );
	float gv = dotNL * sqrt( a2 + ( 1.0 - a2 ) * pow2( dotNV ) );
	float gl = dotNV * sqrt( a2 + ( 1.0 - a2 ) * pow2( dotNL ) );
	return 0.5 / max( gv + gl, EPSILON );
}
float D_GGX( const in float alpha, const in float dotNH ) {
	float a2 = pow2( alpha );
	float denom = pow2( dotNH ) * ( a2 - 1.0 ) + 1.0;
	return RECIPROCAL_PI * a2 / pow2( denom );
}
#ifdef USE_ANISOTROPY
	float V_GGX_SmithCorrelated_Anisotropic( const in float alphaT, const in float alphaB, const in float dotTV, const in float dotBV, const in float dotTL, const in float dotBL, const in float dotNV, const in float dotNL ) {
		float gv = dotNL * length( vec3( alphaT * dotTV, alphaB * dotBV, dotNV ) );
		float gl = dotNV * length( vec3( alphaT * dotTL, alphaB * dotBL, dotNL ) );
		return 0.5 / max( gv + gl, EPSILON );
	}
	float D_GGX_Anisotropic( const in float alphaT, const in float alphaB, const in float dotNH, const in float dotTH, const in float dotBH ) {
		float a2 = alphaT * alphaB;
		highp vec3 v = vec3( alphaB * dotTH, alphaT * dotBH, a2 * dotNH );
		highp float v2 = dot( v, v );
		float w2 = a2 / v2;
		return RECIPROCAL_PI * a2 * pow2 ( w2 );
	}
#endif
#ifdef USE_CLEARCOAT
	vec3 BRDF_GGX_Clearcoat( const in vec3 lightDir, const in vec3 viewDir, const in vec3 normal, const in PhysicalMaterial material) {
		vec3 f0 = material.clearcoatF0;
		float f90 = material.clearcoatF90;
		float roughness = material.clearcoatRoughness;
		float alpha = pow2( roughness );
		vec3 halfDir = normalize( lightDir + viewDir );
		float dotNL = saturate( dot( normal, lightDir ) );
		float dotNV = saturate( dot( normal, viewDir ) );
		float dotNH = saturate( dot( normal, halfDir ) );
		float dotVH = saturate( dot( viewDir, halfDir ) );
		vec3 F = F_Schlick( f0, f90, dotVH );
		float V = V_GGX_SmithCorrelated( alpha, dotNL, dotNV );
		float D = D_GGX( alpha, dotNH );
		return F * ( V * D );
	}
#endif
vec3 BRDF_GGX( const in vec3 lightDir, const in vec3 viewDir, const in vec3 normal, const in PhysicalMaterial material ) {
	vec3 f0 = material.specularColorBlended;
	float f90 = material.specularF90;
	float roughness = material.roughness;
	float alpha = pow2( roughness );
	vec3 halfDir = normalize( lightDir + viewDir );
	float dotNL = saturate( dot( normal, lightDir ) );
	float dotNV = saturate( dot( normal, viewDir ) );
	float dotNH = saturate( dot( normal, halfDir ) );
	float dotVH = saturate( dot( viewDir, halfDir ) );
	vec3 F = F_Schlick( f0, f90, dotVH );
	#ifdef USE_IRIDESCENCE
		F = mix( F, material.iridescenceFresnel, material.iridescence );
	#endif
	#ifdef USE_ANISOTROPY
		float dotTL = dot( material.anisotropyT, lightDir );
		float dotTV = dot( material.anisotropyT, viewDir );
		float dotTH = dot( material.anisotropyT, halfDir );
		float dotBL = dot( material.anisotropyB, lightDir );
		float dotBV = dot( material.anisotropyB, viewDir );
		float dotBH = dot( material.anisotropyB, halfDir );
		float V = V_GGX_SmithCorrelated_Anisotropic( material.alphaT, alpha, dotTV, dotBV, dotTL, dotBL, dotNV, dotNL );
		float D = D_GGX_Anisotropic( material.alphaT, alpha, dotNH, dotTH, dotBH );
	#else
		float V = V_GGX_SmithCorrelated( alpha, dotNL, dotNV );
		float D = D_GGX( alpha, dotNH );
	#endif
	return F * ( V * D );
}
vec2 LTC_Uv( const in vec3 N, const in vec3 V, const in float roughness ) {
	const float LUT_SIZE = 64.0;
	const float LUT_SCALE = ( LUT_SIZE - 1.0 ) / LUT_SIZE;
	const float LUT_BIAS = 0.5 / LUT_SIZE;
	float dotNV = saturate( dot( N, V ) );
	vec2 uv = vec2( roughness, sqrt( 1.0 - dotNV ) );
	uv = uv * LUT_SCALE + LUT_BIAS;
	return uv;
}
float LTC_ClippedSphereFormFactor( const in vec3 f ) {
	float l = length( f );
	return max( ( l * l + f.z ) / ( l + 1.0 ), 0.0 );
}
vec3 LTC_EdgeVectorFormFactor( const in vec3 v1, const in vec3 v2 ) {
	float x = dot( v1, v2 );
	float y = abs( x );
	float a = 0.8543985 + ( 0.4965155 + 0.0145206 * y ) * y;
	float b = 3.4175940 + ( 4.1616724 + y ) * y;
	float v = a / b;
	float theta_sintheta = ( x > 0.0 ) ? v : 0.5 * inversesqrt( max( 1.0 - x * x, 1e-7 ) ) - v;
	return cross( v1, v2 ) * theta_sintheta;
}
vec3 LTC_Evaluate( const in vec3 N, const in vec3 V, const in vec3 P, const in mat3 mInv, const in vec3 rectCoords[ 4 ] ) {
	vec3 v1 = rectCoords[ 1 ] - rectCoords[ 0 ];
	vec3 v2 = rectCoords[ 3 ] - rectCoords[ 0 ];
	vec3 lightNormal = cross( v1, v2 );
	if( dot( lightNormal, P - rectCoords[ 0 ] ) < 0.0 ) return vec3( 0.0 );
	vec3 T1, T2;
	T1 = normalize( V - N * dot( V, N ) );
	T2 = - cross( N, T1 );
	mat3 mat = mInv * transpose( mat3( T1, T2, N ) );
	vec3 coords[ 4 ];
	coords[ 0 ] = mat * ( rectCoords[ 0 ] - P );
	coords[ 1 ] = mat * ( rectCoords[ 1 ] - P );
	coords[ 2 ] = mat * ( rectCoords[ 2 ] - P );
	coords[ 3 ] = mat * ( rectCoords[ 3 ] - P );
	coords[ 0 ] = normalize( coords[ 0 ] );
	coords[ 1 ] = normalize( coords[ 1 ] );
	coords[ 2 ] = normalize( coords[ 2 ] );
	coords[ 3 ] = normalize( coords[ 3 ] );
	vec3 vectorFormFactor = vec3( 0.0 );
	vectorFormFactor += LTC_EdgeVectorFormFactor( coords[ 0 ], coords[ 1 ] );
	vectorFormFactor += LTC_EdgeVectorFormFactor( coords[ 1 ], coords[ 2 ] );
	vectorFormFactor += LTC_EdgeVectorFormFactor( coords[ 2 ], coords[ 3 ] );
	vectorFormFactor += LTC_EdgeVectorFormFactor( coords[ 3 ], coords[ 0 ] );
	float result = LTC_ClippedSphereFormFactor( vectorFormFactor );
	return vec3( result );
}
#if defined( USE_SHEEN )
float D_Charlie( float roughness, float dotNH ) {
	float alpha = pow2( roughness );
	float invAlpha = 1.0 / alpha;
	float cos2h = dotNH * dotNH;
	float sin2h = max( 1.0 - cos2h, 0.0078125 );
	return ( 2.0 + invAlpha ) * pow( sin2h, invAlpha * 0.5 ) / ( 2.0 * PI );
}
float V_Neubelt( float dotNV, float dotNL ) {
	return saturate( 1.0 / ( 4.0 * ( dotNL + dotNV - dotNL * dotNV ) ) );
}
vec3 BRDF_Sheen( const in vec3 lightDir, const in vec3 viewDir, const in vec3 normal, vec3 sheenColor, const in float sheenRoughness ) {
	vec3 halfDir = normalize( lightDir + viewDir );
	float dotNL = saturate( dot( normal, lightDir ) );
	float dotNV = saturate( dot( normal, viewDir ) );
	float dotNH = saturate( dot( normal, halfDir ) );
	float D = D_Charlie( sheenRoughness, dotNH );
	float V = V_Neubelt( dotNV, dotNL );
	return sheenColor * ( D * V );
}
#endif
float IBLSheenBRDF( const in vec3 normal, const in vec3 viewDir, const in float roughness ) {
	float dotNV = saturate( dot( normal, viewDir ) );
	float r2 = roughness * roughness;
	float rInv = 1.0 / ( roughness + 0.1 );
	float a = -1.9362 + 1.0678 * roughness + 0.4573 * r2 - 0.8469 * rInv;
	float b = -0.6014 + 0.5538 * roughness - 0.4670 * r2 - 0.1255 * rInv;
	float DG = exp( a * dotNV + b );
	return saturate( DG );
}
vec3 EnvironmentBRDF( const in vec3 normal, const in vec3 viewDir, const in vec3 specularColor, const in float specularF90, const in float roughness ) {
	float dotNV = saturate( dot( normal, viewDir ) );
	vec2 fab = texture2D( dfgLUT, vec2( roughness, dotNV ) ).rg;
	return specularColor * fab.x + specularF90 * fab.y;
}
#ifdef USE_IRIDESCENCE
void computeMultiscatteringIridescence( const in vec2 fab, const in vec3 specularColor, const in float specularF90, const in float iridescence, const in vec3 iridescenceF0, inout vec3 singleScatter, inout vec3 multiScatter ) {
#else
void computeMultiscattering( const in vec2 fab, const in vec3 specularColor, const in float specularF90, inout vec3 singleScatter, inout vec3 multiScatter ) {
#endif
	#ifdef USE_IRIDESCENCE
		vec3 Fr = mix( specularColor, iridescenceF0, iridescence );
	#else
		vec3 Fr = specularColor;
	#endif
	vec3 FssEss = Fr * fab.x + specularF90 * fab.y;
	float Ess = fab.x + fab.y;
	float Ems = 1.0 - Ess;
	vec3 Favg = Fr + ( 1.0 - Fr ) * 0.047619;	vec3 Fms = FssEss * Favg / ( 1.0 - Ems * Favg );
	singleScatter += FssEss;
	multiScatter += Fms * Ems;
}
#if NUM_RECT_AREA_LIGHTS > 0
	void RE_Direct_RectArea_Physical( const in RectAreaLight rectAreaLight, const in vec3 geometryPosition, const in vec3 geometryNormal, const in vec3 geometryViewDir, const in vec3 geometryClearcoatNormal, const in PhysicalMaterial material, inout ReflectedLight reflectedLight ) {
		vec3 normal = geometryNormal;
		vec3 viewDir = geometryViewDir;
		vec3 position = geometryPosition;
		vec3 lightPos = rectAreaLight.position;
		vec3 halfWidth = rectAreaLight.halfWidth;
		vec3 halfHeight = rectAreaLight.halfHeight;
		vec3 lightColor = rectAreaLight.color;
		float roughness = material.roughness;
		vec3 rectCoords[ 4 ];
		rectCoords[ 0 ] = lightPos + halfWidth - halfHeight;		rectCoords[ 1 ] = lightPos - halfWidth - halfHeight;
		rectCoords[ 2 ] = lightPos - halfWidth + halfHeight;
		rectCoords[ 3 ] = lightPos + halfWidth + halfHeight;
		vec2 uv = LTC_Uv( normal, viewDir, roughness );
		vec4 t1 = texture2D( ltc_1, uv );
		vec4 t2 = texture2D( ltc_2, uv );
		mat3 mInv = mat3(
			vec3( t1.x, 0, t1.y ),
			vec3(    0, 1,    0 ),
			vec3( t1.z, 0, t1.w )
		);
		vec3 fresnel = ( material.specularColorBlended * t2.x + ( material.specularF90 - material.specularColorBlended ) * t2.y );
		reflectedLight.directSpecular += lightColor * fresnel * LTC_Evaluate( normal, viewDir, position, mInv, rectCoords );
		reflectedLight.directDiffuse += lightColor * material.diffuseContribution * LTC_Evaluate( normal, viewDir, position, mat3( 1.0 ), rectCoords );
		#ifdef USE_CLEARCOAT
			vec3 Ncc = geometryClearcoatNormal;
			vec2 uvClearcoat = LTC_Uv( Ncc, viewDir, material.clearcoatRoughness );
			vec4 t1Clearcoat = texture2D( ltc_1, uvClearcoat );
			vec4 t2Clearcoat = texture2D( ltc_2, uvClearcoat );
			mat3 mInvClearcoat = mat3(
				vec3( t1Clearcoat.x, 0, t1Clearcoat.y ),
				vec3(             0, 1,             0 ),
				vec3( t1Clearcoat.z, 0, t1Clearcoat.w )
			);
			vec3 fresnelClearcoat = material.clearcoatF0 * t2Clearcoat.x + ( material.clearcoatF90 - material.clearcoatF0 ) * t2Clearcoat.y;
			clearcoatSpecularDirect += lightColor * fresnelClearcoat * LTC_Evaluate( Ncc, viewDir, position, mInvClearcoat, rectCoords );
		#endif
	}
#endif
void RE_Direct_Physical( const in IncidentLight directLight, const in vec3 geometryPosition, const in vec3 geometryNormal, const in vec3 geometryViewDir, const in vec3 geometryClearcoatNormal, const in PhysicalMaterial material, inout ReflectedLight reflectedLight ) {
	float dotNL = saturate( dot( geometryNormal, directLight.direction ) );
	vec3 irradiance = dotNL * directLight.color;
	#ifdef USE_CLEARCOAT
		float dotNLcc = saturate( dot( geometryClearcoatNormal, directLight.direction ) );
		vec3 ccIrradiance = dotNLcc * directLight.color;
		clearcoatSpecularDirect += ccIrradiance * BRDF_GGX_Clearcoat( directLight.direction, geometryViewDir, geometryClearcoatNormal, material );
	#endif
	#ifdef USE_SHEEN
 
 		sheenSpecularDirect += irradiance * BRDF_Sheen( directLight.direction, geometryViewDir, geometryNormal, material.sheenColor, material.sheenRoughness );
 
 		float sheenAlbedoV = IBLSheenBRDF( geometryNormal, geometryViewDir, material.sheenRoughness );
 		float sheenAlbedoL = IBLSheenBRDF( geometryNormal, directLight.direction, material.sheenRoughness );
 
 		float sheenEnergyComp = 1.0 - max3( material.sheenColor ) * max( sheenAlbedoV, sheenAlbedoL );
 
 		irradiance *= sheenEnergyComp;
 
 	#endif
	vec3 specularBRDF = BRDF_GGX( directLight.direction, geometryViewDir, geometryNormal, material );
	#ifdef USE_RETROREFLECTION
		vec3 retroViewDir = reflect( - geometryViewDir, geometryNormal );
		vec3 retroSpecularBRDF = BRDF_GGX( directLight.direction, retroViewDir, geometryNormal, material );
		specularBRDF = mix( specularBRDF, retroSpecularBRDF, saturate( material.retroreflectivity ) );
	#endif
	reflectedLight.directSpecular += irradiance * specularBRDF * material.multiScatteringCompensation;
	vec3 halfDir = normalize( directLight.direction + geometryViewDir );
	float dotVH = saturate( dot( geometryViewDir, halfDir ) );
	vec3 F = F_Schlick( material.specularColor, material.specularF90, dotVH );
	#ifdef USE_RETROREFLECTION
		vec3 retroHalfDir = normalize( directLight.direction + retroViewDir );
		float dotRetroVH = saturate( dot( retroViewDir, retroHalfDir ) );
		vec3 retroF = F_Schlick( material.specularColor, material.specularF90, dotRetroVH );
		F = mix( F, retroF, saturate( material.retroreflectivity ) );
	#endif
	reflectedLight.directDiffuse += irradiance * BRDF_Lambert( material.diffuseContribution ) * ( 1.0 - F );
}
void RE_IndirectDiffuse_Physical( const in vec3 irradiance, const in vec3 geometryPosition, const in vec3 geometryNormal, const in vec3 geometryViewDir, const in vec3 geometryClearcoatNormal, const in PhysicalMaterial material, inout ReflectedLight reflectedLight ) {
	vec3 singleScattering = vec3( 0.0 );
	vec3 multiScattering = vec3( 0.0 );
	#ifdef USE_IRIDESCENCE
		computeMultiscatteringIridescence( material.dfg, material.specularColor, material.specularF90, material.iridescence, material.iridescenceF0Dielectric, singleScattering, multiScattering );
	#else
		computeMultiscattering( material.dfg, material.specularColor, material.specularF90, singleScattering, multiScattering );
	#endif
	vec3 diffuse = irradiance * BRDF_Lambert( material.diffuseContribution ) * ( 1.0 - singleScattering - multiScattering );
	#ifdef USE_SHEEN
		float sheenAlbedo = IBLSheenBRDF( geometryNormal, geometryViewDir, material.sheenRoughness );
		sheenSpecularIndirect += irradiance * material.sheenColor * sheenAlbedo * RECIPROCAL_PI;
		float sheenEnergyComp = 1.0 - max3( material.sheenColor ) * sheenAlbedo;
		diffuse *= sheenEnergyComp;
	#endif
	reflectedLight.indirectDiffuse += diffuse;
}
void RE_IndirectSpecular_Physical( const in vec3 radiance, const in vec3 irradiance, const in vec3 clearcoatRadiance, const in vec3 geometryPosition, const in vec3 geometryNormal, const in vec3 geometryViewDir, const in vec3 geometryClearcoatNormal, const in PhysicalMaterial material, inout ReflectedLight reflectedLight) {
	#ifdef USE_CLEARCOAT
		clearcoatSpecularIndirect += clearcoatRadiance * EnvironmentBRDF( geometryClearcoatNormal, geometryViewDir, material.clearcoatF0, material.clearcoatF90, material.clearcoatRoughness );
	#endif
	#ifdef USE_SHEEN
		sheenSpecularIndirect += irradiance * material.sheenColor * IBLSheenBRDF( geometryNormal, geometryViewDir, material.sheenRoughness ) * RECIPROCAL_PI;
 	#endif
	vec3 singleScatteringDielectric = vec3( 0.0 );
	vec3 multiScatteringDielectric = vec3( 0.0 );
	vec3 singleScatteringMetallic = vec3( 0.0 );
	vec3 multiScatteringMetallic = vec3( 0.0 );
	#ifdef USE_IRIDESCENCE
		computeMultiscatteringIridescence( material.dfg, material.specularColor, material.specularF90, material.iridescence, material.iridescenceF0Dielectric, singleScatteringDielectric, multiScatteringDielectric );
		computeMultiscatteringIridescence( material.dfg, material.diffuseColor, material.specularF90, material.iridescence, material.iridescenceF0Metallic, singleScatteringMetallic, multiScatteringMetallic );
	#else
		computeMultiscattering( material.dfg, material.specularColor, material.specularF90, singleScatteringDielectric, multiScatteringDielectric );
		computeMultiscattering( material.dfg, material.diffuseColor, material.specularF90, singleScatteringMetallic, multiScatteringMetallic );
	#endif
	vec3 singleScattering = mix( singleScatteringDielectric, singleScatteringMetallic, material.metalness );
	vec3 multiScattering = mix( multiScatteringDielectric, multiScatteringMetallic, material.metalness );
	vec3 totalScatteringDielectric = singleScatteringDielectric + multiScatteringDielectric;
	vec3 diffuse = material.diffuseContribution * ( 1.0 - totalScatteringDielectric );
	vec3 cosineWeightedIrradiance = irradiance * RECIPROCAL_PI;
	vec3 indirectSpecular = radiance * singleScattering;
	indirectSpecular += multiScattering * cosineWeightedIrradiance;
	vec3 indirectDiffuse = diffuse * cosineWeightedIrradiance;
	#ifdef USE_SHEEN
		float sheenAlbedo = IBLSheenBRDF( geometryNormal, geometryViewDir, material.sheenRoughness );
		float sheenEnergyComp = 1.0 - max3( material.sheenColor ) * sheenAlbedo;
		indirectSpecular *= sheenEnergyComp;
		indirectDiffuse *= sheenEnergyComp;
	#endif
	reflectedLight.indirectSpecular += indirectSpecular;
	reflectedLight.indirectDiffuse += indirectDiffuse;
}
#define RE_Direct				RE_Direct_Physical
#define RE_Direct_RectArea		RE_Direct_RectArea_Physical
#define RE_IndirectDiffuse		RE_IndirectDiffuse_Physical
#define RE_IndirectSpecular		RE_IndirectSpecular_Physical
float computeSpecularOcclusion( const in float dotNV, const in float ambientOcclusion, const in float roughness ) {
	return saturate( pow( dotNV + ambientOcclusion, exp2( - 16.0 * roughness - 1.0 ) ) - 1.0 + ambientOcclusion );
}`,UE=`
vec3 geometryPosition = - vViewPosition;
vec3 geometryNormal = normal;
vec3 geometryViewDir = ( isOrthographic ) ? vec3( 0, 0, 1 ) : normalize( vViewPosition );
vec3 geometryClearcoatNormal = vec3( 0.0 );
#ifdef USE_CLEARCOAT
	geometryClearcoatNormal = clearcoatNormal;
#endif
#ifdef USE_IRIDESCENCE
	float dotNVi = saturate( dot( normal, geometryViewDir ) );
	if ( material.iridescenceThickness == 0.0 ) {
		material.iridescence = 0.0;
	} else {
		material.iridescence = saturate( material.iridescence );
	}
	if ( material.iridescence > 0.0 ) {
		vec3 iridescenceFresnelDielectric = evalIridescence( 1.0, material.iridescenceIOR, dotNVi, material.iridescenceThickness, material.specularColor );
		vec3 iridescenceFresnelMetallic = evalIridescence( 1.0, material.iridescenceIOR, dotNVi, material.iridescenceThickness, material.diffuseColor );
		material.iridescenceFresnel = mix( iridescenceFresnelDielectric, iridescenceFresnelMetallic, material.metalness );
		material.iridescenceF0Dielectric = Schlick_to_F0( iridescenceFresnelDielectric, 1.0, dotNVi );
		material.iridescenceF0Metallic = Schlick_to_F0( iridescenceFresnelMetallic, 1.0, dotNVi );
	}
#endif
#ifdef STANDARD
	float dotNVms = saturate( dot( geometryNormal, geometryViewDir ) );
	material.dfg = texture2D( dfgLUT, vec2( material.roughness, dotNVms ) ).rg;
	#if ( NUM_SUN_LIGHTS > 0 || NUM_DIR_LIGHTS > 0 || NUM_POINT_LIGHTS > 0 || NUM_SPOT_LIGHTS > 0 )
		float EssMs = material.dfg.x + material.dfg.y;
		material.multiScatteringCompensation = 1.0 + material.specularColorBlended * ( 1.0 / EssMs - 1.0 );
	#endif
#endif
IncidentLight directLight;
#if ( NUM_POINT_LIGHTS > 0 ) && defined( RE_Direct )
	PointLight pointLight;
	#if defined( USE_SHADOWMAP ) && NUM_POINT_LIGHT_SHADOWS > 0
	PointLightShadow pointLightShadow;
	#endif
	#pragma unroll_loop_start
	for ( int i = 0; i < NUM_POINT_LIGHTS; i ++ ) {
		pointLight = pointLights[ i ];
		getPointLightInfo( pointLight, geometryPosition, directLight );
		#if defined( USE_SHADOWMAP ) && ( UNROLLED_LOOP_INDEX < NUM_POINT_LIGHT_SHADOWS ) && ( defined( SHADOWMAP_TYPE_PCF ) || defined( SHADOWMAP_TYPE_BASIC ) )
		pointLightShadow = pointLightShadows[ i ];
		directLight.color *= ( directLight.visible && receiveShadow ) ? getPointShadow( pointShadowMap[ i ], pointLightShadow.shadowMapSize, pointLightShadow.shadowIntensity, pointLightShadow.shadowBias, pointLightShadow.shadowRadius, vPointShadowCoord[ i ], pointLightShadow.shadowCameraNear, pointLightShadow.shadowCameraFar ) : 1.0;
		#endif
		RE_Direct( directLight, geometryPosition, geometryNormal, geometryViewDir, geometryClearcoatNormal, material, reflectedLight );
	}
	#pragma unroll_loop_end
#endif
#if ( NUM_SPOT_LIGHTS > 0 ) && defined( RE_Direct )
	SpotLight spotLight;
	vec4 spotColor;
	vec3 spotLightCoord;
	bool inSpotLightMap;
	#if defined( USE_SHADOWMAP ) && NUM_SPOT_LIGHT_SHADOWS > 0
	SpotLightShadow spotLightShadow;
	#endif
	#pragma unroll_loop_start
	for ( int i = 0; i < NUM_SPOT_LIGHTS; i ++ ) {
		spotLight = spotLights[ i ];
		getSpotLightInfo( spotLight, geometryPosition, directLight );
		#if ( UNROLLED_LOOP_INDEX < NUM_SPOT_LIGHT_SHADOWS_WITH_MAPS )
		#define SPOT_LIGHT_MAP_INDEX UNROLLED_LOOP_INDEX
		#elif ( UNROLLED_LOOP_INDEX < NUM_SPOT_LIGHT_SHADOWS )
		#define SPOT_LIGHT_MAP_INDEX NUM_SPOT_LIGHT_MAPS
		#else
		#define SPOT_LIGHT_MAP_INDEX ( UNROLLED_LOOP_INDEX - NUM_SPOT_LIGHT_SHADOWS + NUM_SPOT_LIGHT_SHADOWS_WITH_MAPS )
		#endif
		#if ( SPOT_LIGHT_MAP_INDEX < NUM_SPOT_LIGHT_MAPS )
			spotLightCoord = vSpotLightCoord[ i ].xyz / vSpotLightCoord[ i ].w;
			inSpotLightMap = all( lessThan( abs( spotLightCoord * 2. - 1. ), vec3( 1.0 ) ) );
			spotColor = texture2D( spotLightMap[ SPOT_LIGHT_MAP_INDEX ], spotLightCoord.xy );
			directLight.color = inSpotLightMap ? directLight.color * spotColor.rgb : directLight.color;
		#endif
		#undef SPOT_LIGHT_MAP_INDEX
		#if defined( USE_SHADOWMAP ) && ( UNROLLED_LOOP_INDEX < NUM_SPOT_LIGHT_SHADOWS )
		spotLightShadow = spotLightShadows[ i ];
		directLight.color *= ( directLight.visible && receiveShadow ) ? getShadow( spotShadowMap[ i ], spotLightShadow.shadowMapSize, spotLightShadow.shadowIntensity, spotLightShadow.shadowBias, spotLightShadow.shadowRadius, vSpotLightCoord[ i ] ) : 1.0;
		#endif
		RE_Direct( directLight, geometryPosition, geometryNormal, geometryViewDir, geometryClearcoatNormal, material, reflectedLight );
	}
	#pragma unroll_loop_end
#endif
#if ( NUM_SUN_LIGHTS > 0 ) && defined( RE_Direct )
	SunLight sunLight;
	#if defined( USE_SHADOWMAP ) && NUM_SUN_LIGHT_SHADOWS > 0
	SunLightShadow sunLightShadow;
	#endif
	#pragma unroll_loop_start
	for ( int i = 0; i < NUM_SUN_LIGHTS; i ++ ) {
		sunLight = sunLights[ i ];
		getSunLightInfo( sunLight, directLight );
		#if defined( USE_SHADOWMAP ) && ( UNROLLED_LOOP_INDEX < NUM_SUN_LIGHT_SHADOWS )
		sunLightShadow = sunLightShadows[ i ];
		directLight.color *= ( directLight.visible && receiveShadow ) ? getSunShadow( sunShadowMap[ i ], sunLightShadow, UNROLLED_LOOP_INDEX ) : 1.0;
		#endif
		RE_Direct( directLight, geometryPosition, geometryNormal, geometryViewDir, geometryClearcoatNormal, material, reflectedLight );
	}
	#pragma unroll_loop_end
#endif
#if ( NUM_DIR_LIGHTS > 0 ) && defined( RE_Direct )
	DirectionalLight directionalLight;
	#if defined( USE_SHADOWMAP ) && NUM_DIR_LIGHT_SHADOWS > 0
	DirectionalLightShadow directionalLightShadow;
	#endif
	#pragma unroll_loop_start
	for ( int i = 0; i < NUM_DIR_LIGHTS; i ++ ) {
		directionalLight = directionalLights[ i ];
		getDirectionalLightInfo( directionalLight, directLight );
		#if defined( USE_SHADOWMAP ) && ( UNROLLED_LOOP_INDEX < NUM_DIR_LIGHT_SHADOWS )
		directionalLightShadow = directionalLightShadows[ i ];
		directLight.color *= ( directLight.visible && receiveShadow ) ? getShadow( directionalShadowMap[ i ], directionalLightShadow.shadowMapSize, directionalLightShadow.shadowIntensity, directionalLightShadow.shadowBias, directionalLightShadow.shadowRadius, vDirectionalShadowCoord[ i ] ) : 1.0;
		#endif
		RE_Direct( directLight, geometryPosition, geometryNormal, geometryViewDir, geometryClearcoatNormal, material, reflectedLight );
	}
	#pragma unroll_loop_end
#endif
#if ( NUM_RECT_AREA_LIGHTS > 0 ) && defined( RE_Direct_RectArea )
	RectAreaLight rectAreaLight;
	#pragma unroll_loop_start
	for ( int i = 0; i < NUM_RECT_AREA_LIGHTS; i ++ ) {
		rectAreaLight = rectAreaLights[ i ];
		RE_Direct_RectArea( rectAreaLight, geometryPosition, geometryNormal, geometryViewDir, geometryClearcoatNormal, material, reflectedLight );
	}
	#pragma unroll_loop_end
#endif
#if defined( RE_IndirectDiffuse )
	vec3 iblIrradiance = vec3( 0.0 );
	vec3 irradiance = getAmbientLightIrradiance( ambientLightColor );
	#if defined( USE_LIGHT_PROBES )
		irradiance += getLightProbeIrradiance( lightProbe, geometryNormal );
	#endif
	#if ( NUM_HEMI_LIGHTS > 0 )
		#pragma unroll_loop_start
		for ( int i = 0; i < NUM_HEMI_LIGHTS; i ++ ) {
			irradiance += getHemisphereLightIrradiance( hemisphereLights[ i ], geometryNormal );
		}
		#pragma unroll_loop_end
	#endif
	#ifdef USE_LIGHT_PROBES_GRID
		vec3 probeWorldPos = ( ( vec4( geometryPosition, 1.0 ) - viewMatrix[ 3 ] ) * viewMatrix ).xyz;
		vec3 probeWorldNormal = transformNormalByInverseViewMatrix( geometryNormal, viewMatrix );
		irradiance += getLightProbeGridIrradiance( probeWorldPos, probeWorldNormal );
	#endif
#endif
#if defined( RE_IndirectSpecular )
	vec3 radiance = vec3( 0.0 );
	vec3 clearcoatRadiance = vec3( 0.0 );
#endif`,DE=`#if defined( RE_IndirectDiffuse )
	#ifdef USE_LIGHTMAP
		vec4 lightMapTexel = texture2D( lightMap, vLightMapUv );
		vec3 lightMapIrradiance = lightMapTexel.rgb * lightMapIntensity;
		irradiance += lightMapIrradiance;
	#endif
	#if defined( USE_ENVMAP ) && defined( ENVMAP_TYPE_CUBE_UV )
		#if defined( STANDARD ) || defined( LAMBERT ) || defined( PHONG )
			iblIrradiance += getIBLIrradiance( geometryNormal );
		#endif
	#endif
#endif
#if defined( USE_ENVMAP ) && defined( RE_IndirectSpecular )
	#ifdef USE_ANISOTROPY
		vec3 iblRadiance = getIBLAnisotropyRadiance( geometryViewDir, geometryNormal, material.roughness, material.anisotropyB, material.anisotropy );
	#else
		vec3 iblRadiance = getIBLRadiance( geometryViewDir, geometryNormal, material.roughness );
	#endif
	#ifdef USE_RETROREFLECTION
		#ifdef USE_ANISOTROPY
			vec3 retroIBLRadiance = getIBLAnisotropyRetroRadiance( geometryViewDir, geometryNormal, material.roughness, material.anisotropyB, material.anisotropy );
		#else
			vec3 retroIBLRadiance = getIBLRetroRadiance( geometryViewDir, geometryNormal, material.roughness );
		#endif
		iblRadiance = mix( iblRadiance, retroIBLRadiance, saturate( material.retroreflectivity ) );
	#endif
	radiance += iblRadiance;
	#ifdef USE_CLEARCOAT
		clearcoatRadiance += getIBLRadiance( geometryViewDir, geometryClearcoatNormal, material.clearcoatRoughness );
	#endif
#endif`,NE=`#if defined( RE_IndirectDiffuse )
	#if defined( LAMBERT ) || defined( PHONG )
		irradiance += iblIrradiance;
	#endif
	RE_IndirectDiffuse( irradiance, geometryPosition, geometryNormal, geometryViewDir, geometryClearcoatNormal, material, reflectedLight );
#endif
#if defined( RE_IndirectSpecular )
	RE_IndirectSpecular( radiance, iblIrradiance, clearcoatRadiance, geometryPosition, geometryNormal, geometryViewDir, geometryClearcoatNormal, material, reflectedLight );
#endif`,LE=`#ifdef USE_LIGHT_PROBES_GRID
uniform highp sampler3D probesSH;
uniform vec3 probesMin;
uniform vec3 probesMax;
uniform vec3 probesResolution;
vec3 getLightProbeGridIrradiance( vec3 worldPos, vec3 worldNormal ) {
	vec3 res = probesResolution;
	vec3 gridRange = probesMax - probesMin;
	vec3 resMinusOne = res - 1.0;
	vec3 probeSpacing = gridRange / resMinusOne;
	vec3 samplePos = worldPos + worldNormal * probeSpacing * 0.5;
	vec3 uvw = clamp( ( samplePos - probesMin ) / gridRange, 0.0, 1.0 );
	uvw = uvw * resMinusOne / res + 0.5 / res;
	float nz          = res.z;
	float paddedSlices = nz + 2.0;
	float atlasDepth  = 7.0 * paddedSlices;
	float uvZBase     = uvw.z * nz + 1.0;
	vec4 s0 = texture( probesSH, vec3( uvw.xy, ( uvZBase                       ) / atlasDepth ) );
	vec4 s1 = texture( probesSH, vec3( uvw.xy, ( uvZBase +       paddedSlices   ) / atlasDepth ) );
	vec4 s2 = texture( probesSH, vec3( uvw.xy, ( uvZBase + 2.0 * paddedSlices   ) / atlasDepth ) );
	vec4 s3 = texture( probesSH, vec3( uvw.xy, ( uvZBase + 3.0 * paddedSlices   ) / atlasDepth ) );
	vec4 s4 = texture( probesSH, vec3( uvw.xy, ( uvZBase + 4.0 * paddedSlices   ) / atlasDepth ) );
	vec4 s5 = texture( probesSH, vec3( uvw.xy, ( uvZBase + 5.0 * paddedSlices   ) / atlasDepth ) );
	vec4 s6 = texture( probesSH, vec3( uvw.xy, ( uvZBase + 6.0 * paddedSlices   ) / atlasDepth ) );
	vec3 c0 = s0.xyz;
	vec3 c1 = vec3( s0.w, s1.xy );
	vec3 c2 = vec3( s1.zw, s2.x );
	vec3 c3 = s2.yzw;
	vec3 c4 = s3.xyz;
	vec3 c5 = vec3( s3.w, s4.xy );
	vec3 c6 = vec3( s4.zw, s5.x );
	vec3 c7 = s5.yzw;
	vec3 c8 = s6.xyz;
	float x = worldNormal.x, y = worldNormal.y, z = worldNormal.z;
	vec3 result = c0 * 0.886227;
	result += c1 * 2.0 * 0.511664 * y;
	result += c2 * 2.0 * 0.511664 * z;
	result += c3 * 2.0 * 0.511664 * x;
	result += c4 * 2.0 * 0.429043 * x * y;
	result += c5 * 2.0 * 0.429043 * y * z;
	result += c6 * ( 0.743125 * z * z - 0.247708 );
	result += c7 * 2.0 * 0.429043 * x * z;
	result += c8 * 0.429043 * ( x * x - y * y );
	return max( result, vec3( 0.0 ) );
}
#endif`,OE=`#if defined( USE_LOGARITHMIC_DEPTH_BUFFER )
	gl_FragDepth = vIsPerspective == 0.0 ? gl_FragCoord.z : log2( vFragDepth ) * logDepthBufFC * 0.5;
#endif`,PE=`#if defined( USE_LOGARITHMIC_DEPTH_BUFFER )
	uniform float logDepthBufFC;
	varying float vFragDepth;
	varying float vIsPerspective;
#endif`,zE=`#ifdef USE_LOGARITHMIC_DEPTH_BUFFER
	varying float vFragDepth;
	varying float vIsPerspective;
#endif`,FE=`#ifdef USE_LOGARITHMIC_DEPTH_BUFFER
	vFragDepth = 1.0 + gl_Position.w;
	vIsPerspective = float( isPerspectiveMatrix( projectionMatrix ) );
#endif`,BE=`#ifdef USE_MAP
	vec4 sampledDiffuseColor = texture2D( map, vMapUv );
	#ifdef DECODE_VIDEO_TEXTURE
		sampledDiffuseColor = sRGBTransferEOTF( sampledDiffuseColor );
	#endif
	diffuseColor *= sampledDiffuseColor;
#endif`,IE=`#ifdef USE_MAP
	uniform sampler2D map;
#endif`,HE=`#if defined( USE_MAP ) || defined( USE_ALPHAMAP )
	#if defined( USE_POINTS_UV )
		vec2 uv = vUv;
	#else
		vec2 uv = ( uvTransform * vec3( gl_PointCoord.x, 1.0 - gl_PointCoord.y, 1 ) ).xy;
	#endif
#endif
#ifdef USE_MAP
	diffuseColor *= texture2D( map, uv );
#endif
#ifdef USE_ALPHAMAP
	diffuseColor.a *= texture2D( alphaMap, uv ).g;
#endif`,GE=`#if defined( USE_POINTS_UV )
	varying vec2 vUv;
#else
	#if defined( USE_MAP ) || defined( USE_ALPHAMAP )
		uniform mat3 uvTransform;
	#endif
#endif
#ifdef USE_MAP
	uniform sampler2D map;
#endif
#ifdef USE_ALPHAMAP
	uniform sampler2D alphaMap;
#endif`,VE=`float metalnessFactor = metalness;
#ifdef USE_METALNESSMAP
	vec4 texelMetalness = texture2D( metalnessMap, vMetalnessMapUv );
	metalnessFactor *= texelMetalness.b;
#endif`,kE=`#ifdef USE_METALNESSMAP
	uniform sampler2D metalnessMap;
#endif`,XE=`#ifdef USE_INSTANCING_MORPH
	float morphTargetInfluences[ MORPHTARGETS_COUNT ];
	float morphTargetBaseInfluence = texelFetch( morphTexture, ivec2( 0, gl_InstanceID ), 0 ).r;
	for ( int i = 0; i < MORPHTARGETS_COUNT; i ++ ) {
		morphTargetInfluences[i] =  texelFetch( morphTexture, ivec2( i + 1, gl_InstanceID ), 0 ).r;
	}
#endif`,WE=`#if defined( USE_MORPHCOLORS )
	vColor *= morphTargetBaseInfluence;
	for ( int i = 0; i < MORPHTARGETS_COUNT; i ++ ) {
		#if defined( USE_COLOR_ALPHA )
			if ( morphTargetInfluences[ i ] != 0.0 ) vColor += getMorph( gl_VertexID, i, 2 ) * morphTargetInfluences[ i ];
		#elif defined( USE_COLOR )
			if ( morphTargetInfluences[ i ] != 0.0 ) vColor += getMorph( gl_VertexID, i, 2 ).rgb * morphTargetInfluences[ i ];
		#endif
	}
#endif`,qE=`#ifdef USE_MORPHNORMALS
	objectNormal *= morphTargetBaseInfluence;
	for ( int i = 0; i < MORPHTARGETS_COUNT; i ++ ) {
		if ( morphTargetInfluences[ i ] != 0.0 ) objectNormal += getMorph( gl_VertexID, i, 1 ).xyz * morphTargetInfluences[ i ];
	}
#endif`,YE=`#ifdef USE_MORPHTARGETS
	#ifndef USE_INSTANCING_MORPH
		uniform float morphTargetBaseInfluence;
		uniform float morphTargetInfluences[ MORPHTARGETS_COUNT ];
	#endif
	uniform sampler2DArray morphTargetsTexture;
	uniform ivec2 morphTargetsTextureSize;
	vec4 getMorph( const in int vertexIndex, const in int morphTargetIndex, const in int offset ) {
		int texelIndex = vertexIndex * MORPHTARGETS_TEXTURE_STRIDE + offset;
		int y = texelIndex / morphTargetsTextureSize.x;
		int x = texelIndex - y * morphTargetsTextureSize.x;
		ivec3 morphUV = ivec3( x, y, morphTargetIndex );
		return texelFetch( morphTargetsTexture, morphUV, 0 );
	}
#endif`,jE=`#ifdef USE_MORPHTARGETS
	transformed *= morphTargetBaseInfluence;
	for ( int i = 0; i < MORPHTARGETS_COUNT; i ++ ) {
		if ( morphTargetInfluences[ i ] != 0.0 ) transformed += getMorph( gl_VertexID, i, 0 ).xyz * morphTargetInfluences[ i ];
	}
#endif`,ZE=`float faceDirection = gl_FrontFacing ? 1.0 : - 1.0;
#ifdef FLAT_SHADED
	vec3 fdx = dFdx( vViewPosition );
	vec3 fdy = dFdy( vViewPosition );
	vec3 normal = normalize( cross( fdx, fdy ) );
#else
	vec3 normal = normalize( vNormal );
	#ifdef DOUBLE_SIDED
		normal *= faceDirection;
	#endif
#endif
#if defined( USE_NORMALMAP_TANGENTSPACE ) || defined( USE_CLEARCOAT_NORMALMAP ) || defined( USE_ANISOTROPY )
	#ifdef USE_TANGENT
		mat3 tbn = mat3( normalize( vTangent ), normalize( vBitangent ), normal );
	#else
		mat3 tbn = getTangentFrame( - vViewPosition, normal,
		#if defined( USE_NORMALMAP )
			vNormalMapUv
		#elif defined( USE_CLEARCOAT_NORMALMAP )
			vClearcoatNormalMapUv
		#else
			vUv
		#endif
		);
	#endif
	#ifdef DOUBLE_SIDED
		tbn[0] *= faceDirection;
		tbn[1] *= faceDirection;
	#endif
#endif
#ifdef USE_CLEARCOAT_NORMALMAP
	#ifdef USE_TANGENT
		mat3 tbn2 = mat3( normalize( vTangent ), normalize( vBitangent ), normal );
	#else
		mat3 tbn2 = getTangentFrame( - vViewPosition, normal, vClearcoatNormalMapUv );
	#endif
	#ifdef DOUBLE_SIDED
		tbn2[0] *= faceDirection;
		tbn2[1] *= faceDirection;
	#endif
#endif
vec3 nonPerturbedNormal = normal;`,KE=`#ifdef USE_NORMALMAP_OBJECTSPACE
	normal = texture2D( normalMap, vNormalMapUv ).xyz * 2.0 - 1.0;
	#ifdef FLIP_SIDED
		normal = - normal;
	#endif
	#ifdef DOUBLE_SIDED
		normal = normal * faceDirection;
	#endif
	normal = normalize( normalMatrix * normal );
#elif defined( USE_NORMALMAP_TANGENTSPACE )
	vec3 mapN = texture2D( normalMap, vNormalMapUv ).xyz * 2.0 - 1.0;
	#if defined( USE_PACKED_NORMALMAP )
		mapN = vec3( mapN.xy, sqrt( saturate( 1.0 - dot( mapN.xy, mapN.xy ) ) ) );
	#endif
	mapN.xy *= normalScale;
	normal = normalize( tbn * mapN );
#elif defined( USE_BUMPMAP )
	normal = perturbNormalArb( - vViewPosition, normal, dHdxy_fwd(), faceDirection );
#endif`,QE=`#ifndef FLAT_SHADED
	varying vec3 vNormal;
	#ifdef USE_TANGENT
		varying vec3 vTangent;
		varying vec3 vBitangent;
	#endif
#endif`,JE=`#ifndef FLAT_SHADED
	varying vec3 vNormal;
	#ifdef USE_TANGENT
		varying vec3 vTangent;
		varying vec3 vBitangent;
	#endif
#endif`,$E=`#ifndef FLAT_SHADED
	vNormal = normalize( transformedNormal );
	#ifdef USE_TANGENT
		vTangent = normalize( transformedTangent );
		vBitangent = normalize( cross( vNormal, vTangent ) * tangent.w );
		#ifdef FLIP_SIDED
			vBitangent = - vBitangent;
		#endif
	#endif
#endif`,eT=`#ifdef USE_NORMALMAP
	uniform sampler2D normalMap;
	uniform vec2 normalScale;
#endif
#ifdef USE_NORMALMAP_OBJECTSPACE
	uniform mat3 normalMatrix;
#endif
#if ! defined ( USE_TANGENT ) && ( defined ( USE_NORMALMAP_TANGENTSPACE ) || defined ( USE_CLEARCOAT_NORMALMAP ) || defined( USE_ANISOTROPY ) )
	mat3 getTangentFrame( vec3 eye_pos, vec3 surf_norm, vec2 uv ) {
		vec3 q0 = dFdx( eye_pos.xyz );
		vec3 q1 = dFdy( eye_pos.xyz );
		vec2 st0 = dFdx( uv.st );
		vec2 st1 = dFdy( uv.st );
		vec3 N = surf_norm;
		vec3 q1perp = cross( q1, N );
		vec3 q0perp = cross( N, q0 );
		vec3 T = q1perp * st0.x + q0perp * st1.x;
		vec3 B = q1perp * st0.y + q0perp * st1.y;
		float det = max( dot( T, T ), dot( B, B ) );
		float scale = ( det == 0.0 ) ? 0.0 : inversesqrt( det );
		return mat3( T * scale, B * scale, N );
	}
#endif`,tT=`#ifdef USE_CLEARCOAT
	vec3 clearcoatNormal = nonPerturbedNormal;
#endif`,nT=`#ifdef USE_CLEARCOAT_NORMALMAP
	vec3 clearcoatMapN = texture2D( clearcoatNormalMap, vClearcoatNormalMapUv ).xyz * 2.0 - 1.0;
	clearcoatMapN.xy *= clearcoatNormalScale;
	clearcoatNormal = normalize( tbn2 * clearcoatMapN );
#endif`,iT=`#ifdef USE_CLEARCOATMAP
	uniform sampler2D clearcoatMap;
#endif
#ifdef USE_CLEARCOAT_NORMALMAP
	uniform sampler2D clearcoatNormalMap;
	uniform vec2 clearcoatNormalScale;
#endif
#ifdef USE_CLEARCOAT_ROUGHNESSMAP
	uniform sampler2D clearcoatRoughnessMap;
#endif`,aT=`#ifdef USE_IRIDESCENCEMAP
	uniform sampler2D iridescenceMap;
#endif
#ifdef USE_IRIDESCENCE_THICKNESSMAP
	uniform sampler2D iridescenceThicknessMap;
#endif`,rT=`#ifdef OPAQUE
diffuseColor.a = 1.0;
#endif
#ifdef USE_TRANSMISSION
diffuseColor.a *= material.transmissionAlpha;
#endif
gl_FragColor = vec4( outgoingLight, diffuseColor.a );`,sT=`vec3 packNormalToRGB( const in vec3 normal ) {
	return normalize( normal ) * 0.5 + 0.5;
}
vec3 unpackRGBToNormal( const in vec3 rgb ) {
	return 2.0 * rgb.xyz - 1.0;
}
const float PackUpscale = 256. / 255.;const float UnpackDownscale = 255. / 256.;const float ShiftRight8 = 1. / 256.;
const float Inv255 = 1. / 255.;
const vec4 PackFactors = vec4( 1.0, 256.0, 256.0 * 256.0, 256.0 * 256.0 * 256.0 );
const vec2 UnpackFactors2 = vec2( UnpackDownscale, 1.0 / PackFactors.g );
const vec3 UnpackFactors3 = vec3( UnpackDownscale / PackFactors.rg, 1.0 / PackFactors.b );
const vec4 UnpackFactors4 = vec4( UnpackDownscale / PackFactors.rgb, 1.0 / PackFactors.a );
vec4 packDepthToRGBA( const in float v ) {
	if( v <= 0.0 )
		return vec4( 0., 0., 0., 0. );
	if( v >= 1.0 )
		return vec4( 1., 1., 1., 1. );
	float vuf;
	float af = modf( v * PackFactors.a, vuf );
	float bf = modf( vuf * ShiftRight8, vuf );
	float gf = modf( vuf * ShiftRight8, vuf );
	return vec4( vuf * Inv255, gf * PackUpscale, bf * PackUpscale, af );
}
vec3 packDepthToRGB( const in float v ) {
	if( v <= 0.0 )
		return vec3( 0., 0., 0. );
	if( v >= 1.0 )
		return vec3( 1., 1., 1. );
	float vuf;
	float bf = modf( v * PackFactors.b, vuf );
	float gf = modf( vuf * ShiftRight8, vuf );
	return vec3( vuf * Inv255, gf * PackUpscale, bf );
}
vec2 packDepthToRG( const in float v ) {
	if( v <= 0.0 )
		return vec2( 0., 0. );
	if( v >= 1.0 )
		return vec2( 1., 1. );
	float vuf;
	float gf = modf( v * 256., vuf );
	return vec2( vuf * Inv255, gf );
}
float unpackRGBAToDepth( const in vec4 v ) {
	return dot( v, UnpackFactors4 );
}
float unpackRGBToDepth( const in vec3 v ) {
	return dot( v, UnpackFactors3 );
}
float unpackRGToDepth( const in vec2 v ) {
	return v.r * UnpackFactors2.r + v.g * UnpackFactors2.g;
}
vec4 pack2HalfToRGBA( const in vec2 v ) {
	vec4 r = vec4( v.x, fract( v.x * 255.0 ), v.y, fract( v.y * 255.0 ) );
	return vec4( r.x - r.y / 255.0, r.y, r.z - r.w / 255.0, r.w );
}
vec2 unpackRGBATo2Half( const in vec4 v ) {
	return vec2( v.x + ( v.y / 255.0 ), v.z + ( v.w / 255.0 ) );
}
float viewZToOrthographicDepth( const in float viewZ, const in float near, const in float far ) {
	return ( viewZ + near ) / ( near - far );
}
float orthographicDepthToViewZ( const in float depth, const in float near, const in float far ) {
	#ifdef USE_REVERSED_DEPTH_BUFFER
	
		return depth * ( far - near ) - far;
	#else
		return depth * ( near - far ) - near;
	#endif
}
float viewZToPerspectiveDepth( const in float viewZ, const in float near, const in float far ) {
	return ( ( near + viewZ ) * far ) / ( ( far - near ) * viewZ );
}
float perspectiveDepthToViewZ( const in float depth, const in float near, const in float far ) {
	
	#ifdef USE_REVERSED_DEPTH_BUFFER
		return ( near * far ) / ( ( near - far ) * depth - near );
	#else
		return ( near * far ) / ( ( far - near ) * depth - far );
	#endif
}`,oT=`#ifdef PREMULTIPLIED_ALPHA
	gl_FragColor.rgb *= gl_FragColor.a;
#endif`,lT=`vec4 mvPosition = vec4( transformed, 1.0 );
#ifdef USE_BATCHING
	mvPosition = batchingMatrix * mvPosition;
#endif
#ifdef USE_INSTANCING
	mvPosition = instanceMatrix * mvPosition;
#endif
mvPosition = modelViewMatrix * mvPosition;
gl_Position = projectionMatrix * mvPosition;`,cT=`#ifdef DITHERING
	gl_FragColor.rgb = dithering( gl_FragColor.rgb );
#endif`,uT=`#ifdef DITHERING
	vec3 dithering( vec3 color ) {
		float grid_position = rand( gl_FragCoord.xy );
		vec3 dither_shift_RGB = vec3( 0.25 / 255.0, -0.25 / 255.0, 0.25 / 255.0 );
		dither_shift_RGB = mix( 2.0 * dither_shift_RGB, -2.0 * dither_shift_RGB, grid_position );
		return color + dither_shift_RGB;
	}
#endif`,fT=`float roughnessFactor = roughness;
#ifdef USE_ROUGHNESSMAP
	vec4 texelRoughness = texture2D( roughnessMap, vRoughnessMapUv );
	roughnessFactor *= texelRoughness.g;
#endif`,dT=`#ifdef USE_ROUGHNESSMAP
	uniform sampler2D roughnessMap;
#endif`,hT=`#if NUM_SPOT_LIGHT_COORDS > 0
	varying vec4 vSpotLightCoord[ NUM_SPOT_LIGHT_COORDS ];
#endif
#if NUM_SPOT_LIGHT_MAPS > 0
	uniform sampler2D spotLightMap[ NUM_SPOT_LIGHT_MAPS ];
#endif
#ifdef USE_SHADOWMAP
	#if NUM_SUN_LIGHT_SHADOWS > 0
		#define SUN_LIGHT_CASCADES 2
		#if defined( SHADOWMAP_TYPE_PCF )
			uniform sampler2DShadow sunShadowMap[ NUM_SUN_LIGHT_SHADOWS ];
		#else
			uniform sampler2D sunShadowMap[ NUM_SUN_LIGHT_SHADOWS ];
		#endif
		uniform mat4 sunShadowMatrix[ NUM_SUN_LIGHT_SHADOWS * SUN_LIGHT_CASCADES ];
		uniform vec4 sunShadowCascade[ NUM_SUN_LIGHT_SHADOWS * SUN_LIGHT_CASCADES ];
		varying vec4 vSunShadowWorldPosition;
		varying vec3 vSunShadowWorldNormal;
		struct SunLightShadow {
			float shadowIntensity;
			float shadowBias;
			float shadowNormalBias;
			float shadowRadius;
			vec2 shadowMapSize;
		};
		uniform SunLightShadow sunLightShadows[ NUM_SUN_LIGHT_SHADOWS ];
	#endif
	#if NUM_DIR_LIGHT_SHADOWS > 0
		#if defined( SHADOWMAP_TYPE_PCF )
			uniform sampler2DShadow directionalShadowMap[ NUM_DIR_LIGHT_SHADOWS ];
		#else
			uniform sampler2D directionalShadowMap[ NUM_DIR_LIGHT_SHADOWS ];
		#endif
		varying vec4 vDirectionalShadowCoord[ NUM_DIR_LIGHT_SHADOWS ];
		struct DirectionalLightShadow {
			float shadowIntensity;
			float shadowBias;
			float shadowNormalBias;
			float shadowRadius;
			vec2 shadowMapSize;
		};
		uniform DirectionalLightShadow directionalLightShadows[ NUM_DIR_LIGHT_SHADOWS ];
	#endif
	#if NUM_SPOT_LIGHT_SHADOWS > 0
		#if defined( SHADOWMAP_TYPE_PCF )
			uniform sampler2DShadow spotShadowMap[ NUM_SPOT_LIGHT_SHADOWS ];
		#else
			uniform sampler2D spotShadowMap[ NUM_SPOT_LIGHT_SHADOWS ];
		#endif
		struct SpotLightShadow {
			float shadowIntensity;
			float shadowBias;
			float shadowNormalBias;
			float shadowRadius;
			vec2 shadowMapSize;
		};
		uniform SpotLightShadow spotLightShadows[ NUM_SPOT_LIGHT_SHADOWS ];
	#endif
	#if NUM_POINT_LIGHT_SHADOWS > 0
		#if defined( SHADOWMAP_TYPE_PCF )
			uniform samplerCubeShadow pointShadowMap[ NUM_POINT_LIGHT_SHADOWS ];
		#elif defined( SHADOWMAP_TYPE_BASIC )
			uniform samplerCube pointShadowMap[ NUM_POINT_LIGHT_SHADOWS ];
		#endif
		varying vec4 vPointShadowCoord[ NUM_POINT_LIGHT_SHADOWS ];
		struct PointLightShadow {
			float shadowIntensity;
			float shadowBias;
			float shadowNormalBias;
			float shadowRadius;
			vec2 shadowMapSize;
			float shadowCameraNear;
			float shadowCameraFar;
		};
		uniform PointLightShadow pointLightShadows[ NUM_POINT_LIGHT_SHADOWS ];
	#endif
	#if defined( SHADOWMAP_TYPE_PCF )
		float interleavedGradientNoise( vec2 position ) {
			return fract( 52.9829189 * fract( dot( position, vec2( 0.06711056, 0.00583715 ) ) ) );
		}
		vec2 vogelDiskSample( int sampleIndex, int samplesCount, float phi ) {
			const float goldenAngle = 2.399963229728653;
			float r = sqrt( ( float( sampleIndex ) + 0.5 ) / float( samplesCount ) );
			float theta = float( sampleIndex ) * goldenAngle + phi;
			return vec2( cos( theta ), sin( theta ) ) * r;
		}
	#endif
	#if defined( SHADOWMAP_TYPE_PCF )
		float getShadow( sampler2DShadow shadowMap, vec2 shadowMapSize, float shadowIntensity, float shadowBias, float shadowRadius, vec4 shadowCoord ) {
			float shadow = 1.0;
			shadowCoord.xyz /= shadowCoord.w;
			shadowCoord.z += shadowBias;
			bool inFrustum = shadowCoord.x >= 0.0 && shadowCoord.x <= 1.0 && shadowCoord.y >= 0.0 && shadowCoord.y <= 1.0;
			bool frustumTest = inFrustum && shadowCoord.z <= 1.0;
			if ( frustumTest ) {
				vec2 texelSize = vec2( 1.0 ) / shadowMapSize;
				float radius = shadowRadius * texelSize.x;
				float phi = interleavedGradientNoise( gl_FragCoord.xy ) * PI2;
				shadow = (
					texture( shadowMap, vec3( shadowCoord.xy + vogelDiskSample( 0, 5, phi ) * radius, shadowCoord.z ) ) +
					texture( shadowMap, vec3( shadowCoord.xy + vogelDiskSample( 1, 5, phi ) * radius, shadowCoord.z ) ) +
					texture( shadowMap, vec3( shadowCoord.xy + vogelDiskSample( 2, 5, phi ) * radius, shadowCoord.z ) ) +
					texture( shadowMap, vec3( shadowCoord.xy + vogelDiskSample( 3, 5, phi ) * radius, shadowCoord.z ) ) +
					texture( shadowMap, vec3( shadowCoord.xy + vogelDiskSample( 4, 5, phi ) * radius, shadowCoord.z ) )
				) * 0.2;
			}
			return mix( 1.0, shadow, shadowIntensity );
		}
	#elif defined( SHADOWMAP_TYPE_VSM )
		float getShadow( sampler2D shadowMap, vec2 shadowMapSize, float shadowIntensity, float shadowBias, float shadowRadius, vec4 shadowCoord ) {
			float shadow = 1.0;
			shadowCoord.xyz /= shadowCoord.w;
			#ifdef USE_REVERSED_DEPTH_BUFFER
				shadowCoord.z -= shadowBias;
			#else
				shadowCoord.z += shadowBias;
			#endif
			bool inFrustum = shadowCoord.x >= 0.0 && shadowCoord.x <= 1.0 && shadowCoord.y >= 0.0 && shadowCoord.y <= 1.0;
			bool frustumTest = inFrustum && shadowCoord.z <= 1.0;
			if ( frustumTest ) {
				vec2 distribution = texture2D( shadowMap, shadowCoord.xy ).rg;
				float mean = distribution.x;
				float variance = distribution.y * distribution.y;
				#ifdef USE_REVERSED_DEPTH_BUFFER
					float hard_shadow = step( mean, shadowCoord.z );
				#else
					float hard_shadow = step( shadowCoord.z, mean );
				#endif
				
				if ( hard_shadow == 1.0 ) {
					shadow = 1.0;
				} else {
					variance = max( variance, 0.0000001 );
					float d = shadowCoord.z - mean;
					float p_max = variance / ( variance + d * d );
					p_max = clamp( ( p_max - 0.3 ) / 0.65, 0.0, 1.0 );
					shadow = max( hard_shadow, p_max );
				}
			}
			return mix( 1.0, shadow, shadowIntensity );
		}
	#else
		float getShadow( sampler2D shadowMap, vec2 shadowMapSize, float shadowIntensity, float shadowBias, float shadowRadius, vec4 shadowCoord ) {
			float shadow = 1.0;
			shadowCoord.xyz /= shadowCoord.w;
			#ifdef USE_REVERSED_DEPTH_BUFFER
				shadowCoord.z -= shadowBias;
			#else
				shadowCoord.z += shadowBias;
			#endif
			bool inFrustum = shadowCoord.x >= 0.0 && shadowCoord.x <= 1.0 && shadowCoord.y >= 0.0 && shadowCoord.y <= 1.0;
			bool frustumTest = inFrustum && shadowCoord.z <= 1.0;
			if ( frustumTest ) {
				float depth = texture2D( shadowMap, shadowCoord.xy ).r;
				#ifdef USE_REVERSED_DEPTH_BUFFER
					shadow = step( depth, shadowCoord.z );
				#else
					shadow = step( shadowCoord.z, depth );
				#endif
			}
			return mix( 1.0, shadow, shadowIntensity );
		}
	#endif
	#if NUM_SUN_LIGHT_SHADOWS > 0
		float getSunShadow(
			#if defined( SHADOWMAP_TYPE_PCF )
				sampler2DShadow shadowMap,
			#else
				sampler2D shadowMap,
			#endif
			SunLightShadow sunLightShadow,
			int shadowIndex
		) {
			vec4 shadowWorldPosition = vec4( vSunShadowWorldPosition.xyz + vSunShadowWorldNormal * sunLightShadow.shadowNormalBias, 1.0 );
			float viewDepth = vSunShadowWorldPosition.w;
			int cascadeOffset = shadowIndex * SUN_LIGHT_CASCADES;
			float shadow = 1.0;
			for ( int i = SUN_LIGHT_CASCADES - 1; i >= 0; i -- ) {
				vec4 cascade = sunShadowCascade[ cascadeOffset + i ];
				if ( viewDepth >= cascade.x && viewDepth < cascade.y ) {
					float cascadeShadow = getShadow(
						shadowMap,
						sunLightShadow.shadowMapSize,
						sunLightShadow.shadowIntensity,
						sunLightShadow.shadowBias,
						sunLightShadow.shadowRadius,
						sunShadowMatrix[ cascadeOffset + i ] * shadowWorldPosition
					);
					shadow = mix( cascadeShadow, shadow, smoothstep( cascade.z, cascade.y, viewDepth ) );
				}
			}
			return shadow;
		}
	#endif
	#if NUM_POINT_LIGHT_SHADOWS > 0
	#if defined( SHADOWMAP_TYPE_PCF )
	float getPointShadow( samplerCubeShadow shadowMap, vec2 shadowMapSize, float shadowIntensity, float shadowBias, float shadowRadius, vec4 shadowCoord, float shadowCameraNear, float shadowCameraFar ) {
		float shadow = 1.0;
		vec3 lightToPosition = shadowCoord.xyz;
		vec3 bd3D = normalize( lightToPosition );
		vec3 absVec = abs( lightToPosition );
		float viewSpaceZ = max( max( absVec.x, absVec.y ), absVec.z );
		if ( viewSpaceZ - shadowCameraFar <= 0.0 && viewSpaceZ - shadowCameraNear >= 0.0 ) {
			#ifdef USE_REVERSED_DEPTH_BUFFER
				float dp = ( shadowCameraNear * ( shadowCameraFar - viewSpaceZ ) ) / ( viewSpaceZ * ( shadowCameraFar - shadowCameraNear ) );
				dp -= shadowBias;
			#else
				float dp = ( shadowCameraFar * ( viewSpaceZ - shadowCameraNear ) ) / ( viewSpaceZ * ( shadowCameraFar - shadowCameraNear ) );
				dp += shadowBias;
			#endif
			float texelSize = shadowRadius / shadowMapSize.x;
			vec3 absDir = abs( bd3D );
			vec3 tangent = absDir.x > absDir.z ? vec3( 0.0, 1.0, 0.0 ) : vec3( 1.0, 0.0, 0.0 );
			tangent = normalize( cross( bd3D, tangent ) );
			vec3 bitangent = cross( bd3D, tangent );
			float phi = interleavedGradientNoise( gl_FragCoord.xy ) * PI2;
			vec2 sample0 = vogelDiskSample( 0, 5, phi );
			vec2 sample1 = vogelDiskSample( 1, 5, phi );
			vec2 sample2 = vogelDiskSample( 2, 5, phi );
			vec2 sample3 = vogelDiskSample( 3, 5, phi );
			vec2 sample4 = vogelDiskSample( 4, 5, phi );
			shadow = (
				texture( shadowMap, vec4( bd3D + ( tangent * sample0.x + bitangent * sample0.y ) * texelSize, dp ) ) +
				texture( shadowMap, vec4( bd3D + ( tangent * sample1.x + bitangent * sample1.y ) * texelSize, dp ) ) +
				texture( shadowMap, vec4( bd3D + ( tangent * sample2.x + bitangent * sample2.y ) * texelSize, dp ) ) +
				texture( shadowMap, vec4( bd3D + ( tangent * sample3.x + bitangent * sample3.y ) * texelSize, dp ) ) +
				texture( shadowMap, vec4( bd3D + ( tangent * sample4.x + bitangent * sample4.y ) * texelSize, dp ) )
			) * 0.2;
		}
		return mix( 1.0, shadow, shadowIntensity );
	}
	#elif defined( SHADOWMAP_TYPE_BASIC )
	float getPointShadow( samplerCube shadowMap, vec2 shadowMapSize, float shadowIntensity, float shadowBias, float shadowRadius, vec4 shadowCoord, float shadowCameraNear, float shadowCameraFar ) {
		float shadow = 1.0;
		vec3 lightToPosition = shadowCoord.xyz;
		vec3 absVec = abs( lightToPosition );
		float viewSpaceZ = max( max( absVec.x, absVec.y ), absVec.z );
		if ( viewSpaceZ - shadowCameraFar <= 0.0 && viewSpaceZ - shadowCameraNear >= 0.0 ) {
			float dp = ( shadowCameraFar * ( viewSpaceZ - shadowCameraNear ) ) / ( viewSpaceZ * ( shadowCameraFar - shadowCameraNear ) );
			dp += shadowBias;
			vec3 bd3D = normalize( lightToPosition );
			float depth = textureCube( shadowMap, bd3D ).r;
			#ifdef USE_REVERSED_DEPTH_BUFFER
				depth = 1.0 - depth;
			#endif
			shadow = step( dp, depth );
		}
		return mix( 1.0, shadow, shadowIntensity );
	}
	#endif
	#endif
#endif`,pT=`#if NUM_SPOT_LIGHT_COORDS > 0
	uniform mat4 spotLightMatrix[ NUM_SPOT_LIGHT_COORDS ];
	varying vec4 vSpotLightCoord[ NUM_SPOT_LIGHT_COORDS ];
#endif
#ifdef USE_SHADOWMAP
	#if NUM_SUN_LIGHT_SHADOWS > 0
		varying vec4 vSunShadowWorldPosition;
		varying vec3 vSunShadowWorldNormal;
	#endif
	#if NUM_DIR_LIGHT_SHADOWS > 0
		uniform mat4 directionalShadowMatrix[ NUM_DIR_LIGHT_SHADOWS ];
		varying vec4 vDirectionalShadowCoord[ NUM_DIR_LIGHT_SHADOWS ];
		struct DirectionalLightShadow {
			float shadowIntensity;
			float shadowBias;
			float shadowNormalBias;
			float shadowRadius;
			vec2 shadowMapSize;
		};
		uniform DirectionalLightShadow directionalLightShadows[ NUM_DIR_LIGHT_SHADOWS ];
	#endif
	#if NUM_SPOT_LIGHT_SHADOWS > 0
		struct SpotLightShadow {
			float shadowIntensity;
			float shadowBias;
			float shadowNormalBias;
			float shadowRadius;
			vec2 shadowMapSize;
		};
		uniform SpotLightShadow spotLightShadows[ NUM_SPOT_LIGHT_SHADOWS ];
	#endif
	#if NUM_POINT_LIGHT_SHADOWS > 0
		uniform mat4 pointShadowMatrix[ NUM_POINT_LIGHT_SHADOWS ];
		varying vec4 vPointShadowCoord[ NUM_POINT_LIGHT_SHADOWS ];
		struct PointLightShadow {
			float shadowIntensity;
			float shadowBias;
			float shadowNormalBias;
			float shadowRadius;
			vec2 shadowMapSize;
			float shadowCameraNear;
			float shadowCameraFar;
		};
		uniform PointLightShadow pointLightShadows[ NUM_POINT_LIGHT_SHADOWS ];
	#endif
#endif`,mT=`#if ( defined( USE_SHADOWMAP ) && ( NUM_DIR_LIGHT_SHADOWS > 0 || NUM_SUN_LIGHT_SHADOWS > 0 || NUM_POINT_LIGHT_SHADOWS > 0 ) ) || ( NUM_SPOT_LIGHT_COORDS > 0 )
	#ifdef HAS_NORMAL
		vec3 shadowWorldNormal = transformNormalByInverseViewMatrix( transformedNormal, viewMatrix );
	#else
		vec3 shadowWorldNormal = vec3( 0.0 );
	#endif
	vec4 shadowWorldPosition;
#endif
#if defined( USE_SHADOWMAP )
	#if NUM_SUN_LIGHT_SHADOWS > 0
		vSunShadowWorldPosition = vec4( worldPosition.xyz, - mvPosition.z );
		vSunShadowWorldNormal = shadowWorldNormal;
	#endif
	#if NUM_DIR_LIGHT_SHADOWS > 0
		#pragma unroll_loop_start
		for ( int i = 0; i < NUM_DIR_LIGHT_SHADOWS; i ++ ) {
			shadowWorldPosition = worldPosition + vec4( shadowWorldNormal * directionalLightShadows[ i ].shadowNormalBias, 0 );
			vDirectionalShadowCoord[ i ] = directionalShadowMatrix[ i ] * shadowWorldPosition;
		}
		#pragma unroll_loop_end
	#endif
	#if NUM_POINT_LIGHT_SHADOWS > 0
		#pragma unroll_loop_start
		for ( int i = 0; i < NUM_POINT_LIGHT_SHADOWS; i ++ ) {
			shadowWorldPosition = worldPosition + vec4( shadowWorldNormal * pointLightShadows[ i ].shadowNormalBias, 0 );
			vPointShadowCoord[ i ] = pointShadowMatrix[ i ] * shadowWorldPosition;
		}
		#pragma unroll_loop_end
	#endif
#endif
#if NUM_SPOT_LIGHT_COORDS > 0
	#pragma unroll_loop_start
	for ( int i = 0; i < NUM_SPOT_LIGHT_COORDS; i ++ ) {
		shadowWorldPosition = worldPosition;
		#if ( defined( USE_SHADOWMAP ) && UNROLLED_LOOP_INDEX < NUM_SPOT_LIGHT_SHADOWS )
			shadowWorldPosition.xyz += shadowWorldNormal * spotLightShadows[ i ].shadowNormalBias;
		#endif
		vSpotLightCoord[ i ] = spotLightMatrix[ i ] * shadowWorldPosition;
	}
	#pragma unroll_loop_end
#endif`,gT=`float getShadowMask() {
	float shadow = 1.0;
	#ifdef USE_SHADOWMAP
	#if NUM_SUN_LIGHT_SHADOWS > 0
	SunLightShadow sunLight;
	#pragma unroll_loop_start
	for ( int i = 0; i < NUM_SUN_LIGHT_SHADOWS; i ++ ) {
		sunLight = sunLightShadows[ i ];
		shadow *= receiveShadow ? getSunShadow( sunShadowMap[ i ], sunLight, UNROLLED_LOOP_INDEX ) : 1.0;
	}
	#pragma unroll_loop_end
	#endif
	#if NUM_DIR_LIGHT_SHADOWS > 0
	DirectionalLightShadow directionalLight;
	#pragma unroll_loop_start
	for ( int i = 0; i < NUM_DIR_LIGHT_SHADOWS; i ++ ) {
		directionalLight = directionalLightShadows[ i ];
		shadow *= receiveShadow ? getShadow( directionalShadowMap[ i ], directionalLight.shadowMapSize, directionalLight.shadowIntensity, directionalLight.shadowBias, directionalLight.shadowRadius, vDirectionalShadowCoord[ i ] ) : 1.0;
	}
	#pragma unroll_loop_end
	#endif
	#if NUM_SPOT_LIGHT_SHADOWS > 0
	SpotLightShadow spotLight;
	#pragma unroll_loop_start
	for ( int i = 0; i < NUM_SPOT_LIGHT_SHADOWS; i ++ ) {
		spotLight = spotLightShadows[ i ];
		shadow *= receiveShadow ? getShadow( spotShadowMap[ i ], spotLight.shadowMapSize, spotLight.shadowIntensity, spotLight.shadowBias, spotLight.shadowRadius, vSpotLightCoord[ i ] ) : 1.0;
	}
	#pragma unroll_loop_end
	#endif
	#if NUM_POINT_LIGHT_SHADOWS > 0 && ( defined( SHADOWMAP_TYPE_PCF ) || defined( SHADOWMAP_TYPE_BASIC ) )
	PointLightShadow pointLight;
	#pragma unroll_loop_start
	for ( int i = 0; i < NUM_POINT_LIGHT_SHADOWS; i ++ ) {
		pointLight = pointLightShadows[ i ];
		shadow *= receiveShadow ? getPointShadow( pointShadowMap[ i ], pointLight.shadowMapSize, pointLight.shadowIntensity, pointLight.shadowBias, pointLight.shadowRadius, vPointShadowCoord[ i ], pointLight.shadowCameraNear, pointLight.shadowCameraFar ) : 1.0;
	}
	#pragma unroll_loop_end
	#endif
	#endif
	return shadow;
}`,xT=`#ifdef USE_SKINNING
	mat4 boneMatX = getBoneMatrix( skinIndex.x );
	mat4 boneMatY = getBoneMatrix( skinIndex.y );
	mat4 boneMatZ = getBoneMatrix( skinIndex.z );
	mat4 boneMatW = getBoneMatrix( skinIndex.w );
#endif`,vT=`#ifdef USE_SKINNING
	uniform mat4 bindMatrix;
	uniform mat4 bindMatrixInverse;
	uniform highp sampler2D boneTexture;
	mat4 getBoneMatrix( const in float i ) {
		int size = textureSize( boneTexture, 0 ).x;
		int j = int( i ) * 4;
		int x = j % size;
		int y = j / size;
		vec4 v1 = texelFetch( boneTexture, ivec2( x, y ), 0 );
		vec4 v2 = texelFetch( boneTexture, ivec2( x + 1, y ), 0 );
		vec4 v3 = texelFetch( boneTexture, ivec2( x + 2, y ), 0 );
		vec4 v4 = texelFetch( boneTexture, ivec2( x + 3, y ), 0 );
		return mat4( v1, v2, v3, v4 );
	}
#endif`,_T=`#ifdef USE_SKINNING
	vec4 skinVertex = bindMatrix * vec4( transformed, 1.0 );
	vec4 skinned = vec4( 0.0 );
	skinned += boneMatX * skinVertex * skinWeight.x;
	skinned += boneMatY * skinVertex * skinWeight.y;
	skinned += boneMatZ * skinVertex * skinWeight.z;
	skinned += boneMatW * skinVertex * skinWeight.w;
	transformed = ( bindMatrixInverse * skinned ).xyz;
#endif`,yT=`#ifdef USE_SKINNING
	mat4 skinMatrix = mat4( 0.0 );
	skinMatrix += skinWeight.x * boneMatX;
	skinMatrix += skinWeight.y * boneMatY;
	skinMatrix += skinWeight.z * boneMatZ;
	skinMatrix += skinWeight.w * boneMatW;
	skinMatrix = bindMatrixInverse * skinMatrix * bindMatrix;
	objectNormal = vec4( skinMatrix * vec4( objectNormal, 0.0 ) ).xyz;
	#ifdef USE_TANGENT
		objectTangent = vec4( skinMatrix * vec4( objectTangent, 0.0 ) ).xyz;
	#endif
#endif`,ST=`float specularStrength;
#ifdef USE_SPECULARMAP
	vec4 texelSpecular = texture2D( specularMap, vSpecularMapUv );
	specularStrength = texelSpecular.r;
#else
	specularStrength = 1.0;
#endif`,bT=`#ifdef USE_SPECULARMAP
	uniform sampler2D specularMap;
#endif`,MT=`#if defined( TONE_MAPPING )
	gl_FragColor.rgb = toneMapping( gl_FragColor.rgb );
#endif`,ET=`#ifndef saturate
#define saturate( a ) clamp( a, 0.0, 1.0 )
#endif
uniform float toneMappingExposure;
vec3 LinearToneMapping( vec3 color ) {
	return saturate( toneMappingExposure * color );
}
vec3 ReinhardToneMapping( vec3 color ) {
	color *= toneMappingExposure;
	return saturate( color / ( vec3( 1.0 ) + color ) );
}
vec3 CineonToneMapping( vec3 color ) {
	color *= toneMappingExposure;
	color = max( vec3( 0.0 ), color - 0.004 );
	return pow( ( color * ( 6.2 * color + 0.5 ) ) / ( color * ( 6.2 * color + 1.7 ) + 0.06 ), vec3( 2.2 ) );
}
vec3 RRTAndODTFit( vec3 v ) {
	vec3 a = v * ( v + 0.0245786 ) - 0.000090537;
	vec3 b = v * ( 0.983729 * v + 0.4329510 ) + 0.238081;
	return a / b;
}
vec3 ACESFilmicToneMapping( vec3 color ) {
	const mat3 ACESInputMat = mat3(
		vec3( 0.59719, 0.07600, 0.02840 ),		vec3( 0.35458, 0.90834, 0.13383 ),
		vec3( 0.04823, 0.01566, 0.83777 )
	);
	const mat3 ACESOutputMat = mat3(
		vec3(  1.60475, -0.10208, -0.00327 ),		vec3( -0.53108,  1.10813, -0.07276 ),
		vec3( -0.07367, -0.00605,  1.07602 )
	);
	color *= toneMappingExposure / 0.6;
	color = ACESInputMat * color;
	color = RRTAndODTFit( color );
	color = ACESOutputMat * color;
	return saturate( color );
}
const mat3 LINEAR_REC2020_TO_LINEAR_SRGB = mat3(
	vec3( 1.6605, - 0.1246, - 0.0182 ),
	vec3( - 0.5876, 1.1329, - 0.1006 ),
	vec3( - 0.0728, - 0.0083, 1.1187 )
);
const mat3 LINEAR_SRGB_TO_LINEAR_REC2020 = mat3(
	vec3( 0.6274, 0.0691, 0.0164 ),
	vec3( 0.3293, 0.9195, 0.0880 ),
	vec3( 0.0433, 0.0113, 0.8956 )
);
vec3 agxDefaultContrastApprox( vec3 x ) {
	vec3 x2 = x * x;
	vec3 x4 = x2 * x2;
	return + 15.5 * x4 * x2
		- 40.14 * x4 * x
		+ 31.96 * x4
		- 6.868 * x2 * x
		+ 0.4298 * x2
		+ 0.1191 * x
		- 0.00232;
}
vec3 AgXToneMapping( vec3 color ) {
	const mat3 AgXInsetMatrix = mat3(
		vec3( 0.856627153315983, 0.137318972929847, 0.11189821299995 ),
		vec3( 0.0951212405381588, 0.761241990602591, 0.0767994186031903 ),
		vec3( 0.0482516061458583, 0.101439036467562, 0.811302368396859 )
	);
	const mat3 AgXOutsetMatrix = mat3(
		vec3( 1.1271005818144368, - 0.1413297634984383, - 0.14132976349843826 ),
		vec3( - 0.11060664309660323, 1.157823702216272, - 0.11060664309660294 ),
		vec3( - 0.016493938717834573, - 0.016493938717834257, 1.2519364065950405 )
	);
	const float AgxMinEv = - 12.47393;	const float AgxMaxEv = 4.026069;
	color *= toneMappingExposure;
	color = LINEAR_SRGB_TO_LINEAR_REC2020 * color;
	color = AgXInsetMatrix * color;
	color = max( color, 1e-10 );	color = log2( color );
	color = ( color - AgxMinEv ) / ( AgxMaxEv - AgxMinEv );
	color = clamp( color, 0.0, 1.0 );
	color = agxDefaultContrastApprox( color );
	color = AgXOutsetMatrix * color;
	color = pow( max( vec3( 0.0 ), color ), vec3( 2.2 ) );
	color = LINEAR_REC2020_TO_LINEAR_SRGB * color;
	color = clamp( color, 0.0, 1.0 );
	return color;
}
vec3 NeutralToneMapping( vec3 color ) {
	const float StartCompression = 0.8 - 0.04;
	const float Desaturation = 0.15;
	color *= toneMappingExposure;
	float x = min( color.r, min( color.g, color.b ) );
	float offset = x < 0.08 ? x - 6.25 * x * x : 0.04;
	color -= offset;
	float peak = max( color.r, max( color.g, color.b ) );
	if ( peak < StartCompression ) return color;
	float d = 1. - StartCompression;
	float newPeak = 1. - d * d / ( peak + d - StartCompression );
	color *= newPeak / peak;
	float g = 1. - 1. / ( Desaturation * ( peak - newPeak ) + 1. );
	return mix( color, vec3( newPeak ), g );
}
vec3 CustomToneMapping( vec3 color ) { return color; }`,TT=`#ifdef USE_TRANSMISSION
	material.transmission = transmission;
	material.transmissionAlpha = 1.0;
	material.thickness = thickness;
	material.attenuationDistance = attenuationDistance;
	material.attenuationColor = attenuationColor;
	#ifdef USE_TRANSMISSIONMAP
		material.transmission *= texture2D( transmissionMap, vTransmissionMapUv ).r;
	#endif
	#ifdef USE_THICKNESSMAP
		material.thickness *= texture2D( thicknessMap, vThicknessMapUv ).g;
	#endif
	vec3 pos = vWorldPosition;
	vec3 v = normalize( cameraPosition - pos );
	vec3 n = transformNormalByInverseViewMatrix( normal, viewMatrix );
	vec4 transmitted = getIBLVolumeRefraction(
		n, v, material.roughness, material.diffuseContribution, material.specularColorBlended, material.specularF90,
		pos, modelMatrix, viewMatrix, projectionMatrix, material.dispersion, material.ior, material.thickness,
		material.attenuationColor, material.attenuationDistance );
	material.transmissionAlpha = mix( material.transmissionAlpha, transmitted.a, material.transmission );
	totalDiffuse = mix( totalDiffuse, transmitted.rgb, material.transmission );
#endif`,AT=`#ifdef USE_TRANSMISSION
	uniform float transmission;
	uniform float thickness;
	uniform float attenuationDistance;
	uniform vec3 attenuationColor;
	#ifdef USE_TRANSMISSIONMAP
		uniform sampler2D transmissionMap;
	#endif
	#ifdef USE_THICKNESSMAP
		uniform sampler2D thicknessMap;
	#endif
	uniform vec2 transmissionSamplerSize;
	uniform sampler2D transmissionSamplerMap;
	uniform mat4 modelMatrix;
	uniform mat4 projectionMatrix;
	varying vec3 vWorldPosition;
	float w0( float a ) {
		return ( 1.0 / 6.0 ) * ( a * ( a * ( - a + 3.0 ) - 3.0 ) + 1.0 );
	}
	float w1( float a ) {
		return ( 1.0 / 6.0 ) * ( a *  a * ( 3.0 * a - 6.0 ) + 4.0 );
	}
	float w2( float a ){
		return ( 1.0 / 6.0 ) * ( a * ( a * ( - 3.0 * a + 3.0 ) + 3.0 ) + 1.0 );
	}
	float w3( float a ) {
		return ( 1.0 / 6.0 ) * ( a * a * a );
	}
	float g0( float a ) {
		return w0( a ) + w1( a );
	}
	float g1( float a ) {
		return w2( a ) + w3( a );
	}
	float h0( float a ) {
		return - 1.0 + w1( a ) / ( w0( a ) + w1( a ) );
	}
	float h1( float a ) {
		return 1.0 + w3( a ) / ( w2( a ) + w3( a ) );
	}
	vec4 bicubic( sampler2D tex, vec2 uv, vec4 texelSize, float lod ) {
		uv = uv * texelSize.zw + 0.5;
		vec2 iuv = floor( uv );
		vec2 fuv = fract( uv );
		float g0x = g0( fuv.x );
		float g1x = g1( fuv.x );
		float h0x = h0( fuv.x );
		float h1x = h1( fuv.x );
		float h0y = h0( fuv.y );
		float h1y = h1( fuv.y );
		vec2 p0 = ( vec2( iuv.x + h0x, iuv.y + h0y ) - 0.5 ) * texelSize.xy;
		vec2 p1 = ( vec2( iuv.x + h1x, iuv.y + h0y ) - 0.5 ) * texelSize.xy;
		vec2 p2 = ( vec2( iuv.x + h0x, iuv.y + h1y ) - 0.5 ) * texelSize.xy;
		vec2 p3 = ( vec2( iuv.x + h1x, iuv.y + h1y ) - 0.5 ) * texelSize.xy;
		return g0( fuv.y ) * ( g0x * textureLod( tex, p0, lod ) + g1x * textureLod( tex, p1, lod ) ) +
			g1( fuv.y ) * ( g0x * textureLod( tex, p2, lod ) + g1x * textureLod( tex, p3, lod ) );
	}
	vec4 textureBicubic( sampler2D sampler, vec2 uv, float lod ) {
		vec2 fLodSize = vec2( textureSize( sampler, int( lod ) ) );
		vec2 cLodSize = vec2( textureSize( sampler, int( lod + 1.0 ) ) );
		vec2 fLodSizeInv = 1.0 / fLodSize;
		vec2 cLodSizeInv = 1.0 / cLodSize;
		vec4 fSample = bicubic( sampler, uv, vec4( fLodSizeInv, fLodSize ), floor( lod ) );
		vec4 cSample = bicubic( sampler, uv, vec4( cLodSizeInv, cLodSize ), ceil( lod ) );
		return mix( fSample, cSample, fract( lod ) );
	}
	vec3 getVolumeTransmissionRay( const in vec3 n, const in vec3 v, const in float thickness, const in float ior, const in mat4 modelMatrix ) {
		vec3 refractionVector = refract( - v, normalize( n ), 1.0 / ior );
		vec3 modelScale;
		modelScale.x = length( vec3( modelMatrix[ 0 ].xyz ) );
		modelScale.y = length( vec3( modelMatrix[ 1 ].xyz ) );
		modelScale.z = length( vec3( modelMatrix[ 2 ].xyz ) );
		return normalize( refractionVector ) * thickness * modelScale;
	}
	float applyIorToRoughness( const in float roughness, const in float ior ) {
		return roughness * clamp( ior * 2.0 - 2.0, 0.0, 1.0 );
	}
	vec4 getTransmissionSample( const in vec2 fragCoord, const in float roughness, const in float ior ) {
		float lod = log2( transmissionSamplerSize.x ) * applyIorToRoughness( roughness, ior );
		return textureBicubic( transmissionSamplerMap, fragCoord.xy, lod );
	}
	vec3 volumeAttenuation( const in float transmissionDistance, const in vec3 attenuationColor, const in float attenuationDistance ) {
		if ( isinf( attenuationDistance ) ) {
			return vec3( 1.0 );
		} else {
			vec3 attenuationCoefficient = -log( attenuationColor ) / attenuationDistance;
			vec3 transmittance = exp( - attenuationCoefficient * transmissionDistance );			return transmittance;
		}
	}
	vec4 getIBLVolumeRefraction( const in vec3 n, const in vec3 v, const in float roughness, const in vec3 diffuseColor,
		const in vec3 specularColor, const in float specularF90, const in vec3 position, const in mat4 modelMatrix,
		const in mat4 viewMatrix, const in mat4 projMatrix, const in float dispersion, const in float ior, const in float thickness,
		const in vec3 attenuationColor, const in float attenuationDistance ) {
		vec4 transmittedLight;
		vec3 transmittance;
		#ifdef USE_DISPERSION
			float halfSpread = ( ior - 1.0 ) * 0.025 * dispersion;
			vec3 iors = vec3( ior - halfSpread, ior, ior + halfSpread );
			for ( int i = 0; i < 3; i ++ ) {
				vec3 transmissionRay = getVolumeTransmissionRay( n, v, thickness, iors[ i ], modelMatrix );
				vec3 refractedRayExit = position + transmissionRay;
				vec4 ndcPos = projMatrix * viewMatrix * vec4( refractedRayExit, 1.0 );
				vec2 refractionCoords = ndcPos.xy / ndcPos.w;
				refractionCoords += 1.0;
				refractionCoords /= 2.0;
				vec4 transmissionSample = getTransmissionSample( refractionCoords, roughness, iors[ i ] );
				transmittedLight[ i ] = transmissionSample[ i ];
				transmittedLight.a += transmissionSample.a;
				transmittance[ i ] = diffuseColor[ i ] * volumeAttenuation( length( transmissionRay ), attenuationColor, attenuationDistance )[ i ];
			}
			transmittedLight.a /= 3.0;
		#else
			vec3 transmissionRay = getVolumeTransmissionRay( n, v, thickness, ior, modelMatrix );
			vec3 refractedRayExit = position + transmissionRay;
			vec4 ndcPos = projMatrix * viewMatrix * vec4( refractedRayExit, 1.0 );
			vec2 refractionCoords = ndcPos.xy / ndcPos.w;
			refractionCoords += 1.0;
			refractionCoords /= 2.0;
			transmittedLight = getTransmissionSample( refractionCoords, roughness, ior );
			transmittance = diffuseColor * volumeAttenuation( length( transmissionRay ), attenuationColor, attenuationDistance );
		#endif
		vec3 attenuatedColor = transmittance * transmittedLight.rgb;
		vec3 F = EnvironmentBRDF( n, v, specularColor, specularF90, roughness );
		float transmittanceFactor = ( transmittance.r + transmittance.g + transmittance.b ) / 3.0;
		return vec4( ( 1.0 - F ) * attenuatedColor, 1.0 - ( 1.0 - transmittedLight.a ) * transmittanceFactor );
	}
#endif`,wT=`#if defined( USE_UV ) || defined( USE_ANISOTROPY )
	varying vec2 vUv;
#endif
#ifdef USE_MAP
	varying vec2 vMapUv;
#endif
#ifdef USE_ALPHAMAP
	varying vec2 vAlphaMapUv;
#endif
#ifdef USE_LIGHTMAP
	varying vec2 vLightMapUv;
#endif
#ifdef USE_AOMAP
	varying vec2 vAoMapUv;
#endif
#ifdef USE_BUMPMAP
	varying vec2 vBumpMapUv;
#endif
#ifdef USE_NORMALMAP
	varying vec2 vNormalMapUv;
#endif
#ifdef USE_EMISSIVEMAP
	varying vec2 vEmissiveMapUv;
#endif
#ifdef USE_METALNESSMAP
	varying vec2 vMetalnessMapUv;
#endif
#ifdef USE_ROUGHNESSMAP
	varying vec2 vRoughnessMapUv;
#endif
#ifdef USE_ANISOTROPYMAP
	varying vec2 vAnisotropyMapUv;
#endif
#ifdef USE_CLEARCOATMAP
	varying vec2 vClearcoatMapUv;
#endif
#ifdef USE_CLEARCOAT_NORMALMAP
	varying vec2 vClearcoatNormalMapUv;
#endif
#ifdef USE_CLEARCOAT_ROUGHNESSMAP
	varying vec2 vClearcoatRoughnessMapUv;
#endif
#ifdef USE_IRIDESCENCEMAP
	varying vec2 vIridescenceMapUv;
#endif
#ifdef USE_IRIDESCENCE_THICKNESSMAP
	varying vec2 vIridescenceThicknessMapUv;
#endif
#ifdef USE_SHEEN_COLORMAP
	varying vec2 vSheenColorMapUv;
#endif
#ifdef USE_SHEEN_ROUGHNESSMAP
	varying vec2 vSheenRoughnessMapUv;
#endif
#ifdef USE_SPECULARMAP
	varying vec2 vSpecularMapUv;
#endif
#ifdef USE_SPECULAR_COLORMAP
	varying vec2 vSpecularColorMapUv;
#endif
#ifdef USE_SPECULAR_INTENSITYMAP
	varying vec2 vSpecularIntensityMapUv;
#endif
#ifdef USE_TRANSMISSIONMAP
	uniform mat3 transmissionMapTransform;
	varying vec2 vTransmissionMapUv;
#endif
#ifdef USE_THICKNESSMAP
	uniform mat3 thicknessMapTransform;
	varying vec2 vThicknessMapUv;
#endif`,CT=`#if defined( USE_UV ) || defined( USE_ANISOTROPY )
	varying vec2 vUv;
#endif
#ifdef USE_MAP
	uniform mat3 mapTransform;
	varying vec2 vMapUv;
#endif
#ifdef USE_ALPHAMAP
	uniform mat3 alphaMapTransform;
	varying vec2 vAlphaMapUv;
#endif
#ifdef USE_LIGHTMAP
	uniform mat3 lightMapTransform;
	varying vec2 vLightMapUv;
#endif
#ifdef USE_AOMAP
	uniform mat3 aoMapTransform;
	varying vec2 vAoMapUv;
#endif
#ifdef USE_BUMPMAP
	uniform mat3 bumpMapTransform;
	varying vec2 vBumpMapUv;
#endif
#ifdef USE_NORMALMAP
	uniform mat3 normalMapTransform;
	varying vec2 vNormalMapUv;
#endif
#ifdef USE_DISPLACEMENTMAP
	uniform mat3 displacementMapTransform;
	varying vec2 vDisplacementMapUv;
#endif
#ifdef USE_EMISSIVEMAP
	uniform mat3 emissiveMapTransform;
	varying vec2 vEmissiveMapUv;
#endif
#ifdef USE_METALNESSMAP
	uniform mat3 metalnessMapTransform;
	varying vec2 vMetalnessMapUv;
#endif
#ifdef USE_ROUGHNESSMAP
	uniform mat3 roughnessMapTransform;
	varying vec2 vRoughnessMapUv;
#endif
#ifdef USE_ANISOTROPYMAP
	uniform mat3 anisotropyMapTransform;
	varying vec2 vAnisotropyMapUv;
#endif
#ifdef USE_CLEARCOATMAP
	uniform mat3 clearcoatMapTransform;
	varying vec2 vClearcoatMapUv;
#endif
#ifdef USE_CLEARCOAT_NORMALMAP
	uniform mat3 clearcoatNormalMapTransform;
	varying vec2 vClearcoatNormalMapUv;
#endif
#ifdef USE_CLEARCOAT_ROUGHNESSMAP
	uniform mat3 clearcoatRoughnessMapTransform;
	varying vec2 vClearcoatRoughnessMapUv;
#endif
#ifdef USE_SHEEN_COLORMAP
	uniform mat3 sheenColorMapTransform;
	varying vec2 vSheenColorMapUv;
#endif
#ifdef USE_SHEEN_ROUGHNESSMAP
	uniform mat3 sheenRoughnessMapTransform;
	varying vec2 vSheenRoughnessMapUv;
#endif
#ifdef USE_IRIDESCENCEMAP
	uniform mat3 iridescenceMapTransform;
	varying vec2 vIridescenceMapUv;
#endif
#ifdef USE_IRIDESCENCE_THICKNESSMAP
	uniform mat3 iridescenceThicknessMapTransform;
	varying vec2 vIridescenceThicknessMapUv;
#endif
#ifdef USE_SPECULARMAP
	uniform mat3 specularMapTransform;
	varying vec2 vSpecularMapUv;
#endif
#ifdef USE_SPECULAR_COLORMAP
	uniform mat3 specularColorMapTransform;
	varying vec2 vSpecularColorMapUv;
#endif
#ifdef USE_SPECULAR_INTENSITYMAP
	uniform mat3 specularIntensityMapTransform;
	varying vec2 vSpecularIntensityMapUv;
#endif
#ifdef USE_TRANSMISSIONMAP
	uniform mat3 transmissionMapTransform;
	varying vec2 vTransmissionMapUv;
#endif
#ifdef USE_THICKNESSMAP
	uniform mat3 thicknessMapTransform;
	varying vec2 vThicknessMapUv;
#endif`,RT=`#if defined( USE_UV ) || defined( USE_ANISOTROPY )
	vUv = vec3( uv, 1 ).xy;
#endif
#ifdef USE_MAP
	vMapUv = ( mapTransform * vec3( MAP_UV, 1 ) ).xy;
#endif
#ifdef USE_ALPHAMAP
	vAlphaMapUv = ( alphaMapTransform * vec3( ALPHAMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_LIGHTMAP
	vLightMapUv = ( lightMapTransform * vec3( LIGHTMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_AOMAP
	vAoMapUv = ( aoMapTransform * vec3( AOMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_BUMPMAP
	vBumpMapUv = ( bumpMapTransform * vec3( BUMPMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_NORMALMAP
	vNormalMapUv = ( normalMapTransform * vec3( NORMALMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_DISPLACEMENTMAP
	vDisplacementMapUv = ( displacementMapTransform * vec3( DISPLACEMENTMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_EMISSIVEMAP
	vEmissiveMapUv = ( emissiveMapTransform * vec3( EMISSIVEMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_METALNESSMAP
	vMetalnessMapUv = ( metalnessMapTransform * vec3( METALNESSMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_ROUGHNESSMAP
	vRoughnessMapUv = ( roughnessMapTransform * vec3( ROUGHNESSMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_ANISOTROPYMAP
	vAnisotropyMapUv = ( anisotropyMapTransform * vec3( ANISOTROPYMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_CLEARCOATMAP
	vClearcoatMapUv = ( clearcoatMapTransform * vec3( CLEARCOATMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_CLEARCOAT_NORMALMAP
	vClearcoatNormalMapUv = ( clearcoatNormalMapTransform * vec3( CLEARCOAT_NORMALMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_CLEARCOAT_ROUGHNESSMAP
	vClearcoatRoughnessMapUv = ( clearcoatRoughnessMapTransform * vec3( CLEARCOAT_ROUGHNESSMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_IRIDESCENCEMAP
	vIridescenceMapUv = ( iridescenceMapTransform * vec3( IRIDESCENCEMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_IRIDESCENCE_THICKNESSMAP
	vIridescenceThicknessMapUv = ( iridescenceThicknessMapTransform * vec3( IRIDESCENCE_THICKNESSMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_SHEEN_COLORMAP
	vSheenColorMapUv = ( sheenColorMapTransform * vec3( SHEEN_COLORMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_SHEEN_ROUGHNESSMAP
	vSheenRoughnessMapUv = ( sheenRoughnessMapTransform * vec3( SHEEN_ROUGHNESSMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_SPECULARMAP
	vSpecularMapUv = ( specularMapTransform * vec3( SPECULARMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_SPECULAR_COLORMAP
	vSpecularColorMapUv = ( specularColorMapTransform * vec3( SPECULAR_COLORMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_SPECULAR_INTENSITYMAP
	vSpecularIntensityMapUv = ( specularIntensityMapTransform * vec3( SPECULAR_INTENSITYMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_TRANSMISSIONMAP
	vTransmissionMapUv = ( transmissionMapTransform * vec3( TRANSMISSIONMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_THICKNESSMAP
	vThicknessMapUv = ( thicknessMapTransform * vec3( THICKNESSMAP_UV, 1 ) ).xy;
#endif`,UT=`#if defined( USE_ENVMAP ) || defined( DISTANCE ) || defined ( USE_SHADOWMAP ) || defined ( USE_TRANSMISSION ) || NUM_SPOT_LIGHT_COORDS > 0
	vec4 worldPosition = vec4( transformed, 1.0 );
	#ifdef USE_BATCHING
		worldPosition = batchingMatrix * worldPosition;
	#endif
	#ifdef USE_INSTANCING
		worldPosition = instanceMatrix * worldPosition;
	#endif
	worldPosition = modelMatrix * worldPosition;
#endif`;const DT=`varying vec2 vUv;
uniform mat3 uvTransform;
void main() {
	vUv = ( uvTransform * vec3( uv, 1 ) ).xy;
	gl_Position = vec4( position.xy, 1.0, 1.0 );
}`,NT=`uniform sampler2D t2D;
uniform float backgroundIntensity;
varying vec2 vUv;
void main() {
	vec4 texColor = texture2D( t2D, vUv );
	#ifdef DECODE_VIDEO_TEXTURE
		texColor = vec4( mix( pow( texColor.rgb * 0.9478672986 + vec3( 0.0521327014 ), vec3( 2.4 ) ), texColor.rgb * 0.0773993808, vec3( lessThanEqual( texColor.rgb, vec3( 0.04045 ) ) ) ), texColor.w );
	#endif
	texColor.rgb *= backgroundIntensity;
	gl_FragColor = texColor;
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
}`,LT=`varying vec3 vWorldDirection;
#include <common>
void main() {
	vWorldDirection = transformDirection( position, modelMatrix );
	#include <begin_vertex>
	#include <project_vertex>
	gl_Position.z = gl_Position.w;
}`,OT=`#ifdef ENVMAP_TYPE_CUBE
	uniform samplerCube envMap;
#elif defined( ENVMAP_TYPE_CUBE_UV )
	uniform sampler2D envMap;
#endif
uniform float backgroundBlurriness;
uniform float backgroundIntensity;
uniform mat3 backgroundRotation;
varying vec3 vWorldDirection;
#include <cube_uv_reflection_fragment>
void main() {
	#ifdef ENVMAP_TYPE_CUBE
		vec4 texColor = textureCube( envMap, backgroundRotation * vWorldDirection );
	#elif defined( ENVMAP_TYPE_CUBE_UV )
		vec4 texColor = textureCubeUV( envMap, backgroundRotation * vWorldDirection, backgroundBlurriness );
	#else
		vec4 texColor = vec4( 0.0, 0.0, 0.0, 1.0 );
	#endif
	texColor.rgb *= backgroundIntensity;
	gl_FragColor = texColor;
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
}`,PT=`varying vec3 vWorldDirection;
#include <common>
void main() {
	vWorldDirection = transformDirection( position, modelMatrix );
	#include <begin_vertex>
	#include <project_vertex>
	gl_Position.z = gl_Position.w;
}`,zT=`uniform samplerCube tCube;
uniform float tFlip;
uniform float opacity;
varying vec3 vWorldDirection;
void main() {
	vec4 texColor = textureCube( tCube, vec3( tFlip * vWorldDirection.x, vWorldDirection.yz ) );
	gl_FragColor = texColor;
	gl_FragColor.a *= opacity;
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
}`,FT=`#include <common>
#include <batching_pars_vertex>
#include <uv_pars_vertex>
#include <displacementmap_pars_vertex>
#include <morphtarget_pars_vertex>
#include <skinning_pars_vertex>
#include <logdepthbuf_pars_vertex>
#include <clipping_planes_pars_vertex>
varying vec2 vHighPrecisionZW;
void main() {
	#include <uv_vertex>
	#include <batching_vertex>
	#include <skinbase_vertex>
	#include <morphinstance_vertex>
	#ifdef USE_DISPLACEMENTMAP
		#include <beginnormal_vertex>
		#include <morphnormal_vertex>
		#include <skinnormal_vertex>
	#endif
	#include <begin_vertex>
	#include <morphtarget_vertex>
	#include <skinning_vertex>
	#include <displacementmap_vertex>
	#include <project_vertex>
	#include <logdepthbuf_vertex>
	#include <clipping_planes_vertex>
	vHighPrecisionZW = gl_Position.zw;
}`,BT=`#if DEPTH_PACKING == 3200
	uniform float opacity;
#endif
#include <common>
#include <packing>
#include <uv_pars_fragment>
#include <map_pars_fragment>
#include <alphamap_pars_fragment>
#include <alphatest_pars_fragment>
#include <alphahash_pars_fragment>
#include <logdepthbuf_pars_fragment>
#include <clipping_planes_pars_fragment>
varying vec2 vHighPrecisionZW;
void main() {
	vec4 diffuseColor = vec4( 1.0 );
	#include <clipping_planes_fragment>
	#if DEPTH_PACKING == 3200
		diffuseColor.a = opacity;
	#endif
	#include <map_fragment>
	#include <alphamap_fragment>
	#include <alphatest_fragment>
	#include <alphahash_fragment>
	#include <logdepthbuf_fragment>
	#ifdef USE_REVERSED_DEPTH_BUFFER
		float fragCoordZ = vHighPrecisionZW[ 0 ] / vHighPrecisionZW[ 1 ];
	#else
		float fragCoordZ = 0.5 * vHighPrecisionZW[ 0 ] / vHighPrecisionZW[ 1 ] + 0.5;
	#endif
	#if DEPTH_PACKING == 3200
		gl_FragColor = vec4( vec3( 1.0 - fragCoordZ ), opacity );
	#elif DEPTH_PACKING == 3201
		gl_FragColor = packDepthToRGBA( fragCoordZ );
	#elif DEPTH_PACKING == 3202
		gl_FragColor = vec4( packDepthToRGB( fragCoordZ ), 1.0 );
	#elif DEPTH_PACKING == 3203
		gl_FragColor = vec4( packDepthToRG( fragCoordZ ), 0.0, 1.0 );
	#endif
}`,IT=`#define DISTANCE
varying vec3 vWorldPosition;
#include <common>
#include <batching_pars_vertex>
#include <uv_pars_vertex>
#include <displacementmap_pars_vertex>
#include <morphtarget_pars_vertex>
#include <skinning_pars_vertex>
#include <clipping_planes_pars_vertex>
void main() {
	#include <uv_vertex>
	#include <batching_vertex>
	#include <skinbase_vertex>
	#include <morphinstance_vertex>
	#ifdef USE_DISPLACEMENTMAP
		#include <beginnormal_vertex>
		#include <morphnormal_vertex>
		#include <skinnormal_vertex>
	#endif
	#include <begin_vertex>
	#include <morphtarget_vertex>
	#include <skinning_vertex>
	#include <displacementmap_vertex>
	#include <project_vertex>
	#include <worldpos_vertex>
	#include <clipping_planes_vertex>
	vWorldPosition = worldPosition.xyz;
}`,HT=`#define DISTANCE
uniform vec3 referencePosition;
uniform float nearDistance;
uniform float farDistance;
varying vec3 vWorldPosition;
#include <common>
#include <uv_pars_fragment>
#include <map_pars_fragment>
#include <alphamap_pars_fragment>
#include <alphatest_pars_fragment>
#include <alphahash_pars_fragment>
#include <clipping_planes_pars_fragment>
void main() {
	vec4 diffuseColor = vec4( 1.0 );
	#include <clipping_planes_fragment>
	#include <map_fragment>
	#include <alphamap_fragment>
	#include <alphatest_fragment>
	#include <alphahash_fragment>
	float dist = length( vWorldPosition - referencePosition );
	dist = ( dist - nearDistance ) / ( farDistance - nearDistance );
	dist = saturate( dist );
	gl_FragColor = vec4( dist, 0.0, 0.0, 1.0 );
}`,GT=`varying vec3 vWorldDirection;
#include <common>
void main() {
	vWorldDirection = transformDirection( position, modelMatrix );
	#include <begin_vertex>
	#include <project_vertex>
}`,VT=`uniform sampler2D tEquirect;
varying vec3 vWorldDirection;
#include <common>
void main() {
	vec3 direction = normalize( vWorldDirection );
	vec2 sampleUV = equirectUv( direction );
	gl_FragColor = texture2D( tEquirect, sampleUV );
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
}`,kT=`uniform float scale;
attribute float lineDistance;
varying float vLineDistance;
#include <common>
#include <uv_pars_vertex>
#include <color_pars_vertex>
#include <fog_pars_vertex>
#include <morphtarget_pars_vertex>
#include <logdepthbuf_pars_vertex>
#include <clipping_planes_pars_vertex>
void main() {
	vLineDistance = scale * lineDistance;
	#include <uv_vertex>
	#include <color_vertex>
	#include <morphinstance_vertex>
	#include <morphcolor_vertex>
	#include <begin_vertex>
	#include <morphtarget_vertex>
	#include <project_vertex>
	#include <logdepthbuf_vertex>
	#include <clipping_planes_vertex>
	#include <fog_vertex>
}`,XT=`uniform vec3 diffuse;
uniform float opacity;
uniform float dashSize;
uniform float totalSize;
varying float vLineDistance;
#include <common>
#include <color_pars_fragment>
#include <uv_pars_fragment>
#include <map_pars_fragment>
#include <fog_pars_fragment>
#include <logdepthbuf_pars_fragment>
#include <clipping_planes_pars_fragment>
void main() {
	vec4 diffuseColor = vec4( diffuse, opacity );
	#include <clipping_planes_fragment>
	if ( mod( vLineDistance, totalSize ) > dashSize ) {
		discard;
	}
	vec3 outgoingLight = vec3( 0.0 );
	#include <logdepthbuf_fragment>
	#include <map_fragment>
	#include <color_fragment>
	outgoingLight = diffuseColor.rgb;
	#include <opaque_fragment>
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
	#include <fog_fragment>
	#include <premultiplied_alpha_fragment>
}`,WT=`#include <common>
#include <batching_pars_vertex>
#include <uv_pars_vertex>
#include <envmap_pars_vertex>
#include <color_pars_vertex>
#include <fog_pars_vertex>
#include <morphtarget_pars_vertex>
#include <skinning_pars_vertex>
#include <logdepthbuf_pars_vertex>
#include <clipping_planes_pars_vertex>
void main() {
	#include <uv_vertex>
	#include <color_vertex>
	#include <morphinstance_vertex>
	#include <morphcolor_vertex>
	#include <batching_vertex>
	#if defined ( USE_ENVMAP ) || defined ( USE_SKINNING )
		#include <beginnormal_vertex>
		#include <morphnormal_vertex>
		#include <skinbase_vertex>
		#include <skinnormal_vertex>
		#include <defaultnormal_vertex>
	#endif
	#include <begin_vertex>
	#include <morphtarget_vertex>
	#include <skinning_vertex>
	#include <project_vertex>
	#include <logdepthbuf_vertex>
	#include <clipping_planes_vertex>
	#include <worldpos_vertex>
	#include <envmap_vertex>
	#include <fog_vertex>
}`,qT=`uniform vec3 diffuse;
uniform float opacity;
#ifndef FLAT_SHADED
	varying vec3 vNormal;
#endif
#include <common>
#include <dithering_pars_fragment>
#include <color_pars_fragment>
#include <uv_pars_fragment>
#include <map_pars_fragment>
#include <alphamap_pars_fragment>
#include <alphatest_pars_fragment>
#include <alphahash_pars_fragment>
#include <aomap_pars_fragment>
#include <lightmap_pars_fragment>
#include <envmap_common_pars_fragment>
#include <envmap_pars_fragment>
#include <fog_pars_fragment>
#include <specularmap_pars_fragment>
#include <logdepthbuf_pars_fragment>
#include <clipping_planes_pars_fragment>
void main() {
	vec4 diffuseColor = vec4( diffuse, opacity );
	#include <clipping_planes_fragment>
	#include <logdepthbuf_fragment>
	#include <map_fragment>
	#include <color_fragment>
	#include <alphamap_fragment>
	#include <alphatest_fragment>
	#include <alphahash_fragment>
	#include <specularmap_fragment>
	ReflectedLight reflectedLight = ReflectedLight( vec3( 0.0 ), vec3( 0.0 ), vec3( 0.0 ), vec3( 0.0 ) );
	#ifdef USE_LIGHTMAP
		vec4 lightMapTexel = texture2D( lightMap, vLightMapUv );
		reflectedLight.indirectDiffuse += lightMapTexel.rgb * lightMapIntensity * RECIPROCAL_PI;
	#else
		reflectedLight.indirectDiffuse += vec3( 1.0 );
	#endif
	#include <aomap_fragment>
	reflectedLight.indirectDiffuse *= diffuseColor.rgb;
	vec3 outgoingLight = reflectedLight.indirectDiffuse;
	#include <envmap_fragment>
	#include <opaque_fragment>
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
	#include <fog_fragment>
	#include <premultiplied_alpha_fragment>
	#include <dithering_fragment>
}`,YT=`#define LAMBERT
varying vec3 vViewPosition;
#include <common>
#include <batching_pars_vertex>
#include <uv_pars_vertex>
#include <displacementmap_pars_vertex>
#include <envmap_pars_vertex>
#include <color_pars_vertex>
#include <fog_pars_vertex>
#include <normal_pars_vertex>
#include <morphtarget_pars_vertex>
#include <skinning_pars_vertex>
#include <shadowmap_pars_vertex>
#include <logdepthbuf_pars_vertex>
#include <clipping_planes_pars_vertex>
void main() {
	#include <uv_vertex>
	#include <color_vertex>
	#include <morphinstance_vertex>
	#include <morphcolor_vertex>
	#include <batching_vertex>
	#include <beginnormal_vertex>
	#include <morphnormal_vertex>
	#include <skinbase_vertex>
	#include <skinnormal_vertex>
	#include <defaultnormal_vertex>
	#include <normal_vertex>
	#include <begin_vertex>
	#include <morphtarget_vertex>
	#include <skinning_vertex>
	#include <displacementmap_vertex>
	#include <project_vertex>
	#include <logdepthbuf_vertex>
	#include <clipping_planes_vertex>
	vViewPosition = - mvPosition.xyz;
	#include <worldpos_vertex>
	#include <envmap_vertex>
	#include <shadowmap_vertex>
	#include <fog_vertex>
}`,jT=`#define LAMBERT
uniform vec3 diffuse;
uniform vec3 emissive;
uniform float opacity;
#include <common>
#include <dithering_pars_fragment>
#include <color_pars_fragment>
#include <uv_pars_fragment>
#include <map_pars_fragment>
#include <alphamap_pars_fragment>
#include <alphatest_pars_fragment>
#include <alphahash_pars_fragment>
#include <aomap_pars_fragment>
#include <lightmap_pars_fragment>
#include <emissivemap_pars_fragment>
#include <cube_uv_reflection_fragment>
#include <envmap_common_pars_fragment>
#include <envmap_pars_fragment>
#include <envmap_physical_pars_fragment>
#include <fog_pars_fragment>
#include <bsdfs>
#include <lights_pars_begin>
#include <normal_pars_fragment>
#include <lights_lambert_pars_fragment>
#include <shadowmap_pars_fragment>
#include <bumpmap_pars_fragment>
#include <normalmap_pars_fragment>
#include <specularmap_pars_fragment>
#include <logdepthbuf_pars_fragment>
#include <clipping_planes_pars_fragment>
void main() {
	vec4 diffuseColor = vec4( diffuse, opacity );
	#include <clipping_planes_fragment>
	ReflectedLight reflectedLight = ReflectedLight( vec3( 0.0 ), vec3( 0.0 ), vec3( 0.0 ), vec3( 0.0 ) );
	vec3 totalEmissiveRadiance = emissive;
	#include <logdepthbuf_fragment>
	#include <map_fragment>
	#include <color_fragment>
	#include <alphamap_fragment>
	#include <alphatest_fragment>
	#include <alphahash_fragment>
	#include <specularmap_fragment>
	#include <normal_fragment_begin>
	#include <normal_fragment_maps>
	#include <emissivemap_fragment>
	#include <lights_lambert_fragment>
	#include <lights_fragment_begin>
	#include <lights_fragment_maps>
	#include <lights_fragment_end>
	#include <aomap_fragment>
	vec3 outgoingLight = reflectedLight.directDiffuse + reflectedLight.indirectDiffuse + totalEmissiveRadiance;
	#include <envmap_fragment>
	#include <opaque_fragment>
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
	#include <fog_fragment>
	#include <premultiplied_alpha_fragment>
	#include <dithering_fragment>
}`,ZT=`#define MATCAP
varying vec3 vViewPosition;
#include <common>
#include <batching_pars_vertex>
#include <uv_pars_vertex>
#include <color_pars_vertex>
#include <displacementmap_pars_vertex>
#include <fog_pars_vertex>
#include <normal_pars_vertex>
#include <morphtarget_pars_vertex>
#include <skinning_pars_vertex>
#include <logdepthbuf_pars_vertex>
#include <clipping_planes_pars_vertex>
void main() {
	#include <uv_vertex>
	#include <color_vertex>
	#include <morphinstance_vertex>
	#include <morphcolor_vertex>
	#include <batching_vertex>
	#include <beginnormal_vertex>
	#include <morphnormal_vertex>
	#include <skinbase_vertex>
	#include <skinnormal_vertex>
	#include <defaultnormal_vertex>
	#include <normal_vertex>
	#include <begin_vertex>
	#include <morphtarget_vertex>
	#include <skinning_vertex>
	#include <displacementmap_vertex>
	#include <project_vertex>
	#include <logdepthbuf_vertex>
	#include <clipping_planes_vertex>
	#include <fog_vertex>
	vViewPosition = - mvPosition.xyz;
}`,KT=`#define MATCAP
uniform vec3 diffuse;
uniform float opacity;
uniform sampler2D matcap;
varying vec3 vViewPosition;
#include <common>
#include <dithering_pars_fragment>
#include <color_pars_fragment>
#include <uv_pars_fragment>
#include <map_pars_fragment>
#include <alphamap_pars_fragment>
#include <alphatest_pars_fragment>
#include <alphahash_pars_fragment>
#include <fog_pars_fragment>
#include <normal_pars_fragment>
#include <bumpmap_pars_fragment>
#include <normalmap_pars_fragment>
#include <logdepthbuf_pars_fragment>
#include <clipping_planes_pars_fragment>
void main() {
	vec4 diffuseColor = vec4( diffuse, opacity );
	#include <clipping_planes_fragment>
	#include <logdepthbuf_fragment>
	#include <map_fragment>
	#include <color_fragment>
	#include <alphamap_fragment>
	#include <alphatest_fragment>
	#include <alphahash_fragment>
	#include <normal_fragment_begin>
	#include <normal_fragment_maps>
	vec3 viewDir = normalize( vViewPosition );
	vec3 x = normalize( vec3( viewDir.z, 0.0, - viewDir.x ) );
	vec3 y = cross( viewDir, x );
	vec2 uv = vec2( dot( x, normal ), dot( y, normal ) ) * 0.495 + 0.5;
	#ifdef USE_MATCAP
		vec4 matcapColor = texture2D( matcap, uv );
	#else
		vec4 matcapColor = vec4( vec3( mix( 0.2, 0.8, uv.y ) ), 1.0 );
	#endif
	vec3 outgoingLight = diffuseColor.rgb * matcapColor.rgb;
	#include <opaque_fragment>
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
	#include <fog_fragment>
	#include <premultiplied_alpha_fragment>
	#include <dithering_fragment>
}`,QT=`#define NORMAL
#if defined( FLAT_SHADED ) || defined( USE_BUMPMAP ) || defined( USE_NORMALMAP_TANGENTSPACE )
	varying vec3 vViewPosition;
#endif
#include <common>
#include <batching_pars_vertex>
#include <uv_pars_vertex>
#include <displacementmap_pars_vertex>
#include <normal_pars_vertex>
#include <morphtarget_pars_vertex>
#include <skinning_pars_vertex>
#include <logdepthbuf_pars_vertex>
#include <clipping_planes_pars_vertex>
void main() {
	#include <uv_vertex>
	#include <batching_vertex>
	#include <beginnormal_vertex>
	#include <morphinstance_vertex>
	#include <morphnormal_vertex>
	#include <skinbase_vertex>
	#include <skinnormal_vertex>
	#include <defaultnormal_vertex>
	#include <normal_vertex>
	#include <begin_vertex>
	#include <morphtarget_vertex>
	#include <skinning_vertex>
	#include <displacementmap_vertex>
	#include <project_vertex>
	#include <logdepthbuf_vertex>
	#include <clipping_planes_vertex>
#if defined( FLAT_SHADED ) || defined( USE_BUMPMAP ) || defined( USE_NORMALMAP_TANGENTSPACE )
	vViewPosition = - mvPosition.xyz;
#endif
}`,JT=`#define NORMAL
uniform float opacity;
#if defined( FLAT_SHADED ) || defined( USE_BUMPMAP ) || defined( USE_NORMALMAP_TANGENTSPACE )
	varying vec3 vViewPosition;
#endif
#include <uv_pars_fragment>
#include <normal_pars_fragment>
#include <bumpmap_pars_fragment>
#include <normalmap_pars_fragment>
#include <logdepthbuf_pars_fragment>
#include <clipping_planes_pars_fragment>
void main() {
	vec4 diffuseColor = vec4( 0.0, 0.0, 0.0, opacity );
	#include <clipping_planes_fragment>
	#include <logdepthbuf_fragment>
	#include <normal_fragment_begin>
	#include <normal_fragment_maps>
	gl_FragColor = vec4( normalize( normal ) * 0.5 + 0.5, diffuseColor.a );
	#ifdef OPAQUE
		gl_FragColor.a = 1.0;
	#endif
}`,$T=`#define PHONG
varying vec3 vViewPosition;
#include <common>
#include <batching_pars_vertex>
#include <uv_pars_vertex>
#include <displacementmap_pars_vertex>
#include <envmap_pars_vertex>
#include <color_pars_vertex>
#include <fog_pars_vertex>
#include <normal_pars_vertex>
#include <morphtarget_pars_vertex>
#include <skinning_pars_vertex>
#include <shadowmap_pars_vertex>
#include <logdepthbuf_pars_vertex>
#include <clipping_planes_pars_vertex>
void main() {
	#include <uv_vertex>
	#include <color_vertex>
	#include <morphcolor_vertex>
	#include <batching_vertex>
	#include <beginnormal_vertex>
	#include <morphinstance_vertex>
	#include <morphnormal_vertex>
	#include <skinbase_vertex>
	#include <skinnormal_vertex>
	#include <defaultnormal_vertex>
	#include <normal_vertex>
	#include <begin_vertex>
	#include <morphtarget_vertex>
	#include <skinning_vertex>
	#include <displacementmap_vertex>
	#include <project_vertex>
	#include <logdepthbuf_vertex>
	#include <clipping_planes_vertex>
	vViewPosition = - mvPosition.xyz;
	#include <worldpos_vertex>
	#include <envmap_vertex>
	#include <shadowmap_vertex>
	#include <fog_vertex>
}`,e2=`#define PHONG
uniform vec3 diffuse;
uniform vec3 emissive;
uniform vec3 specular;
uniform float shininess;
uniform float opacity;
#include <common>
#include <dithering_pars_fragment>
#include <color_pars_fragment>
#include <uv_pars_fragment>
#include <map_pars_fragment>
#include <alphamap_pars_fragment>
#include <alphatest_pars_fragment>
#include <alphahash_pars_fragment>
#include <aomap_pars_fragment>
#include <lightmap_pars_fragment>
#include <emissivemap_pars_fragment>
#include <cube_uv_reflection_fragment>
#include <envmap_common_pars_fragment>
#include <envmap_pars_fragment>
#include <envmap_physical_pars_fragment>
#include <fog_pars_fragment>
#include <bsdfs>
#include <lights_pars_begin>
#include <normal_pars_fragment>
#include <lights_phong_pars_fragment>
#include <shadowmap_pars_fragment>
#include <bumpmap_pars_fragment>
#include <normalmap_pars_fragment>
#include <specularmap_pars_fragment>
#include <logdepthbuf_pars_fragment>
#include <clipping_planes_pars_fragment>
void main() {
	vec4 diffuseColor = vec4( diffuse, opacity );
	#include <clipping_planes_fragment>
	ReflectedLight reflectedLight = ReflectedLight( vec3( 0.0 ), vec3( 0.0 ), vec3( 0.0 ), vec3( 0.0 ) );
	vec3 totalEmissiveRadiance = emissive;
	#include <logdepthbuf_fragment>
	#include <map_fragment>
	#include <color_fragment>
	#include <alphamap_fragment>
	#include <alphatest_fragment>
	#include <alphahash_fragment>
	#include <specularmap_fragment>
	#include <normal_fragment_begin>
	#include <normal_fragment_maps>
	#include <emissivemap_fragment>
	#include <lights_phong_fragment>
	#include <lights_fragment_begin>
	#include <lights_fragment_maps>
	#include <lights_fragment_end>
	#include <aomap_fragment>
	vec3 outgoingLight = reflectedLight.directDiffuse + reflectedLight.indirectDiffuse + reflectedLight.directSpecular + reflectedLight.indirectSpecular + totalEmissiveRadiance;
	#include <envmap_fragment>
	#include <opaque_fragment>
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
	#include <fog_fragment>
	#include <premultiplied_alpha_fragment>
	#include <dithering_fragment>
}`,t2=`#define STANDARD
varying vec3 vViewPosition;
#ifdef USE_TRANSMISSION
	varying vec3 vWorldPosition;
#endif
#include <common>
#include <batching_pars_vertex>
#include <uv_pars_vertex>
#include <displacementmap_pars_vertex>
#include <color_pars_vertex>
#include <fog_pars_vertex>
#include <normal_pars_vertex>
#include <morphtarget_pars_vertex>
#include <skinning_pars_vertex>
#include <shadowmap_pars_vertex>
#include <logdepthbuf_pars_vertex>
#include <clipping_planes_pars_vertex>
void main() {
	#include <uv_vertex>
	#include <color_vertex>
	#include <morphinstance_vertex>
	#include <morphcolor_vertex>
	#include <batching_vertex>
	#include <beginnormal_vertex>
	#include <morphnormal_vertex>
	#include <skinbase_vertex>
	#include <skinnormal_vertex>
	#include <defaultnormal_vertex>
	#include <normal_vertex>
	#include <begin_vertex>
	#include <morphtarget_vertex>
	#include <skinning_vertex>
	#include <displacementmap_vertex>
	#include <project_vertex>
	#include <logdepthbuf_vertex>
	#include <clipping_planes_vertex>
	vViewPosition = - mvPosition.xyz;
	#include <worldpos_vertex>
	#include <shadowmap_vertex>
	#include <fog_vertex>
#ifdef USE_TRANSMISSION
	vWorldPosition = worldPosition.xyz;
#endif
}`,n2=`#define STANDARD
#ifdef PHYSICAL
	#define IOR
	#define USE_SPECULAR
#endif
uniform vec3 diffuse;
uniform vec3 emissive;
uniform float roughness;
uniform float metalness;
uniform float opacity;
#ifdef IOR
	uniform float ior;
#endif
#ifdef USE_SPECULAR
	uniform float specularIntensity;
	uniform vec3 specularColor;
	#ifdef USE_SPECULAR_COLORMAP
		uniform sampler2D specularColorMap;
	#endif
	#ifdef USE_SPECULAR_INTENSITYMAP
		uniform sampler2D specularIntensityMap;
	#endif
#endif
#ifdef USE_CLEARCOAT
	uniform float clearcoat;
	uniform float clearcoatRoughness;
#endif
#ifdef USE_DISPERSION
	uniform float dispersion;
#endif
#ifdef USE_RETROREFLECTION
	uniform float retroreflectivity;
#endif
#ifdef USE_IRIDESCENCE
	uniform float iridescence;
	uniform float iridescenceIOR;
	uniform float iridescenceThicknessMinimum;
	uniform float iridescenceThicknessMaximum;
#endif
#ifdef USE_SHEEN
	uniform vec3 sheenColor;
	uniform float sheenRoughness;
	#ifdef USE_SHEEN_COLORMAP
		uniform sampler2D sheenColorMap;
	#endif
	#ifdef USE_SHEEN_ROUGHNESSMAP
		uniform sampler2D sheenRoughnessMap;
	#endif
#endif
#ifdef USE_ANISOTROPY
	uniform vec2 anisotropyVector;
	#ifdef USE_ANISOTROPYMAP
		uniform sampler2D anisotropyMap;
	#endif
#endif
varying vec3 vViewPosition;
#include <common>
#include <dithering_pars_fragment>
#include <color_pars_fragment>
#include <uv_pars_fragment>
#include <map_pars_fragment>
#include <alphamap_pars_fragment>
#include <alphatest_pars_fragment>
#include <alphahash_pars_fragment>
#include <aomap_pars_fragment>
#include <lightmap_pars_fragment>
#include <emissivemap_pars_fragment>
#include <iridescence_fragment>
#include <cube_uv_reflection_fragment>
#include <envmap_common_pars_fragment>
#include <envmap_physical_pars_fragment>
#include <fog_pars_fragment>
#include <lights_pars_begin>
#include <normal_pars_fragment>
#include <lights_physical_pars_fragment>
#include <transmission_pars_fragment>
#include <shadowmap_pars_fragment>
#include <bumpmap_pars_fragment>
#include <normalmap_pars_fragment>
#include <clearcoat_pars_fragment>
#include <iridescence_pars_fragment>
#include <roughnessmap_pars_fragment>
#include <metalnessmap_pars_fragment>
#include <logdepthbuf_pars_fragment>
#include <clipping_planes_pars_fragment>
void main() {
	vec4 diffuseColor = vec4( diffuse, opacity );
	#include <clipping_planes_fragment>
	ReflectedLight reflectedLight = ReflectedLight( vec3( 0.0 ), vec3( 0.0 ), vec3( 0.0 ), vec3( 0.0 ) );
	vec3 totalEmissiveRadiance = emissive;
	#include <logdepthbuf_fragment>
	#include <map_fragment>
	#include <color_fragment>
	#include <alphamap_fragment>
	#include <alphatest_fragment>
	#include <alphahash_fragment>
	#include <roughnessmap_fragment>
	#include <metalnessmap_fragment>
	#include <normal_fragment_begin>
	#include <normal_fragment_maps>
	#include <clearcoat_normal_fragment_begin>
	#include <clearcoat_normal_fragment_maps>
	#include <emissivemap_fragment>
	#include <lights_physical_fragment>
	#include <lights_fragment_begin>
	#include <lights_fragment_maps>
	#include <lights_fragment_end>
	#include <aomap_fragment>
	vec3 totalDiffuse = reflectedLight.directDiffuse + reflectedLight.indirectDiffuse;
	vec3 totalSpecular = reflectedLight.directSpecular + reflectedLight.indirectSpecular;
	#include <transmission_fragment>
	vec3 outgoingLight = totalDiffuse + totalSpecular + totalEmissiveRadiance;
	#ifdef USE_SHEEN
 
		outgoingLight = outgoingLight + sheenSpecularDirect + sheenSpecularIndirect;
 
 	#endif
	#ifdef USE_CLEARCOAT
		float dotNVcc = saturate( dot( geometryClearcoatNormal, geometryViewDir ) );
		vec3 Fcc = F_Schlick( material.clearcoatF0, material.clearcoatF90, dotNVcc );
		outgoingLight = outgoingLight * ( 1.0 - material.clearcoat * Fcc ) + ( clearcoatSpecularDirect + clearcoatSpecularIndirect ) * material.clearcoat;
	#endif
	#include <opaque_fragment>
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
	#include <fog_fragment>
	#include <premultiplied_alpha_fragment>
	#include <dithering_fragment>
}`,i2=`#define TOON
varying vec3 vViewPosition;
#include <common>
#include <batching_pars_vertex>
#include <uv_pars_vertex>
#include <displacementmap_pars_vertex>
#include <color_pars_vertex>
#include <fog_pars_vertex>
#include <normal_pars_vertex>
#include <morphtarget_pars_vertex>
#include <skinning_pars_vertex>
#include <shadowmap_pars_vertex>
#include <logdepthbuf_pars_vertex>
#include <clipping_planes_pars_vertex>
void main() {
	#include <uv_vertex>
	#include <color_vertex>
	#include <morphinstance_vertex>
	#include <morphcolor_vertex>
	#include <batching_vertex>
	#include <beginnormal_vertex>
	#include <morphnormal_vertex>
	#include <skinbase_vertex>
	#include <skinnormal_vertex>
	#include <defaultnormal_vertex>
	#include <normal_vertex>
	#include <begin_vertex>
	#include <morphtarget_vertex>
	#include <skinning_vertex>
	#include <displacementmap_vertex>
	#include <project_vertex>
	#include <logdepthbuf_vertex>
	#include <clipping_planes_vertex>
	vViewPosition = - mvPosition.xyz;
	#include <worldpos_vertex>
	#include <shadowmap_vertex>
	#include <fog_vertex>
}`,a2=`#define TOON
uniform vec3 diffuse;
uniform vec3 emissive;
uniform float opacity;
#include <common>
#include <dithering_pars_fragment>
#include <color_pars_fragment>
#include <uv_pars_fragment>
#include <map_pars_fragment>
#include <alphamap_pars_fragment>
#include <alphatest_pars_fragment>
#include <alphahash_pars_fragment>
#include <aomap_pars_fragment>
#include <lightmap_pars_fragment>
#include <emissivemap_pars_fragment>
#include <gradientmap_pars_fragment>
#include <fog_pars_fragment>
#include <bsdfs>
#include <lights_pars_begin>
#include <normal_pars_fragment>
#include <lights_toon_pars_fragment>
#include <shadowmap_pars_fragment>
#include <bumpmap_pars_fragment>
#include <normalmap_pars_fragment>
#include <logdepthbuf_pars_fragment>
#include <clipping_planes_pars_fragment>
void main() {
	vec4 diffuseColor = vec4( diffuse, opacity );
	#include <clipping_planes_fragment>
	ReflectedLight reflectedLight = ReflectedLight( vec3( 0.0 ), vec3( 0.0 ), vec3( 0.0 ), vec3( 0.0 ) );
	vec3 totalEmissiveRadiance = emissive;
	#include <logdepthbuf_fragment>
	#include <map_fragment>
	#include <color_fragment>
	#include <alphamap_fragment>
	#include <alphatest_fragment>
	#include <alphahash_fragment>
	#include <normal_fragment_begin>
	#include <normal_fragment_maps>
	#include <emissivemap_fragment>
	#include <lights_toon_fragment>
	#include <lights_fragment_begin>
	#include <lights_fragment_maps>
	#include <lights_fragment_end>
	#include <aomap_fragment>
	vec3 outgoingLight = reflectedLight.directDiffuse + reflectedLight.indirectDiffuse + totalEmissiveRadiance;
	#include <opaque_fragment>
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
	#include <fog_fragment>
	#include <premultiplied_alpha_fragment>
	#include <dithering_fragment>
}`,r2=`uniform float size;
uniform float scale;
#include <common>
#include <color_pars_vertex>
#include <fog_pars_vertex>
#include <morphtarget_pars_vertex>
#include <logdepthbuf_pars_vertex>
#include <clipping_planes_pars_vertex>
#ifdef USE_POINTS_UV
	varying vec2 vUv;
	uniform mat3 uvTransform;
#endif
void main() {
	#ifdef USE_POINTS_UV
		vUv = ( uvTransform * vec3( uv, 1 ) ).xy;
	#endif
	#include <color_vertex>
	#include <morphinstance_vertex>
	#include <morphcolor_vertex>
	#include <begin_vertex>
	#include <morphtarget_vertex>
	#include <project_vertex>
	gl_PointSize = size;
	#ifdef USE_SIZEATTENUATION
		bool isPerspective = isPerspectiveMatrix( projectionMatrix );
		if ( isPerspective ) gl_PointSize *= ( scale / - mvPosition.z );
	#endif
	#include <logdepthbuf_vertex>
	#include <clipping_planes_vertex>
	#include <worldpos_vertex>
	#include <fog_vertex>
}`,s2=`uniform vec3 diffuse;
uniform float opacity;
#include <common>
#include <color_pars_fragment>
#include <map_particle_pars_fragment>
#include <alphatest_pars_fragment>
#include <alphahash_pars_fragment>
#include <fog_pars_fragment>
#include <logdepthbuf_pars_fragment>
#include <clipping_planes_pars_fragment>
void main() {
	vec4 diffuseColor = vec4( diffuse, opacity );
	#include <clipping_planes_fragment>
	vec3 outgoingLight = vec3( 0.0 );
	#include <logdepthbuf_fragment>
	#include <map_particle_fragment>
	#include <color_fragment>
	#include <alphatest_fragment>
	#include <alphahash_fragment>
	outgoingLight = diffuseColor.rgb;
	#include <opaque_fragment>
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
	#include <fog_fragment>
	#include <premultiplied_alpha_fragment>
}`,o2=`#include <common>
#include <batching_pars_vertex>
#include <fog_pars_vertex>
#include <morphtarget_pars_vertex>
#include <skinning_pars_vertex>
#include <logdepthbuf_pars_vertex>
#include <shadowmap_pars_vertex>
void main() {
	#include <batching_vertex>
	#include <beginnormal_vertex>
	#include <morphinstance_vertex>
	#include <morphnormal_vertex>
	#include <skinbase_vertex>
	#include <skinnormal_vertex>
	#include <defaultnormal_vertex>
	#include <begin_vertex>
	#include <morphtarget_vertex>
	#include <skinning_vertex>
	#include <project_vertex>
	#include <logdepthbuf_vertex>
	#include <worldpos_vertex>
	#include <shadowmap_vertex>
	#include <fog_vertex>
}`,l2=`uniform vec3 color;
uniform float opacity;
#include <common>
#include <fog_pars_fragment>
#include <bsdfs>
#include <lights_pars_begin>
#include <logdepthbuf_pars_fragment>
#include <shadowmap_pars_fragment>
#include <shadowmask_pars_fragment>
void main() {
	#include <logdepthbuf_fragment>
	gl_FragColor = vec4( color, opacity * ( 1.0 - getShadowMask() ) );
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
	#include <fog_fragment>
	#include <premultiplied_alpha_fragment>
}`,c2=`uniform float rotation;
uniform vec2 center;
#include <common>
#include <uv_pars_vertex>
#include <fog_pars_vertex>
#include <logdepthbuf_pars_vertex>
#include <clipping_planes_pars_vertex>
void main() {
	#include <uv_vertex>
	vec4 mvPosition = modelViewMatrix[ 3 ];
	vec2 scale = vec2( length( modelMatrix[ 0 ].xyz ), length( modelMatrix[ 1 ].xyz ) );
	#ifndef USE_SIZEATTENUATION
		bool isPerspective = isPerspectiveMatrix( projectionMatrix );
		if ( isPerspective ) scale *= - mvPosition.z;
	#endif
	vec2 alignedPosition = ( position.xy - ( center - vec2( 0.5 ) ) ) * scale;
	vec2 rotatedPosition;
	rotatedPosition.x = cos( rotation ) * alignedPosition.x - sin( rotation ) * alignedPosition.y;
	rotatedPosition.y = sin( rotation ) * alignedPosition.x + cos( rotation ) * alignedPosition.y;
	mvPosition.xy += rotatedPosition;
	gl_Position = projectionMatrix * mvPosition;
	#include <logdepthbuf_vertex>
	#include <clipping_planes_vertex>
	#include <fog_vertex>
}`,u2=`uniform vec3 diffuse;
uniform float opacity;
#include <common>
#include <uv_pars_fragment>
#include <map_pars_fragment>
#include <alphamap_pars_fragment>
#include <alphatest_pars_fragment>
#include <alphahash_pars_fragment>
#include <fog_pars_fragment>
#include <logdepthbuf_pars_fragment>
#include <clipping_planes_pars_fragment>
void main() {
	vec4 diffuseColor = vec4( diffuse, opacity );
	#include <clipping_planes_fragment>
	vec3 outgoingLight = vec3( 0.0 );
	#include <logdepthbuf_fragment>
	#include <map_fragment>
	#include <alphamap_fragment>
	#include <alphatest_fragment>
	#include <alphahash_fragment>
	outgoingLight = diffuseColor.rgb;
	#include <opaque_fragment>
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
	#include <fog_fragment>
}`,Rt={alphahash_fragment:DM,alphahash_pars_fragment:NM,alphamap_fragment:LM,alphamap_pars_fragment:OM,alphatest_fragment:PM,alphatest_pars_fragment:zM,aomap_fragment:FM,aomap_pars_fragment:BM,batching_pars_vertex:IM,batching_vertex:HM,begin_vertex:GM,beginnormal_vertex:VM,bsdfs:kM,iridescence_fragment:XM,bumpmap_pars_fragment:WM,clipping_planes_fragment:qM,clipping_planes_pars_fragment:YM,clipping_planes_pars_vertex:jM,clipping_planes_vertex:ZM,color_fragment:KM,color_pars_fragment:QM,color_pars_vertex:JM,color_vertex:$M,common:eE,cube_uv_reflection_fragment:tE,defaultnormal_vertex:nE,displacementmap_pars_vertex:iE,displacementmap_vertex:aE,emissivemap_fragment:rE,emissivemap_pars_fragment:sE,colorspace_fragment:oE,colorspace_pars_fragment:lE,envmap_fragment:cE,envmap_common_pars_fragment:uE,envmap_pars_fragment:fE,envmap_pars_vertex:dE,envmap_physical_pars_fragment:ME,envmap_vertex:hE,fog_vertex:pE,fog_pars_vertex:mE,fog_fragment:gE,fog_pars_fragment:xE,gradientmap_pars_fragment:vE,lightmap_pars_fragment:_E,lights_lambert_fragment:yE,lights_lambert_pars_fragment:SE,lights_pars_begin:bE,lights_toon_fragment:EE,lights_toon_pars_fragment:TE,lights_phong_fragment:AE,lights_phong_pars_fragment:wE,lights_physical_fragment:CE,lights_physical_pars_fragment:RE,lights_fragment_begin:UE,lights_fragment_maps:DE,lights_fragment_end:NE,lightprobes_pars_fragment:LE,logdepthbuf_fragment:OE,logdepthbuf_pars_fragment:PE,logdepthbuf_pars_vertex:zE,logdepthbuf_vertex:FE,map_fragment:BE,map_pars_fragment:IE,map_particle_fragment:HE,map_particle_pars_fragment:GE,metalnessmap_fragment:VE,metalnessmap_pars_fragment:kE,morphinstance_vertex:XE,morphcolor_vertex:WE,morphnormal_vertex:qE,morphtarget_pars_vertex:YE,morphtarget_vertex:jE,normal_fragment_begin:ZE,normal_fragment_maps:KE,normal_pars_fragment:QE,normal_pars_vertex:JE,normal_vertex:$E,normalmap_pars_fragment:eT,clearcoat_normal_fragment_begin:tT,clearcoat_normal_fragment_maps:nT,clearcoat_pars_fragment:iT,iridescence_pars_fragment:aT,opaque_fragment:rT,packing:sT,premultiplied_alpha_fragment:oT,project_vertex:lT,dithering_fragment:cT,dithering_pars_fragment:uT,roughnessmap_fragment:fT,roughnessmap_pars_fragment:dT,shadowmap_pars_fragment:hT,shadowmap_pars_vertex:pT,shadowmap_vertex:mT,shadowmask_pars_fragment:gT,skinbase_vertex:xT,skinning_pars_vertex:vT,skinning_vertex:_T,skinnormal_vertex:yT,specularmap_fragment:ST,specularmap_pars_fragment:bT,tonemapping_fragment:MT,tonemapping_pars_fragment:ET,transmission_fragment:TT,transmission_pars_fragment:AT,uv_pars_fragment:wT,uv_pars_vertex:CT,uv_vertex:RT,worldpos_vertex:UT,background_vert:DT,background_frag:NT,backgroundCube_vert:LT,backgroundCube_frag:OT,cube_vert:PT,cube_frag:zT,depth_vert:FT,depth_frag:BT,distance_vert:IT,distance_frag:HT,equirect_vert:GT,equirect_frag:VT,linedashed_vert:kT,linedashed_frag:XT,meshbasic_vert:WT,meshbasic_frag:qT,meshlambert_vert:YT,meshlambert_frag:jT,meshmatcap_vert:ZT,meshmatcap_frag:KT,meshnormal_vert:QT,meshnormal_frag:JT,meshphong_vert:$T,meshphong_frag:e2,meshphysical_vert:t2,meshphysical_frag:n2,meshtoon_vert:i2,meshtoon_frag:a2,points_vert:r2,points_frag:s2,shadow_vert:o2,shadow_frag:l2,sprite_vert:c2,sprite_frag:u2},je={common:{diffuse:{value:new wt(16777215)},opacity:{value:1},map:{value:null},mapTransform:{value:new St},alphaMap:{value:null},alphaMapTransform:{value:new St},alphaTest:{value:0}},specularmap:{specularMap:{value:null},specularMapTransform:{value:new St}},envmap:{envMap:{value:null},envMapRotation:{value:new St},reflectivity:{value:1},ior:{value:1.5},refractionRatio:{value:.98},dfgLUT:{value:null}},aomap:{aoMap:{value:null},aoMapIntensity:{value:1},aoMapTransform:{value:new St}},lightmap:{lightMap:{value:null},lightMapIntensity:{value:1},lightMapTransform:{value:new St}},bumpmap:{bumpMap:{value:null},bumpMapTransform:{value:new St},bumpScale:{value:1}},normalmap:{normalMap:{value:null},normalMapTransform:{value:new St},normalScale:{value:new Kt(1,1)}},displacementmap:{displacementMap:{value:null},displacementMapTransform:{value:new St},displacementScale:{value:1},displacementBias:{value:0}},emissivemap:{emissiveMap:{value:null},emissiveMapTransform:{value:new St}},metalnessmap:{metalnessMap:{value:null},metalnessMapTransform:{value:new St}},roughnessmap:{roughnessMap:{value:null},roughnessMapTransform:{value:new St}},gradientmap:{gradientMap:{value:null}},fog:{fogDensity:{value:25e-5},fogNear:{value:1},fogFar:{value:2e3},fogColor:{value:new wt(16777215)}},lights:{ambientLightColor:{value:[]},lightProbe:{value:[]},sunLights:{value:[],properties:{direction:{},color:{}}},sunLightShadows:{value:[],properties:{shadowIntensity:1,shadowBias:{},shadowNormalBias:{},shadowRadius:{},shadowMapSize:{}}},sunShadowMatrix:{value:[]},sunShadowCascade:{value:[]},directionalLights:{value:[],properties:{direction:{},color:{}}},directionalLightShadows:{value:[],properties:{shadowIntensity:1,shadowBias:{},shadowNormalBias:{},shadowRadius:{},shadowMapSize:{}}},directionalShadowMatrix:{value:[]},spotLights:{value:[],properties:{color:{},position:{},direction:{},distance:{},coneCos:{},penumbraCos:{},decay:{}}},spotLightShadows:{value:[],properties:{shadowIntensity:1,shadowBias:{},shadowNormalBias:{},shadowRadius:{},shadowMapSize:{}}},spotLightMap:{value:[]},spotLightMatrix:{value:[]},pointLights:{value:[],properties:{color:{},position:{},decay:{},distance:{}}},pointLightShadows:{value:[],properties:{shadowIntensity:1,shadowBias:{},shadowNormalBias:{},shadowRadius:{},shadowMapSize:{},shadowCameraNear:{},shadowCameraFar:{}}},pointShadowMatrix:{value:[]},hemisphereLights:{value:[],properties:{direction:{},skyColor:{},groundColor:{}}},rectAreaLights:{value:[],properties:{color:{},position:{},width:{},height:{}}},ltc_1:{value:null},ltc_2:{value:null},probesSH:{value:null},probesMin:{value:new Q},probesMax:{value:new Q},probesResolution:{value:new Q}},points:{diffuse:{value:new wt(16777215)},opacity:{value:1},size:{value:1},scale:{value:1},map:{value:null},alphaMap:{value:null},alphaMapTransform:{value:new St},alphaTest:{value:0},uvTransform:{value:new St}},sprite:{diffuse:{value:new wt(16777215)},opacity:{value:1},center:{value:new Kt(.5,.5)},rotation:{value:0},map:{value:null},mapTransform:{value:new St},alphaMap:{value:null},alphaMapTransform:{value:new St},alphaTest:{value:0}}},Ha={basic:{uniforms:Mi([je.common,je.specularmap,je.envmap,je.aomap,je.lightmap,je.fog]),vertexShader:Rt.meshbasic_vert,fragmentShader:Rt.meshbasic_frag},lambert:{uniforms:Mi([je.common,je.specularmap,je.envmap,je.aomap,je.lightmap,je.emissivemap,je.bumpmap,je.normalmap,je.displacementmap,je.fog,je.lights,{emissive:{value:new wt(0)},envMapIntensity:{value:1}}]),vertexShader:Rt.meshlambert_vert,fragmentShader:Rt.meshlambert_frag},phong:{uniforms:Mi([je.common,je.specularmap,je.envmap,je.aomap,je.lightmap,je.emissivemap,je.bumpmap,je.normalmap,je.displacementmap,je.fog,je.lights,{emissive:{value:new wt(0)},specular:{value:new wt(1118481)},shininess:{value:30},envMapIntensity:{value:1}}]),vertexShader:Rt.meshphong_vert,fragmentShader:Rt.meshphong_frag},standard:{uniforms:Mi([je.common,je.envmap,je.aomap,je.lightmap,je.emissivemap,je.bumpmap,je.normalmap,je.displacementmap,je.roughnessmap,je.metalnessmap,je.fog,je.lights,{emissive:{value:new wt(0)},roughness:{value:1},metalness:{value:0},envMapIntensity:{value:1}}]),vertexShader:Rt.meshphysical_vert,fragmentShader:Rt.meshphysical_frag},toon:{uniforms:Mi([je.common,je.aomap,je.lightmap,je.emissivemap,je.bumpmap,je.normalmap,je.displacementmap,je.gradientmap,je.fog,je.lights,{emissive:{value:new wt(0)}}]),vertexShader:Rt.meshtoon_vert,fragmentShader:Rt.meshtoon_frag},matcap:{uniforms:Mi([je.common,je.bumpmap,je.normalmap,je.displacementmap,je.fog,{matcap:{value:null}}]),vertexShader:Rt.meshmatcap_vert,fragmentShader:Rt.meshmatcap_frag},points:{uniforms:Mi([je.points,je.fog]),vertexShader:Rt.points_vert,fragmentShader:Rt.points_frag},dashed:{uniforms:Mi([je.common,je.fog,{scale:{value:1},dashSize:{value:1},totalSize:{value:2}}]),vertexShader:Rt.linedashed_vert,fragmentShader:Rt.linedashed_frag},depth:{uniforms:Mi([je.common,je.displacementmap]),vertexShader:Rt.depth_vert,fragmentShader:Rt.depth_frag},normal:{uniforms:Mi([je.common,je.bumpmap,je.normalmap,je.displacementmap,{opacity:{value:1}}]),vertexShader:Rt.meshnormal_vert,fragmentShader:Rt.meshnormal_frag},sprite:{uniforms:Mi([je.sprite,je.fog]),vertexShader:Rt.sprite_vert,fragmentShader:Rt.sprite_frag},background:{uniforms:{uvTransform:{value:new St},t2D:{value:null},backgroundIntensity:{value:1}},vertexShader:Rt.background_vert,fragmentShader:Rt.background_frag},backgroundCube:{uniforms:{envMap:{value:null},backgroundBlurriness:{value:0},backgroundIntensity:{value:1},backgroundRotation:{value:new St}},vertexShader:Rt.backgroundCube_vert,fragmentShader:Rt.backgroundCube_frag},cube:{uniforms:{tCube:{value:null},tFlip:{value:-1},opacity:{value:1}},vertexShader:Rt.cube_vert,fragmentShader:Rt.cube_frag},equirect:{uniforms:{tEquirect:{value:null}},vertexShader:Rt.equirect_vert,fragmentShader:Rt.equirect_frag},distance:{uniforms:Mi([je.common,je.displacementmap,{referencePosition:{value:new Q},nearDistance:{value:1},farDistance:{value:1e3}}]),vertexShader:Rt.distance_vert,fragmentShader:Rt.distance_frag},shadow:{uniforms:Mi([je.lights,je.fog,{color:{value:new wt(0)},opacity:{value:1}}]),vertexShader:Rt.shadow_vert,fragmentShader:Rt.shadow_frag}};Ha.physical={uniforms:Mi([Ha.standard.uniforms,{clearcoat:{value:0},clearcoatMap:{value:null},clearcoatMapTransform:{value:new St},clearcoatNormalMap:{value:null},clearcoatNormalMapTransform:{value:new St},clearcoatNormalScale:{value:new Kt(1,1)},clearcoatRoughness:{value:0},clearcoatRoughnessMap:{value:null},clearcoatRoughnessMapTransform:{value:new St},dispersion:{value:0},retroreflectivity:{value:0},iridescence:{value:0},iridescenceMap:{value:null},iridescenceMapTransform:{value:new St},iridescenceIOR:{value:1.3},iridescenceThicknessMinimum:{value:100},iridescenceThicknessMaximum:{value:400},iridescenceThicknessMap:{value:null},iridescenceThicknessMapTransform:{value:new St},sheen:{value:0},sheenColor:{value:new wt(0)},sheenColorMap:{value:null},sheenColorMapTransform:{value:new St},sheenRoughness:{value:1},sheenRoughnessMap:{value:null},sheenRoughnessMapTransform:{value:new St},transmission:{value:0},transmissionMap:{value:null},transmissionMapTransform:{value:new St},transmissionSamplerSize:{value:new Kt},transmissionSamplerMap:{value:null},thickness:{value:0},thicknessMap:{value:null},thicknessMapTransform:{value:new St},attenuationDistance:{value:0},attenuationColor:{value:new wt(0)},specularColor:{value:new wt(1,1,1)},specularColorMap:{value:null},specularColorMapTransform:{value:new St},specularIntensity:{value:1},specularIntensityMap:{value:null},specularIntensityMapTransform:{value:new St},anisotropyVector:{value:new Kt},anisotropyMap:{value:null},anisotropyMapTransform:{value:new St}}]),vertexShader:Rt.meshphysical_vert,fragmentShader:Rt.meshphysical_frag};const Cu={r:0,b:0,g:0},f2=new En,k_=new St;k_.set(-1,0,0,0,1,0,0,0,1);function d2(r,e,i,s,l,c){const f=new wt(0);let h=l===!0?0:1,m,p,g=null,v=0,x=null;function _(F){let G=F.isScene===!0?F.background:null;if(G&&G.isTexture){const w=F.backgroundBlurriness>0;G=e.get(G,w)}return G}function E(F){let G=!1;const w=_(F);w===null?b(f,h):w&&w.isColor&&(b(w,1),G=!0);const N=r.xr.getEnvironmentBlendMode();N==="additive"?i.buffers.color.setClear(0,0,0,1,c):N==="alpha-blend"&&i.buffers.color.setClear(0,0,0,0,c),(r.autoClear||G)&&(i.buffers.depth.setTest(!0),i.buffers.depth.setMask(!0),i.buffers.color.setMask(!0),r.clear(r.autoClearColor,r.autoClearDepth,r.autoClearStencil))}function R(F,G){const w=_(G);w&&(w.isCubeTexture||w.mapping===Ku)?(p===void 0&&(p=new ji(new $l(1,1,1),new Yn({name:"BackgroundCubeMaterial",uniforms:Ho(Ha.backgroundCube.uniforms),vertexShader:Ha.backgroundCube.vertexShader,fragmentShader:Ha.backgroundCube.fragmentShader,side:Oi,depthTest:!1,depthWrite:!1,fog:!1,allowOverride:!1})),p.geometry.deleteAttribute("normal"),p.geometry.deleteAttribute("uv"),p.onBeforeRender=function(N,L,z){this.matrixWorld.copyPosition(z.matrixWorld)},Object.defineProperty(p.material,"envMap",{get:function(){return this.uniforms.envMap.value}}),s.update(p)),p.material.uniforms.envMap.value=w,p.material.uniforms.backgroundBlurriness.value=G.backgroundBlurriness,p.material.uniforms.backgroundIntensity.value=G.backgroundIntensity,p.material.uniforms.backgroundRotation.value.setFromMatrix4(f2.makeRotationFromEuler(G.backgroundRotation)).transpose(),w.isCubeTexture&&w.isRenderTargetTexture===!1&&p.material.uniforms.backgroundRotation.value.premultiply(k_),p.material.toneMapped=kt.getTransfer(w.colorSpace)!==cn,(g!==w||v!==w.version||x!==r.toneMapping)&&(p.material.needsUpdate=!0,g=w,v=w.version,x=r.toneMapping),p.layers.enableAll(),F.unshift(p,p.geometry,p.material,0,0,null)):w&&w.isTexture&&(m===void 0&&(m=new ji(new ec(2,2),new Yn({name:"BackgroundMaterial",uniforms:Ho(Ha.background.uniforms),vertexShader:Ha.background.vertexShader,fragmentShader:Ha.background.fragmentShader,side:Ls,depthTest:!1,depthWrite:!1,fog:!1,allowOverride:!1})),m.geometry.deleteAttribute("normal"),Object.defineProperty(m.material,"map",{get:function(){return this.uniforms.t2D.value}}),s.update(m)),m.material.uniforms.t2D.value=w,m.material.uniforms.backgroundIntensity.value=G.backgroundIntensity,m.material.toneMapped=kt.getTransfer(w.colorSpace)!==cn,w.matrixAutoUpdate===!0&&w.updateMatrix(),m.material.uniforms.uvTransform.value.copy(w.matrix),(g!==w||v!==w.version||x!==r.toneMapping)&&(m.material.needsUpdate=!0,g=w,v=w.version,x=r.toneMapping),m.layers.enableAll(),F.unshift(m,m.geometry,m.material,0,0,null))}function b(F,G){F.getRGB(Cu,I_(r)),i.buffers.color.setClear(Cu.r,Cu.g,Cu.b,G,c)}function S(){p!==void 0&&(p.geometry.dispose(),p.material.dispose(),p=void 0),m!==void 0&&(m.geometry.dispose(),m.material.dispose(),m=void 0)}return{getClearColor:function(){return f},setClearColor:function(F,G=1){f.set(F),h=G,b(f,h)},getClearAlpha:function(){return h},setClearAlpha:function(F){h=F,b(f,h)},render:E,addToRenderList:R,dispose:S}}function h2(r,e){const i=r.getParameter(r.MAX_VERTEX_ATTRIBS),s={},l=x(null);let c=l,f=!1;function h(W,J,re,k,K){let B=!1;const V=v(W,k,re,J);c!==V&&(c=V,p(c.object)),B=_(W,k,re,K),B&&E(W,k,re,K),K!==null&&e.update(K,r.ELEMENT_ARRAY_BUFFER),(B||f)&&(f=!1,w(W,J,re,k),K!==null&&r.bindBuffer(r.ELEMENT_ARRAY_BUFFER,e.get(K).buffer))}function m(){return r.createVertexArray()}function p(W){return r.bindVertexArray(W)}function g(W){return r.deleteVertexArray(W)}function v(W,J,re,k){const K=k.wireframe===!0;let B=s[J.id];B===void 0&&(B={},s[J.id]=B);const V=W.isInstancedMesh===!0?W.id:0;let ee=B[V];ee===void 0&&(ee={},B[V]=ee);let oe=ee[re.id];oe===void 0&&(oe={},ee[re.id]=oe);let fe=oe[K];return fe===void 0&&(fe=x(m()),oe[K]=fe),fe}function x(W){const J=[],re=[],k=[];for(let K=0;K<i;K++)J[K]=0,re[K]=0,k[K]=0;return{geometry:null,program:null,wireframe:!1,newAttributes:J,enabledAttributes:re,attributeDivisors:k,object:W,attributes:{},index:null}}function _(W,J,re,k){const K=c.attributes,B=J.attributes;let V=0;const ee=re.getAttributes();for(const oe in ee)if(ee[oe].location>=0){const D=K[oe];let se=B[oe];if(se===void 0&&(oe==="instanceMatrix"&&W.instanceMatrix&&(se=W.instanceMatrix),oe==="instanceColor"&&W.instanceColor&&(se=W.instanceColor)),D===void 0||D.attribute!==se||se&&D.data!==se.data)return!0;V++}return c.attributesNum!==V||c.index!==k}function E(W,J,re,k){const K={},B=J.attributes;let V=0;const ee=re.getAttributes();for(const oe in ee)if(ee[oe].location>=0){let D=B[oe];D===void 0&&(oe==="instanceMatrix"&&W.instanceMatrix&&(D=W.instanceMatrix),oe==="instanceColor"&&W.instanceColor&&(D=W.instanceColor));const se={};se.attribute=D,D&&D.data&&(se.data=D.data),K[oe]=se,V++}c.attributes=K,c.attributesNum=V,c.index=k}function R(){const W=c.newAttributes;for(let J=0,re=W.length;J<re;J++)W[J]=0}function b(W){S(W,0)}function S(W,J){const re=c.newAttributes,k=c.enabledAttributes,K=c.attributeDivisors;re[W]=1,k[W]===0&&(r.enableVertexAttribArray(W),k[W]=1),K[W]!==J&&(r.vertexAttribDivisor(W,J),K[W]=J)}function F(){const W=c.newAttributes,J=c.enabledAttributes;for(let re=0,k=J.length;re<k;re++)J[re]!==W[re]&&(r.disableVertexAttribArray(re),J[re]=0)}function G(W,J,re,k,K,B,V){V===!0?r.vertexAttribIPointer(W,J,re,K,B):r.vertexAttribPointer(W,J,re,k,K,B)}function w(W,J,re,k){R();const K=k.attributes,B=re.getAttributes(),V=J.defaultAttributeValues;for(const ee in B){const oe=B[ee];if(oe.location>=0){let fe=K[ee];if(fe===void 0&&(ee==="instanceMatrix"&&W.instanceMatrix&&(fe=W.instanceMatrix),ee==="instanceColor"&&W.instanceColor&&(fe=W.instanceColor)),fe!==void 0){const D=fe.normalized,se=fe.itemSize,_e=e.get(fe);if(_e===void 0)continue;const De=_e.buffer,ze=_e.type,Xe=_e.bytesPerElement,ue=ze===r.INT||ze===r.UNSIGNED_INT||fe.gpuType===Bp;if(fe.isInterleavedBufferAttribute){const Se=fe.data,Re=Se.stride,at=fe.offset;if(Se.isInstancedInterleavedBuffer){for(let Ge=0;Ge<oe.locationSize;Ge++)S(oe.location+Ge,Se.meshPerAttribute);W.isInstancedMesh!==!0&&k._maxInstanceCount===void 0&&(k._maxInstanceCount=Se.meshPerAttribute*Se.count)}else for(let Ge=0;Ge<oe.locationSize;Ge++)b(oe.location+Ge);r.bindBuffer(r.ARRAY_BUFFER,De);for(let Ge=0;Ge<oe.locationSize;Ge++)G(oe.location+Ge,se/oe.locationSize,ze,D,Re*Xe,(at+se/oe.locationSize*Ge)*Xe,ue)}else{if(fe.isInstancedBufferAttribute){for(let Se=0;Se<oe.locationSize;Se++)S(oe.location+Se,fe.meshPerAttribute);W.isInstancedMesh!==!0&&k._maxInstanceCount===void 0&&(k._maxInstanceCount=fe.meshPerAttribute*fe.count)}else for(let Se=0;Se<oe.locationSize;Se++)b(oe.location+Se);r.bindBuffer(r.ARRAY_BUFFER,De);for(let Se=0;Se<oe.locationSize;Se++)G(oe.location+Se,se/oe.locationSize,ze,D,se*Xe,se/oe.locationSize*Se*Xe,ue)}}else if(V!==void 0){const D=V[ee];if(D!==void 0)switch(D.length){case 2:r.vertexAttrib2fv(oe.location,D);break;case 3:r.vertexAttrib3fv(oe.location,D);break;case 4:r.vertexAttrib4fv(oe.location,D);break;default:r.vertexAttrib1fv(oe.location,D)}}}}F()}function N(){O();for(const W in s){const J=s[W];for(const re in J){const k=J[re];for(const K in k){const B=k[K];for(const V in B)g(B[V].object),delete B[V];delete k[K]}}delete s[W]}}function L(W){if(s[W.id]===void 0)return;const J=s[W.id];for(const re in J){const k=J[re];for(const K in k){const B=k[K];for(const V in B)g(B[V].object),delete B[V];delete k[K]}}delete s[W.id]}function z(W){for(const J in s){const re=s[J];for(const k in re){const K=re[k];if(K[W.id]===void 0)continue;const B=K[W.id];for(const V in B)g(B[V].object),delete B[V];delete K[W.id]}}}function T(W){for(const J in s){const re=s[J],k=W.isInstancedMesh===!0?W.id:0,K=re[k];if(K!==void 0){for(const B in K){const V=K[B];for(const ee in V)g(V[ee].object),delete V[ee];delete K[B]}delete re[k],Object.keys(re).length===0&&delete s[J]}}}function O(){I(),f=!0,c!==l&&(c=l,p(c.object))}function I(){l.geometry=null,l.program=null,l.wireframe=!1}return{setup:h,reset:O,resetDefaultState:I,dispose:N,releaseStatesOfGeometry:L,releaseStatesOfObject:T,releaseStatesOfProgram:z,initAttributes:R,enableAttribute:b,disableUnusedAttributes:F}}function p2(r,e,i){let s;function l(m){s=m}function c(m,p){r.drawArrays(s,m,p),i.update(p,s,1)}function f(m,p,g){g!==0&&(r.drawArraysInstanced(s,m,p,g),i.update(p,s,g))}function h(m,p,g){if(g===0)return;e.get("WEBGL_multi_draw").multiDrawArraysWEBGL(s,m,0,p,0,g);let x=0;for(let _=0;_<g;_++)x+=p[_];i.update(x,s,1)}this.setMode=l,this.render=c,this.renderInstances=f,this.renderMultiDraw=h}function m2(r,e,i,s){let l;function c(){if(l!==void 0)return l;if(e.has("EXT_texture_filter_anisotropic")===!0){const z=e.get("EXT_texture_filter_anisotropic");l=r.getParameter(z.MAX_TEXTURE_MAX_ANISOTROPY_EXT)}else l=0;return l}function f(z){return!(z!==Ta&&s.convert(z)!==r.getParameter(r.IMPLEMENTATION_COLOR_READ_FORMAT))}function h(z){const T=z===Wa&&(e.has("EXT_color_buffer_half_float")||e.has("EXT_color_buffer_float"));return!(z!==fa&&z!==Ga&&!T&&s.convert(z)!==r.getParameter(r.IMPLEMENTATION_COLOR_READ_TYPE))}function m(z){if(z==="highp"){if(r.getShaderPrecisionFormat(r.VERTEX_SHADER,r.HIGH_FLOAT).precision>0&&r.getShaderPrecisionFormat(r.FRAGMENT_SHADER,r.HIGH_FLOAT).precision>0)return"highp";z="mediump"}return z==="mediump"&&r.getShaderPrecisionFormat(r.VERTEX_SHADER,r.MEDIUM_FLOAT).precision>0&&r.getShaderPrecisionFormat(r.FRAGMENT_SHADER,r.MEDIUM_FLOAT).precision>0?"mediump":"lowp"}let p=i.precision!==void 0?i.precision:"highp";const g=m(p);g!==p&&(ht("WebGLRenderer:",p,"not supported, using",g,"instead."),p=g);const v=i.logarithmicDepthBuffer===!0,x=i.reversedDepthBuffer===!0&&e.has("EXT_clip_control");i.reversedDepthBuffer===!0&&x===!1&&ht("WebGLRenderer: Unable to use reversed depth buffer due to missing EXT_clip_control extension. Fallback to default depth buffer.");const _=r.getParameter(r.MAX_TEXTURE_IMAGE_UNITS),E=r.getParameter(r.MAX_VERTEX_TEXTURE_IMAGE_UNITS),R=r.getParameter(r.MAX_TEXTURE_SIZE),b=r.getParameter(r.MAX_CUBE_MAP_TEXTURE_SIZE),S=r.getParameter(r.MAX_VERTEX_ATTRIBS),F=r.getParameter(r.MAX_VERTEX_UNIFORM_VECTORS),G=r.getParameter(r.MAX_VARYING_VECTORS),w=r.getParameter(r.MAX_FRAGMENT_UNIFORM_VECTORS),N=r.getParameter(r.MAX_SAMPLES),L=r.getParameter(r.SAMPLES);return{isWebGL2:!0,getMaxAnisotropy:c,getMaxPrecision:m,textureFormatReadable:f,textureTypeReadable:h,precision:p,logarithmicDepthBuffer:v,reversedDepthBuffer:x,maxTextures:_,maxVertexTextures:E,maxTextureSize:R,maxCubemapSize:b,maxAttributes:S,maxVertexUniforms:F,maxVaryings:G,maxFragmentUniforms:w,maxSamples:N,samples:L}}function g2(r){const e=this;let i=null,s=0,l=!1,c=!1;const f=new ts,h=new St,m={value:null,needsUpdate:!1};this.uniform=m,this.numPlanes=0,this.numIntersection=0,this.init=function(v,x){const _=v.length!==0||x||s!==0||l;return l=x,s=v.length,_},this.beginShadows=function(){c=!0,g(null)},this.endShadows=function(){c=!1},this.setGlobalState=function(v,x){i=g(v,x,0)},this.setState=function(v,x,_){const E=v.clippingPlanes,R=v.clipIntersection,b=v.clipShadows,S=r.get(v);if(!l||E===null||E.length===0||c&&!b)c?g(null):p();else{const F=c?0:s,G=F*4;let w=S.clippingState||null;m.value=w,w=g(E,x,G,_);for(let N=0;N!==G;++N)w[N]=i[N];S.clippingState=w,this.numIntersection=R?this.numPlanes:0,this.numPlanes+=F}};function p(){m.value!==i&&(m.value=i,m.needsUpdate=s>0),e.numPlanes=s,e.numIntersection=0}function g(v,x,_,E){const R=v!==null?v.length:0;let b=null;if(R!==0){if(b=m.value,E!==!0||b===null){const S=_+R*4,F=x.matrixWorldInverse;h.getNormalMatrix(F),(b===null||b.length<S)&&(b=new Float32Array(S));for(let G=0,w=_;G!==R;++G,w+=4)f.copy(v[G]).applyMatrix4(F,h),f.normal.toArray(b,w),b[w+3]=f.constant}m.value=b,m.needsUpdate=!0}return e.numPlanes=R,e.numIntersection=0,b}}const Po=4,x2=6,v2=20,_2=256,zl=new G_,Dv=new wt;let zh=null,Fh=0,Bh=0,Ih=!1;const y2=new Q,Cs=new Q;class Nv{constructor(e){this._renderer=e,this._pingPongRenderTarget=null,this._lodMax=0,this._cubeSize=0,this._sizeLods=[],this._lodMeshes=[],this._backgroundBox=null,this._cubemapMaterial=null,this._equirectMaterial=null,this._blurMaterial=null,this._ggxMaterial=null}fromScene(e,i=0,s=.1,l=100,c={}){const{size:f=256,position:h=y2}=c;zh=this._renderer.getRenderTarget(),Fh=this._renderer.getActiveCubeFace(),Bh=this._renderer.getActiveMipmapLevel(),Ih=this._renderer.xr.enabled,this._renderer.xr.enabled=!1,this._setSize(f);const m=this._allocateTargets();return m.depthBuffer=!0,this._sceneToCubeUV(e,s,l,m,h),i>0&&this._blur(m,0,0,i),this._applyPMREM(m),this._cleanup(m),m}fromEquirectangular(e,i=null){return this._fromTexture(e,i)}fromCubemap(e,i=null){return this._fromTexture(e,i)}compileCubemapShader(){this._cubemapMaterial===null&&(this._cubemapMaterial=Pv(),this._compileMaterial(this._cubemapMaterial))}compileEquirectangularShader(){this._equirectMaterial===null&&(this._equirectMaterial=Ov(),this._compileMaterial(this._equirectMaterial))}dispose(){this._dispose(),this._cubemapMaterial!==null&&this._cubemapMaterial.dispose(),this._equirectMaterial!==null&&this._equirectMaterial.dispose(),this._backgroundBox!==null&&(this._backgroundBox.geometry.dispose(),this._backgroundBox.material.dispose())}_setSize(e){this._lodMax=Math.floor(Math.log2(e)),this._cubeSize=Math.pow(2,this._lodMax)}_dispose(){this._blurMaterial!==null&&this._blurMaterial.dispose(),this._ggxMaterial!==null&&this._ggxMaterial.dispose(),this._pingPongRenderTarget!==null&&this._pingPongRenderTarget.dispose();for(let e=0;e<this._lodMeshes.length;e++)this._lodMeshes[e].geometry.dispose()}_cleanup(e){this._renderer.setRenderTarget(zh,Fh,Bh),this._renderer.xr.enabled=Ih,e.scissorTest=!1,Do(e,0,0,e.width,e.height)}_fromTexture(e,i){e.mapping===Os||e.mapping===Io?this._setSize(e.image.length===0?16:e.image[0].width||e.image[0].image.width):this._setSize(e.image.width/4),zh=this._renderer.getRenderTarget(),Fh=this._renderer.getActiveCubeFace(),Bh=this._renderer.getActiveMipmapLevel(),Ih=this._renderer.xr.enabled,this._renderer.xr.enabled=!1;const s=i||this._allocateTargets();return this._textureToCubeUV(e,s),this._applyPMREM(s),this._cleanup(s),s}_allocateTargets(){const e=3*Math.max(this._cubeSize,112),i=4*this._cubeSize,s={magFilter:mi,minFilter:mi,generateMipmaps:!1,type:Wa,format:Ta,colorSpace:ku,depthBuffer:!1},l=Lv(e,i,s);if(this._pingPongRenderTarget===null||this._pingPongRenderTarget.width!==e||this._pingPongRenderTarget.height!==i){this._pingPongRenderTarget!==null&&this._dispose(),this._pingPongRenderTarget=Lv(e,i,s);const{_lodMax:c}=this;({lodMeshes:this._lodMeshes,sizeLods:this._sizeLods}=S2(c)),this._blurMaterial=M2(c,e,i),this._ggxMaterial=b2(c,e,i)}return l}_compileMaterial(e){const i=new ji(new Bn,e);this._renderer.compile(i,zl)}_sceneToCubeUV(e,i,s,l,c){const m=new Yi(90,1,i,s),p=[1,-1,1,1,1,1],g=[1,1,1,-1,-1,-1],v=this._renderer,x=v.autoClear,_=v.toneMapping;v.getClearColor(Dv),v.toneMapping=ka,v.autoClear=!1,v.state.buffers.depth.getReversed()&&(v.setRenderTarget(l),v.clearDepth(),v.setRenderTarget(null)),this._backgroundBox===null&&(this._backgroundBox=new ji(new $l,new Ju({name:"PMREM.Background",side:Oi,depthWrite:!1,depthTest:!1})));const R=this._backgroundBox,b=R.material;let S=!1;const F=e.background;F?F.isColor&&(b.color.copy(F),e.background=null,S=!0):(b.color.copy(Dv),S=!0);for(let G=0;G<6;G++){const w=G%3;w===0?(m.up.set(0,p[G],0),m.position.set(c.x,c.y,c.z),m.lookAt(c.x+g[G],c.y,c.z)):w===1?(m.up.set(0,0,p[G]),m.position.set(c.x,c.y,c.z),m.lookAt(c.x,c.y+g[G],c.z)):(m.up.set(0,p[G],0),m.position.set(c.x,c.y,c.z),m.lookAt(c.x,c.y,c.z+g[G]));const N=this._cubeSize;Do(l,w*N,G>2?N:0,N,N),v.setRenderTarget(l),S&&v.render(R,m),v.render(e,m)}v.toneMapping=_,v.autoClear=x,e.background=F}_textureToCubeUV(e,i){const s=this._renderer,l=e.mapping===Os||e.mapping===Io;l?(this._cubemapMaterial===null&&(this._cubemapMaterial=Pv()),this._cubemapMaterial.uniforms.flipEnvMap.value=e.isRenderTargetTexture===!1?-1:1):this._equirectMaterial===null&&(this._equirectMaterial=Ov());const c=l?this._cubemapMaterial:this._equirectMaterial,f=this._lodMeshes[0];f.material=c;const h=c.uniforms;h.envMap.value=e;const m=this._cubeSize;Do(i,0,0,3*m,2*m),s.setRenderTarget(i),s.render(f,zl)}_applyPMREM(e){const i=this._renderer,s=i.autoClear;i.autoClear=!1;const l=this._lodMeshes.length;for(let c=1;c<l;c++)this._applyGGXFilter(e,c-1,c);i.autoClear=s}_applyGGXFilter(e,i,s){const l=this._renderer,c=this._pingPongRenderTarget,f=this._ggxMaterial,h=this._lodMeshes[s];h.material=f;const m=f.uniforms,p=s/(this._lodMeshes.length-1),g=i/(this._lodMeshes.length-1),v=Math.sqrt(p*p-g*g),x=p*1.25,_=v*x,{_lodMax:E}=this,R=this._sizeLods[s],b=3*R*(s>E-Po?s-E+Po:0),S=4*(this._cubeSize-R);m.envMap.value=e.texture,m.roughness.value=_,m.mipInt.value=E-i,Do(c,b,S,3*R,2*R),l.setRenderTarget(c),l.render(h,zl),m.envMap.value=c.texture,m.roughness.value=0,m.mipInt.value=E-s,Do(e,b,S,3*R,2*R),l.setRenderTarget(e),l.render(h,zl)}_blur(e,i,s,l){const c=this._pingPongRenderTarget,f=Math.min(l,Math.PI)/Math.SQRT2;this._blurPass(e,c,i,s,f),this._blurPass(c,e,s,s,f)}_blurPass(e,i,s,l,c){const f=this._renderer,h=this._blurMaterial,m=this._lodMeshes[l];m.material=h;const p=h.uniforms;p.envMap.value=e.texture,p.sigma.value=c,p.mipInt.value=this._lodMax-s;const g=this._sizeLods[l],v=3*g*(l>this._lodMax-Po?l-this._lodMax+Po:0),x=4*(this._cubeSize-g);Do(i,v,x,3*g,2*g),f.setRenderTarget(i),f.render(m,zl)}}function S2(r){const e=[],i=[];let s=r;const l=r-Po+1+x2;for(let c=0;c<l;c++){const f=Math.pow(2,s);e.push(f);const h=1/(f-2),m=-h,p=1+h,g=[m,m,p,m,p,p,m,m,p,p,m,p],v=6,x=6,_=3,E=new Float32Array(_*x*v),R=new Float32Array(_*x*v);for(let S=0;S<v;S++){const F=S%3*2/3-1,G=S>2?0:-1,w=[F,G,0,F+2/3,G,0,F+2/3,G+1,0,F,G,0,F+2/3,G+1,0,F,G+1,0];E.set(w,_*x*S);for(let N=0;N<x;N++){const L=g[N*2]*2-1,z=g[N*2+1]*2-1;S===0?Cs.set(1,z,L):S===1?Cs.set(-L,1,-z):S===2?Cs.set(-L,z,1):S===3?Cs.set(-1,z,-L):S===4?Cs.set(-L,-1,z):Cs.set(L,z,-1),Cs.toArray(R,(S*x+N)*_)}}const b=new Bn;b.setAttribute("position",new Fn(E,_)),b.setAttribute("outputDirection",new Fn(R,_)),i.push(new ji(b,null)),s>Po&&s--}return{lodMeshes:i,sizeLods:e}}function Lv(r,e,i){const s=new wa(r,e,i);return s.texture.mapping=Ku,s.texture.name="PMREM.cubeUv",s.scissorTest=!0,s}function Do(r,e,i,s,l){r.viewport.set(e,i,s,l),r.scissor.set(e,i,s,l)}function b2(r,e,i){return new Yn({name:"PMREMGGXConvolution",defines:{GGX_SAMPLES:_2,CUBEUV_TEXEL_WIDTH:1/e,CUBEUV_TEXEL_HEIGHT:1/i,CUBEUV_MAX_MIP:`${r}.0`},uniforms:{envMap:{value:null},roughness:{value:0},mipInt:{value:0}},vertexShader:$u(),fragmentShader:`

			precision highp float;
			precision highp int;

			varying vec3 vOutputDirection;

			uniform sampler2D envMap;
			uniform float roughness;
			uniform float mipInt;

			#define ENVMAP_TYPE_CUBE_UV
			#include <cube_uv_reflection_fragment>

			#define PI 3.14159265359

			// Van der Corput radical inverse
			float radicalInverse_VdC(uint bits) {
				bits = (bits << 16u) | (bits >> 16u);
				bits = ((bits & 0x55555555u) << 1u) | ((bits & 0xAAAAAAAAu) >> 1u);
				bits = ((bits & 0x33333333u) << 2u) | ((bits & 0xCCCCCCCCu) >> 2u);
				bits = ((bits & 0x0F0F0F0Fu) << 4u) | ((bits & 0xF0F0F0F0u) >> 4u);
				bits = ((bits & 0x00FF00FFu) << 8u) | ((bits & 0xFF00FF00u) >> 8u);
				return float(bits) * 2.3283064365386963e-10; // / 0x100000000
			}

			// Hammersley sequence
			vec2 hammersley(uint i, uint N) {
				return vec2(float(i) / float(N), radicalInverse_VdC(i));
			}

			// GGX VNDF importance sampling (Eric Heitz 2018)
			// "Sampling the GGX Distribution of Visible Normals"
			// https://jcgt.org/published/0007/04/01/
			vec3 importanceSampleGGX_VNDF(vec2 Xi, vec3 V, float roughness) {
				float alpha = roughness * roughness;

				// Section 4.1: Orthonormal basis
				vec3 T1 = vec3(1.0, 0.0, 0.0);
				vec3 T2 = cross(V, T1);

				// Section 4.2: Parameterization of projected area
				float r = sqrt(Xi.x);
				float phi = 2.0 * PI * Xi.y;
				float t1 = r * cos(phi);
				float t2 = r * sin(phi);
				float s = 0.5 * (1.0 + V.z);
				t2 = (1.0 - s) * sqrt(1.0 - t1 * t1) + s * t2;

				// Section 4.3: Reprojection onto hemisphere
				vec3 Nh = t1 * T1 + t2 * T2 + sqrt(max(0.0, 1.0 - t1 * t1 - t2 * t2)) * V;

				// Section 3.4: Transform back to ellipsoid configuration
				return normalize(vec3(alpha * Nh.x, alpha * Nh.y, max(0.0, Nh.z)));
			}

			void main() {
				vec3 N = normalize(vOutputDirection);
				vec3 V = N; // Assume view direction equals normal for pre-filtering

				vec3 prefilteredColor = vec3(0.0);
				float totalWeight = 0.0;

				// For very low roughness, just sample the environment directly
				if (roughness < 0.001) {
					gl_FragColor = vec4(bilinearCubeUV(envMap, N, mipInt), 1.0);
					return;
				}

				// Tangent space basis for VNDF sampling
				vec3 up = abs(N.z) < 0.999 ? vec3(0.0, 0.0, 1.0) : vec3(1.0, 0.0, 0.0);
				vec3 tangent = normalize(cross(up, N));
				vec3 bitangent = cross(N, tangent);

				for(uint i = 0u; i < uint(GGX_SAMPLES); i++) {
					vec2 Xi = hammersley(i, uint(GGX_SAMPLES));

					// For PMREM, V = N, so in tangent space V is always (0, 0, 1)
					vec3 H_tangent = importanceSampleGGX_VNDF(Xi, vec3(0.0, 0.0, 1.0), roughness);

					// Transform H back to world space
					vec3 H = normalize(tangent * H_tangent.x + bitangent * H_tangent.y + N * H_tangent.z);
					vec3 L = normalize(2.0 * dot(V, H) * H - V);

					float NdotL = max(dot(N, L), 0.0);

					if(NdotL > 0.0) {
						// Sample environment at fixed mip level
						// VNDF importance sampling handles the distribution filtering
						vec3 sampleColor = bilinearCubeUV(envMap, L, mipInt);

						// Weight by NdotL for the split-sum approximation
						// VNDF PDF naturally accounts for the visible microfacet distribution
						prefilteredColor += sampleColor * NdotL;
						totalWeight += NdotL;
					}
				}

				if (totalWeight > 0.0) {
					prefilteredColor = prefilteredColor / totalWeight;
				}

				gl_FragColor = vec4(prefilteredColor, 1.0);
			}
		`,blending:Sr,depthTest:!1,depthWrite:!1})}function M2(r,e,i){return new Yn({name:"SphericalGaussianBlur",defines:{SAMPLES:v2,CUBEUV_TEXEL_WIDTH:1/e,CUBEUV_TEXEL_HEIGHT:1/i,CUBEUV_MAX_MIP:`${r}.0`},uniforms:{envMap:{value:null},sigma:{value:0},mipInt:{value:0}},vertexShader:$u(),fragmentShader:`

			precision highp float;
			precision highp int;

			varying vec3 vOutputDirection;

			uniform sampler2D envMap;
			uniform float sigma;
			uniform float mipInt;

			#define ENVMAP_TYPE_CUBE_UV
			#include <cube_uv_reflection_fragment>

			#define PI 3.14159265359
			#define GOLDEN_ANGLE 2.39996322973

			void main() {

				if ( sigma == 0.0 ) {

					gl_FragColor = vec4( bilinearCubeUV( envMap, vOutputDirection, mipInt ), 1.0 );
					return;

				}

				vec3 outputDirection = normalize( vOutputDirection );

				vec3 up = abs( outputDirection.z ) < 0.999 ? vec3( 0.0, 0.0, 1.0 ) : vec3( 1.0, 0.0, 0.0 );
				vec3 tangent = normalize( cross( up, outputDirection ) );
				vec3 bitangent = cross( outputDirection, tangent );

				// Truncate the kernel at three standard deviations or at the antipode.
				float thetaMax = min( 3.0 * sigma, PI );
				float truncation = 1.0 - exp( - 0.5 * thetaMax * thetaMax / ( sigma * sigma ) );

				vec3 accumColor = vec3( 0.0 );
				float accumWeight = 0.0;

				for ( int i = 0; i < SAMPLES; i ++ ) {

					// Stratified inverse-CDF sampling of the Gaussian, placed on a golden-angle spiral.
					float stratum = ( float( i ) + 0.5 ) / float( SAMPLES );
					float theta = sigma * sqrt( - 2.0 * log( 1.0 - stratum * truncation ) );
					float phi = float( i ) * GOLDEN_ANGLE;

					vec3 offset = cos( phi ) * tangent + sin( phi ) * bitangent;
					vec3 sampleDirection = cos( theta ) * outputDirection + sin( theta ) * offset;

					// Correct the planar sample density to solid angle.
					float weight = sin( theta ) / theta;

					accumColor += weight * bilinearCubeUV( envMap, sampleDirection, mipInt );
					accumWeight += weight;

				}

				gl_FragColor = vec4( accumColor / accumWeight, 1.0 );

			}
		`,blending:Sr,depthTest:!1,depthWrite:!1})}function Ov(){return new Yn({name:"EquirectangularToCubeUV",uniforms:{envMap:{value:null}},vertexShader:$u(),fragmentShader:`

			precision mediump float;
			precision mediump int;

			varying vec3 vOutputDirection;

			uniform sampler2D envMap;

			#include <common>

			void main() {

				vec3 outputDirection = normalize( vOutputDirection );
				vec2 uv = equirectUv( outputDirection );

				gl_FragColor = vec4( texture2D ( envMap, uv ).rgb, 1.0 );

			}
		`,blending:Sr,depthTest:!1,depthWrite:!1})}function Pv(){return new Yn({name:"CubemapToCubeUV",uniforms:{envMap:{value:null},flipEnvMap:{value:-1}},vertexShader:$u(),fragmentShader:`

			precision mediump float;
			precision mediump int;

			uniform float flipEnvMap;

			varying vec3 vOutputDirection;

			uniform samplerCube envMap;

			void main() {

				gl_FragColor = textureCube( envMap, vec3( flipEnvMap * vOutputDirection.x, vOutputDirection.yz ) );

			}
		`,blending:Sr,depthTest:!1,depthWrite:!1})}function $u(){return`

		precision mediump float;
		precision mediump int;

		attribute vec3 outputDirection;

		varying vec3 vOutputDirection;

		void main() {

			vOutputDirection = outputDirection;
			gl_Position = vec4( position, 1.0 );

		}
	`}class X_ extends wa{constructor(e=1,i={}){super(e,e,i),this.isWebGLCubeRenderTarget=!0;const s={width:e,height:e,depth:1},l=[s,s,s,s,s,s];this.texture=new z_(l),this._setTextureOptions(i),this.texture.isRenderTargetTexture=!0}fromEquirectangularTexture(e,i){this.texture.type=i.type,this.texture.colorSpace=i.colorSpace,this.texture.generateMipmaps=i.generateMipmaps,this.texture.minFilter=i.minFilter,this.texture.magFilter=i.magFilter;const s={uniforms:{tEquirect:{value:null}},vertexShader:`

				varying vec3 vWorldDirection;

				vec3 transformDirection( in vec3 dir, in mat4 matrix ) {

					return normalize( ( matrix * vec4( dir, 0.0 ) ).xyz );

				}

				void main() {

					vWorldDirection = transformDirection( position, modelMatrix );

					#include <begin_vertex>
					#include <project_vertex>

				}
			`,fragmentShader:`

				uniform sampler2D tEquirect;

				varying vec3 vWorldDirection;

				#include <common>

				void main() {

					vec3 direction = normalize( vWorldDirection );

					vec2 sampleUV = equirectUv( direction );

					gl_FragColor = texture2D( tEquirect, sampleUV );

				}
			`},l=new $l(5,5,5),c=new Yn({name:"CubemapFromEquirect",uniforms:Ho(s.uniforms),vertexShader:s.vertexShader,fragmentShader:s.fragmentShader,side:Oi,blending:Sr});c.uniforms.tEquirect.value=i;const f=new ji(l,c),h=i.minFilter;return i.minFilter===Rs&&(i.minFilter=mi),new AM(1,10,this).update(e,f),i.minFilter=h,f.geometry.dispose(),f.material.dispose(),this}clear(e,i=!0,s=!0,l=!0){const c=e.getRenderTarget();for(let f=0;f<6;f++)e.setRenderTarget(this,f),e.clear(i,s,l);e.setRenderTarget(c)}}function E2(r){let e=new WeakMap,i=new WeakMap,s=null;function l(x,_=!1){return x==null?null:_?f(x):c(x)}function c(x){if(x&&x.isTexture){const _=x.mapping;if(_===rh||_===sh)if(e.has(x)){const E=e.get(x).texture;return h(E,x.mapping)}else{const E=x.image;if(E&&E.height>0){const R=new X_(E.height);return R.fromEquirectangularTexture(r,x),e.set(x,R),x.addEventListener("dispose",p),h(R.texture,x.mapping)}else return null}}return x}function f(x){if(x&&x.isTexture){const _=x.mapping,E=_===rh||_===sh,R=_===Os||_===Io;if(E||R){let b=i.get(x);const S=b!==void 0?b.texture.pmremVersion:0;if(x.isRenderTargetTexture&&x.pmremVersion!==S)return s===null&&(s=new Nv(r)),b=E?s.fromEquirectangular(x,b):s.fromCubemap(x,b),b.texture.pmremVersion=x.pmremVersion,i.set(x,b),b.texture;if(b!==void 0)return b.texture;{const F=x.image;return E&&F&&F.height>0||R&&F&&m(F)?(s===null&&(s=new Nv(r)),b=E?s.fromEquirectangular(x):s.fromCubemap(x),b.texture.pmremVersion=x.pmremVersion,i.set(x,b),x.addEventListener("dispose",g),b.texture):null}}}return x}function h(x,_){return _===rh?x.mapping=Os:_===sh&&(x.mapping=Io),x}function m(x){let _=0;const E=6;for(let R=0;R<E;R++)x[R]!==void 0&&_++;return _===E}function p(x){const _=x.target;_.removeEventListener("dispose",p);const E=e.get(_);E!==void 0&&(e.delete(_),E.dispose())}function g(x){const _=x.target;_.removeEventListener("dispose",g);const E=i.get(_);E!==void 0&&(i.delete(_),E.dispose())}function v(){e=new WeakMap,i=new WeakMap,s!==null&&(s.dispose(),s=null)}return{get:l,dispose:v}}function T2(r){const e={};function i(s){if(e[s]!==void 0)return e[s];const l=r.getExtension(s);return e[s]=l,l}return{has:function(s){return i(s)!==null},init:function(){i("EXT_color_buffer_float"),i("WEBGL_clip_cull_distance"),i("OES_texture_float_linear"),i("EXT_color_buffer_half_float"),i("WEBGL_multisampled_render_to_texture"),i("WEBGL_render_shared_exponent")},get:function(s){const l=i(s);return l===null&&Fo("WebGLRenderer: "+s+" extension not supported."),l}}}function A2(r,e,i,s){const l={},c=new WeakMap;function f(v){const x=v.target;x.index!==null&&e.remove(x.index);for(const E in x.attributes)e.remove(x.attributes[E]);x.removeEventListener("dispose",f),delete l[x.id];const _=c.get(x);_&&(e.remove(_),c.delete(x)),s.releaseStatesOfGeometry(x),x.isInstancedBufferGeometry===!0&&delete x._maxInstanceCount,i.memory.geometries--}function h(v,x){return l[x.id]===!0||(x.addEventListener("dispose",f),l[x.id]=!0,i.memory.geometries++),x}function m(v){const x=v.attributes;for(const _ in x)e.update(x[_],r.ARRAY_BUFFER)}function p(v){const x=[],_=v.index,E=v.attributes.position;let R=0;if(E===void 0)return;if(_!==null){const F=_.array;R=_.version;for(let G=0,w=F.length;G<w;G+=3){const N=F[G+0],L=F[G+1],z=F[G+2];x.push(N,L,L,z,z,N)}}else{const F=E.array;R=E.version;for(let G=0,w=F.length/3-1;G<w;G+=3){const N=G+0,L=G+1,z=G+2;x.push(N,L,L,z,z,N)}}const b=new(E.count>=65535?O_:L_)(x,1);b.version=R;const S=c.get(v);S&&e.remove(S),c.set(v,b)}function g(v){const x=c.get(v);if(x){const _=v.index;_!==null&&x.version<_.version&&p(v)}else p(v);return c.get(v)}return{get:h,update:m,getWireframeAttribute:g}}function w2(r,e,i){let s;function l(v){s=v}let c,f;function h(v){c=v.type,f=v.bytesPerElement}function m(v,x){r.drawElements(s,x,c,v*f),i.update(x,s,1)}function p(v,x,_){_!==0&&(r.drawElementsInstanced(s,x,c,v*f,_),i.update(x,s,_))}function g(v,x,_){if(_===0)return;e.get("WEBGL_multi_draw").multiDrawElementsWEBGL(s,x,0,c,v,0,_);let R=0;for(let b=0;b<_;b++)R+=x[b];i.update(R,s,1)}this.setMode=l,this.setIndex=h,this.render=m,this.renderInstances=p,this.renderMultiDraw=g}function C2(r){const e={geometries:0,textures:0},i={frame:0,calls:0,triangles:0,points:0,lines:0};function s(c,f,h){switch(i.calls++,f){case r.TRIANGLES:i.triangles+=h*(c/3);break;case r.LINES:i.lines+=h*(c/2);break;case r.LINE_STRIP:i.lines+=h*(c-1);break;case r.LINE_LOOP:i.lines+=h*c;break;case r.POINTS:i.points+=h*c;break;default:Zt("WebGLInfo: Unknown draw mode:",f);break}}function l(){i.calls=0,i.triangles=0,i.points=0,i.lines=0}return{memory:e,render:i,programs:null,autoReset:!0,reset:l,update:s}}function R2(r,e,i){const s=new WeakMap,l=new Ln;function c(f,h,m){const p=f.morphTargetInfluences,g=h.morphAttributes.position||h.morphAttributes.normal||h.morphAttributes.color,v=g!==void 0?g.length:0;let x=s.get(h);if(x===void 0||x.count!==v){let O=function(){z.dispose(),s.delete(h),h.removeEventListener("dispose",O)};x!==void 0&&x.texture.dispose();const _=h.morphAttributes.position!==void 0,E=h.morphAttributes.normal!==void 0,R=h.morphAttributes.color!==void 0,b=h.morphAttributes.position||[],S=h.morphAttributes.normal||[],F=h.morphAttributes.color||[];let G=0;_===!0&&(G=1),E===!0&&(G=2),R===!0&&(G=3);let w=h.attributes.position.count*G,N=1;w>e.maxTextureSize&&(N=Math.ceil(w/e.maxTextureSize),w=e.maxTextureSize);const L=new Float32Array(w*N*4*v),z=new U_(L,w,N,v);z.type=Ga,z.needsUpdate=!0;const T=G*4;for(let I=0;I<v;I++){const W=b[I],J=S[I],re=F[I],k=w*N*4*I;for(let K=0;K<W.count;K++){const B=K*T;_===!0&&(l.fromBufferAttribute(W,K),L[k+B+0]=l.x,L[k+B+1]=l.y,L[k+B+2]=l.z,L[k+B+3]=0),E===!0&&(l.fromBufferAttribute(J,K),L[k+B+4]=l.x,L[k+B+5]=l.y,L[k+B+6]=l.z,L[k+B+7]=0),R===!0&&(l.fromBufferAttribute(re,K),L[k+B+8]=l.x,L[k+B+9]=l.y,L[k+B+10]=l.z,L[k+B+11]=re.itemSize===4?l.w:1)}}x={count:v,texture:z,size:new Kt(w,N)},s.set(h,x),h.addEventListener("dispose",O)}if(f.isInstancedMesh===!0&&f.morphTexture!==null)m.getUniforms().setValue(r,"morphTexture",f.morphTexture,i);else{let _=0;for(let R=0;R<p.length;R++)_+=p[R];const E=h.morphTargetsRelative?1:1-_;m.getUniforms().setValue(r,"morphTargetBaseInfluence",E),m.getUniforms().setValue(r,"morphTargetInfluences",p)}m.getUniforms().setValue(r,"morphTargetsTexture",x.texture,i),m.getUniforms().setValue(r,"morphTargetsTextureSize",x.size)}return{update:c}}function U2(r,e,i,s,l){let c=new WeakMap;function f(p){const g=l.render.frame,v=p.geometry,x=e.get(p,v);if(c.get(x)!==g&&(e.update(x),c.set(x,g)),p.isInstancedMesh&&(p.hasEventListener("dispose",m)===!1&&p.addEventListener("dispose",m),c.get(p)!==g&&(i.update(p.instanceMatrix,r.ARRAY_BUFFER),p.instanceColor!==null&&i.update(p.instanceColor,r.ARRAY_BUFFER),c.set(p,g))),p.isSkinnedMesh){const _=p.skeleton;c.get(_)!==g&&(_.update(),c.set(_,g))}return x}function h(){c=new WeakMap}function m(p){const g=p.target;g.removeEventListener("dispose",m),s.releaseStatesOfObject(g),i.remove(g.instanceMatrix),g.instanceColor!==null&&i.remove(g.instanceColor)}return{update:f,dispose:h}}const D2={[p_]:"LINEAR_TONE_MAPPING",[m_]:"REINHARD_TONE_MAPPING",[g_]:"CINEON_TONE_MAPPING",[x_]:"ACES_FILMIC_TONE_MAPPING",[__]:"AGX_TONE_MAPPING",[y_]:"NEUTRAL_TONE_MAPPING",[v_]:"CUSTOM_TONE_MAPPING"};function N2(r,e,i,s,l,c){const f=new wa(e,i,{type:r,depthBuffer:l,stencilBuffer:c,samples:s?4:0,storeMultisampledDepthBuffer:!1,storeMultisampledStencilBuffer:!1,resolveDepthBuffer:!1,resolveStencilBuffer:!1});let h=null,m=null;const p=new Bn;p.setAttribute("position",new Cn([-1,3,0,-1,-1,0,3,-1,0],3)),p.setAttribute("uv",new Cn([0,2,0,0,2,0],2));const g=new _M({uniforms:{tDiffuse:{value:null}},vertexShader:`
			precision highp float;

			uniform mat4 modelViewMatrix;
			uniform mat4 projectionMatrix;

			attribute vec3 position;
			attribute vec2 uv;

			varying vec2 vUv;

			void main() {
				vUv = uv;
				gl_Position = projectionMatrix * modelViewMatrix * vec4( position, 1.0 );
			}`,fragmentShader:`
			precision highp float;

			uniform sampler2D tDiffuse;

			varying vec2 vUv;

			#include <tonemapping_pars_fragment>
			#include <colorspace_pars_fragment>

			void main() {
				gl_FragColor = texture2D( tDiffuse, vUv );

				#ifdef LINEAR_TONE_MAPPING
					gl_FragColor.rgb = LinearToneMapping( gl_FragColor.rgb );
				#elif defined( REINHARD_TONE_MAPPING )
					gl_FragColor.rgb = ReinhardToneMapping( gl_FragColor.rgb );
				#elif defined( CINEON_TONE_MAPPING )
					gl_FragColor.rgb = CineonToneMapping( gl_FragColor.rgb );
				#elif defined( ACES_FILMIC_TONE_MAPPING )
					gl_FragColor.rgb = ACESFilmicToneMapping( gl_FragColor.rgb );
				#elif defined( AGX_TONE_MAPPING )
					gl_FragColor.rgb = AgXToneMapping( gl_FragColor.rgb );
				#elif defined( NEUTRAL_TONE_MAPPING )
					gl_FragColor.rgb = NeutralToneMapping( gl_FragColor.rgb );
				#elif defined( CUSTOM_TONE_MAPPING )
					gl_FragColor.rgb = CustomToneMapping( gl_FragColor.rgb );
				#endif

				#ifdef SRGB_TRANSFER
					gl_FragColor = sRGBTransferOETF( gl_FragColor );
				#endif
			}`,depthTest:!1,depthWrite:!1}),v=new ji(p,g),x=new G_(-1,1,1,-1,0,1);let _=null,E=null,R=!1,b,S=null,F=[],G=!1;this.setSize=function(w,N){f.setSize(w,N),h!==null&&h.setSize(w,N),m!==null&&m.setSize(w,N);for(let L=0;L<F.length;L++){const z=F[L];z.setSize&&z.setSize(w,N)}},this.setEffects=function(w){F=w,G=F.length>0&&F[0].isRenderPass===!0;const N=f.width,L=f.height;F.length>0&&h===null&&(h=new wa(N,L,{type:Wa,depthBuffer:!1,stencilBuffer:!1}),m=new wa(N,L,{type:Wa,depthBuffer:!1,stencilBuffer:!1}));for(let z=0;z<F.length;z++){const T=F[z];T.setSize&&T.setSize(N,L)}},this.begin=function(w,N){if(R||w.toneMapping===ka&&F.length===0)return!1;if(S=N,N!==null){const L=N.width,z=N.height;(f.width!==L||f.height!==z)&&this.setSize(L,z)}return G===!1&&w.setRenderTarget(f),b=w.toneMapping,w.toneMapping=ka,!0},this.hasRenderPass=function(){return G},this.end=function(w,N){w.toneMapping=b,R=!0;let L=f,z=h;for(let T=0;T<F.length;T++){const O=F[T];O.enabled!==!1&&(O.render(w,z,L,N),O.needsSwap!==!1&&(L=z,z=z===h?m:h))}if(_!==w.outputColorSpace||E!==w.toneMapping){_=w.outputColorSpace,E=w.toneMapping,g.defines={},kt.getTransfer(_)===cn&&(g.defines.SRGB_TRANSFER="");const T=D2[E];T&&(g.defines[T]=""),g.needsUpdate=!0}g.uniforms.tDiffuse.value=L.texture,w.setRenderTarget(S),w.render(v,x),S=null,R=!1},this.isCompositing=function(){return R},this.dispose=function(){f.dispose(),h!==null&&h.dispose(),m!==null&&m.dispose(),p.dispose(),g.dispose()}}const W_=new gi,Dp=new Ql(1,1),q_=new U_,Y_=new Xb,j_=new z_,zv=[],Fv=[],Bv=new Float32Array(16),Iv=new Float32Array(9),Hv=new Float32Array(4);function Xo(r,e,i){const s=r[0];if(s<=0||s>0)return r;const l=e*i;let c=zv[l];if(c===void 0&&(c=new Float32Array(l),zv[l]=c),e!==0){s.toArray(c,0);for(let f=1,h=0;f!==e;++f)h+=i,r[f].toArray(c,h)}return c}function jn(r,e){if(r.length!==e.length)return!1;for(let i=0,s=r.length;i<s;i++)if(r[i]!==e[i])return!1;return!0}function Zn(r,e){for(let i=0,s=e.length;i<s;i++)r[i]=e[i]}function ef(r,e){let i=Fv[e];i===void 0&&(i=new Int32Array(e),Fv[e]=i);for(let s=0;s!==e;++s)i[s]=r.allocateTextureUnit();return i}function L2(r,e){const i=this.cache;i[0]!==e&&(r.uniform1f(this.addr,e),i[0]=e)}function O2(r,e){const i=this.cache;if(e.x!==void 0)(i[0]!==e.x||i[1]!==e.y)&&(r.uniform2f(this.addr,e.x,e.y),i[0]=e.x,i[1]=e.y);else{if(jn(i,e))return;r.uniform2fv(this.addr,e),Zn(i,e)}}function P2(r,e){const i=this.cache;if(e.x!==void 0)(i[0]!==e.x||i[1]!==e.y||i[2]!==e.z)&&(r.uniform3f(this.addr,e.x,e.y,e.z),i[0]=e.x,i[1]=e.y,i[2]=e.z);else if(e.r!==void 0)(i[0]!==e.r||i[1]!==e.g||i[2]!==e.b)&&(r.uniform3f(this.addr,e.r,e.g,e.b),i[0]=e.r,i[1]=e.g,i[2]=e.b);else{if(jn(i,e))return;r.uniform3fv(this.addr,e),Zn(i,e)}}function z2(r,e){const i=this.cache;if(e.x!==void 0)(i[0]!==e.x||i[1]!==e.y||i[2]!==e.z||i[3]!==e.w)&&(r.uniform4f(this.addr,e.x,e.y,e.z,e.w),i[0]=e.x,i[1]=e.y,i[2]=e.z,i[3]=e.w);else{if(jn(i,e))return;r.uniform4fv(this.addr,e),Zn(i,e)}}function F2(r,e){const i=this.cache,s=e.elements;if(s===void 0){if(jn(i,e))return;r.uniformMatrix2fv(this.addr,!1,e),Zn(i,e)}else{if(jn(i,s))return;Hv.set(s),r.uniformMatrix2fv(this.addr,!1,Hv),Zn(i,s)}}function B2(r,e){const i=this.cache,s=e.elements;if(s===void 0){if(jn(i,e))return;r.uniformMatrix3fv(this.addr,!1,e),Zn(i,e)}else{if(jn(i,s))return;Iv.set(s),r.uniformMatrix3fv(this.addr,!1,Iv),Zn(i,s)}}function I2(r,e){const i=this.cache,s=e.elements;if(s===void 0){if(jn(i,e))return;r.uniformMatrix4fv(this.addr,!1,e),Zn(i,e)}else{if(jn(i,s))return;Bv.set(s),r.uniformMatrix4fv(this.addr,!1,Bv),Zn(i,s)}}function H2(r,e){const i=this.cache;i[0]!==e&&(r.uniform1i(this.addr,e),i[0]=e)}function G2(r,e){const i=this.cache;if(e.x!==void 0)(i[0]!==e.x||i[1]!==e.y)&&(r.uniform2i(this.addr,e.x,e.y),i[0]=e.x,i[1]=e.y);else{if(jn(i,e))return;r.uniform2iv(this.addr,e),Zn(i,e)}}function V2(r,e){const i=this.cache;if(e.x!==void 0)(i[0]!==e.x||i[1]!==e.y||i[2]!==e.z)&&(r.uniform3i(this.addr,e.x,e.y,e.z),i[0]=e.x,i[1]=e.y,i[2]=e.z);else{if(jn(i,e))return;r.uniform3iv(this.addr,e),Zn(i,e)}}function k2(r,e){const i=this.cache;if(e.x!==void 0)(i[0]!==e.x||i[1]!==e.y||i[2]!==e.z||i[3]!==e.w)&&(r.uniform4i(this.addr,e.x,e.y,e.z,e.w),i[0]=e.x,i[1]=e.y,i[2]=e.z,i[3]=e.w);else{if(jn(i,e))return;r.uniform4iv(this.addr,e),Zn(i,e)}}function X2(r,e){const i=this.cache;i[0]!==e&&(r.uniform1ui(this.addr,e),i[0]=e)}function W2(r,e){const i=this.cache;if(e.x!==void 0)(i[0]!==e.x||i[1]!==e.y)&&(r.uniform2ui(this.addr,e.x,e.y),i[0]=e.x,i[1]=e.y);else{if(jn(i,e))return;r.uniform2uiv(this.addr,e),Zn(i,e)}}function q2(r,e){const i=this.cache;if(e.x!==void 0)(i[0]!==e.x||i[1]!==e.y||i[2]!==e.z)&&(r.uniform3ui(this.addr,e.x,e.y,e.z),i[0]=e.x,i[1]=e.y,i[2]=e.z);else{if(jn(i,e))return;r.uniform3uiv(this.addr,e),Zn(i,e)}}function Y2(r,e){const i=this.cache;if(e.x!==void 0)(i[0]!==e.x||i[1]!==e.y||i[2]!==e.z||i[3]!==e.w)&&(r.uniform4ui(this.addr,e.x,e.y,e.z,e.w),i[0]=e.x,i[1]=e.y,i[2]=e.z,i[3]=e.w);else{if(jn(i,e))return;r.uniform4uiv(this.addr,e),Zn(i,e)}}function j2(r,e,i){const s=this.cache,l=i.allocateTextureUnit();s[0]!==l&&(r.uniform1i(this.addr,l),s[0]=l);let c;this.type===r.SAMPLER_2D_SHADOW?(Dp.compareFunction=i.isReversedDepthBuffer()?Wp:Xp,c=Dp):c=W_,i.setTexture2D(e||c,l)}function Z2(r,e,i){const s=this.cache,l=i.allocateTextureUnit();s[0]!==l&&(r.uniform1i(this.addr,l),s[0]=l),i.setTexture3D(e||Y_,l)}function K2(r,e,i){const s=this.cache,l=i.allocateTextureUnit();s[0]!==l&&(r.uniform1i(this.addr,l),s[0]=l),i.setTextureCube(e||j_,l)}function Q2(r,e,i){const s=this.cache,l=i.allocateTextureUnit();s[0]!==l&&(r.uniform1i(this.addr,l),s[0]=l),i.setTexture2DArray(e||q_,l)}function J2(r){switch(r){case 5126:return L2;case 35664:return O2;case 35665:return P2;case 35666:return z2;case 35674:return F2;case 35675:return B2;case 35676:return I2;case 5124:case 35670:return H2;case 35667:case 35671:return G2;case 35668:case 35672:return V2;case 35669:case 35673:return k2;case 5125:return X2;case 36294:return W2;case 36295:return q2;case 36296:return Y2;case 35678:case 36198:case 36298:case 36306:case 35682:return j2;case 35679:case 36299:case 36307:return Z2;case 35680:case 36300:case 36308:case 36293:return K2;case 36289:case 36303:case 36311:case 36292:return Q2}}function $2(r,e){r.uniform1fv(this.addr,e)}function eA(r,e){const i=Xo(e,this.size,2);r.uniform2fv(this.addr,i)}function tA(r,e){const i=Xo(e,this.size,3);r.uniform3fv(this.addr,i)}function nA(r,e){const i=Xo(e,this.size,4);r.uniform4fv(this.addr,i)}function iA(r,e){const i=Xo(e,this.size,4);r.uniformMatrix2fv(this.addr,!1,i)}function aA(r,e){const i=Xo(e,this.size,9);r.uniformMatrix3fv(this.addr,!1,i)}function rA(r,e){const i=Xo(e,this.size,16);r.uniformMatrix4fv(this.addr,!1,i)}function sA(r,e){r.uniform1iv(this.addr,e)}function oA(r,e){r.uniform2iv(this.addr,e)}function lA(r,e){r.uniform3iv(this.addr,e)}function cA(r,e){r.uniform4iv(this.addr,e)}function uA(r,e){r.uniform1uiv(this.addr,e)}function fA(r,e){r.uniform2uiv(this.addr,e)}function dA(r,e){r.uniform3uiv(this.addr,e)}function hA(r,e){r.uniform4uiv(this.addr,e)}function pA(r,e,i){const s=this.cache,l=e.length,c=ef(i,l);jn(s,c)||(r.uniform1iv(this.addr,c),Zn(s,c));let f;this.type===r.SAMPLER_2D_SHADOW?f=Dp:f=W_;for(let h=0;h!==l;++h)i.setTexture2D(e[h]||f,c[h])}function mA(r,e,i){const s=this.cache,l=e.length,c=ef(i,l);jn(s,c)||(r.uniform1iv(this.addr,c),Zn(s,c));for(let f=0;f!==l;++f)i.setTexture3D(e[f]||Y_,c[f])}function gA(r,e,i){const s=this.cache,l=e.length,c=ef(i,l);jn(s,c)||(r.uniform1iv(this.addr,c),Zn(s,c));for(let f=0;f!==l;++f)i.setTextureCube(e[f]||j_,c[f])}function xA(r,e,i){const s=this.cache,l=e.length,c=ef(i,l);jn(s,c)||(r.uniform1iv(this.addr,c),Zn(s,c));for(let f=0;f!==l;++f)i.setTexture2DArray(e[f]||q_,c[f])}function vA(r){switch(r){case 5126:return $2;case 35664:return eA;case 35665:return tA;case 35666:return nA;case 35674:return iA;case 35675:return aA;case 35676:return rA;case 5124:case 35670:return sA;case 35667:case 35671:return oA;case 35668:case 35672:return lA;case 35669:case 35673:return cA;case 5125:return uA;case 36294:return fA;case 36295:return dA;case 36296:return hA;case 35678:case 36198:case 36298:case 36306:case 35682:return pA;case 35679:case 36299:case 36307:return mA;case 35680:case 36300:case 36308:case 36293:return gA;case 36289:case 36303:case 36311:case 36292:return xA}}class _A{constructor(e,i,s){this.id=e,this.addr=s,this.cache=[],this.type=i.type,this.setValue=J2(i.type)}}class yA{constructor(e,i,s){this.id=e,this.addr=s,this.cache=[],this.type=i.type,this.size=i.size,this.setValue=vA(i.type)}}class SA{constructor(e){this.id=e,this.seq=[],this.map={}}setValue(e,i,s){const l=this.seq;for(let c=0,f=l.length;c!==f;++c){const h=l[c];h.setValue(e,i[h.id],s)}}}const Hh=/(\w+)(\])?(\[|\.)?/g;function Gv(r,e){r.seq.push(e),r.map[e.id]=e}function bA(r,e,i){const s=r.name,l=s.length;for(Hh.lastIndex=0;;){const c=Hh.exec(s),f=Hh.lastIndex;let h=c[1];const m=c[2]==="]",p=c[3];if(m&&(h=h|0),p===void 0||p==="["&&f+2===l){Gv(i,p===void 0?new _A(h,r,e):new yA(h,r,e));break}else{let v=i.map[h];v===void 0&&(v=new SA(h),Gv(i,v)),i=v}}}class Fu{constructor(e,i){this.seq=[],this.map={};const s=e.getProgramParameter(i,e.ACTIVE_UNIFORMS);for(let f=0;f<s;++f){const h=e.getActiveUniform(i,f),m=e.getUniformLocation(i,h.name);bA(h,m,this)}const l=[],c=[];for(const f of this.seq)f.type===e.SAMPLER_2D_SHADOW||f.type===e.SAMPLER_CUBE_SHADOW||f.type===e.SAMPLER_2D_ARRAY_SHADOW?l.push(f):c.push(f);l.length>0&&(this.seq=l.concat(c))}setValue(e,i,s,l){const c=this.map[i];c!==void 0&&c.setValue(e,s,l)}setOptional(e,i,s){const l=i[s];l!==void 0&&this.setValue(e,s,l)}static upload(e,i,s,l){for(let c=0,f=i.length;c!==f;++c){const h=i[c],m=s[h.id];m.needsUpdate!==!1&&h.setValue(e,m.value,l)}}static seqWithValue(e,i){const s=[];for(let l=0,c=e.length;l!==c;++l){const f=e[l];f.id in i&&s.push(f)}return s}}function Vv(r,e,i){const s=r.createShader(e);return r.shaderSource(s,i),r.compileShader(s),s}const MA=37297;let EA=0;function TA(r,e){const i=r.split(`
`),s=[],l=Math.max(e-6,0),c=Math.min(e+6,i.length);for(let f=l;f<c;f++){const h=f+1;s.push(`${h===e?">":" "} ${h}: ${i[f]}`)}return s.join(`
`)}const kv=new St;function AA(r){kt._getMatrix(kv,kt.workingColorSpace,r);const e=`mat3( ${kv.elements.map(i=>i.toFixed(4))} )`;switch(kt.getTransfer(r)){case Xu:return[e,"LinearTransferOETF"];case cn:return[e,"sRGBTransferOETF"];default:return ht("WebGLProgram: Unsupported color space: ",r),[e,"LinearTransferOETF"]}}function Xv(r,e,i){const s=r.getShaderParameter(e,r.COMPILE_STATUS),c=(r.getShaderInfoLog(e)||"").trim();if(s&&c==="")return"";const f=/ERROR: 0:(\d+)/.exec(c);if(f){const h=parseInt(f[1]);return i.toUpperCase()+`

`+c+`

`+TA(r.getShaderSource(e),h)}else return c}function wA(r,e){const i=AA(e);return[`vec4 ${r}( vec4 value ) {`,`	return ${i[1]}( vec4( value.rgb * ${i[0]}, value.a ) );`,"}"].join(`
`)}const CA={[p_]:"Linear",[m_]:"Reinhard",[g_]:"Cineon",[x_]:"ACESFilmic",[__]:"AgX",[y_]:"Neutral",[v_]:"Custom"};function RA(r,e){const i=CA[e];return i===void 0?(ht("WebGLProgram: Unsupported toneMapping:",e),"vec3 "+r+"( vec3 color ) { return LinearToneMapping( color ); }"):"vec3 "+r+"( vec3 color ) { return "+i+"ToneMapping( color ); }"}const Ru=new Q;function UA(){kt.getLuminanceCoefficients(Ru);const r=Ru.x.toFixed(4),e=Ru.y.toFixed(4),i=Ru.z.toFixed(4);return["float luminance( const in vec3 rgb ) {",`	const vec3 weights = vec3( ${r}, ${e}, ${i} );`,"	return dot( weights, rgb );","}"].join(`
`)}function DA(r){return[r.extensionClipCullDistance?"#extension GL_ANGLE_clip_cull_distance : require":"",r.extensionMultiDraw?"#extension GL_ANGLE_multi_draw : require":""].filter(Hl).join(`
`)}function NA(r){const e=[];for(const i in r){const s=r[i];s!==!1&&e.push("#define "+i+" "+s)}return e.join(`
`)}function LA(r,e){const i={},s=r.getProgramParameter(e,r.ACTIVE_ATTRIBUTES);for(let l=0;l<s;l++){const c=r.getActiveAttrib(e,l),f=c.name;let h=1;c.type===r.FLOAT_MAT2&&(h=2),c.type===r.FLOAT_MAT3&&(h=3),c.type===r.FLOAT_MAT4&&(h=4),i[f]={type:c.type,location:r.getAttribLocation(e,f),locationSize:h}}return i}function Hl(r){return r!==""}function Wv(r,e){const i=e.numSpotLightShadows+e.numSpotLightMaps-e.numSpotLightShadowsWithMaps;return r.replace(/NUM_SUN_LIGHTS/g,e.numSunLights).replace(/NUM_DIR_LIGHTS/g,e.numDirLights).replace(/NUM_SPOT_LIGHTS/g,e.numSpotLights).replace(/NUM_SPOT_LIGHT_MAPS/g,e.numSpotLightMaps).replace(/NUM_SPOT_LIGHT_COORDS/g,i).replace(/NUM_RECT_AREA_LIGHTS/g,e.numRectAreaLights).replace(/NUM_POINT_LIGHTS/g,e.numPointLights).replace(/NUM_HEMI_LIGHTS/g,e.numHemiLights).replace(/NUM_SUN_LIGHT_SHADOWS/g,e.numSunLightShadows).replace(/NUM_DIR_LIGHT_SHADOWS/g,e.numDirLightShadows).replace(/NUM_SPOT_LIGHT_SHADOWS_WITH_MAPS/g,e.numSpotLightShadowsWithMaps).replace(/NUM_SPOT_LIGHT_SHADOWS/g,e.numSpotLightShadows).replace(/NUM_POINT_LIGHT_SHADOWS/g,e.numPointLightShadows)}function qv(r,e){return r.replace(/NUM_CLIPPING_PLANES/g,e.numClippingPlanes).replace(/UNION_CLIPPING_PLANES/g,e.numClippingPlanes-e.numClipIntersection)}const OA=/^[ \t]*#include +<([\w\d./]+)>/gm;function Np(r){return r.replace(OA,zA)}const PA=new Map;function zA(r,e){let i=Rt[e];if(i===void 0){const s=PA.get(e);if(s!==void 0)i=Rt[s],ht('WebGLRenderer: Shader chunk "%s" has been deprecated. Use "%s" instead.',e,s);else throw new Error("THREE.WebGLProgram: Can not resolve #include <"+e+">")}return Np(i)}const FA=/#pragma unroll_loop_start\s+for\s*\(\s*int\s+i\s*=\s*(\d+)\s*;\s*i\s*<\s*(\d+)\s*;\s*i\s*\+\+\s*\)\s*{([\s\S]+?)}\s+#pragma unroll_loop_end/g;function Yv(r){return r.replace(FA,BA)}function BA(r,e,i,s){let l="";for(let c=parseInt(e);c<parseInt(i);c++)l+=s.replace(/\[\s*i\s*\]/g,"[ "+c+" ]").replace(/UNROLLED_LOOP_INDEX/g,c);return l}function jv(r){let e=`precision ${r.precision} float;
	precision ${r.precision} int;
	precision ${r.precision} sampler2D;
	precision ${r.precision} samplerCube;
	precision ${r.precision} sampler3D;
	precision ${r.precision} sampler2DArray;
	precision ${r.precision} sampler2DShadow;
	precision ${r.precision} samplerCubeShadow;
	precision ${r.precision} sampler2DArrayShadow;
	precision ${r.precision} isampler2D;
	precision ${r.precision} isampler3D;
	precision ${r.precision} isamplerCube;
	precision ${r.precision} isampler2DArray;
	precision ${r.precision} usampler2D;
	precision ${r.precision} usampler3D;
	precision ${r.precision} usamplerCube;
	precision ${r.precision} usampler2DArray;
	`;return r.precision==="highp"?e+=`
#define HIGH_PRECISION`:r.precision==="mediump"?e+=`
#define MEDIUM_PRECISION`:r.precision==="lowp"&&(e+=`
#define LOW_PRECISION`),e}const IA={[Nu]:"SHADOWMAP_TYPE_PCF",[Il]:"SHADOWMAP_TYPE_VSM"};function HA(r){return IA[r.shadowMapType]||"SHADOWMAP_TYPE_BASIC"}const GA={[Os]:"ENVMAP_TYPE_CUBE",[Io]:"ENVMAP_TYPE_CUBE",[Ku]:"ENVMAP_TYPE_CUBE_UV"};function VA(r){return r.envMap===!1?"ENVMAP_TYPE_CUBE":GA[r.envMapMode]||"ENVMAP_TYPE_CUBE"}const kA={[Io]:"ENVMAP_MODE_REFRACTION"};function XA(r){return r.envMap===!1?"ENVMAP_MODE_REFLECTION":kA[r.envMapMode]||"ENVMAP_MODE_REFLECTION"}const WA={[h_]:"ENVMAP_BLENDING_MULTIPLY",[sb]:"ENVMAP_BLENDING_MIX",[ob]:"ENVMAP_BLENDING_ADD"};function qA(r){return r.envMap===!1?"ENVMAP_BLENDING_NONE":WA[r.combine]||"ENVMAP_BLENDING_NONE"}function YA(r){const e=r.envMapCubeUVHeight;if(e===null)return null;const i=Math.log2(e)-2,s=1/e;return{texelWidth:1/(3*Math.max(Math.pow(2,i),112)),texelHeight:s,maxMip:i}}function jA(r,e,i,s){const l=r.getContext(),c=i.defines;let f=i.vertexShader,h=i.fragmentShader;const m=HA(i),p=VA(i),g=XA(i),v=qA(i),x=YA(i),_=DA(i),E=NA(c),R=l.createProgram();let b,S,F=i.glslVersion?"#version "+i.glslVersion+`
`:"";i.isRawShaderMaterial?(b=["#define SHADER_TYPE "+i.shaderType,"#define SHADER_NAME "+i.shaderName,E].filter(Hl).join(`
`),b.length>0&&(b+=`
`),S=["#define SHADER_TYPE "+i.shaderType,"#define SHADER_NAME "+i.shaderName,E].filter(Hl).join(`
`),S.length>0&&(S+=`
`)):(b=[jv(i),"#define SHADER_TYPE "+i.shaderType,"#define SHADER_NAME "+i.shaderName,E,i.extensionClipCullDistance?"#define USE_CLIP_DISTANCE":"",i.batching?"#define USE_BATCHING":"",i.batchingColor?"#define USE_BATCHING_COLOR":"",i.instancing?"#define USE_INSTANCING":"",i.instancingColor?"#define USE_INSTANCING_COLOR":"",i.instancingMorph?"#define USE_INSTANCING_MORPH":"",i.useFog&&i.fog?"#define USE_FOG":"",i.useFog&&i.fogExp2?"#define FOG_EXP2":"",i.map?"#define USE_MAP":"",i.envMap?"#define USE_ENVMAP":"",i.envMap?"#define "+g:"",i.lightMap?"#define USE_LIGHTMAP":"",i.aoMap?"#define USE_AOMAP":"",i.bumpMap?"#define USE_BUMPMAP":"",i.normalMap?"#define USE_NORMALMAP":"",i.normalMapObjectSpace?"#define USE_NORMALMAP_OBJECTSPACE":"",i.normalMapTangentSpace?"#define USE_NORMALMAP_TANGENTSPACE":"",i.displacementMap?"#define USE_DISPLACEMENTMAP":"",i.emissiveMap?"#define USE_EMISSIVEMAP":"",i.anisotropy?"#define USE_ANISOTROPY":"",i.anisotropyMap?"#define USE_ANISOTROPYMAP":"",i.clearcoatMap?"#define USE_CLEARCOATMAP":"",i.clearcoatRoughnessMap?"#define USE_CLEARCOAT_ROUGHNESSMAP":"",i.clearcoatNormalMap?"#define USE_CLEARCOAT_NORMALMAP":"",i.iridescenceMap?"#define USE_IRIDESCENCEMAP":"",i.iridescenceThicknessMap?"#define USE_IRIDESCENCE_THICKNESSMAP":"",i.specularMap?"#define USE_SPECULARMAP":"",i.specularColorMap?"#define USE_SPECULAR_COLORMAP":"",i.specularIntensityMap?"#define USE_SPECULAR_INTENSITYMAP":"",i.roughnessMap?"#define USE_ROUGHNESSMAP":"",i.metalnessMap?"#define USE_METALNESSMAP":"",i.alphaMap?"#define USE_ALPHAMAP":"",i.alphaHash?"#define USE_ALPHAHASH":"",i.transmission?"#define USE_TRANSMISSION":"",i.transmissionMap?"#define USE_TRANSMISSIONMAP":"",i.thicknessMap?"#define USE_THICKNESSMAP":"",i.sheenColorMap?"#define USE_SHEEN_COLORMAP":"",i.sheenRoughnessMap?"#define USE_SHEEN_ROUGHNESSMAP":"",i.mapUv?"#define MAP_UV "+i.mapUv:"",i.alphaMapUv?"#define ALPHAMAP_UV "+i.alphaMapUv:"",i.lightMapUv?"#define LIGHTMAP_UV "+i.lightMapUv:"",i.aoMapUv?"#define AOMAP_UV "+i.aoMapUv:"",i.emissiveMapUv?"#define EMISSIVEMAP_UV "+i.emissiveMapUv:"",i.bumpMapUv?"#define BUMPMAP_UV "+i.bumpMapUv:"",i.normalMapUv?"#define NORMALMAP_UV "+i.normalMapUv:"",i.displacementMapUv?"#define DISPLACEMENTMAP_UV "+i.displacementMapUv:"",i.metalnessMapUv?"#define METALNESSMAP_UV "+i.metalnessMapUv:"",i.roughnessMapUv?"#define ROUGHNESSMAP_UV "+i.roughnessMapUv:"",i.anisotropyMapUv?"#define ANISOTROPYMAP_UV "+i.anisotropyMapUv:"",i.clearcoatMapUv?"#define CLEARCOATMAP_UV "+i.clearcoatMapUv:"",i.clearcoatNormalMapUv?"#define CLEARCOAT_NORMALMAP_UV "+i.clearcoatNormalMapUv:"",i.clearcoatRoughnessMapUv?"#define CLEARCOAT_ROUGHNESSMAP_UV "+i.clearcoatRoughnessMapUv:"",i.iridescenceMapUv?"#define IRIDESCENCEMAP_UV "+i.iridescenceMapUv:"",i.iridescenceThicknessMapUv?"#define IRIDESCENCE_THICKNESSMAP_UV "+i.iridescenceThicknessMapUv:"",i.sheenColorMapUv?"#define SHEEN_COLORMAP_UV "+i.sheenColorMapUv:"",i.sheenRoughnessMapUv?"#define SHEEN_ROUGHNESSMAP_UV "+i.sheenRoughnessMapUv:"",i.specularMapUv?"#define SPECULARMAP_UV "+i.specularMapUv:"",i.specularColorMapUv?"#define SPECULAR_COLORMAP_UV "+i.specularColorMapUv:"",i.specularIntensityMapUv?"#define SPECULAR_INTENSITYMAP_UV "+i.specularIntensityMapUv:"",i.transmissionMapUv?"#define TRANSMISSIONMAP_UV "+i.transmissionMapUv:"",i.thicknessMapUv?"#define THICKNESSMAP_UV "+i.thicknessMapUv:"",i.vertexTangents&&i.flatShading===!1?"#define USE_TANGENT":"",i.vertexNormals?"#define HAS_NORMAL":"",i.vertexColors?"#define USE_COLOR":"",i.vertexAlphas?"#define USE_COLOR_ALPHA":"",i.vertexUv1s?"#define USE_UV1":"",i.vertexUv2s?"#define USE_UV2":"",i.vertexUv3s?"#define USE_UV3":"",i.pointsUvs?"#define USE_POINTS_UV":"",i.flatShading?"#define FLAT_SHADED":"",i.skinning?"#define USE_SKINNING":"",i.morphTargets?"#define USE_MORPHTARGETS":"",i.morphNormals&&i.flatShading===!1?"#define USE_MORPHNORMALS":"",i.morphColors?"#define USE_MORPHCOLORS":"",i.morphTargetsCount>0?"#define MORPHTARGETS_TEXTURE_STRIDE "+i.morphTextureStride:"",i.morphTargetsCount>0?"#define MORPHTARGETS_COUNT "+i.morphTargetsCount:"",i.doubleSided?"#define DOUBLE_SIDED":"",i.flipSided?"#define FLIP_SIDED":"",i.shadowMapEnabled?"#define USE_SHADOWMAP":"",i.shadowMapEnabled?"#define "+m:"",i.sizeAttenuation?"#define USE_SIZEATTENUATION":"",i.numLightProbes>0?"#define USE_LIGHT_PROBES":"",i.logarithmicDepthBuffer?"#define USE_LOGARITHMIC_DEPTH_BUFFER":"",i.reversedDepthBuffer?"#define USE_REVERSED_DEPTH_BUFFER":"","uniform mat4 modelMatrix;","uniform mat4 modelViewMatrix;","uniform mat4 projectionMatrix;","uniform mat4 viewMatrix;","uniform mat3 normalMatrix;","uniform vec3 cameraPosition;","uniform bool isOrthographic;","#ifdef USE_INSTANCING","	attribute mat4 instanceMatrix;","#endif","#ifdef USE_INSTANCING_COLOR","	attribute vec3 instanceColor;","#endif","#ifdef USE_INSTANCING_MORPH","	uniform sampler2D morphTexture;","#endif","attribute vec3 position;","attribute vec3 normal;","attribute vec2 uv;","#ifdef USE_UV1","	attribute vec2 uv1;","#endif","#ifdef USE_UV2","	attribute vec2 uv2;","#endif","#ifdef USE_UV3","	attribute vec2 uv3;","#endif","#ifdef USE_TANGENT","	attribute vec4 tangent;","#endif","#if defined( USE_COLOR_ALPHA )","	attribute vec4 color;","#elif defined( USE_COLOR )","	attribute vec3 color;","#endif","#ifdef USE_SKINNING","	attribute vec4 skinIndex;","	attribute vec4 skinWeight;","#endif",`
`].filter(Hl).join(`
`),S=[jv(i),"#define SHADER_TYPE "+i.shaderType,"#define SHADER_NAME "+i.shaderName,E,i.useFog&&i.fog?"#define USE_FOG":"",i.useFog&&i.fogExp2?"#define FOG_EXP2":"",i.alphaToCoverage?"#define ALPHA_TO_COVERAGE":"",i.map?"#define USE_MAP":"",i.matcap?"#define USE_MATCAP":"",i.envMap?"#define USE_ENVMAP":"",i.envMap?"#define "+p:"",i.envMap?"#define "+g:"",i.envMap?"#define "+v:"",x?"#define CUBEUV_TEXEL_WIDTH "+x.texelWidth:"",x?"#define CUBEUV_TEXEL_HEIGHT "+x.texelHeight:"",x?"#define CUBEUV_MAX_MIP "+x.maxMip+".0":"",i.lightMap?"#define USE_LIGHTMAP":"",i.aoMap?"#define USE_AOMAP":"",i.bumpMap?"#define USE_BUMPMAP":"",i.normalMap?"#define USE_NORMALMAP":"",i.normalMapObjectSpace?"#define USE_NORMALMAP_OBJECTSPACE":"",i.normalMapTangentSpace?"#define USE_NORMALMAP_TANGENTSPACE":"",i.packedNormalMap?"#define USE_PACKED_NORMALMAP":"",i.emissiveMap?"#define USE_EMISSIVEMAP":"",i.anisotropy?"#define USE_ANISOTROPY":"",i.anisotropyMap?"#define USE_ANISOTROPYMAP":"",i.clearcoat?"#define USE_CLEARCOAT":"",i.clearcoatMap?"#define USE_CLEARCOATMAP":"",i.clearcoatRoughnessMap?"#define USE_CLEARCOAT_ROUGHNESSMAP":"",i.clearcoatNormalMap?"#define USE_CLEARCOAT_NORMALMAP":"",i.dispersion?"#define USE_DISPERSION":"",i.retroreflection?"#define USE_RETROREFLECTION":"",i.iridescence?"#define USE_IRIDESCENCE":"",i.iridescenceMap?"#define USE_IRIDESCENCEMAP":"",i.iridescenceThicknessMap?"#define USE_IRIDESCENCE_THICKNESSMAP":"",i.specularMap?"#define USE_SPECULARMAP":"",i.specularColorMap?"#define USE_SPECULAR_COLORMAP":"",i.specularIntensityMap?"#define USE_SPECULAR_INTENSITYMAP":"",i.roughnessMap?"#define USE_ROUGHNESSMAP":"",i.metalnessMap?"#define USE_METALNESSMAP":"",i.alphaMap?"#define USE_ALPHAMAP":"",i.alphaTest?"#define USE_ALPHATEST":"",i.alphaHash?"#define USE_ALPHAHASH":"",i.sheen?"#define USE_SHEEN":"",i.sheenColorMap?"#define USE_SHEEN_COLORMAP":"",i.sheenRoughnessMap?"#define USE_SHEEN_ROUGHNESSMAP":"",i.transmission?"#define USE_TRANSMISSION":"",i.transmissionMap?"#define USE_TRANSMISSIONMAP":"",i.thicknessMap?"#define USE_THICKNESSMAP":"",i.vertexTangents&&i.flatShading===!1?"#define USE_TANGENT":"",i.vertexColors||i.instancingColor?"#define USE_COLOR":"",i.vertexAlphas||i.batchingColor?"#define USE_COLOR_ALPHA":"",i.vertexUv1s?"#define USE_UV1":"",i.vertexUv2s?"#define USE_UV2":"",i.vertexUv3s?"#define USE_UV3":"",i.pointsUvs?"#define USE_POINTS_UV":"",i.gradientMap?"#define USE_GRADIENTMAP":"",i.flatShading?"#define FLAT_SHADED":"",i.doubleSided?"#define DOUBLE_SIDED":"",i.flipSided?"#define FLIP_SIDED":"",i.shadowMapEnabled?"#define USE_SHADOWMAP":"",i.shadowMapEnabled?"#define "+m:"",i.premultipliedAlpha?"#define PREMULTIPLIED_ALPHA":"",i.numLightProbes>0?"#define USE_LIGHT_PROBES":"",i.numLightProbeGrids>0?"#define USE_LIGHT_PROBES_GRID":"",i.decodeVideoTexture?"#define DECODE_VIDEO_TEXTURE":"",i.decodeVideoTextureEmissive?"#define DECODE_VIDEO_TEXTURE_EMISSIVE":"",i.logarithmicDepthBuffer?"#define USE_LOGARITHMIC_DEPTH_BUFFER":"",i.reversedDepthBuffer?"#define USE_REVERSED_DEPTH_BUFFER":"","uniform mat4 viewMatrix;","uniform vec3 cameraPosition;","uniform bool isOrthographic;",i.toneMapping!==ka?"#define TONE_MAPPING":"",i.toneMapping!==ka?Rt.tonemapping_pars_fragment:"",i.toneMapping!==ka?RA("toneMapping",i.toneMapping):"",i.dithering?"#define DITHERING":"",i.opaque?"#define OPAQUE":"",Rt.colorspace_pars_fragment,wA("linearToOutputTexel",i.outputColorSpace),UA(),i.useDepthPacking?"#define DEPTH_PACKING "+i.depthPacking:"",`
`].filter(Hl).join(`
`)),f=Np(f),f=Wv(f,i),f=qv(f,i),h=Np(h),h=Wv(h,i),h=qv(h,i),f=Yv(f),h=Yv(h),i.isRawShaderMaterial!==!0&&(F=`#version 300 es
`,b=[_,"#define attribute in","#define varying out","#define texture2D texture"].join(`
`)+`
`+b,S=["#define varying in",i.glslVersion===Qx?"":"layout(location = 0) out highp vec4 pc_fragColor;",i.glslVersion===Qx?"":"#define gl_FragColor pc_fragColor","#define gl_FragDepthEXT gl_FragDepth","#define texture2D texture","#define textureCube texture","#define texture2DProj textureProj","#define texture2DLodEXT textureLod","#define texture2DProjLodEXT textureProjLod","#define textureCubeLodEXT textureLod","#define texture2DGradEXT textureGrad","#define texture2DProjGradEXT textureProjGrad","#define textureCubeGradEXT textureGrad"].join(`
`)+`
`+S);const G=F+b+f,w=F+S+h,N=Vv(l,l.VERTEX_SHADER,G),L=Vv(l,l.FRAGMENT_SHADER,w);l.attachShader(R,N),l.attachShader(R,L),i.index0AttributeName!==void 0?l.bindAttribLocation(R,0,i.index0AttributeName):i.hasPositionAttribute===!0&&l.bindAttribLocation(R,0,"position"),l.linkProgram(R);function z(W){if(r.debug.checkShaderErrors){const J=l.getProgramInfoLog(R)||"",re=l.getShaderInfoLog(N)||"",k=l.getShaderInfoLog(L)||"",K=J.trim(),B=re.trim(),V=k.trim();let ee=!0,oe=!0;if(l.getProgramParameter(R,l.LINK_STATUS)===!1)if(ee=!1,typeof r.debug.onShaderError=="function")r.debug.onShaderError(l,R,N,L);else{const fe=Xv(l,N,"vertex"),D=Xv(l,L,"fragment");Zt("WebGLProgram: Shader Error "+l.getError()+" - VALIDATE_STATUS "+l.getProgramParameter(R,l.VALIDATE_STATUS)+`

Material Name: `+W.name+`
Material Type: `+W.type+`

Program Info Log: `+K+`
`+fe+`
`+D)}else K!==""?ht("WebGLProgram: Program Info Log:",K):(B===""||V==="")&&(oe=!1);oe&&(W.diagnostics={runnable:ee,programLog:K,vertexShader:{log:B,prefix:b},fragmentShader:{log:V,prefix:S}})}l.deleteShader(N),l.deleteShader(L),T=new Fu(l,R),O=LA(l,R)}let T;this.getUniforms=function(){return T===void 0&&z(this),T};let O;this.getAttributes=function(){return O===void 0&&z(this),O};let I=i.rendererExtensionParallelShaderCompile===!1;return this.isReady=function(){return I===!1&&(I=l.getProgramParameter(R,MA)),I},this.destroy=function(){s.releaseStatesOfProgram(this),l.deleteProgram(R),this.program=void 0},this.type=i.shaderType,this.name=i.shaderName,this.id=EA++,this.cacheKey=e,this.usedTimes=1,this.program=R,this.vertexShader=N,this.fragmentShader=L,this}let ZA=0;class KA{constructor(){this.shaderCache=new Map,this.materialCache=new Map}update(e,i,s){const l=this._getShaderCacheForMaterial(e);return l.has(i)===!1&&(l.add(i),i.usedTimes++),l.has(s)===!1&&(l.add(s),s.usedTimes++),this}remove(e){const i=this.materialCache.get(e);for(const s of i)s.usedTimes--,s.usedTimes===0&&this.shaderCache.delete(s.code);return this.materialCache.delete(e),this}getVertexShaderStage(e){return this._getShaderStage(e.vertexShader)}getFragmentShaderStage(e){return this._getShaderStage(e.fragmentShader)}dispose(){this.shaderCache.clear(),this.materialCache.clear()}_getShaderCacheForMaterial(e){const i=this.materialCache;let s=i.get(e);return s===void 0&&(s=new Set,i.set(e,s)),s}_getShaderStage(e){const i=this.shaderCache;let s=i.get(e);return s===void 0&&(s=new QA(e),i.set(e,s)),s}}class QA{constructor(e){this.id=ZA++,this.code=e,this.usedTimes=0}}function JA(r){return r===Ps||r===Gu||r===Vu}function $A(r,e,i,s,l,c){const f=new jp,h=new KA,m=new Set,p=[],g=new Map,v=s.logarithmicDepthBuffer;let x=s.precision;const _={MeshDepthMaterial:"depth",MeshDistanceMaterial:"distance",MeshNormalMaterial:"normal",MeshBasicMaterial:"basic",MeshLambertMaterial:"lambert",MeshPhongMaterial:"phong",MeshToonMaterial:"toon",MeshStandardMaterial:"physical",MeshPhysicalMaterial:"physical",MeshMatcapMaterial:"matcap",LineBasicMaterial:"basic",LineDashedMaterial:"dashed",PointsMaterial:"points",ShadowMaterial:"shadow",SpriteMaterial:"sprite"};function E(T){return m.add(T),T===0?"uv":`uv${T}`}function R(T,O,I,W,J,re){const k=W.fog,K=J.geometry,B=T.isMeshStandardMaterial||T.isMeshLambertMaterial||T.isMeshPhongMaterial?W.environment:null,V=T.isMeshStandardMaterial||T.isMeshLambertMaterial&&!T.envMap||T.isMeshPhongMaterial&&!T.envMap,ee=e.get(T.envMap||B,V),oe=ee&&ee.mapping===Ku?ee.image.height:null,fe=_[T.type];T.precision!==null&&(x=s.getMaxPrecision(T.precision),x!==T.precision&&ht("WebGLProgram.getParameters:",T.precision,"not supported, using",x,"instead."));const D=K.morphAttributes.position||K.morphAttributes.normal||K.morphAttributes.color,se=D!==void 0?D.length:0;let _e=0;K.morphAttributes.position!==void 0&&(_e=1),K.morphAttributes.normal!==void 0&&(_e=2),K.morphAttributes.color!==void 0&&(_e=3);let De,ze,Xe,ue;if(fe){const Qt=Ha[fe];De=Qt.vertexShader,ze=Qt.fragmentShader}else{De=T.vertexShader,ze=T.fragmentShader;const Qt=h.getVertexShaderStage(T),Nt=h.getFragmentShaderStage(T);h.update(T,Qt,Nt),Xe=Qt.id,ue=Nt.id}const Se=r.getRenderTarget(),Re=r.state.buffers.depth.getReversed(),at=J.isInstancedMesh===!0,Ge=J.isBatchedMesh===!0,mt=!!T.map,un=!!T.matcap,ut=!!ee,xt=!!T.aoMap,bt=!!T.lightMap,pt=!!T.bumpMap&&T.wireframe===!1,vt=!!T.normalMap,Gt=!!T.displacementMap,vn=!!T.emissiveMap,Xt=!!T.metalnessMap,fn=!!T.roughnessMap,j=T.anisotropy>0,Ft=T.clearcoat>0,Ut=T.dispersion>0,P=T.retroreflectivity>0,M=T.iridescence>0,Z=T.sheen>0,ce=T.transmission>0,xe=j&&!!T.anisotropyMap,ne=Ft&&!!T.clearcoatMap,Ae=Ft&&!!T.clearcoatNormalMap,pe=Ft&&!!T.clearcoatRoughnessMap,ye=M&&!!T.iridescenceMap,Ne=M&&!!T.iridescenceThicknessMap,Ze=Z&&!!T.sheenColorMap,He=Z&&!!T.sheenRoughnessMap,Fe=!!T.specularMap,rt=!!T.specularColorMap,lt=!!T.specularIntensityMap,dt=ce&&!!T.transmissionMap,q=ce&&!!T.thicknessMap,Oe=!!T.gradientMap,be=!!T.alphaMap,Pe=T.alphaTest>0,Ve=!!T.alphaHash,we=!!T.extensions;let et=ka;T.toneMapped&&(Se===null||Se.isXRRenderTarget===!0)&&(et=r.toneMapping);const Je={shaderID:fe,shaderType:T.type,shaderName:T.name,vertexShader:De,fragmentShader:ze,defines:T.defines,customVertexShaderID:Xe,customFragmentShaderID:ue,isRawShaderMaterial:T.isRawShaderMaterial===!0,glslVersion:T.glslVersion,precision:x,batching:Ge,batchingColor:Ge&&J._colorsTexture!==null,instancing:at,instancingColor:at&&J.instanceColor!==null,instancingMorph:at&&J.morphTexture!==null,outputColorSpace:Se===null?r.outputColorSpace:Se.isXRRenderTarget===!0?Se.texture.colorSpace:kt.workingColorSpace,alphaToCoverage:!!T.alphaToCoverage,map:mt,matcap:un,envMap:ut,envMapMode:ut&&ee.mapping,envMapCubeUVHeight:oe,aoMap:xt,lightMap:bt,bumpMap:pt,normalMap:vt,displacementMap:Gt,emissiveMap:vn,normalMapObjectSpace:vt&&T.normalMapType===ub,normalMapTangentSpace:vt&&T.normalMapType===Kx,packedNormalMap:vt&&T.normalMapType===Kx&&JA(T.normalMap.format),metalnessMap:Xt,roughnessMap:fn,anisotropy:j,anisotropyMap:xe,clearcoat:Ft,clearcoatMap:ne,clearcoatNormalMap:Ae,clearcoatRoughnessMap:pe,dispersion:Ut,retroreflection:P,iridescence:M,iridescenceMap:ye,iridescenceThicknessMap:Ne,sheen:Z,sheenColorMap:Ze,sheenRoughnessMap:He,specularMap:Fe,specularColorMap:rt,specularIntensityMap:lt,transmission:ce,transmissionMap:dt,thicknessMap:q,gradientMap:Oe,opaque:T.transparent===!1&&T.blending===zo&&T.alphaToCoverage===!1,alphaMap:be,alphaTest:Pe,alphaHash:Ve,combine:T.combine,mapUv:mt&&E(T.map.channel),aoMapUv:xt&&E(T.aoMap.channel),lightMapUv:bt&&E(T.lightMap.channel),bumpMapUv:pt&&E(T.bumpMap.channel),normalMapUv:vt&&E(T.normalMap.channel),displacementMapUv:Gt&&E(T.displacementMap.channel),emissiveMapUv:vn&&E(T.emissiveMap.channel),metalnessMapUv:Xt&&E(T.metalnessMap.channel),roughnessMapUv:fn&&E(T.roughnessMap.channel),anisotropyMapUv:xe&&E(T.anisotropyMap.channel),clearcoatMapUv:ne&&E(T.clearcoatMap.channel),clearcoatNormalMapUv:Ae&&E(T.clearcoatNormalMap.channel),clearcoatRoughnessMapUv:pe&&E(T.clearcoatRoughnessMap.channel),iridescenceMapUv:ye&&E(T.iridescenceMap.channel),iridescenceThicknessMapUv:Ne&&E(T.iridescenceThicknessMap.channel),sheenColorMapUv:Ze&&E(T.sheenColorMap.channel),sheenRoughnessMapUv:He&&E(T.sheenRoughnessMap.channel),specularMapUv:Fe&&E(T.specularMap.channel),specularColorMapUv:rt&&E(T.specularColorMap.channel),specularIntensityMapUv:lt&&E(T.specularIntensityMap.channel),transmissionMapUv:dt&&E(T.transmissionMap.channel),thicknessMapUv:q&&E(T.thicknessMap.channel),alphaMapUv:be&&E(T.alphaMap.channel),vertexTangents:!!K.attributes.tangent&&(vt||j),vertexNormals:!!K.attributes.normal,vertexColors:T.vertexColors,vertexAlphas:T.vertexColors===!0&&!!K.attributes.color&&K.attributes.color.itemSize===4,pointsUvs:J.isPoints===!0&&!!K.attributes.uv&&(mt||be),fog:!!k,useFog:T.fog===!0,fogExp2:!!k&&k.isFogExp2,flatShading:T.wireframe===!1&&(T.flatShading===!0||K.attributes.normal===void 0&&vt===!1&&(T.isMeshLambertMaterial||T.isMeshPhongMaterial||T.isMeshStandardMaterial||T.isMeshPhysicalMaterial)),sizeAttenuation:T.sizeAttenuation===!0,logarithmicDepthBuffer:v,reversedDepthBuffer:Re,skinning:J.isSkinnedMesh===!0,hasPositionAttribute:K.attributes.position!==void 0,morphTargets:K.morphAttributes.position!==void 0,morphNormals:K.morphAttributes.normal!==void 0,morphColors:K.morphAttributes.color!==void 0,morphTargetsCount:se,morphTextureStride:_e,numSunLights:O.sun.length,numDirLights:O.directional.length,numPointLights:O.point.length,numSpotLights:O.spot.length,numSpotLightMaps:O.spotLightMap.length,numRectAreaLights:O.rectArea.length,numHemiLights:O.hemi.length,numSunLightShadows:O.sunShadowMap.length,numDirLightShadows:O.directionalShadowMap.length,numPointLightShadows:O.pointShadowMap.length,numSpotLightShadows:O.spotShadowMap.length,numSpotLightShadowsWithMaps:O.numSpotLightShadowsWithMaps,numLightProbes:O.numLightProbes,numLightProbeGrids:re.length,numClippingPlanes:c.numPlanes,numClipIntersection:c.numIntersection,dithering:T.dithering,shadowMapEnabled:r.shadowMap.enabled&&I.length>0,shadowMapType:r.shadowMap.type,toneMapping:et,decodeVideoTexture:mt&&T.map.isVideoTexture===!0&&kt.getTransfer(T.map.colorSpace)===cn,decodeVideoTextureEmissive:vn&&T.emissiveMap.isVideoTexture===!0&&kt.getTransfer(T.emissiveMap.colorSpace)===cn,premultipliedAlpha:T.premultipliedAlpha,doubleSided:T.side===vr,flipSided:T.side===Oi,useDepthPacking:T.depthPacking>=0,depthPacking:T.depthPacking||0,index0AttributeName:T.index0AttributeName,extensionClipCullDistance:we&&T.extensions.clipCullDistance===!0&&i.has("WEBGL_clip_cull_distance"),extensionMultiDraw:(we&&T.extensions.multiDraw===!0||Ge)&&i.has("WEBGL_multi_draw"),rendererExtensionParallelShaderCompile:i.has("KHR_parallel_shader_compile"),customProgramCacheKey:T.customProgramCacheKey()};return Je.vertexUv1s=m.has(1),Je.vertexUv2s=m.has(2),Je.vertexUv3s=m.has(3),m.clear(),Je}function b(T){const O=[];if(T.shaderID?O.push(T.shaderID):(O.push(T.customVertexShaderID),O.push(T.customFragmentShaderID)),T.defines!==void 0)for(const I in T.defines)O.push(I),O.push(T.defines[I]);return T.isRawShaderMaterial===!1&&(S(O,T),F(O,T),O.push(r.outputColorSpace)),O.push(T.customProgramCacheKey),O.join()}function S(T,O){T.push(O.precision),T.push(O.outputColorSpace),T.push(O.envMapMode),T.push(O.envMapCubeUVHeight),T.push(O.mapUv),T.push(O.alphaMapUv),T.push(O.lightMapUv),T.push(O.aoMapUv),T.push(O.bumpMapUv),T.push(O.normalMapUv),T.push(O.displacementMapUv),T.push(O.emissiveMapUv),T.push(O.metalnessMapUv),T.push(O.roughnessMapUv),T.push(O.anisotropyMapUv),T.push(O.clearcoatMapUv),T.push(O.clearcoatNormalMapUv),T.push(O.clearcoatRoughnessMapUv),T.push(O.iridescenceMapUv),T.push(O.iridescenceThicknessMapUv),T.push(O.sheenColorMapUv),T.push(O.sheenRoughnessMapUv),T.push(O.specularMapUv),T.push(O.specularColorMapUv),T.push(O.specularIntensityMapUv),T.push(O.transmissionMapUv),T.push(O.thicknessMapUv),T.push(O.combine),T.push(O.fogExp2),T.push(O.sizeAttenuation),T.push(O.morphTargetsCount),T.push(O.morphAttributeCount),T.push(O.numSunLights),T.push(O.numDirLights),T.push(O.numPointLights),T.push(O.numSpotLights),T.push(O.numSpotLightMaps),T.push(O.numHemiLights),T.push(O.numRectAreaLights),T.push(O.numSunLightShadows),T.push(O.numDirLightShadows),T.push(O.numPointLightShadows),T.push(O.numSpotLightShadows),T.push(O.numSpotLightShadowsWithMaps),T.push(O.numLightProbes),T.push(O.shadowMapType),T.push(O.toneMapping),T.push(O.numClippingPlanes),T.push(O.numClipIntersection),T.push(O.depthPacking)}function F(T,O){f.disableAll(),O.instancing&&f.enable(0),O.instancingColor&&f.enable(1),O.instancingMorph&&f.enable(2),O.matcap&&f.enable(3),O.envMap&&f.enable(4),O.normalMapObjectSpace&&f.enable(5),O.normalMapTangentSpace&&f.enable(6),O.clearcoat&&f.enable(7),O.iridescence&&f.enable(8),O.alphaTest&&f.enable(9),O.vertexColors&&f.enable(10),O.vertexAlphas&&f.enable(11),O.vertexUv1s&&f.enable(12),O.vertexUv2s&&f.enable(13),O.vertexUv3s&&f.enable(14),O.vertexTangents&&f.enable(15),O.anisotropy&&f.enable(16),O.alphaHash&&f.enable(17),O.batching&&f.enable(18),O.dispersion&&f.enable(19),O.retroreflection&&f.enable(24),O.batchingColor&&f.enable(20),O.gradientMap&&f.enable(21),O.packedNormalMap&&f.enable(22),O.vertexNormals&&f.enable(23),T.push(f.mask),f.disableAll(),O.fog&&f.enable(0),O.useFog&&f.enable(1),O.flatShading&&f.enable(2),O.logarithmicDepthBuffer&&f.enable(3),O.reversedDepthBuffer&&f.enable(4),O.skinning&&f.enable(5),O.morphTargets&&f.enable(6),O.morphNormals&&f.enable(7),O.morphColors&&f.enable(8),O.premultipliedAlpha&&f.enable(9),O.shadowMapEnabled&&f.enable(10),O.doubleSided&&f.enable(11),O.flipSided&&f.enable(12),O.useDepthPacking&&f.enable(13),O.dithering&&f.enable(14),O.transmission&&f.enable(15),O.sheen&&f.enable(16),O.opaque&&f.enable(17),O.pointsUvs&&f.enable(18),O.decodeVideoTexture&&f.enable(19),O.decodeVideoTextureEmissive&&f.enable(20),O.alphaToCoverage&&f.enable(21),O.numLightProbeGrids>0&&f.enable(22),O.hasPositionAttribute&&f.enable(23),T.push(f.mask)}function G(T){const O=_[T.type];let I;if(O){const W=Ha[O];I=gM.clone(W.uniforms)}else I=T.uniforms;return I}function w(T,O){let I=g.get(O);return I!==void 0?++I.usedTimes:(I=new jA(r,O,T,l),p.push(I),g.set(O,I)),I}function N(T){if(--T.usedTimes===0){const O=p.indexOf(T);p[O]=p[p.length-1],p.pop(),g.delete(T.cacheKey),T.destroy()}}function L(T){h.remove(T)}function z(){h.dispose()}return{getParameters:R,getProgramCacheKey:b,getUniforms:G,acquireProgram:w,releaseProgram:N,releaseShaderCache:L,programs:p,dispose:z}}function ew(){let r=new WeakMap;function e(f){return r.has(f)}function i(f){let h=r.get(f);return h===void 0&&(h={},r.set(f,h)),h}function s(f){r.delete(f)}function l(f,h,m){r.get(f)[h]=m}function c(){r=new WeakMap}return{has:e,get:i,remove:s,update:l,dispose:c}}function tw(r,e){return r.groupOrder!==e.groupOrder?r.groupOrder-e.groupOrder:r.renderOrder!==e.renderOrder?r.renderOrder-e.renderOrder:r.material.id!==e.material.id?r.material.id-e.material.id:r.materialVariant!==e.materialVariant?r.materialVariant-e.materialVariant:r.z!==e.z?r.z-e.z:r.id-e.id}function Zv(r,e){return r.groupOrder!==e.groupOrder?r.groupOrder-e.groupOrder:r.renderOrder!==e.renderOrder?r.renderOrder-e.renderOrder:r.z!==e.z?e.z-r.z:r.id-e.id}function Kv(){const r=[];let e=0;const i=[],s=[],l=[];function c(){e=0,i.length=0,s.length=0,l.length=0}function f(x){let _=0;return x.isInstancedMesh&&(_+=2),x.isSkinnedMesh&&(_+=1),_}function h(x,_,E,R,b,S){let F=r[e];return F===void 0?(F={id:x.id,object:x,geometry:_,material:E,materialVariant:f(x),groupOrder:R,renderOrder:x.renderOrder,z:b,group:S},r[e]=F):(F.id=x.id,F.object=x,F.geometry=_,F.material=E,F.materialVariant=f(x),F.groupOrder=R,F.renderOrder=x.renderOrder,F.z=b,F.group=S),e++,F}function m(x,_,E,R,b,S,F){F.reversedDepth===!0&&(b=-b);const G=h(x,_,E,R,b,S);E.transmission>0?s.push(G):E.transparent===!0?l.push(G):i.push(G)}function p(x,_,E,R,b,S){const F=h(x,_,E,R,b,S);E.transmission>0?s.unshift(F):E.transparent===!0?l.unshift(F):i.unshift(F)}function g(x,_){i.length>1&&i.sort(x||tw),s.length>1&&s.sort(_||Zv),l.length>1&&l.sort(_||Zv)}function v(){for(let x=e,_=r.length;x<_;x++){const E=r[x];if(E.id===null)break;E.id=null,E.object=null,E.geometry=null,E.material=null,E.group=null}}return{opaque:i,transmissive:s,transparent:l,init:c,push:m,unshift:p,finish:v,sort:g}}function nw(){let r=new WeakMap;function e(s,l){const c=r.get(s);let f;return c===void 0?(f=new Kv,r.set(s,[f])):l>=c.length?(f=new Kv,c.push(f)):f=c[l],f}function i(){r=new WeakMap}return{get:e,dispose:i}}function iw(){const r={};return{get:function(e){if(r[e.id]!==void 0)return r[e.id];let i;switch(e.type){case"SunLight":case"DirectionalLight":i={direction:new Q,color:new wt};break;case"SpotLight":i={position:new Q,direction:new Q,color:new wt,distance:0,coneCos:0,penumbraCos:0,decay:0};break;case"PointLight":i={position:new Q,color:new wt,distance:0,decay:0};break;case"HemisphereLight":i={direction:new Q,skyColor:new wt,groundColor:new wt};break;case"RectAreaLight":i={color:new wt,position:new Q,halfWidth:new Q,halfHeight:new Q};break}return r[e.id]=i,i}}}function aw(){const r={};return{get:function(e){if(r[e.id]!==void 0)return r[e.id];let i;switch(e.type){case"SunLight":case"DirectionalLight":i={shadowIntensity:1,shadowBias:0,shadowNormalBias:0,shadowRadius:1,shadowMapSize:new Kt};break;case"SpotLight":i={shadowIntensity:1,shadowBias:0,shadowNormalBias:0,shadowRadius:1,shadowMapSize:new Kt};break;case"PointLight":i={shadowIntensity:1,shadowBias:0,shadowNormalBias:0,shadowRadius:1,shadowMapSize:new Kt,shadowCameraNear:1,shadowCameraFar:1e3};break}return r[e.id]=i,i}}}let rw=0;function sw(r,e){return(e.castShadow?2:0)-(r.castShadow?2:0)+(e.map?1:0)-(r.map?1:0)}function ow(r){const e=new iw,i=aw(),s={version:0,hash:{sunLength:-1,directionalLength:-1,pointLength:-1,spotLength:-1,rectAreaLength:-1,hemiLength:-1,numSunShadows:-1,numDirectionalShadows:-1,numPointShadows:-1,numSpotShadows:-1,numSpotMaps:-1,numLightProbes:-1},ambient:[0,0,0],probe:[],sun:[],sunShadow:[],sunShadowMap:[],sunShadowMatrix:[],sunShadowCascade:[],directional:[],directionalShadow:[],directionalShadowMap:[],directionalShadowMatrix:[],spot:[],spotLightMap:[],spotShadow:[],spotShadowMap:[],spotLightMatrix:[],rectArea:[],rectAreaLTC1:null,rectAreaLTC2:null,point:[],pointShadow:[],pointShadowMap:[],pointShadowMatrix:[],hemi:[],numSpotLightShadowsWithMaps:0,numLightProbes:0};for(let p=0;p<9;p++)s.probe.push(new Q);const l=new Q,c=new En,f=new En;function h(p){let g=0,v=0,x=0;for(let J=0;J<9;J++)s.probe[J].set(0,0,0);let _=0,E=0,R=0,b=0,S=0,F=0,G=0,w=0,N=0,L=0,z=0,T=0,O=0,I=0;p.sort(sw);for(let J=0,re=p.length;J<re;J++){const k=p[J],K=k.color,B=k.intensity,V=k.distance;let ee=null;if(k.shadow&&k.shadow.map&&(k.shadow.map.texture.format===Ps?ee=k.shadow.map.texture:ee=k.shadow.map.depthTexture||k.shadow.map.texture),k.isAmbientLight)g+=K.r*B,v+=K.g*B,x+=K.b*B;else if(k.isLightProbe){for(let oe=0;oe<9;oe++)s.probe[oe].addScaledVector(k.sh.coefficients[oe],B);I++}else if(k.isSunLight){const oe=e.get(k);if(oe.color.copy(k.color).multiplyScalar(k.intensity),k.castShadow){const fe=k.shadow,D=i.get(k);D.shadowIntensity=fe.intensity,D.shadowBias=fe.bias,D.shadowNormalBias=fe.normalBias,D.shadowRadius=fe.radius,D.shadowMapSize.copy(fe.mapSize).multiply(fe.getFrameExtents()),s.sunShadow[E]=D,s.sunShadowMap[E]=ee;const se=fe.getViewportCount();for(let _e=0;_e<se;_e++)s.sunShadowMatrix[R+_e]=fe.getMatrix(_e),s.sunShadowCascade[R+_e]=fe._cascadeData[_e];R+=se,E++}s.sun[_]=oe,_++}else if(k.isDirectionalLight){const oe=e.get(k);if(oe.color.copy(k.color).multiplyScalar(k.intensity),k.castShadow){const fe=k.shadow,D=i.get(k);D.shadowIntensity=fe.intensity,D.shadowBias=fe.bias,D.shadowNormalBias=fe.normalBias,D.shadowRadius=fe.radius,D.shadowMapSize=fe.mapSize,s.directionalShadow[b]=D,s.directionalShadowMap[b]=ee,s.directionalShadowMatrix[b]=k.shadow.matrix,N++}s.directional[b]=oe,b++}else if(k.isSpotLight){const oe=e.get(k);oe.position.setFromMatrixPosition(k.matrixWorld),oe.color.copy(K).multiplyScalar(B),oe.distance=V,oe.coneCos=Math.cos(k.angle),oe.penumbraCos=Math.cos(k.angle*(1-k.penumbra)),oe.decay=k.decay,s.spot[F]=oe;const fe=k.shadow;if(k.map&&(s.spotLightMap[T]=k.map,T++,fe.updateMatrices(k),k.castShadow&&O++),s.spotLightMatrix[F]=fe.matrix,k.castShadow){const D=i.get(k);D.shadowIntensity=fe.intensity,D.shadowBias=fe.bias,D.shadowNormalBias=fe.normalBias,D.shadowRadius=fe.radius,D.shadowMapSize=fe.mapSize,s.spotShadow[F]=D,s.spotShadowMap[F]=ee,z++}F++}else if(k.isRectAreaLight){const oe=e.get(k);oe.color.copy(K).multiplyScalar(B),oe.halfWidth.set(k.width*.5,0,0),oe.halfHeight.set(0,k.height*.5,0),s.rectArea[G]=oe,G++}else if(k.isPointLight){const oe=e.get(k);if(oe.color.copy(k.color).multiplyScalar(k.intensity),oe.distance=k.distance,oe.decay=k.decay,k.castShadow){const fe=k.shadow,D=i.get(k);D.shadowIntensity=fe.intensity,D.shadowBias=fe.bias,D.shadowNormalBias=fe.normalBias,D.shadowRadius=fe.radius,D.shadowMapSize=fe.mapSize,D.shadowCameraNear=fe.camera.near,D.shadowCameraFar=fe.camera.far,s.pointShadow[S]=D,s.pointShadowMap[S]=ee,s.pointShadowMatrix[S]=k.shadow.matrix,L++}s.point[S]=oe,S++}else if(k.isHemisphereLight){const oe=e.get(k);oe.skyColor.copy(k.color).multiplyScalar(B),oe.groundColor.copy(k.groundColor).multiplyScalar(B),s.hemi[w]=oe,w++}}G>0&&(r.has("OES_texture_float_linear")===!0?(s.rectAreaLTC1=je.LTC_FLOAT_1,s.rectAreaLTC2=je.LTC_FLOAT_2):(s.rectAreaLTC1=je.LTC_HALF_1,s.rectAreaLTC2=je.LTC_HALF_2)),s.ambient[0]=g,s.ambient[1]=v,s.ambient[2]=x;const W=s.hash;(W.sunLength!==_||W.directionalLength!==b||W.pointLength!==S||W.spotLength!==F||W.rectAreaLength!==G||W.hemiLength!==w||W.numSunShadows!==E||W.numDirectionalShadows!==N||W.numPointShadows!==L||W.numSpotShadows!==z||W.numSpotMaps!==T||W.numLightProbes!==I)&&(s.sun.length=_,s.directional.length=b,s.spot.length=F,s.rectArea.length=G,s.point.length=S,s.hemi.length=w,s.sunShadow.length=E,s.sunShadowMap.length=E,s.sunShadowMatrix.length=R,s.sunShadowCascade.length=R,s.directionalShadow.length=N,s.directionalShadowMap.length=N,s.directionalShadowMatrix.length=N,s.pointShadow.length=L,s.pointShadowMap.length=L,s.pointShadowMatrix.length=L,s.spotShadow.length=z,s.spotShadowMap.length=z,s.spotLightMatrix.length=z+T-O,s.spotLightMap.length=T,s.numSpotLightShadowsWithMaps=O,s.numLightProbes=I,W.sunLength=_,W.directionalLength=b,W.pointLength=S,W.spotLength=F,W.rectAreaLength=G,W.hemiLength=w,W.numSunShadows=E,W.numDirectionalShadows=N,W.numPointShadows=L,W.numSpotShadows=z,W.numSpotMaps=T,W.numLightProbes=I,s.version=rw++)}function m(p,g){let v=0,x=0,_=0,E=0,R=0,b=0;const S=g.matrixWorldInverse;for(let F=0,G=p.length;F<G;F++){const w=p[F];if(w.isSunLight){const N=s.sun[v];N.direction.setFromMatrixPosition(w.matrixWorld),N.direction.transformDirection(S),v++}else if(w.isDirectionalLight){const N=s.directional[x];N.direction.setFromMatrixPosition(w.matrixWorld),l.setFromMatrixPosition(w.target.matrixWorld),N.direction.sub(l),N.direction.transformDirection(S),x++}else if(w.isSpotLight){const N=s.spot[E];N.position.setFromMatrixPosition(w.matrixWorld),N.position.applyMatrix4(S),N.direction.setFromMatrixPosition(w.matrixWorld),l.setFromMatrixPosition(w.target.matrixWorld),N.direction.sub(l),N.direction.transformDirection(S),E++}else if(w.isRectAreaLight){const N=s.rectArea[R];N.position.setFromMatrixPosition(w.matrixWorld),N.position.applyMatrix4(S),f.identity(),c.copy(w.matrixWorld),c.premultiply(S),f.extractRotation(c),N.halfWidth.set(w.width*.5,0,0),N.halfHeight.set(0,w.height*.5,0),N.halfWidth.applyMatrix4(f),N.halfHeight.applyMatrix4(f),R++}else if(w.isPointLight){const N=s.point[_];N.position.setFromMatrixPosition(w.matrixWorld),N.position.applyMatrix4(S),_++}else if(w.isHemisphereLight){const N=s.hemi[b];N.direction.setFromMatrixPosition(w.matrixWorld),N.direction.transformDirection(S),b++}}}return{setup:h,setupView:m,state:s}}function Qv(r){const e=new ow(r),i=[],s=[],l=[];function c(x){v.camera=x,i.length=0,s.length=0,l.length=0}function f(x){i.push(x)}function h(x){s.push(x)}function m(x){l.push(x)}function p(){e.setup(i)}function g(x){e.setupView(i,x)}const v={lightsArray:i,shadowsArray:s,lightProbeGridArray:l,camera:null,lights:e,transmissionRenderTarget:{},textureUnits:0};return{init:c,state:v,setupLights:p,setupLightsView:g,pushLight:f,pushShadow:h,pushLightProbeGrid:m}}function lw(r){let e=new WeakMap;function i(l,c=0){const f=e.get(l);let h;return f===void 0?(h=new Qv(r),e.set(l,[h])):c>=f.length?(h=new Qv(r),f.push(h)):h=f[c],h}function s(){e=new WeakMap}return{get:i,dispose:s}}const cw=`void main() {
	gl_Position = vec4( position, 1.0 );
}`,uw=`uniform sampler2D shadow_pass;
uniform vec2 resolution;
uniform float radius;
void main() {
	const float samples = float( VSM_SAMPLES );
	float mean = 0.0;
	float squared_mean = 0.0;
	float uvStride = samples <= 1.0 ? 0.0 : 2.0 / ( samples - 1.0 );
	float uvStart = samples <= 1.0 ? 0.0 : - 1.0;
	for ( float i = 0.0; i < samples; i ++ ) {
		float uvOffset = uvStart + i * uvStride;
		#ifdef HORIZONTAL_PASS
			vec2 distribution = texture2D( shadow_pass, ( gl_FragCoord.xy + vec2( uvOffset, 0.0 ) * radius ) / resolution ).rg;
			mean += distribution.x;
			squared_mean += distribution.y * distribution.y + distribution.x * distribution.x;
		#else
			float depth = texture2D( shadow_pass, ( gl_FragCoord.xy + vec2( 0.0, uvOffset ) * radius ) / resolution ).r;
			mean += depth;
			squared_mean += depth * depth;
		#endif
	}
	mean = mean / samples;
	squared_mean = squared_mean / samples;
	float std_dev = sqrt( max( 0.0, squared_mean - mean * mean ) );
	gl_FragColor = vec4( mean, std_dev, 0.0, 1.0 );
}`,fw=[new Q(1,0,0),new Q(-1,0,0),new Q(0,1,0),new Q(0,-1,0),new Q(0,0,1),new Q(0,0,-1)],dw=[new Q(0,-1,0),new Q(0,-1,0),new Q(0,0,1),new Q(0,0,-1),new Q(0,-1,0),new Q(0,-1,0)],Jv=new En,Fl=new Q,Gh=new Q;function hw(r,e,i){let s=new P_;const l=new Kt,c=new Kt,f=new Ln,h=new yM,m=new SM,p={},g=i.maxTextureSize,v={[Ls]:Oi,[Oi]:Ls,[vr]:vr},x=new Yn({defines:{VSM_SAMPLES:8},uniforms:{shadow_pass:{value:null},resolution:{value:new Kt},radius:{value:4}},vertexShader:cw,fragmentShader:uw}),_=x.clone();_.defines.HORIZONTAL_PASS=1;const E=new Bn;E.setAttribute("position",new Fn(new Float32Array([-1,-1,.5,3,-1,.5,-1,3,.5]),3));const R=new ji(E,x),b=this;this.enabled=!1,this.autoUpdate=!0,this.needsUpdate=!1,this.type=Nu;let S=this.type;this.render=function(L,z,T){if(b.enabled===!1||b.autoUpdate===!1&&b.needsUpdate===!1||L.length===0)return;this.type===G1&&(ht("WebGLShadowMap: PCFSoftShadowMap has been removed. Using PCFShadowMap instead."),this.type=Nu);const O=r.getRenderTarget(),I=r.getActiveCubeFace(),W=r.getActiveMipmapLevel(),J=r.state;J.setBlending(Sr),J.buffers.depth.getReversed()===!0?J.buffers.color.setClear(0,0,0,0):J.buffers.color.setClear(1,1,1,1),J.buffers.depth.setTest(!0),J.setScissorTest(!1);const re=S!==this.type;re&&z.traverse(function(k){k.material&&(Array.isArray(k.material)?k.material.forEach(K=>K.needsUpdate=!0):k.material.needsUpdate=!0)});for(let k=0,K=L.length;k<K;k++){const B=L[k],V=B.shadow;if(V===void 0){ht("WebGLShadowMap:",B,"has no shadow.");continue}if(V.autoUpdate===!1&&V.needsUpdate===!1)continue;l.copy(V.mapSize);const ee=V.getFrameExtents();l.multiply(ee),c.copy(V.mapSize),(l.x>g||l.y>g)&&(l.x>g&&(c.x=Math.floor(g/ee.x),l.x=c.x*ee.x,V.mapSize.x=c.x),l.y>g&&(c.y=Math.floor(g/ee.y),l.y=c.y*ee.y,V.mapSize.y=c.y));const oe=r.state.buffers.depth.getReversed();if(V.camera._reversedDepth=oe,V.map===null||re===!0){if(V.map!==null&&(V.map.depthTexture!==null&&(V.map.depthTexture.dispose(),V.map.depthTexture=null),V.map.dispose()),this.type===Il){if(B.isPointLight){ht("WebGLShadowMap: VSM shadow maps are not supported for PointLights. Use PCF or BasicShadowMap instead.");continue}V.map=new wa(l.x,l.y,{format:Ps,type:Wa,minFilter:mi,magFilter:mi,generateMipmaps:!1}),V.map.texture.name=B.name+".shadowMap",V.map.depthTexture=new Ql(l.x,l.y,Ga),V.map.depthTexture.name=B.name+".shadowMapDepth",V.map.depthTexture.format=Mr,V.map.depthTexture.compareFunction=null,V.map.depthTexture.minFilter=li,V.map.depthTexture.magFilter=li}else B.isPointLight?(V.map=new X_(l.x),V.map.depthTexture=new cM(l.x,Xa)):(V.map=new wa(l.x,l.y),V.map.depthTexture=new Ql(l.x,l.y,Xa)),V.map.depthTexture.name=B.name+".shadowMap",V.map.depthTexture.format=Mr,this.type===Nu?(V.map.depthTexture.compareFunction=oe?Wp:Xp,V.map.depthTexture.minFilter=mi,V.map.depthTexture.magFilter=mi):(V.map.depthTexture.compareFunction=null,V.map.depthTexture.minFilter=li,V.map.depthTexture.magFilter=li);V.camera.updateProjectionMatrix()}V.map.isWebGLCubeRenderTarget!==!0&&(V.map.width!==l.x||V.map.height!==l.y)&&V.map.setSize(l.x,l.y);const fe=V.map.isWebGLCubeRenderTarget?6:V.getViewportCount();B.isPointLight!==!0&&V.updateMatrices(B,T);for(let D=0;D<fe;D++){const se=V.getCamera(D);if(B.isPointLight){const _e=V.camera,De=V.matrix,ze=B.distance||_e.far;ze!==_e.far&&(_e.far=ze,_e.updateProjectionMatrix()),Fl.setFromMatrixPosition(B.matrixWorld),_e.position.copy(Fl),Gh.copy(_e.position),Gh.add(fw[D]),_e.up.copy(dw[D]),_e.lookAt(Gh),_e.updateMatrixWorld(),De.makeTranslation(-Fl.x,-Fl.y,-Fl.z),Jv.multiplyMatrices(_e.projectionMatrix,_e.matrixWorldInverse),V._frustum.setFromProjectionMatrix(Jv,_e.coordinateSystem,_e.reversedDepth)}if(V.map.isWebGLCubeRenderTarget)r.setRenderTarget(V.map,D),r.clear();else{D===0&&(r.setRenderTarget(V.map),r.clear());const _e=V.getViewport(D);f.set(c.x*_e.x,c.y*_e.y,c.x*_e.z,c.y*_e.w),J.viewport(f)}s=V.getFrustum(D),w(z,T,se,B,this.type)}V.isPointLightShadow!==!0&&this.type===Il&&F(V,T),V.needsUpdate=!1}S=this.type,b.needsUpdate=!1,r.setRenderTarget(O,I,W)};function F(L,z){const T=e.update(R);x.defines.VSM_SAMPLES!==L.blurSamples&&(x.defines.VSM_SAMPLES=L.blurSamples,_.defines.VSM_SAMPLES=L.blurSamples,x.needsUpdate=!0,_.needsUpdate=!0),L.mapPass===null?L.mapPass=new wa(l.x,l.y,{format:Ps,type:Wa}):(L.mapPass.width!==L.map.width||L.mapPass.height!==L.map.height)&&L.mapPass.setSize(L.map.width,L.map.height),x.uniforms.shadow_pass.value=L.map.depthTexture,x.uniforms.resolution.value.set(L.map.width,L.map.height),x.uniforms.radius.value=L.radius,r.setRenderTarget(L.mapPass),r.clear(),r.renderBufferDirect(z,null,T,x,R,null),_.uniforms.shadow_pass.value=L.mapPass.texture,_.uniforms.resolution.value.set(L.map.width,L.map.height),_.uniforms.radius.value=L.radius,r.setRenderTarget(L.map),r.clear(),r.renderBufferDirect(z,null,T,_,R,null)}function G(L,z,T,O){let I=null;const W=T.isPointLight===!0?L.customDistanceMaterial:L.customDepthMaterial;if(W!==void 0)I=W;else if(I=T.isPointLight===!0?m:h,r.localClippingEnabled&&z.clipShadows===!0&&Array.isArray(z.clippingPlanes)&&z.clippingPlanes.length!==0||z.displacementMap&&z.displacementScale!==0||z.alphaMap&&z.alphaTest>0||z.map&&z.alphaTest>0||z.alphaToCoverage===!0){const J=I.uuid,re=z.uuid;let k=p[J];k===void 0&&(k={},p[J]=k);let K=k[re];K===void 0&&(K=I.clone(),k[re]=K,z.addEventListener("dispose",N)),I=K}if(I.visible=z.visible,I.wireframe=z.wireframe,O===Il?I.side=z.shadowSide!==null?z.shadowSide:z.side:I.side=z.shadowSide!==null?z.shadowSide:v[z.side],I.alphaMap=z.alphaMap,I.alphaTest=z.alphaToCoverage===!0?.5:z.alphaTest,I.map=z.map,I.clipShadows=z.clipShadows,I.clippingPlanes=z.clippingPlanes,I.clipIntersection=z.clipIntersection,I.displacementMap=z.displacementMap,I.displacementScale=z.displacementScale,I.displacementBias=z.displacementBias,I.wireframeLinewidth=z.wireframeLinewidth,I.linewidth=z.linewidth,T.isPointLight===!0&&I.isMeshDistanceMaterial===!0){const J=r.properties.get(I);J.light=T}return I}function w(L,z,T,O,I){if(L.visible===!1)return;if(L.layers.test(z.layers)&&(L.isMesh||L.isLine||L.isPoints)&&(L.castShadow||L.receiveShadow&&I===Il)&&(!L.frustumCulled||L.intersectsFrustum(s))){L.modelViewMatrix.multiplyMatrices(T.matrixWorldInverse,L.matrixWorld);const re=e.update(L),k=L.material;if(Array.isArray(k)){const K=re.groups;for(let B=0,V=K.length;B<V;B++){const ee=K[B],oe=k[ee.materialIndex];if(oe&&oe.visible){const fe=G(L,oe,O,I);L.onBeforeShadow(r,L,z,T,re,fe,ee),r.renderBufferDirect(T,null,re,fe,L,ee),L.onAfterShadow(r,L,z,T,re,fe,ee)}}}else if(k.visible){const K=G(L,k,O,I);L.onBeforeShadow(r,L,z,T,re,K,null),r.renderBufferDirect(T,null,re,K,L,null),L.onAfterShadow(r,L,z,T,re,K,null)}}const J=L.children;for(let re=0,k=J.length;re<k;re++)w(J[re],z,T,O,I)}function N(L){L.target.removeEventListener("dispose",N);for(const T in p){const O=p[T],I=L.target.uuid;I in O&&(O[I].dispose(),delete O[I])}}}function pw(r,e){function i(){let q=!1;const Oe=new Ln;let be=null;const Pe=new Ln(0,0,0,0);return{setMask:function(Ve){be!==Ve&&!q&&(r.colorMask(Ve,Ve,Ve,Ve),be=Ve)},setLocked:function(Ve){q=Ve},setClear:function(Ve,we,et,Je,Qt){Qt===!0&&(Ve*=Je,we*=Je,et*=Je),Oe.set(Ve,we,et,Je),Pe.equals(Oe)===!1&&(r.clearColor(Ve,we,et,Je),Pe.copy(Oe))},reset:function(){q=!1,be=null,Pe.set(-1,0,0,0)}}}function s(){let q=!1,Oe=!1,be=null,Pe=null,Ve=null;return{setReversed:function(we){if(Oe!==we){const et=e.get("EXT_clip_control");we?et.clipControlEXT(et.LOWER_LEFT_EXT,et.ZERO_TO_ONE_EXT):et.clipControlEXT(et.LOWER_LEFT_EXT,et.NEGATIVE_ONE_TO_ONE_EXT),Oe=we;const Je=Ve;Ve=null,this.setClear(Je)}},getReversed:function(){return Oe},setTest:function(we){we?Se(r.DEPTH_TEST):Re(r.DEPTH_TEST)},setMask:function(we){be!==we&&!q&&(r.depthMask(we),be=we)},setFunc:function(we){if(Oe&&(we=bb[we]),Pe!==we){switch(we){case Xh:r.depthFunc(r.NEVER);break;case Wh:r.depthFunc(r.ALWAYS);break;case qh:r.depthFunc(r.LESS);break;case ql:r.depthFunc(r.LEQUAL);break;case Yh:r.depthFunc(r.EQUAL);break;case jh:r.depthFunc(r.GEQUAL);break;case Zh:r.depthFunc(r.GREATER);break;case Kh:r.depthFunc(r.NOTEQUAL);break;default:r.depthFunc(r.LEQUAL)}Pe=we}},setLocked:function(we){q=we},setClear:function(we){Ve!==we&&(Ve=we,Oe&&(we=1-we),r.clearDepth(we))},reset:function(){q=!1,be=null,Pe=null,Ve=null,Oe=!1}}}function l(){let q=!1,Oe=null,be=null,Pe=null,Ve=null,we=null,et=null,Je=null,Qt=null;return{setTest:function(Nt){q||(Nt?Se(r.STENCIL_TEST):Re(r.STENCIL_TEST))},setMask:function(Nt){Oe!==Nt&&!q&&(r.stencilMask(Nt),Oe=Nt)},setFunc:function(Nt,ei,ti){(be!==Nt||Pe!==ei||Ve!==ti)&&(r.stencilFunc(Nt,ei,ti),be=Nt,Pe=ei,Ve=ti)},setOp:function(Nt,ei,ti){(we!==Nt||et!==ei||Je!==ti)&&(r.stencilOp(Nt,ei,ti),we=Nt,et=ei,Je=ti)},setLocked:function(Nt){q=Nt},setClear:function(Nt){Qt!==Nt&&(r.clearStencil(Nt),Qt=Nt)},reset:function(){q=!1,Oe=null,be=null,Pe=null,Ve=null,we=null,et=null,Je=null,Qt=null}}}const c=new i,f=new s,h=new l,m=new WeakMap,p=new WeakMap;let g={},v={},x={},_=new WeakMap,E=[],R=null,b=!1,S=null,F=null,G=null,w=null,N=null,L=null,z=null,T=new wt(0,0,0),O=0,I=!1,W=null,J=null,re=null,k=null,K=null;const B=r.getParameter(r.MAX_COMBINED_TEXTURE_IMAGE_UNITS);let V=!1,ee=0;const oe=r.getParameter(r.VERSION);oe.indexOf("WebGL")!==-1?(ee=parseFloat(/^WebGL (\d)/.exec(oe)[1]),V=ee>=1):oe.indexOf("OpenGL ES")!==-1&&(ee=parseFloat(/^OpenGL ES (\d)/.exec(oe)[1]),V=ee>=2);let fe=null,D={};const se=r.getParameter(r.SCISSOR_BOX),_e=r.getParameter(r.VIEWPORT),De=new Ln().fromArray(se),ze=new Ln().fromArray(_e);function Xe(q,Oe,be,Pe){const Ve=new Uint8Array(4),we=r.createTexture();r.bindTexture(q,we),r.texParameteri(q,r.TEXTURE_MIN_FILTER,r.NEAREST),r.texParameteri(q,r.TEXTURE_MAG_FILTER,r.NEAREST);for(let et=0;et<be;et++)q===r.TEXTURE_3D||q===r.TEXTURE_2D_ARRAY?r.texImage3D(Oe,0,r.RGBA,1,1,Pe,0,r.RGBA,r.UNSIGNED_BYTE,Ve):r.texImage2D(Oe+et,0,r.RGBA,1,1,0,r.RGBA,r.UNSIGNED_BYTE,Ve);return we}const ue={};ue[r.TEXTURE_2D]=Xe(r.TEXTURE_2D,r.TEXTURE_2D,1),ue[r.TEXTURE_CUBE_MAP]=Xe(r.TEXTURE_CUBE_MAP,r.TEXTURE_CUBE_MAP_POSITIVE_X,6),ue[r.TEXTURE_2D_ARRAY]=Xe(r.TEXTURE_2D_ARRAY,r.TEXTURE_2D_ARRAY,1,1),ue[r.TEXTURE_3D]=Xe(r.TEXTURE_3D,r.TEXTURE_3D,1,1),c.setClear(0,0,0,1),f.setClear(1),h.setClear(0),Se(r.DEPTH_TEST),f.setFunc(ql),pt(!1),vt(Yx),Se(r.CULL_FACE),xt(Sr);function Se(q){g[q]!==!0&&(r.enable(q),g[q]=!0)}function Re(q){g[q]!==!1&&(r.disable(q),g[q]=!1)}function at(q,Oe){return x[q]!==Oe?(r.bindFramebuffer(q,Oe),x[q]=Oe,q===r.DRAW_FRAMEBUFFER&&(x[r.FRAMEBUFFER]=Oe),q===r.FRAMEBUFFER&&(x[r.DRAW_FRAMEBUFFER]=Oe),!0):!1}function Ge(q,Oe){let be=E,Pe=!1;if(q){be=_.get(Oe),be===void 0&&(be=[],_.set(Oe,be));const Ve=q.textures;if(be.length!==Ve.length||be[0]!==r.COLOR_ATTACHMENT0){for(let we=0,et=Ve.length;we<et;we++)be[we]=r.COLOR_ATTACHMENT0+we;be.length=Ve.length,Pe=!0}}else be[0]!==r.BACK&&(be[0]=r.BACK,Pe=!0);Pe&&r.drawBuffers(be)}function mt(q){return R!==q?(r.useProgram(q),R=q,!0):!1}const un={[No]:r.FUNC_ADD,[k1]:r.FUNC_SUBTRACT,[X1]:r.FUNC_REVERSE_SUBTRACT};un[W1]=r.MIN,un[q1]=r.MAX;const ut={[Y1]:r.ZERO,[j1]:r.ONE,[Z1]:r.SRC_COLOR,[f_]:r.SRC_ALPHA,[tb]:r.SRC_ALPHA_SATURATE,[$1]:r.DST_COLOR,[Q1]:r.DST_ALPHA,[K1]:r.ONE_MINUS_SRC_COLOR,[d_]:r.ONE_MINUS_SRC_ALPHA,[eb]:r.ONE_MINUS_DST_COLOR,[J1]:r.ONE_MINUS_DST_ALPHA,[nb]:r.CONSTANT_COLOR,[ib]:r.ONE_MINUS_CONSTANT_COLOR,[ab]:r.CONSTANT_ALPHA,[rb]:r.ONE_MINUS_CONSTANT_ALPHA};function xt(q,Oe,be,Pe,Ve,we,et,Je,Qt,Nt){if(q===Sr){b===!0&&(Re(r.BLEND),b=!1);return}if(b===!1&&(Se(r.BLEND),b=!0),q!==V1){if(q!==S||Nt!==I){if((F!==No||N!==No)&&(r.blendEquation(r.FUNC_ADD),F=No,N=No),Nt)switch(q){case zo:r.blendFuncSeparate(r.ONE,r.ONE_MINUS_SRC_ALPHA,r.ONE,r.ONE_MINUS_SRC_ALPHA);break;case Aa:r.blendFunc(r.ONE,r.ONE);break;case jx:r.blendFuncSeparate(r.ZERO,r.ONE_MINUS_SRC_COLOR,r.ZERO,r.ONE);break;case Zx:r.blendFuncSeparate(r.DST_COLOR,r.ONE_MINUS_SRC_ALPHA,r.ZERO,r.ONE);break;default:Zt("WebGLState: Invalid blending: ",q);break}else switch(q){case zo:r.blendFuncSeparate(r.SRC_ALPHA,r.ONE_MINUS_SRC_ALPHA,r.ONE,r.ONE_MINUS_SRC_ALPHA);break;case Aa:r.blendFuncSeparate(r.SRC_ALPHA,r.ONE,r.ONE,r.ONE);break;case jx:Zt("WebGLState: SubtractiveBlending requires material.premultipliedAlpha = true");break;case Zx:Zt("WebGLState: MultiplyBlending requires material.premultipliedAlpha = true");break;default:Zt("WebGLState: Invalid blending: ",q);break}G=null,w=null,L=null,z=null,T.set(0,0,0),O=0,S=q,I=Nt}return}Ve=Ve||Oe,we=we||be,et=et||Pe,(Oe!==F||Ve!==N)&&(r.blendEquationSeparate(un[Oe],un[Ve]),F=Oe,N=Ve),(be!==G||Pe!==w||we!==L||et!==z)&&(r.blendFuncSeparate(ut[be],ut[Pe],ut[we],ut[et]),G=be,w=Pe,L=we,z=et),(Je.equals(T)===!1||Qt!==O)&&(r.blendColor(Je.r,Je.g,Je.b,Qt),T.copy(Je),O=Qt),S=q,I=!1}function bt(q,Oe){q.side===vr?Re(r.CULL_FACE):Se(r.CULL_FACE);let be=q.side===Oi;Oe&&(be=!be),pt(be),q.blending===zo&&q.transparent===!1?xt(Sr):xt(q.blending,q.blendEquation,q.blendSrc,q.blendDst,q.blendEquationAlpha,q.blendSrcAlpha,q.blendDstAlpha,q.blendColor,q.blendAlpha,q.premultipliedAlpha),f.setFunc(q.depthFunc),f.setTest(q.depthTest),f.setMask(q.depthWrite),c.setMask(q.colorWrite);const Pe=q.stencilWrite;h.setTest(Pe),Pe&&(h.setMask(q.stencilWriteMask),h.setFunc(q.stencilFunc,q.stencilRef,q.stencilFuncMask),h.setOp(q.stencilFail,q.stencilZFail,q.stencilZPass)),vn(q.polygonOffset,q.polygonOffsetFactor,q.polygonOffsetUnits),q.alphaToCoverage===!0?Se(r.SAMPLE_ALPHA_TO_COVERAGE):Re(r.SAMPLE_ALPHA_TO_COVERAGE)}function pt(q){W!==q&&(q?r.frontFace(r.CW):r.frontFace(r.CCW),W=q)}function vt(q){q!==I1?(Se(r.CULL_FACE),q!==J&&(q===Yx?r.cullFace(r.BACK):q===H1?r.cullFace(r.FRONT):r.cullFace(r.FRONT_AND_BACK))):Re(r.CULL_FACE),J=q}function Gt(q){q!==re&&(V&&r.lineWidth(q),re=q)}function vn(q,Oe,be){q?(Se(r.POLYGON_OFFSET_FILL),(k!==Oe||K!==be)&&(k=Oe,K=be,f.getReversed()&&(Oe=-Oe),r.polygonOffset(Oe,be))):Re(r.POLYGON_OFFSET_FILL)}function Xt(q){q?Se(r.SCISSOR_TEST):Re(r.SCISSOR_TEST)}function fn(q){q===void 0&&(q=r.TEXTURE0+B-1),fe!==q&&(r.activeTexture(q),fe=q)}function j(q,Oe,be){be===void 0&&(fe===null?be=r.TEXTURE0+B-1:be=fe);let Pe=D[be];Pe===void 0&&(Pe={type:void 0,texture:void 0},D[be]=Pe),(Pe.type!==q||Pe.texture!==Oe)&&(fe!==be&&(r.activeTexture(be),fe=be),r.bindTexture(q,Oe||ue[q]),Pe.type=q,Pe.texture=Oe)}function Ft(){const q=D[fe];q!==void 0&&q.type!==void 0&&(r.bindTexture(q.type,null),q.type=void 0,q.texture=void 0)}function Ut(){try{r.compressedTexImage2D(...arguments)}catch(q){Zt("WebGLState:",q)}}function P(){try{r.compressedTexImage3D(...arguments)}catch(q){Zt("WebGLState:",q)}}function M(){try{r.texSubImage2D(...arguments)}catch(q){Zt("WebGLState:",q)}}function Z(){try{r.texSubImage3D(...arguments)}catch(q){Zt("WebGLState:",q)}}function ce(){try{r.compressedTexSubImage2D(...arguments)}catch(q){Zt("WebGLState:",q)}}function xe(){try{r.compressedTexSubImage3D(...arguments)}catch(q){Zt("WebGLState:",q)}}function ne(){try{r.texStorage2D(...arguments)}catch(q){Zt("WebGLState:",q)}}function Ae(){try{r.texStorage3D(...arguments)}catch(q){Zt("WebGLState:",q)}}function pe(){try{r.texImage2D(...arguments)}catch(q){Zt("WebGLState:",q)}}function ye(){try{r.texImage3D(...arguments)}catch(q){Zt("WebGLState:",q)}}function Ne(q){return v[q]!==void 0?v[q]:r.getParameter(q)}function Ze(q,Oe){v[q]!==Oe&&(r.pixelStorei(q,Oe),v[q]=Oe)}function He(q){De.equals(q)===!1&&(r.scissor(q.x,q.y,q.z,q.w),De.copy(q))}function Fe(q){ze.equals(q)===!1&&(r.viewport(q.x,q.y,q.z,q.w),ze.copy(q))}function rt(q,Oe){let be=p.get(Oe);be===void 0&&(be=new WeakMap,p.set(Oe,be));let Pe=be.get(q);Pe===void 0&&(Pe=r.getUniformBlockIndex(Oe,q.name),be.set(q,Pe))}function lt(q,Oe){const Pe=p.get(Oe).get(q);m.get(Oe)!==Pe&&(r.uniformBlockBinding(Oe,Pe,q.__bindingPointIndex),m.set(Oe,Pe))}function dt(){r.disable(r.BLEND),r.disable(r.CULL_FACE),r.disable(r.DEPTH_TEST),r.disable(r.POLYGON_OFFSET_FILL),r.disable(r.SCISSOR_TEST),r.disable(r.STENCIL_TEST),r.disable(r.SAMPLE_ALPHA_TO_COVERAGE),r.blendEquation(r.FUNC_ADD),r.blendFunc(r.ONE,r.ZERO),r.blendFuncSeparate(r.ONE,r.ZERO,r.ONE,r.ZERO),r.blendColor(0,0,0,0),r.colorMask(!0,!0,!0,!0),r.clearColor(0,0,0,0),r.depthMask(!0),r.depthFunc(r.LESS),f.setReversed(!1),r.clearDepth(1),r.stencilMask(4294967295),r.stencilFunc(r.ALWAYS,0,4294967295),r.stencilOp(r.KEEP,r.KEEP,r.KEEP),r.clearStencil(0),r.cullFace(r.BACK),r.frontFace(r.CCW),r.polygonOffset(0,0),r.activeTexture(r.TEXTURE0),r.bindFramebuffer(r.FRAMEBUFFER,null),r.bindFramebuffer(r.DRAW_FRAMEBUFFER,null),r.bindFramebuffer(r.READ_FRAMEBUFFER,null),r.useProgram(null),r.lineWidth(1),r.scissor(0,0,r.canvas.width,r.canvas.height),r.viewport(0,0,r.canvas.width,r.canvas.height),r.pixelStorei(r.PACK_ALIGNMENT,4),r.pixelStorei(r.UNPACK_ALIGNMENT,4),r.pixelStorei(r.UNPACK_FLIP_Y_WEBGL,!1),r.pixelStorei(r.UNPACK_PREMULTIPLY_ALPHA_WEBGL,!1),r.pixelStorei(r.UNPACK_COLORSPACE_CONVERSION_WEBGL,r.BROWSER_DEFAULT_WEBGL),r.pixelStorei(r.PACK_ROW_LENGTH,0),r.pixelStorei(r.PACK_SKIP_PIXELS,0),r.pixelStorei(r.PACK_SKIP_ROWS,0),r.pixelStorei(r.UNPACK_ROW_LENGTH,0),r.pixelStorei(r.UNPACK_IMAGE_HEIGHT,0),r.pixelStorei(r.UNPACK_SKIP_PIXELS,0),r.pixelStorei(r.UNPACK_SKIP_ROWS,0),r.pixelStorei(r.UNPACK_SKIP_IMAGES,0),g={},v={},fe=null,D={},x={},_=new WeakMap,E=[],R=null,b=!1,S=null,F=null,G=null,w=null,N=null,L=null,z=null,T=new wt(0,0,0),O=0,I=!1,W=null,J=null,re=null,k=null,K=null,De.set(0,0,r.canvas.width,r.canvas.height),ze.set(0,0,r.canvas.width,r.canvas.height),c.reset(),f.reset(),h.reset()}return{buffers:{color:c,depth:f,stencil:h},enable:Se,disable:Re,bindFramebuffer:at,drawBuffers:Ge,useProgram:mt,setBlending:xt,setMaterial:bt,setFlipSided:pt,setCullFace:vt,setLineWidth:Gt,setPolygonOffset:vn,setScissorTest:Xt,activeTexture:fn,bindTexture:j,unbindTexture:Ft,compressedTexImage2D:Ut,compressedTexImage3D:P,texImage2D:pe,texImage3D:ye,pixelStorei:Ze,getParameter:Ne,updateUBOMapping:rt,uniformBlockBinding:lt,texStorage2D:ne,texStorage3D:Ae,texSubImage2D:M,texSubImage3D:Z,compressedTexSubImage2D:ce,compressedTexSubImage3D:xe,scissor:He,viewport:Fe,reset:dt}}function mw(r,e,i,s,l,c,f){const h=e.has("WEBGL_multisampled_render_to_texture")?e.get("WEBGL_multisampled_render_to_texture"):null,m=typeof navigator>"u"?!1:/OculusBrowser/g.test(navigator.userAgent),p=new Kt,g=new WeakMap,v=new Set;let x;const _=new WeakMap;let E=!1;try{E=typeof OffscreenCanvas<"u"&&new OffscreenCanvas(1,1).getContext("2d")!==null}catch{}function R(P,M){return E?new OffscreenCanvas(P,M):Zl("canvas")}function b(P,M,Z){let ce=1;const xe=Ut(P);if((xe.width>Z||xe.height>Z)&&(ce=Z/Math.max(xe.width,xe.height)),ce<1)if(typeof HTMLImageElement<"u"&&P instanceof HTMLImageElement||typeof HTMLCanvasElement<"u"&&P instanceof HTMLCanvasElement||typeof ImageBitmap<"u"&&P instanceof ImageBitmap||typeof VideoFrame<"u"&&P instanceof VideoFrame){const ne=Math.floor(ce*xe.width),Ae=Math.floor(ce*xe.height);x===void 0&&(x=R(ne,Ae));const pe=M?R(ne,Ae):x;return pe.width=ne,pe.height=Ae,pe.getContext("2d").drawImage(P,0,0,ne,Ae),ht("WebGLRenderer: Texture has been resized from ("+xe.width+"x"+xe.height+") to ("+ne+"x"+Ae+")."),pe}else return"data"in P&&ht("WebGLRenderer: Image in DataTexture is too big ("+xe.width+"x"+xe.height+")."),P;return P}function S(P){return P.generateMipmaps}function F(P){r.generateMipmap(P)}function G(P){return P.isWebGLCubeRenderTarget?r.TEXTURE_CUBE_MAP:P.isWebGL3DRenderTarget?r.TEXTURE_3D:P.isWebGLArrayRenderTarget||P.isCompressedArrayTexture?r.TEXTURE_2D_ARRAY:r.TEXTURE_2D}function w(P,M,Z,ce,xe,ne=!1){if(P!==null){if(r[P]!==void 0)return r[P];ht("WebGLRenderer: Attempt to use non-existing WebGL internal format '"+P+"'")}let Ae;ce&&(Ae=e.get("EXT_texture_norm16"),Ae||ht("WebGLRenderer: Unable to use normalized textures without EXT_texture_norm16 extension"));let pe=M;if(M===r.RED&&(Z===r.FLOAT&&(pe=r.R32F),Z===r.HALF_FLOAT&&(pe=r.R16F),Z===r.UNSIGNED_BYTE&&(pe=r.R8),Z===r.UNSIGNED_SHORT&&Ae&&(pe=Ae.R16_EXT),Z===r.SHORT&&Ae&&(pe=Ae.R16_SNORM_EXT)),M===r.RED_INTEGER&&(Z===r.UNSIGNED_BYTE&&(pe=r.R8UI),Z===r.UNSIGNED_SHORT&&(pe=r.R16UI),Z===r.UNSIGNED_INT&&(pe=r.R32UI),Z===r.BYTE&&(pe=r.R8I),Z===r.SHORT&&(pe=r.R16I),Z===r.INT&&(pe=r.R32I)),M===r.RG&&(Z===r.FLOAT&&(pe=r.RG32F),Z===r.HALF_FLOAT&&(pe=r.RG16F),Z===r.UNSIGNED_BYTE&&(pe=r.RG8),Z===r.UNSIGNED_SHORT&&Ae&&(pe=Ae.RG16_EXT),Z===r.SHORT&&Ae&&(pe=Ae.RG16_SNORM_EXT)),M===r.RG_INTEGER&&(Z===r.UNSIGNED_BYTE&&(pe=r.RG8UI),Z===r.UNSIGNED_SHORT&&(pe=r.RG16UI),Z===r.UNSIGNED_INT&&(pe=r.RG32UI),Z===r.BYTE&&(pe=r.RG8I),Z===r.SHORT&&(pe=r.RG16I),Z===r.INT&&(pe=r.RG32I)),M===r.RGB_INTEGER&&(Z===r.UNSIGNED_BYTE&&(pe=r.RGB8UI),Z===r.UNSIGNED_SHORT&&(pe=r.RGB16UI),Z===r.UNSIGNED_INT&&(pe=r.RGB32UI),Z===r.BYTE&&(pe=r.RGB8I),Z===r.SHORT&&(pe=r.RGB16I),Z===r.INT&&(pe=r.RGB32I)),M===r.RGBA_INTEGER&&(Z===r.UNSIGNED_BYTE&&(pe=r.RGBA8UI),Z===r.UNSIGNED_SHORT&&(pe=r.RGBA16UI),Z===r.UNSIGNED_INT&&(pe=r.RGBA32UI),Z===r.BYTE&&(pe=r.RGBA8I),Z===r.SHORT&&(pe=r.RGBA16I),Z===r.INT&&(pe=r.RGBA32I)),M===r.RGB&&(Z===r.UNSIGNED_SHORT&&Ae&&(pe=Ae.RGB16_EXT),Z===r.SHORT&&Ae&&(pe=Ae.RGB16_SNORM_EXT),Z===r.UNSIGNED_INT_5_9_9_9_REV&&(pe=r.RGB9_E5),Z===r.UNSIGNED_INT_10F_11F_11F_REV&&(pe=r.R11F_G11F_B10F)),M===r.RGBA){const ye=ne?Xu:kt.getTransfer(xe);Z===r.FLOAT&&(pe=r.RGBA32F),Z===r.HALF_FLOAT&&(pe=r.RGBA16F),Z===r.UNSIGNED_BYTE&&(pe=ye===cn?r.SRGB8_ALPHA8:r.RGBA8),Z===r.UNSIGNED_SHORT&&Ae&&(pe=Ae.RGBA16_EXT),Z===r.SHORT&&Ae&&(pe=Ae.RGBA16_SNORM_EXT),Z===r.UNSIGNED_SHORT_4_4_4_4&&(pe=r.RGBA4),Z===r.UNSIGNED_SHORT_5_5_5_1&&(pe=r.RGB5_A1)}return(pe===r.R16F||pe===r.R32F||pe===r.RG16F||pe===r.RG32F||pe===r.RGBA16F||pe===r.RGBA32F)&&e.get("EXT_color_buffer_float"),pe}function N(P,M){let Z;return P?M===null||M===Xa||M===jl?Z=r.DEPTH24_STENCIL8:M===Ga?Z=r.DEPTH32F_STENCIL8:M===Yl&&(Z=r.DEPTH24_STENCIL8,ht("DepthTexture: 16 bit depth attachment is not supported with stencil. Using 24-bit attachment.")):M===null||M===Xa||M===jl?Z=r.DEPTH_COMPONENT24:M===Ga?Z=r.DEPTH_COMPONENT32F:M===Yl&&(Z=r.DEPTH_COMPONENT16),Z}function L(P,M){return S(P)===!0||P.isFramebufferTexture&&P.minFilter!==li&&P.minFilter!==mi?Math.log2(Math.max(M.width,M.height))+1:P.mipmaps!==void 0&&P.mipmaps.length>0?P.mipmaps.length:P.isCompressedTexture&&Array.isArray(P.image)?M.mipmaps.length:1}function z(P){const M=P.target;M.removeEventListener("dispose",z),O(M),M.isVideoTexture&&g.delete(M),M.isHTMLTexture&&v.delete(M)}function T(P){const M=P.target;M.removeEventListener("dispose",T),W(M)}function O(P){const M=s.get(P);if(M.__webglInit===void 0)return;const Z=P.source,ce=_.get(Z);if(ce){const xe=ce[M.__cacheKey];xe.usedTimes--,xe.usedTimes===0&&I(P),Object.keys(ce).length===0&&_.delete(Z)}s.remove(P)}function I(P){const M=s.get(P);r.deleteTexture(M.__webglTexture);const Z=P.source,ce=_.get(Z);delete ce[M.__cacheKey],f.memory.textures--}function W(P){const M=s.get(P);if(P.depthTexture&&(P.depthTexture.dispose(),s.remove(P.depthTexture)),P.isWebGLCubeRenderTarget)for(let ce=0;ce<6;ce++){if(Array.isArray(M.__webglFramebuffer[ce]))for(let xe=0;xe<M.__webglFramebuffer[ce].length;xe++)r.deleteFramebuffer(M.__webglFramebuffer[ce][xe]);else r.deleteFramebuffer(M.__webglFramebuffer[ce]);M.__webglDepthbuffer&&r.deleteRenderbuffer(M.__webglDepthbuffer[ce])}else{if(Array.isArray(M.__webglFramebuffer))for(let ce=0;ce<M.__webglFramebuffer.length;ce++)r.deleteFramebuffer(M.__webglFramebuffer[ce]);else r.deleteFramebuffer(M.__webglFramebuffer);if(M.__webglDepthbuffer&&r.deleteRenderbuffer(M.__webglDepthbuffer),M.__webglMultisampledFramebuffer&&r.deleteFramebuffer(M.__webglMultisampledFramebuffer),M.__webglColorRenderbuffer)for(let ce=0;ce<M.__webglColorRenderbuffer.length;ce++)M.__webglColorRenderbuffer[ce]&&r.deleteRenderbuffer(M.__webglColorRenderbuffer[ce]);M.__webglDepthRenderbuffer&&r.deleteRenderbuffer(M.__webglDepthRenderbuffer)}const Z=P.textures;for(let ce=0,xe=Z.length;ce<xe;ce++){const ne=s.get(Z[ce]);ne.__webglTexture&&(r.deleteTexture(ne.__webglTexture),f.memory.textures--),s.remove(Z[ce])}s.remove(P)}let J=0;function re(){J=0}function k(){return J}function K(P){J=P}function B(){const P=J;return P>=l.maxTextures&&ht("WebGLTextures: Trying to use "+(P+1)+" texture units while this GPU supports only "+l.maxTextures),J+=1,P}function V(P){const M=[];return M.push(P.wrapS),M.push(P.wrapT),M.push(P.wrapR||0),M.push(P.magFilter),M.push(P.minFilter),M.push(P.anisotropy),M.push(P.internalFormat),M.push(P.format),M.push(P.type),M.push(P.generateMipmaps),M.push(P.premultiplyAlpha),M.push(P.flipY),M.push(P.unpackAlignment),M.push(P.colorSpace),M.join()}function ee(P,M){const Z=s.get(P);if(P.isVideoTexture&&j(P),P.isRenderTargetTexture===!1&&P.isExternalTexture!==!0&&P.version>0&&Z.__version!==P.version){const ce=P.image;if(ce===null)ht("WebGLRenderer: Texture marked for update but no image data found.");else if(ce.complete===!1)ht("WebGLRenderer: Texture marked for update but image is incomplete");else{Re(Z,P,M);return}}else P.isExternalTexture&&(Z.__webglTexture=P.sourceTexture?P.sourceTexture:null);i.bindTexture(r.TEXTURE_2D,Z.__webglTexture,r.TEXTURE0+M)}function oe(P,M){const Z=s.get(P);if(P.isRenderTargetTexture===!1&&P.version>0&&Z.__version!==P.version){Re(Z,P,M);return}else P.isExternalTexture&&(Z.__webglTexture=P.sourceTexture?P.sourceTexture:null);i.bindTexture(r.TEXTURE_2D_ARRAY,Z.__webglTexture,r.TEXTURE0+M)}function fe(P,M){const Z=s.get(P);if(P.isRenderTargetTexture===!1&&P.version>0&&Z.__version!==P.version){Re(Z,P,M);return}i.bindTexture(r.TEXTURE_3D,Z.__webglTexture,r.TEXTURE0+M)}function D(P,M){const Z=s.get(P);if(P.isCubeDepthTexture!==!0&&P.version>0&&Z.__version!==P.version){at(Z,P,M);return}i.bindTexture(r.TEXTURE_CUBE_MAP,Z.__webglTexture,r.TEXTURE0+M)}const se={[Qh]:r.REPEAT,[_r]:r.CLAMP_TO_EDGE,[Jh]:r.MIRRORED_REPEAT},_e={[li]:r.NEAREST,[lb]:r.NEAREST_MIPMAP_NEAREST,[au]:r.NEAREST_MIPMAP_LINEAR,[mi]:r.LINEAR,[oh]:r.LINEAR_MIPMAP_NEAREST,[Rs]:r.LINEAR_MIPMAP_LINEAR},De={[db]:r.NEVER,[xb]:r.ALWAYS,[hb]:r.LESS,[Xp]:r.LEQUAL,[pb]:r.EQUAL,[Wp]:r.GEQUAL,[mb]:r.GREATER,[gb]:r.NOTEQUAL};function ze(P,M){if(M.type===Ga&&e.has("OES_texture_float_linear")===!1&&(M.magFilter===mi||M.magFilter===oh||M.magFilter===au||M.magFilter===Rs||M.minFilter===mi||M.minFilter===oh||M.minFilter===au||M.minFilter===Rs)&&ht("WebGLRenderer: Unable to use linear filtering with floating point textures. OES_texture_float_linear not supported on this device."),r.texParameteri(P,r.TEXTURE_WRAP_S,se[M.wrapS]),r.texParameteri(P,r.TEXTURE_WRAP_T,se[M.wrapT]),(P===r.TEXTURE_3D||P===r.TEXTURE_2D_ARRAY)&&r.texParameteri(P,r.TEXTURE_WRAP_R,se[M.wrapR]),r.texParameteri(P,r.TEXTURE_MAG_FILTER,_e[M.magFilter]),r.texParameteri(P,r.TEXTURE_MIN_FILTER,_e[M.minFilter]),M.compareFunction&&(r.texParameteri(P,r.TEXTURE_COMPARE_MODE,r.COMPARE_REF_TO_TEXTURE),r.texParameteri(P,r.TEXTURE_COMPARE_FUNC,De[M.compareFunction])),e.has("EXT_texture_filter_anisotropic")===!0){if(M.magFilter===li||M.minFilter!==au&&M.minFilter!==Rs||M.type===Ga&&e.has("OES_texture_float_linear")===!1)return;if(M.anisotropy>1||s.get(M).__currentAnisotropy){const Z=e.get("EXT_texture_filter_anisotropic");r.texParameterf(P,Z.TEXTURE_MAX_ANISOTROPY_EXT,Math.min(M.anisotropy,l.getMaxAnisotropy())),s.get(M).__currentAnisotropy=M.anisotropy}}}function Xe(P,M){let Z=!1;P.__webglInit===void 0&&(P.__webglInit=!0,M.addEventListener("dispose",z));const ce=M.source;let xe=_.get(ce);xe===void 0&&(xe={},_.set(ce,xe));const ne=V(M);if(ne!==P.__cacheKey){xe[ne]===void 0&&(xe[ne]={texture:r.createTexture(),usedTimes:0},f.memory.textures++,Z=!0),xe[ne].usedTimes++;const Ae=xe[P.__cacheKey];Ae!==void 0&&(xe[P.__cacheKey].usedTimes--,Ae.usedTimes===0&&I(M)),P.__cacheKey=ne,P.__webglTexture=xe[ne].texture}return Z}function ue(P,M,Z){return Math.floor(Math.floor(P/Z)/M)}function Se(P,M,Z,ce){const ne=P.updateRanges;if(ne.length===0)i.texSubImage2D(r.TEXTURE_2D,0,0,0,M.width,M.height,Z,ce,M.data);else{ne.sort((Ze,He)=>Ze.start-He.start);let Ae=0;for(let Ze=1;Ze<ne.length;Ze++){const He=ne[Ae],Fe=ne[Ze],rt=He.start+He.count,lt=ue(Fe.start,M.width,4),dt=ue(He.start,M.width,4);Fe.start<=rt+1&&lt===dt&&ue(Fe.start+Fe.count-1,M.width,4)===lt?He.count=Math.max(He.count,Fe.start+Fe.count-He.start):(++Ae,ne[Ae]=Fe)}ne.length=Ae+1;const pe=i.getParameter(r.UNPACK_ROW_LENGTH),ye=i.getParameter(r.UNPACK_SKIP_PIXELS),Ne=i.getParameter(r.UNPACK_SKIP_ROWS);i.pixelStorei(r.UNPACK_ROW_LENGTH,M.width);for(let Ze=0,He=ne.length;Ze<He;Ze++){const Fe=ne[Ze],rt=Math.floor(Fe.start/4),lt=Math.ceil(Fe.count/4),dt=rt%M.width,q=Math.floor(rt/M.width),Oe=lt,be=1;i.pixelStorei(r.UNPACK_SKIP_PIXELS,dt),i.pixelStorei(r.UNPACK_SKIP_ROWS,q),i.texSubImage2D(r.TEXTURE_2D,0,dt,q,Oe,be,Z,ce,M.data)}P.clearUpdateRanges(),i.pixelStorei(r.UNPACK_ROW_LENGTH,pe),i.pixelStorei(r.UNPACK_SKIP_PIXELS,ye),i.pixelStorei(r.UNPACK_SKIP_ROWS,Ne)}}function Re(P,M,Z){let ce=r.TEXTURE_2D;(M.isDataArrayTexture||M.isCompressedArrayTexture)&&(ce=r.TEXTURE_2D_ARRAY),M.isData3DTexture&&(ce=r.TEXTURE_3D);const xe=Xe(P,M),ne=M.source;i.bindTexture(ce,P.__webglTexture,r.TEXTURE0+Z);const Ae=s.get(ne);if(ne.version!==Ae.__version||xe===!0){if(i.activeTexture(r.TEXTURE0+Z),(typeof ImageBitmap<"u"&&M.image instanceof ImageBitmap)===!1){const be=kt.getPrimaries(kt.workingColorSpace),Pe=M.colorSpace===ns?null:kt.getPrimaries(M.colorSpace),Ve=M.colorSpace===ns||be===Pe?r.NONE:r.BROWSER_DEFAULT_WEBGL;i.pixelStorei(r.UNPACK_FLIP_Y_WEBGL,M.flipY),i.pixelStorei(r.UNPACK_PREMULTIPLY_ALPHA_WEBGL,M.premultiplyAlpha),i.pixelStorei(r.UNPACK_COLORSPACE_CONVERSION_WEBGL,Ve)}i.pixelStorei(r.UNPACK_ALIGNMENT,M.unpackAlignment);let ye=b(M.image,!1,l.maxTextureSize);ye=Ft(M,ye);const Ne=c.convert(M.format,M.colorSpace),Ze=c.convert(M.type);let He=w(M.internalFormat,Ne,Ze,M.normalized,M.colorSpace,M.isVideoTexture);ze(ce,M);let Fe;const rt=M.mipmaps,lt=M.isVideoTexture!==!0,dt=Ae.__version===void 0||xe===!0,q=ne.dataReady,Oe=L(M,ye);if(M.isDepthTexture)He=N(M.format===Us,M.type),dt&&(lt?i.texStorage2D(r.TEXTURE_2D,1,He,ye.width,ye.height):i.texImage2D(r.TEXTURE_2D,0,He,ye.width,ye.height,0,Ne,Ze,null));else if(M.isDataTexture)if(rt.length>0){lt&&dt&&i.texStorage2D(r.TEXTURE_2D,Oe,He,rt[0].width,rt[0].height);for(let be=0,Pe=rt.length;be<Pe;be++)Fe=rt[be],lt?q&&i.texSubImage2D(r.TEXTURE_2D,be,0,0,Fe.width,Fe.height,Ne,Ze,Fe.data):i.texImage2D(r.TEXTURE_2D,be,He,Fe.width,Fe.height,0,Ne,Ze,Fe.data);M.generateMipmaps=!1}else lt?(dt&&i.texStorage2D(r.TEXTURE_2D,Oe,He,ye.width,ye.height),q&&Se(M,ye,Ne,Ze)):i.texImage2D(r.TEXTURE_2D,0,He,ye.width,ye.height,0,Ne,Ze,ye.data);else if(M.isCompressedTexture)if(M.isCompressedArrayTexture){lt&&dt&&i.texStorage3D(r.TEXTURE_2D_ARRAY,Oe,He,rt[0].width,rt[0].height,ye.depth);for(let be=0,Pe=rt.length;be<Pe;be++)if(Fe=rt[be],M.format!==Ta)if(Ne!==null)if(lt){if(q)if(M.layerUpdates.size>0){const Ve=Uv(Fe.width,Fe.height,M.format,M.type);for(const we of M.layerUpdates){const et=Fe.data.subarray(we*Ve/Fe.data.BYTES_PER_ELEMENT,(we+1)*Ve/Fe.data.BYTES_PER_ELEMENT);i.compressedTexSubImage3D(r.TEXTURE_2D_ARRAY,be,0,0,we,Fe.width,Fe.height,1,Ne,et)}}else i.compressedTexSubImage3D(r.TEXTURE_2D_ARRAY,be,0,0,0,Fe.width,Fe.height,ye.depth,Ne,Fe.data)}else i.compressedTexImage3D(r.TEXTURE_2D_ARRAY,be,He,Fe.width,Fe.height,ye.depth,0,Fe.data,0,0);else ht("WebGLRenderer: Attempt to load unsupported compressed texture format in .uploadTexture()");else lt?q&&i.texSubImage3D(r.TEXTURE_2D_ARRAY,be,0,0,0,Fe.width,Fe.height,ye.depth,Ne,Ze,Fe.data):i.texImage3D(r.TEXTURE_2D_ARRAY,be,He,Fe.width,Fe.height,ye.depth,0,Ne,Ze,Fe.data);M.layerUpdates.size>0&&M.clearLayerUpdates()}else{lt&&dt&&i.texStorage2D(r.TEXTURE_2D,Oe,He,rt[0].width,rt[0].height);for(let be=0,Pe=rt.length;be<Pe;be++)Fe=rt[be],M.format!==Ta?Ne!==null?lt?q&&i.compressedTexSubImage2D(r.TEXTURE_2D,be,0,0,Fe.width,Fe.height,Ne,Fe.data):i.compressedTexImage2D(r.TEXTURE_2D,be,He,Fe.width,Fe.height,0,Fe.data):ht("WebGLRenderer: Attempt to load unsupported compressed texture format in .uploadTexture()"):lt?q&&i.texSubImage2D(r.TEXTURE_2D,be,0,0,Fe.width,Fe.height,Ne,Ze,Fe.data):i.texImage2D(r.TEXTURE_2D,be,He,Fe.width,Fe.height,0,Ne,Ze,Fe.data)}else if(M.isDataArrayTexture)if(lt){if(dt&&i.texStorage3D(r.TEXTURE_2D_ARRAY,Oe,He,ye.width,ye.height,ye.depth),q)if(M.layerUpdates.size>0){const be=Uv(ye.width,ye.height,M.format,M.type);for(const Pe of M.layerUpdates){const Ve=ye.data.subarray(Pe*be/ye.data.BYTES_PER_ELEMENT,(Pe+1)*be/ye.data.BYTES_PER_ELEMENT);i.texSubImage3D(r.TEXTURE_2D_ARRAY,0,0,0,Pe,ye.width,ye.height,1,Ne,Ze,Ve)}M.clearLayerUpdates()}else i.texSubImage3D(r.TEXTURE_2D_ARRAY,0,0,0,0,ye.width,ye.height,ye.depth,Ne,Ze,ye.data)}else i.texImage3D(r.TEXTURE_2D_ARRAY,0,He,ye.width,ye.height,ye.depth,0,Ne,Ze,ye.data);else if(M.isData3DTexture)lt?(dt&&i.texStorage3D(r.TEXTURE_3D,Oe,He,ye.width,ye.height,ye.depth),q&&i.texSubImage3D(r.TEXTURE_3D,0,0,0,0,ye.width,ye.height,ye.depth,Ne,Ze,ye.data)):i.texImage3D(r.TEXTURE_3D,0,He,ye.width,ye.height,ye.depth,0,Ne,Ze,ye.data);else if(M.isFramebufferTexture){if(dt)if(lt)i.texStorage2D(r.TEXTURE_2D,Oe,He,ye.width,ye.height);else{let be=ye.width,Pe=ye.height;for(let Ve=0;Ve<Oe;Ve++)i.texImage2D(r.TEXTURE_2D,Ve,He,be,Pe,0,Ne,Ze,null),be>>=1,Pe>>=1}}else if(M.isHTMLTexture){if("texElementImage2D"in r){const be=r.canvas;if(be.hasAttribute("layoutsubtree")||be.setAttribute("layoutsubtree","true"),ye.parentNode!==be){be.appendChild(ye),v.add(M),be.onpaint=Pe=>{const Ve=Pe.changedElements;for(const we of v)Ve.includes(we.image)&&(we.needsUpdate=!0)},be.requestPaint();return}if(r.texElementImage2D.length===3)r.texElementImage2D(r.TEXTURE_2D,r.RGBA8,ye);else{const Ve=r.RGBA,we=r.RGBA,et=r.UNSIGNED_BYTE;r.texElementImage2D(r.TEXTURE_2D,0,Ve,we,et,ye)}r.texParameteri(r.TEXTURE_2D,r.TEXTURE_MIN_FILTER,r.LINEAR),r.texParameteri(r.TEXTURE_2D,r.TEXTURE_WRAP_S,r.CLAMP_TO_EDGE),r.texParameteri(r.TEXTURE_2D,r.TEXTURE_WRAP_T,r.CLAMP_TO_EDGE)}}else if(rt.length>0){if(lt&&dt){const be=Ut(rt[0]);i.texStorage2D(r.TEXTURE_2D,Oe,He,be.width,be.height)}for(let be=0,Pe=rt.length;be<Pe;be++)Fe=rt[be],lt?q&&i.texSubImage2D(r.TEXTURE_2D,be,0,0,Ne,Ze,Fe):i.texImage2D(r.TEXTURE_2D,be,He,Ne,Ze,Fe);M.generateMipmaps=!1}else if(lt){if(dt){const be=Ut(ye);i.texStorage2D(r.TEXTURE_2D,Oe,He,be.width,be.height)}q&&i.texSubImage2D(r.TEXTURE_2D,0,0,0,Ne,Ze,ye)}else i.texImage2D(r.TEXTURE_2D,0,He,Ne,Ze,ye);S(M)&&F(ce),Ae.__version=ne.version,M.onUpdate&&M.onUpdate(M)}P.__version=M.version}function at(P,M,Z){if(M.image.length!==6)return;const ce=Xe(P,M),xe=M.source;i.bindTexture(r.TEXTURE_CUBE_MAP,P.__webglTexture,r.TEXTURE0+Z);const ne=s.get(xe);if(xe.version!==ne.__version||ce===!0){i.activeTexture(r.TEXTURE0+Z);const Ae=kt.getPrimaries(kt.workingColorSpace),pe=M.colorSpace===ns?null:kt.getPrimaries(M.colorSpace),ye=M.colorSpace===ns||Ae===pe?r.NONE:r.BROWSER_DEFAULT_WEBGL;i.pixelStorei(r.UNPACK_FLIP_Y_WEBGL,M.flipY),i.pixelStorei(r.UNPACK_PREMULTIPLY_ALPHA_WEBGL,M.premultiplyAlpha),i.pixelStorei(r.UNPACK_ALIGNMENT,M.unpackAlignment),i.pixelStorei(r.UNPACK_COLORSPACE_CONVERSION_WEBGL,ye);const Ne=M.isCompressedTexture||M.image[0].isCompressedTexture,Ze=M.image[0]&&M.image[0].isDataTexture,He=[];for(let we=0;we<6;we++)!Ne&&!Ze?He[we]=b(M.image[we],!0,l.maxCubemapSize):He[we]=Ze?M.image[we].image:M.image[we],He[we]=Ft(M,He[we]);const Fe=He[0],rt=c.convert(M.format,M.colorSpace),lt=c.convert(M.type),dt=w(M.internalFormat,rt,lt,M.normalized,M.colorSpace),q=M.isVideoTexture!==!0,Oe=ne.__version===void 0||ce===!0,be=xe.dataReady;let Pe=L(M,Fe);ze(r.TEXTURE_CUBE_MAP,M);let Ve;if(Ne){q&&Oe&&i.texStorage2D(r.TEXTURE_CUBE_MAP,Pe,dt,Fe.width,Fe.height);for(let we=0;we<6;we++){Ve=He[we].mipmaps;for(let et=0;et<Ve.length;et++){const Je=Ve[et];M.format!==Ta?rt!==null?q?be&&i.compressedTexSubImage2D(r.TEXTURE_CUBE_MAP_POSITIVE_X+we,et,0,0,Je.width,Je.height,rt,Je.data):i.compressedTexImage2D(r.TEXTURE_CUBE_MAP_POSITIVE_X+we,et,dt,Je.width,Je.height,0,Je.data):ht("WebGLRenderer: Attempt to load unsupported compressed texture format in .setTextureCube()"):q?be&&i.texSubImage2D(r.TEXTURE_CUBE_MAP_POSITIVE_X+we,et,0,0,Je.width,Je.height,rt,lt,Je.data):i.texImage2D(r.TEXTURE_CUBE_MAP_POSITIVE_X+we,et,dt,Je.width,Je.height,0,rt,lt,Je.data)}}}else{if(Ve=M.mipmaps,q&&Oe){Ve.length>0&&Pe++;const we=Ut(He[0]);i.texStorage2D(r.TEXTURE_CUBE_MAP,Pe,dt,we.width,we.height)}for(let we=0;we<6;we++)if(Ze){q?be&&i.texSubImage2D(r.TEXTURE_CUBE_MAP_POSITIVE_X+we,0,0,0,He[we].width,He[we].height,rt,lt,He[we].data):i.texImage2D(r.TEXTURE_CUBE_MAP_POSITIVE_X+we,0,dt,He[we].width,He[we].height,0,rt,lt,He[we].data);for(let et=0;et<Ve.length;et++){const Qt=Ve[et].image[we].image;q?be&&i.texSubImage2D(r.TEXTURE_CUBE_MAP_POSITIVE_X+we,et+1,0,0,Qt.width,Qt.height,rt,lt,Qt.data):i.texImage2D(r.TEXTURE_CUBE_MAP_POSITIVE_X+we,et+1,dt,Qt.width,Qt.height,0,rt,lt,Qt.data)}}else{q?be&&i.texSubImage2D(r.TEXTURE_CUBE_MAP_POSITIVE_X+we,0,0,0,rt,lt,He[we]):i.texImage2D(r.TEXTURE_CUBE_MAP_POSITIVE_X+we,0,dt,rt,lt,He[we]);for(let et=0;et<Ve.length;et++){const Je=Ve[et];q?be&&i.texSubImage2D(r.TEXTURE_CUBE_MAP_POSITIVE_X+we,et+1,0,0,rt,lt,Je.image[we]):i.texImage2D(r.TEXTURE_CUBE_MAP_POSITIVE_X+we,et+1,dt,rt,lt,Je.image[we])}}}S(M)&&F(r.TEXTURE_CUBE_MAP),ne.__version=xe.version,M.onUpdate&&M.onUpdate(M)}P.__version=M.version}function Ge(P,M,Z,ce,xe,ne){const Ae=c.convert(Z.format,Z.colorSpace),pe=c.convert(Z.type),ye=w(Z.internalFormat,Ae,pe,Z.normalized,Z.colorSpace),Ne=s.get(M),Ze=s.get(Z);if(Ze.__renderTarget=M,!Ne.__hasExternalTextures){const He=Math.max(1,M.width>>ne),Fe=Math.max(1,M.height>>ne);xe===r.TEXTURE_3D||xe===r.TEXTURE_2D_ARRAY?i.texImage3D(xe,ne,ye,He,Fe,M.depth,0,Ae,pe,null):i.texImage2D(xe,ne,ye,He,Fe,0,Ae,pe,null)}i.bindFramebuffer(r.FRAMEBUFFER,P),fn(M)?h.framebufferTexture2DMultisampleEXT(r.FRAMEBUFFER,ce,xe,Ze.__webglTexture,0,Xt(M)):(xe===r.TEXTURE_2D||xe>=r.TEXTURE_CUBE_MAP_POSITIVE_X&&xe<=r.TEXTURE_CUBE_MAP_NEGATIVE_Z)&&r.framebufferTexture2D(r.FRAMEBUFFER,ce,xe,Ze.__webglTexture,ne),i.bindFramebuffer(r.FRAMEBUFFER,null)}function mt(P,M,Z){if(r.bindRenderbuffer(r.RENDERBUFFER,P),M.depthBuffer){const ce=M.depthTexture,xe=ce&&ce.isDepthTexture?ce.type:null,ne=N(M.stencilBuffer,xe),Ae=M.stencilBuffer?r.DEPTH_STENCIL_ATTACHMENT:r.DEPTH_ATTACHMENT;fn(M)?h.renderbufferStorageMultisampleEXT(r.RENDERBUFFER,Xt(M),ne,M.width,M.height):Z?r.renderbufferStorageMultisample(r.RENDERBUFFER,Xt(M),ne,M.width,M.height):r.renderbufferStorage(r.RENDERBUFFER,ne,M.width,M.height),r.framebufferRenderbuffer(r.FRAMEBUFFER,Ae,r.RENDERBUFFER,P)}else{const ce=M.textures;for(let xe=0;xe<ce.length;xe++){const ne=ce[xe],Ae=c.convert(ne.format,ne.colorSpace),pe=c.convert(ne.type),ye=w(ne.internalFormat,Ae,pe,ne.normalized,ne.colorSpace);fn(M)?h.renderbufferStorageMultisampleEXT(r.RENDERBUFFER,Xt(M),ye,M.width,M.height):Z?r.renderbufferStorageMultisample(r.RENDERBUFFER,Xt(M),ye,M.width,M.height):r.renderbufferStorage(r.RENDERBUFFER,ye,M.width,M.height)}}r.bindRenderbuffer(r.RENDERBUFFER,null)}function un(P,M,Z){const ce=M.isWebGLCubeRenderTarget===!0;if(i.bindFramebuffer(r.FRAMEBUFFER,P),!(M.depthTexture&&M.depthTexture.isDepthTexture))throw new Error("THREE.WebGLTextures: renderTarget.depthTexture must be an instance of THREE.DepthTexture.");const xe=s.get(M.depthTexture);if(xe.__renderTarget=M,(!xe.__webglTexture||M.depthTexture.image.width!==M.width||M.depthTexture.image.height!==M.height)&&(M.depthTexture.image.width=M.width,M.depthTexture.image.height=M.height,M.depthTexture.needsUpdate=!0),ce){if(xe.__webglInit===void 0&&(xe.__webglInit=!0,M.depthTexture.addEventListener("dispose",z)),xe.__webglTexture===void 0){xe.__webglTexture=r.createTexture(),i.bindTexture(r.TEXTURE_CUBE_MAP,xe.__webglTexture),ze(r.TEXTURE_CUBE_MAP,M.depthTexture);const Ne=c.convert(M.depthTexture.format),Ze=c.convert(M.depthTexture.type);let He;M.depthTexture.format===Mr?He=r.DEPTH_COMPONENT24:M.depthTexture.format===Us&&(He=r.DEPTH24_STENCIL8);for(let Fe=0;Fe<6;Fe++)r.texImage2D(r.TEXTURE_CUBE_MAP_POSITIVE_X+Fe,0,He,M.width,M.height,0,Ne,Ze,null)}}else ee(M.depthTexture,0);const ne=xe.__webglTexture,Ae=Xt(M),pe=ce?r.TEXTURE_CUBE_MAP_POSITIVE_X+Z:r.TEXTURE_2D,ye=M.depthTexture.format===Us?r.DEPTH_STENCIL_ATTACHMENT:r.DEPTH_ATTACHMENT;if(M.depthTexture.format===Mr)fn(M)?h.framebufferTexture2DMultisampleEXT(r.FRAMEBUFFER,ye,pe,ne,0,Ae):r.framebufferTexture2D(r.FRAMEBUFFER,ye,pe,ne,0);else if(M.depthTexture.format===Us)fn(M)?h.framebufferTexture2DMultisampleEXT(r.FRAMEBUFFER,ye,pe,ne,0,Ae):r.framebufferTexture2D(r.FRAMEBUFFER,ye,pe,ne,0);else throw new Error("THREE.WebGLTextures: Unknown depthTexture format.")}function ut(P){const M=s.get(P),Z=P.isWebGLCubeRenderTarget===!0;if(M.__boundDepthTexture!==P.depthTexture){const ce=P.depthTexture;if(M.__depthDisposeCallback&&M.__depthDisposeCallback(),ce){const xe=()=>{delete M.__boundDepthTexture,delete M.__depthDisposeCallback,ce.removeEventListener("dispose",xe)};ce.addEventListener("dispose",xe),M.__depthDisposeCallback=xe}M.__boundDepthTexture=ce}if(P.depthTexture&&!M.__autoAllocateDepthBuffer)if(Z)for(let ce=0;ce<6;ce++)un(M.__webglFramebuffer[ce],P,ce);else{const ce=P.texture.mipmaps;ce&&ce.length>0?un(M.__webglFramebuffer[0],P,0):un(M.__webglFramebuffer,P,0)}else if(Z){M.__webglDepthbuffer=[];for(let ce=0;ce<6;ce++)if(i.bindFramebuffer(r.FRAMEBUFFER,M.__webglFramebuffer[ce]),M.__webglDepthbuffer[ce]===void 0)M.__webglDepthbuffer[ce]=r.createRenderbuffer(),mt(M.__webglDepthbuffer[ce],P,!1);else{const xe=P.stencilBuffer?r.DEPTH_STENCIL_ATTACHMENT:r.DEPTH_ATTACHMENT,ne=M.__webglDepthbuffer[ce];r.bindRenderbuffer(r.RENDERBUFFER,ne),r.framebufferRenderbuffer(r.FRAMEBUFFER,xe,r.RENDERBUFFER,ne)}}else{const ce=P.texture.mipmaps;if(ce&&ce.length>0?i.bindFramebuffer(r.FRAMEBUFFER,M.__webglFramebuffer[0]):i.bindFramebuffer(r.FRAMEBUFFER,M.__webglFramebuffer),M.__webglDepthbuffer===void 0)M.__webglDepthbuffer=r.createRenderbuffer(),mt(M.__webglDepthbuffer,P,!1);else{const xe=P.stencilBuffer?r.DEPTH_STENCIL_ATTACHMENT:r.DEPTH_ATTACHMENT,ne=M.__webglDepthbuffer;r.bindRenderbuffer(r.RENDERBUFFER,ne),r.framebufferRenderbuffer(r.FRAMEBUFFER,xe,r.RENDERBUFFER,ne)}}i.bindFramebuffer(r.FRAMEBUFFER,null)}function xt(P,M,Z){const ce=s.get(P);M!==void 0&&Ge(ce.__webglFramebuffer,P,P.texture,r.COLOR_ATTACHMENT0,r.TEXTURE_2D,0),Z!==void 0&&ut(P)}function bt(P){const M=P.texture,Z=s.get(P),ce=s.get(M);P.addEventListener("dispose",T);const xe=P.textures,ne=P.isWebGLCubeRenderTarget===!0,Ae=xe.length>1;if(Ae||(ce.__webglTexture===void 0&&(ce.__webglTexture=r.createTexture()),ce.__version=M.version,f.memory.textures++),ne){Z.__webglFramebuffer=[];for(let pe=0;pe<6;pe++)if(M.mipmaps&&M.mipmaps.length>0){Z.__webglFramebuffer[pe]=[];for(let ye=0;ye<M.mipmaps.length;ye++)Z.__webglFramebuffer[pe][ye]=r.createFramebuffer()}else Z.__webglFramebuffer[pe]=r.createFramebuffer()}else{if(M.mipmaps&&M.mipmaps.length>0){Z.__webglFramebuffer=[];for(let pe=0;pe<M.mipmaps.length;pe++)Z.__webglFramebuffer[pe]=r.createFramebuffer()}else Z.__webglFramebuffer=r.createFramebuffer();if(Ae)for(let pe=0,ye=xe.length;pe<ye;pe++){const Ne=s.get(xe[pe]);Ne.__webglTexture===void 0&&(Ne.__webglTexture=r.createTexture(),f.memory.textures++)}if(P.samples>0&&fn(P)===!1){Z.__webglMultisampledFramebuffer=r.createFramebuffer(),Z.__webglColorRenderbuffer=[],i.bindFramebuffer(r.FRAMEBUFFER,Z.__webglMultisampledFramebuffer);for(let pe=0;pe<xe.length;pe++){const ye=xe[pe];Z.__webglColorRenderbuffer[pe]=r.createRenderbuffer(),r.bindRenderbuffer(r.RENDERBUFFER,Z.__webglColorRenderbuffer[pe]);const Ne=c.convert(ye.format,ye.colorSpace),Ze=c.convert(ye.type),He=w(ye.internalFormat,Ne,Ze,ye.normalized,ye.colorSpace,P.isXRRenderTarget===!0),Fe=Xt(P);r.renderbufferStorageMultisample(r.RENDERBUFFER,Fe,He,P.width,P.height),r.framebufferRenderbuffer(r.FRAMEBUFFER,r.COLOR_ATTACHMENT0+pe,r.RENDERBUFFER,Z.__webglColorRenderbuffer[pe])}r.bindRenderbuffer(r.RENDERBUFFER,null),P.depthBuffer&&(Z.__webglDepthRenderbuffer=r.createRenderbuffer(),mt(Z.__webglDepthRenderbuffer,P,!0)),i.bindFramebuffer(r.FRAMEBUFFER,null)}}if(ne){i.bindTexture(r.TEXTURE_CUBE_MAP,ce.__webglTexture),ze(r.TEXTURE_CUBE_MAP,M);for(let pe=0;pe<6;pe++)if(M.mipmaps&&M.mipmaps.length>0)for(let ye=0;ye<M.mipmaps.length;ye++)Ge(Z.__webglFramebuffer[pe][ye],P,M,r.COLOR_ATTACHMENT0,r.TEXTURE_CUBE_MAP_POSITIVE_X+pe,ye);else Ge(Z.__webglFramebuffer[pe],P,M,r.COLOR_ATTACHMENT0,r.TEXTURE_CUBE_MAP_POSITIVE_X+pe,0);S(M)&&F(r.TEXTURE_CUBE_MAP),i.unbindTexture()}else if(Ae){for(let pe=0,ye=xe.length;pe<ye;pe++){const Ne=xe[pe],Ze=s.get(Ne);let He=r.TEXTURE_2D;(P.isWebGL3DRenderTarget||P.isWebGLArrayRenderTarget)&&(He=P.isWebGL3DRenderTarget?r.TEXTURE_3D:r.TEXTURE_2D_ARRAY),i.bindTexture(He,Ze.__webglTexture),ze(He,Ne),Ge(Z.__webglFramebuffer,P,Ne,r.COLOR_ATTACHMENT0+pe,He,0),S(Ne)&&F(He)}i.unbindTexture()}else{let pe=r.TEXTURE_2D;if((P.isWebGL3DRenderTarget||P.isWebGLArrayRenderTarget)&&(pe=P.isWebGL3DRenderTarget?r.TEXTURE_3D:r.TEXTURE_2D_ARRAY),i.bindTexture(pe,ce.__webglTexture),ze(pe,M),M.mipmaps&&M.mipmaps.length>0)for(let ye=0;ye<M.mipmaps.length;ye++)Ge(Z.__webglFramebuffer[ye],P,M,r.COLOR_ATTACHMENT0,pe,ye);else Ge(Z.__webglFramebuffer,P,M,r.COLOR_ATTACHMENT0,pe,0);S(M)&&F(pe),i.unbindTexture()}P.depthBuffer&&ut(P)}function pt(P){const M=P.textures;for(let Z=0,ce=M.length;Z<ce;Z++){const xe=M[Z];if(S(xe)){const ne=G(P),Ae=s.get(xe).__webglTexture;i.bindTexture(ne,Ae),F(ne),i.unbindTexture()}}}const vt=[],Gt=[];function vn(P){if(P.samples>0){if(fn(P)===!1){const M=P.textures,Z=P.width,ce=P.height;let xe=r.COLOR_BUFFER_BIT;const ne=P.stencilBuffer?r.DEPTH_STENCIL_ATTACHMENT:r.DEPTH_ATTACHMENT,Ae=s.get(P),pe=M.length>1;if(pe)for(let Ne=0;Ne<M.length;Ne++)i.bindFramebuffer(r.FRAMEBUFFER,Ae.__webglMultisampledFramebuffer),r.framebufferRenderbuffer(r.FRAMEBUFFER,r.COLOR_ATTACHMENT0+Ne,r.RENDERBUFFER,null),i.bindFramebuffer(r.FRAMEBUFFER,Ae.__webglFramebuffer),r.framebufferTexture2D(r.DRAW_FRAMEBUFFER,r.COLOR_ATTACHMENT0+Ne,r.TEXTURE_2D,null,0);i.bindFramebuffer(r.READ_FRAMEBUFFER,Ae.__webglMultisampledFramebuffer);const ye=P.texture.mipmaps;ye&&ye.length>0?i.bindFramebuffer(r.DRAW_FRAMEBUFFER,Ae.__webglFramebuffer[0]):i.bindFramebuffer(r.DRAW_FRAMEBUFFER,Ae.__webglFramebuffer);for(let Ne=0;Ne<M.length;Ne++){if(P.resolveDepthBuffer&&(P.depthBuffer&&(xe|=r.DEPTH_BUFFER_BIT),P.stencilBuffer&&P.resolveStencilBuffer&&(xe|=r.STENCIL_BUFFER_BIT)),pe){r.framebufferRenderbuffer(r.READ_FRAMEBUFFER,r.COLOR_ATTACHMENT0,r.RENDERBUFFER,Ae.__webglColorRenderbuffer[Ne]);const Ze=s.get(M[Ne]).__webglTexture;r.framebufferTexture2D(r.DRAW_FRAMEBUFFER,r.COLOR_ATTACHMENT0,r.TEXTURE_2D,Ze,0)}r.blitFramebuffer(0,0,Z,ce,0,0,Z,ce,xe,r.NEAREST),m===!0&&(vt.length=0,Gt.length=0,vt.push(r.COLOR_ATTACHMENT0+Ne),P.depthBuffer&&P.storeMultisampledDepthBuffer===!1&&(vt.push(ne),Gt.push(ne),r.invalidateFramebuffer(r.DRAW_FRAMEBUFFER,Gt)),r.invalidateFramebuffer(r.READ_FRAMEBUFFER,vt))}if(i.bindFramebuffer(r.READ_FRAMEBUFFER,null),i.bindFramebuffer(r.DRAW_FRAMEBUFFER,null),pe)for(let Ne=0;Ne<M.length;Ne++){i.bindFramebuffer(r.FRAMEBUFFER,Ae.__webglMultisampledFramebuffer),r.framebufferRenderbuffer(r.FRAMEBUFFER,r.COLOR_ATTACHMENT0+Ne,r.RENDERBUFFER,Ae.__webglColorRenderbuffer[Ne]);const Ze=s.get(M[Ne]).__webglTexture;i.bindFramebuffer(r.FRAMEBUFFER,Ae.__webglFramebuffer),r.framebufferTexture2D(r.DRAW_FRAMEBUFFER,r.COLOR_ATTACHMENT0+Ne,r.TEXTURE_2D,Ze,0)}i.bindFramebuffer(r.DRAW_FRAMEBUFFER,Ae.__webglMultisampledFramebuffer)}else if(P.depthBuffer&&P.storeMultisampledDepthBuffer===!1&&m){const M=P.stencilBuffer?r.DEPTH_STENCIL_ATTACHMENT:r.DEPTH_ATTACHMENT;r.invalidateFramebuffer(r.DRAW_FRAMEBUFFER,[M])}}}function Xt(P){return Math.min(l.maxSamples,P.samples)}function fn(P){const M=s.get(P);return P.samples>0&&e.has("WEBGL_multisampled_render_to_texture")===!0&&M.__useRenderToTexture!==!1}function j(P){const M=f.render.frame;g.get(P)!==M&&(g.set(P,M),P.update())}function Ft(P,M){const Z=P.colorSpace,ce=P.format,xe=P.type;return P.isCompressedTexture===!0||P.isVideoTexture===!0||Z!==ku&&Z!==ns&&(kt.getTransfer(Z)===cn?(ce!==Ta||xe!==fa)&&ht("WebGLTextures: sRGB encoded textures have to use RGBAFormat and UnsignedByteType."):Zt("WebGLTextures: Unsupported texture color space:",Z)),M}function Ut(P){return typeof HTMLImageElement<"u"&&P instanceof HTMLImageElement?(p.width=P.naturalWidth||P.width,p.height=P.naturalHeight||P.height):typeof VideoFrame<"u"&&P instanceof VideoFrame?(p.width=P.displayWidth,p.height=P.displayHeight):(p.width=P.width,p.height=P.height),p}this.allocateTextureUnit=B,this.resetTextureUnits=re,this.getTextureUnits=k,this.setTextureUnits=K,this.setTexture2D=ee,this.setTexture2DArray=oe,this.setTexture3D=fe,this.setTextureCube=D,this.rebindTextures=xt,this.setupRenderTarget=bt,this.updateRenderTargetMipmap=pt,this.updateMultisampleRenderTarget=vn,this.setupDepthRenderbuffer=ut,this.setupFrameBufferTexture=Ge,this.useMultisampledRTT=fn,this.isReversedDepthBuffer=function(){return i.buffers.depth.getReversed()}}function gw(r,e){function i(s,l=ns){let c;const f=kt.getTransfer(l);if(s===fa)return r.UNSIGNED_BYTE;if(s===Ip)return r.UNSIGNED_SHORT_4_4_4_4;if(s===Hp)return r.UNSIGNED_SHORT_5_5_5_1;if(s===E_)return r.UNSIGNED_INT_5_9_9_9_REV;if(s===T_)return r.UNSIGNED_INT_10F_11F_11F_REV;if(s===b_)return r.BYTE;if(s===M_)return r.SHORT;if(s===Yl)return r.UNSIGNED_SHORT;if(s===Bp)return r.INT;if(s===Xa)return r.UNSIGNED_INT;if(s===Ga)return r.FLOAT;if(s===Wa)return r.HALF_FLOAT;if(s===A_)return r.ALPHA;if(s===w_)return r.RGB;if(s===Ta)return r.RGBA;if(s===Mr)return r.DEPTH_COMPONENT;if(s===Us)return r.DEPTH_STENCIL;if(s===C_)return r.RED;if(s===Gp)return r.RED_INTEGER;if(s===Ps)return r.RG;if(s===Vp)return r.RG_INTEGER;if(s===kp)return r.RGBA_INTEGER;if(s===Lu||s===Ou||s===Pu||s===zu)if(f===cn)if(c=e.get("WEBGL_compressed_texture_s3tc_srgb"),c!==null){if(s===Lu)return c.COMPRESSED_SRGB_S3TC_DXT1_EXT;if(s===Ou)return c.COMPRESSED_SRGB_ALPHA_S3TC_DXT1_EXT;if(s===Pu)return c.COMPRESSED_SRGB_ALPHA_S3TC_DXT3_EXT;if(s===zu)return c.COMPRESSED_SRGB_ALPHA_S3TC_DXT5_EXT}else return null;else if(c=e.get("WEBGL_compressed_texture_s3tc"),c!==null){if(s===Lu)return c.COMPRESSED_RGB_S3TC_DXT1_EXT;if(s===Ou)return c.COMPRESSED_RGBA_S3TC_DXT1_EXT;if(s===Pu)return c.COMPRESSED_RGBA_S3TC_DXT3_EXT;if(s===zu)return c.COMPRESSED_RGBA_S3TC_DXT5_EXT}else return null;if(s===$h||s===ep||s===tp||s===np)if(c=e.get("WEBGL_compressed_texture_pvrtc"),c!==null){if(s===$h)return c.COMPRESSED_RGB_PVRTC_4BPPV1_IMG;if(s===ep)return c.COMPRESSED_RGB_PVRTC_2BPPV1_IMG;if(s===tp)return c.COMPRESSED_RGBA_PVRTC_4BPPV1_IMG;if(s===np)return c.COMPRESSED_RGBA_PVRTC_2BPPV1_IMG}else return null;if(s===ip||s===ap||s===rp||s===sp||s===op||s===Gu||s===lp)if(c=e.get("WEBGL_compressed_texture_etc"),c!==null){if(s===ip||s===ap)return f===cn?c.COMPRESSED_SRGB8_ETC2:c.COMPRESSED_RGB8_ETC2;if(s===rp)return f===cn?c.COMPRESSED_SRGB8_ALPHA8_ETC2_EAC:c.COMPRESSED_RGBA8_ETC2_EAC;if(s===sp)return c.COMPRESSED_R11_EAC;if(s===op)return c.COMPRESSED_SIGNED_R11_EAC;if(s===Gu)return c.COMPRESSED_RG11_EAC;if(s===lp)return c.COMPRESSED_SIGNED_RG11_EAC}else return null;if(s===cp||s===up||s===fp||s===dp||s===hp||s===pp||s===mp||s===gp||s===xp||s===vp||s===_p||s===yp||s===Sp||s===bp)if(c=e.get("WEBGL_compressed_texture_astc"),c!==null){if(s===cp)return f===cn?c.COMPRESSED_SRGB8_ALPHA8_ASTC_4x4_KHR:c.COMPRESSED_RGBA_ASTC_4x4_KHR;if(s===up)return f===cn?c.COMPRESSED_SRGB8_ALPHA8_ASTC_5x4_KHR:c.COMPRESSED_RGBA_ASTC_5x4_KHR;if(s===fp)return f===cn?c.COMPRESSED_SRGB8_ALPHA8_ASTC_5x5_KHR:c.COMPRESSED_RGBA_ASTC_5x5_KHR;if(s===dp)return f===cn?c.COMPRESSED_SRGB8_ALPHA8_ASTC_6x5_KHR:c.COMPRESSED_RGBA_ASTC_6x5_KHR;if(s===hp)return f===cn?c.COMPRESSED_SRGB8_ALPHA8_ASTC_6x6_KHR:c.COMPRESSED_RGBA_ASTC_6x6_KHR;if(s===pp)return f===cn?c.COMPRESSED_SRGB8_ALPHA8_ASTC_8x5_KHR:c.COMPRESSED_RGBA_ASTC_8x5_KHR;if(s===mp)return f===cn?c.COMPRESSED_SRGB8_ALPHA8_ASTC_8x6_KHR:c.COMPRESSED_RGBA_ASTC_8x6_KHR;if(s===gp)return f===cn?c.COMPRESSED_SRGB8_ALPHA8_ASTC_8x8_KHR:c.COMPRESSED_RGBA_ASTC_8x8_KHR;if(s===xp)return f===cn?c.COMPRESSED_SRGB8_ALPHA8_ASTC_10x5_KHR:c.COMPRESSED_RGBA_ASTC_10x5_KHR;if(s===vp)return f===cn?c.COMPRESSED_SRGB8_ALPHA8_ASTC_10x6_KHR:c.COMPRESSED_RGBA_ASTC_10x6_KHR;if(s===_p)return f===cn?c.COMPRESSED_SRGB8_ALPHA8_ASTC_10x8_KHR:c.COMPRESSED_RGBA_ASTC_10x8_KHR;if(s===yp)return f===cn?c.COMPRESSED_SRGB8_ALPHA8_ASTC_10x10_KHR:c.COMPRESSED_RGBA_ASTC_10x10_KHR;if(s===Sp)return f===cn?c.COMPRESSED_SRGB8_ALPHA8_ASTC_12x10_KHR:c.COMPRESSED_RGBA_ASTC_12x10_KHR;if(s===bp)return f===cn?c.COMPRESSED_SRGB8_ALPHA8_ASTC_12x12_KHR:c.COMPRESSED_RGBA_ASTC_12x12_KHR}else return null;if(s===Mp||s===Ep||s===Tp)if(c=e.get("EXT_texture_compression_bptc"),c!==null){if(s===Mp)return f===cn?c.COMPRESSED_SRGB_ALPHA_BPTC_UNORM_EXT:c.COMPRESSED_RGBA_BPTC_UNORM_EXT;if(s===Ep)return c.COMPRESSED_RGB_BPTC_SIGNED_FLOAT_EXT;if(s===Tp)return c.COMPRESSED_RGB_BPTC_UNSIGNED_FLOAT_EXT}else return null;if(s===Ap||s===wp||s===Vu||s===Cp)if(c=e.get("EXT_texture_compression_rgtc"),c!==null){if(s===Ap)return c.COMPRESSED_RED_RGTC1_EXT;if(s===wp)return c.COMPRESSED_SIGNED_RED_RGTC1_EXT;if(s===Vu)return c.COMPRESSED_RED_GREEN_RGTC2_EXT;if(s===Cp)return c.COMPRESSED_SIGNED_RED_GREEN_RGTC2_EXT}else return null;return s===jl?r.UNSIGNED_INT_24_8:r[s]!==void 0?r[s]:null}return{convert:i}}const xw=`
void main() {

	gl_Position = vec4( position, 1.0 );

}`,vw=`
uniform sampler2DArray depthColor;
uniform float depthWidth;
uniform float depthHeight;

void main() {

	vec2 coord = vec2( gl_FragCoord.x / depthWidth, gl_FragCoord.y / depthHeight );

	if ( coord.x >= 1.0 ) {

		gl_FragDepth = texture( depthColor, vec3( coord.x - 1.0, coord.y, 1 ) ).r;

	} else {

		gl_FragDepth = texture( depthColor, vec3( coord.x, coord.y, 0 ) ).r;

	}

}`;class _w{constructor(){this.texture=null,this.mesh=null,this.depthNear=0,this.depthFar=0}init(e,i){if(this.texture===null){const s=new F_(e.texture);(e.depthNear!==i.depthNear||e.depthFar!==i.depthFar)&&(this.depthNear=e.depthNear,this.depthFar=e.depthFar),this.texture=s}}getMesh(e){if(this.texture!==null&&this.mesh===null){const i=e.cameras[0].viewport,s=new Yn({vertexShader:xw,fragmentShader:vw,uniforms:{depthColor:{value:this.texture},depthWidth:{value:i.z},depthHeight:{value:i.w}}});this.mesh=new ji(new ec(20,20),s)}return this.mesh}reset(){this.texture=null,this.mesh=null}getDepthTexture(){return this.texture}}class yw extends Fs{constructor(e,i){super();const s=this;let l=null,c=1,f=null,h="local-floor",m=1,p=null,g=null,v=null,x=null,_=null,E=null;const R=typeof XRWebGLBinding<"u",b=new _w,S={},F=i.getContextAttributes();let G=null,w=null;const N=[],L=[],z=new Kt;let T=null,O=null;const I=new Yi;I.viewport=new Ln;const W=new Yi;W.viewport=new Ln;const J=[I,W],re=new wM;let k=null,K=null;this.cameraAutoUpdate=!0,this.enabled=!1,this.isPresenting=!1,this.getController=function(ue){let Se=N[ue];return Se===void 0&&(Se=new mh,N[ue]=Se),Se.getTargetRaySpace()},this.getControllerGrip=function(ue){let Se=N[ue];return Se===void 0&&(Se=new mh,N[ue]=Se),Se.getGripSpace()},this.getHand=function(ue){let Se=N[ue];return Se===void 0&&(Se=new mh,N[ue]=Se),Se.getHandSpace()};function B(ue){const Se=L.indexOf(ue.inputSource);if(Se===-1)return;const Re=N[Se];Re!==void 0&&(Re.update(ue.inputSource,ue.frame,p||f),Re.dispatchEvent({type:ue.type,data:ue.inputSource}))}function V(){l.removeEventListener("select",B),l.removeEventListener("selectstart",B),l.removeEventListener("selectend",B),l.removeEventListener("squeeze",B),l.removeEventListener("squeezestart",B),l.removeEventListener("squeezeend",B),l.removeEventListener("end",V),l.removeEventListener("inputsourceschange",ee);for(let ue=0;ue<N.length;ue++){const Se=L[ue];Se!==null&&(L[ue]=null,N[ue].disconnect(Se))}k=null,K=null,b.reset();for(const ue in S)delete S[ue];if(e.setRenderTarget(G),_=null,x=null,v=null,l=null,w=null,Xe.stop(),s.isPresenting=!1,e.setPixelRatio(T),e.setSize(z.width,z.height,!1),O!==null){const ue=O.camera;ue.fov=O.fov,ue.zoom=O.zoom,ue.updateProjectionMatrix(),O=null}s.dispatchEvent({type:"sessionend"})}this.setFramebufferScaleFactor=function(ue){c=ue,s.isPresenting===!0&&ht("WebXRManager: Cannot change framebuffer scale while presenting.")},this.setReferenceSpaceType=function(ue){h=ue,s.isPresenting===!0&&ht("WebXRManager: Cannot change reference space type while presenting.")},this.getReferenceSpace=function(){return p||f},this.setReferenceSpace=function(ue){p=ue},this.getBaseLayer=function(){return x!==null?x:_},this.getBinding=function(){return v===null&&R&&(v=new XRWebGLBinding(l,i)),v},this.getFrame=function(){return E},this.getSession=function(){return l},this.setSession=async function(ue){if(l=ue,l!==null){if(G=e.getRenderTarget(),l.addEventListener("select",B),l.addEventListener("selectstart",B),l.addEventListener("selectend",B),l.addEventListener("squeeze",B),l.addEventListener("squeezestart",B),l.addEventListener("squeezeend",B),l.addEventListener("end",V),l.addEventListener("inputsourceschange",ee),F.xrCompatible!==!0&&await i.makeXRCompatible(),T=e.getPixelRatio(),e.getSize(z),R&&"createProjectionLayer"in XRWebGLBinding.prototype){let Re=null,at=null,Ge=null;F.depth&&(Ge=F.stencil?i.DEPTH24_STENCIL8:i.DEPTH_COMPONENT24,Re=F.stencil?Us:Mr,at=F.stencil?jl:Xa);const mt={colorFormat:i.RGBA8,depthFormat:Ge,scaleFactor:c};v=this.getBinding(),x=v.createProjectionLayer(mt),l.updateRenderState({layers:[x]}),e.setPixelRatio(1),e.setSize(x.textureWidth,x.textureHeight,!1),w=new wa(x.textureWidth,x.textureHeight,{format:Ta,type:fa,depthTexture:new Ql(x.textureWidth,x.textureHeight,at,void 0,void 0,void 0,void 0,void 0,void 0,Re),stencilBuffer:F.stencil,colorSpace:e.outputColorSpace,samples:F.antialias?4:0,resolveDepthBuffer:x.ignoreDepthValues===!1,resolveStencilBuffer:x.ignoreDepthValues===!1,storeMultisampledDepthBuffer:x.ignoreDepthValues===!1,storeMultisampledStencilBuffer:x.ignoreDepthValues===!1})}else{const Re={antialias:F.antialias,alpha:!0,depth:F.depth,stencil:F.stencil,framebufferScaleFactor:c};_=new XRWebGLLayer(l,i,Re),l.updateRenderState({baseLayer:_}),e.setPixelRatio(1),e.setSize(_.framebufferWidth,_.framebufferHeight,!1),w=new wa(_.framebufferWidth,_.framebufferHeight,{format:Ta,type:fa,colorSpace:e.outputColorSpace,stencilBuffer:F.stencil,resolveDepthBuffer:_.ignoreDepthValues===!1,resolveStencilBuffer:_.ignoreDepthValues===!1,storeMultisampledDepthBuffer:_.ignoreDepthValues===!1,storeMultisampledStencilBuffer:_.ignoreDepthValues===!1})}w.isXRRenderTarget=!0,this.setFoveation(m),p=null,f=await l.requestReferenceSpace(h),Xe.setContext(l),Xe.start(),s.isPresenting=!0,s.dispatchEvent({type:"sessionstart"})}},this.getEnvironmentBlendMode=function(){if(l!==null)return l.environmentBlendMode},this.getDepthTexture=function(){return b.getDepthTexture()};function ee(ue){for(let Se=0;Se<ue.removed.length;Se++){const Re=ue.removed[Se],at=L.indexOf(Re);at>=0&&(L[at]=null,N[at].disconnect(Re))}for(let Se=0;Se<ue.added.length;Se++){const Re=ue.added[Se];let at=L.indexOf(Re);if(at===-1){for(let mt=0;mt<N.length;mt++)if(mt>=L.length){L.push(Re),at=mt;break}else if(L[mt]===null){L[mt]=Re,at=mt;break}if(at===-1)break}const Ge=N[at];Ge&&Ge.connect(Re)}}const oe=new Q,fe=new Q;function D(ue,Se,Re){oe.setFromMatrixPosition(Se.matrixWorld),fe.setFromMatrixPosition(Re.matrixWorld);const at=oe.distanceTo(fe),Ge=Se.projectionMatrix.elements,mt=Re.projectionMatrix.elements,un=Ge[14]/(Ge[10]-1),ut=Ge[14]/(Ge[10]+1),xt=(Ge[9]+1)/Ge[5],bt=(Ge[9]-1)/Ge[5],pt=(Ge[8]-1)/Ge[0],vt=(mt[8]+1)/mt[0],Gt=un*pt,vn=un*vt,Xt=at/(-pt+vt),fn=Xt*-pt;if(Se.matrixWorld.decompose(ue.position,ue.quaternion,ue.scale),ue.translateX(fn),ue.translateZ(Xt),ue.matrixWorld.compose(ue.position,ue.quaternion,ue.scale),ue.matrixWorldInverse.copy(ue.matrixWorld).invert(),Ge[10]===-1)ue.projectionMatrix.copy(Se.projectionMatrix),ue.projectionMatrixInverse.copy(Se.projectionMatrixInverse);else{const j=un+Xt,Ft=ut+Xt,Ut=Gt-fn,P=vn+(at-fn),M=xt*ut/Ft*j,Z=bt*ut/Ft*j;ue.projectionMatrix.makePerspective(Ut,P,M,Z,j,Ft),ue.projectionMatrixInverse.copy(ue.projectionMatrix).invert()}}function se(ue,Se){Se===null?ue.matrixWorld.copy(ue.matrix):ue.matrixWorld.multiplyMatrices(Se.matrixWorld,ue.matrix),ue.matrixWorldInverse.copy(ue.matrixWorld).invert()}this.updateCamera=function(ue){if(l===null)return;let Se=ue.near,Re=ue.far;b.texture!==null&&(b.depthNear>0&&(Se=b.depthNear),b.depthFar>0&&(Re=b.depthFar)),re.near=W.near=I.near=Se,re.far=W.far=I.far=Re,(k!==re.near||K!==re.far)&&(l.updateRenderState({depthNear:re.near,depthFar:re.far}),k=re.near,K=re.far),re.layers.mask=ue.layers.mask|6,I.layers.mask=re.layers.mask&-5,W.layers.mask=re.layers.mask&-3;const at=ue.parent,Ge=re.cameras;se(re,at);for(let mt=0;mt<Ge.length;mt++)se(Ge[mt],at);Ge.length===2?D(re,I,W):re.projectionMatrix.copy(I.projectionMatrix),O===null&&ue.isPerspectiveCamera&&(O={camera:ue,fov:ue.fov,zoom:ue.zoom}),_e(ue,re,at)};function _e(ue,Se,Re){Re===null?ue.matrix.copy(Se.matrixWorld):(ue.matrix.copy(Re.matrixWorld),ue.matrix.invert(),ue.matrix.multiply(Se.matrixWorld)),ue.matrix.decompose(ue.position,ue.quaternion,ue.scale),ue.updateMatrixWorld(!0),ue.projectionMatrix.copy(Se.projectionMatrix),ue.projectionMatrixInverse.copy(Se.projectionMatrixInverse),ue.isPerspectiveCamera&&(ue.fov=Kl*2*Math.atan(1/ue.projectionMatrix.elements[5]),ue.zoom=1)}this.getCamera=function(){return re},this.getFoveation=function(){if(!(x===null&&_===null))return m},this.setFoveation=function(ue){m=ue,x!==null&&(x.fixedFoveation=ue),_!==null&&_.fixedFoveation!==void 0&&(_.fixedFoveation=ue)},this.hasDepthSensing=function(){return b.texture!==null},this.getDepthSensingMesh=function(){return b.getMesh(re)},this.getCameraTexture=function(ue){return S[ue]};let De=null;function ze(ue,Se){if(g=Se.getViewerPose(p||f),E=Se,g!==null){const Re=g.views;_!==null&&(e.setRenderTargetFramebuffer(w,_.framebuffer),e.setRenderTarget(w));let at=!1;Re.length!==re.cameras.length&&(re.cameras.length=0,at=!0);for(let ut=0;ut<Re.length;ut++){const xt=Re[ut];let bt=null;if(_!==null)bt=_.getViewport(xt);else{const vt=v.getViewSubImage(x,xt);bt=vt.viewport,ut===0&&(e.setRenderTargetTextures(w,vt.colorTexture,vt.depthStencilTexture),e.setRenderTarget(w))}let pt=J[ut];pt===void 0&&(pt=new Yi,pt.layers.enable(ut),pt.viewport=new Ln,J[ut]=pt),pt.matrix.fromArray(xt.transform.matrix),pt.matrix.decompose(pt.position,pt.quaternion,pt.scale),pt.projectionMatrix.fromArray(xt.projectionMatrix),pt.projectionMatrixInverse.copy(pt.projectionMatrix).invert(),pt.viewport.set(bt.x,bt.y,bt.width,bt.height),ut===0&&(re.matrix.copy(pt.matrix),re.matrix.decompose(re.position,re.quaternion,re.scale)),at===!0&&re.cameras.push(pt)}const Ge=l.enabledFeatures;if(Ge&&Ge.includes("depth-sensing")&&l.depthUsage=="gpu-optimized"&&R){v=s.getBinding();const ut=v.getDepthInformation(Re[0]);ut&&ut.isValid&&ut.texture&&b.init(ut,l.renderState)}if(Ge&&Ge.includes("camera-access")&&R){e.state.unbindTexture(),v=s.getBinding();for(let ut=0;ut<Re.length;ut++){const xt=Re[ut].camera;if(xt){let bt=S[xt];bt||(bt=new F_,S[xt]=bt);const pt=v.getCameraImage(xt);bt.sourceTexture=pt}}}}for(let Re=0;Re<N.length;Re++){const at=L[Re],Ge=N[Re];at!==null&&Ge!==void 0&&Ge.update(at,Se,p||f)}De&&De(ue,Se),Se.detectedPlanes&&s.dispatchEvent({type:"planesdetected",data:Se}),E=null}const Xe=new V_;Xe.setAnimationLoop(ze),this.setAnimationLoop=function(ue){De=ue},this.dispose=function(){}}}const Sw=new En,Z_=new St;Z_.set(-1,0,0,0,1,0,0,0,1);function bw(r,e){function i(b,S){b.matrixAutoUpdate===!0&&b.updateMatrix(),S.value.copy(b.matrix)}function s(b,S){S.color.getRGB(b.fogColor.value,I_(r)),S.isFog?(b.fogNear.value=S.near,b.fogFar.value=S.far):S.isFogExp2&&(b.fogDensity.value=S.density)}function l(b,S,F,G,w){S.isNodeMaterial?S.uniformsNeedUpdate=!1:S.isMeshBasicMaterial?c(b,S):S.isMeshLambertMaterial?(c(b,S),S.envMap&&(b.envMapIntensity.value=S.envMapIntensity)):S.isMeshToonMaterial?(c(b,S),v(b,S)):S.isMeshPhongMaterial?(c(b,S),g(b,S),S.envMap&&(b.envMapIntensity.value=S.envMapIntensity)):S.isMeshStandardMaterial?(c(b,S),x(b,S),S.isMeshPhysicalMaterial&&_(b,S,w)):S.isMeshMatcapMaterial?(c(b,S),E(b,S)):S.isMeshDepthMaterial?c(b,S):S.isMeshDistanceMaterial?(c(b,S),R(b,S)):S.isMeshNormalMaterial?c(b,S):S.isLineBasicMaterial?(f(b,S),S.isLineDashedMaterial&&h(b,S)):S.isPointsMaterial?m(b,S,F,G):S.isSpriteMaterial?p(b,S):S.isShadowMaterial?(b.color.value.copy(S.color),b.opacity.value=S.opacity):S.isShaderMaterial&&(S.uniformsNeedUpdate=!1)}function c(b,S){b.opacity.value=S.opacity,S.color&&b.diffuse.value.copy(S.color),S.emissive&&b.emissive.value.copy(S.emissive).multiplyScalar(S.emissiveIntensity),S.map&&(b.map.value=S.map,i(S.map,b.mapTransform)),S.alphaMap&&(b.alphaMap.value=S.alphaMap,i(S.alphaMap,b.alphaMapTransform)),S.bumpMap&&(b.bumpMap.value=S.bumpMap,i(S.bumpMap,b.bumpMapTransform),b.bumpScale.value=S.bumpScale,S.side===Oi&&(b.bumpScale.value*=-1)),S.normalMap&&(b.normalMap.value=S.normalMap,i(S.normalMap,b.normalMapTransform),b.normalScale.value.copy(S.normalScale),S.side===Oi&&b.normalScale.value.negate()),S.displacementMap&&(b.displacementMap.value=S.displacementMap,i(S.displacementMap,b.displacementMapTransform),b.displacementScale.value=S.displacementScale,b.displacementBias.value=S.displacementBias),S.emissiveMap&&(b.emissiveMap.value=S.emissiveMap,i(S.emissiveMap,b.emissiveMapTransform)),S.specularMap&&(b.specularMap.value=S.specularMap,i(S.specularMap,b.specularMapTransform)),S.alphaTest>0&&(b.alphaTest.value=S.alphaTest);const F=e.get(S),G=F.envMap,w=F.envMapRotation;G&&(b.envMap.value=G,b.envMapRotation.value.setFromMatrix4(Sw.makeRotationFromEuler(w)).transpose(),G.isCubeTexture&&G.isRenderTargetTexture===!1&&b.envMapRotation.value.premultiply(Z_),b.reflectivity.value=S.reflectivity,b.ior.value=S.ior,b.refractionRatio.value=S.refractionRatio),S.lightMap&&(b.lightMap.value=S.lightMap,b.lightMapIntensity.value=S.lightMapIntensity,i(S.lightMap,b.lightMapTransform)),S.aoMap&&(b.aoMap.value=S.aoMap,b.aoMapIntensity.value=S.aoMapIntensity,i(S.aoMap,b.aoMapTransform))}function f(b,S){b.diffuse.value.copy(S.color),b.opacity.value=S.opacity,S.map&&(b.map.value=S.map,i(S.map,b.mapTransform))}function h(b,S){b.dashSize.value=S.dashSize,b.totalSize.value=S.dashSize+S.gapSize,b.scale.value=S.scale}function m(b,S,F,G){b.diffuse.value.copy(S.color),b.opacity.value=S.opacity,b.size.value=S.size*F,b.scale.value=G*.5,S.map&&(b.map.value=S.map,i(S.map,b.uvTransform)),S.alphaMap&&(b.alphaMap.value=S.alphaMap,i(S.alphaMap,b.alphaMapTransform)),S.alphaTest>0&&(b.alphaTest.value=S.alphaTest)}function p(b,S){b.diffuse.value.copy(S.color),b.opacity.value=S.opacity,b.rotation.value=S.rotation,S.map&&(b.map.value=S.map,i(S.map,b.mapTransform)),S.alphaMap&&(b.alphaMap.value=S.alphaMap,i(S.alphaMap,b.alphaMapTransform)),S.alphaTest>0&&(b.alphaTest.value=S.alphaTest)}function g(b,S){b.specular.value.copy(S.specular),b.shininess.value=Math.max(S.shininess,1e-4)}function v(b,S){S.gradientMap&&(b.gradientMap.value=S.gradientMap)}function x(b,S){b.metalness.value=S.metalness,S.metalnessMap&&(b.metalnessMap.value=S.metalnessMap,i(S.metalnessMap,b.metalnessMapTransform)),b.roughness.value=S.roughness,S.roughnessMap&&(b.roughnessMap.value=S.roughnessMap,i(S.roughnessMap,b.roughnessMapTransform)),S.envMap&&(b.envMapIntensity.value=S.envMapIntensity)}function _(b,S,F){b.ior.value=S.ior,S.sheen>0&&(b.sheenColor.value.copy(S.sheenColor).multiplyScalar(S.sheen),b.sheenRoughness.value=S.sheenRoughness,S.sheenColorMap&&(b.sheenColorMap.value=S.sheenColorMap,i(S.sheenColorMap,b.sheenColorMapTransform)),S.sheenRoughnessMap&&(b.sheenRoughnessMap.value=S.sheenRoughnessMap,i(S.sheenRoughnessMap,b.sheenRoughnessMapTransform))),S.clearcoat>0&&(b.clearcoat.value=S.clearcoat,b.clearcoatRoughness.value=S.clearcoatRoughness,S.clearcoatMap&&(b.clearcoatMap.value=S.clearcoatMap,i(S.clearcoatMap,b.clearcoatMapTransform)),S.clearcoatRoughnessMap&&(b.clearcoatRoughnessMap.value=S.clearcoatRoughnessMap,i(S.clearcoatRoughnessMap,b.clearcoatRoughnessMapTransform)),S.clearcoatNormalMap&&(b.clearcoatNormalMap.value=S.clearcoatNormalMap,i(S.clearcoatNormalMap,b.clearcoatNormalMapTransform),b.clearcoatNormalScale.value.copy(S.clearcoatNormalScale),S.side===Oi&&b.clearcoatNormalScale.value.negate())),S.dispersion>0&&(b.dispersion.value=S.dispersion),S.retroreflectivity>0&&(b.retroreflectivity.value=S.retroreflectivity),S.iridescence>0&&(b.iridescence.value=S.iridescence,b.iridescenceIOR.value=S.iridescenceIOR,b.iridescenceThicknessMinimum.value=S.iridescenceThicknessRange[0],b.iridescenceThicknessMaximum.value=S.iridescenceThicknessRange[1],S.iridescenceMap&&(b.iridescenceMap.value=S.iridescenceMap,i(S.iridescenceMap,b.iridescenceMapTransform)),S.iridescenceThicknessMap&&(b.iridescenceThicknessMap.value=S.iridescenceThicknessMap,i(S.iridescenceThicknessMap,b.iridescenceThicknessMapTransform))),S.transmission>0&&(b.transmission.value=S.transmission,b.transmissionSamplerMap.value=F.texture,b.transmissionSamplerSize.value.set(F.width,F.height),S.transmissionMap&&(b.transmissionMap.value=S.transmissionMap,i(S.transmissionMap,b.transmissionMapTransform)),b.thickness.value=S.thickness,S.thicknessMap&&(b.thicknessMap.value=S.thicknessMap,i(S.thicknessMap,b.thicknessMapTransform)),b.attenuationDistance.value=S.attenuationDistance,b.attenuationColor.value.copy(S.attenuationColor)),S.anisotropy>0&&(b.anisotropyVector.value.set(S.anisotropy*Math.cos(S.anisotropyRotation),S.anisotropy*Math.sin(S.anisotropyRotation)),S.anisotropyMap&&(b.anisotropyMap.value=S.anisotropyMap,i(S.anisotropyMap,b.anisotropyMapTransform))),b.specularIntensity.value=S.specularIntensity,b.specularColor.value.copy(S.specularColor),S.specularColorMap&&(b.specularColorMap.value=S.specularColorMap,i(S.specularColorMap,b.specularColorMapTransform)),S.specularIntensityMap&&(b.specularIntensityMap.value=S.specularIntensityMap,i(S.specularIntensityMap,b.specularIntensityMapTransform))}function E(b,S){S.matcap&&(b.matcap.value=S.matcap)}function R(b,S){const F=e.get(S).light;b.referencePosition.value.setFromMatrixPosition(F.matrixWorld),b.nearDistance.value=F.shadow.camera.near,b.farDistance.value=F.shadow.camera.far}return{refreshFogUniforms:s,refreshMaterialUniforms:l}}function Mw(r,e,i,s){let l={},c={},f=[];const h=r.getParameter(r.MAX_UNIFORM_BUFFER_BINDINGS);function m(w,N){const L=N.program;s.uniformBlockBinding(w,L)}function p(w,N){let L=l[w.id];L===void 0&&(b(w),L=g(w),l[w.id]=L,w.addEventListener("dispose",F));const z=N.program;s.updateUBOMapping(w,z);const T=e.render.frame;c[w.id]!==T&&(x(w),c[w.id]=T)}function g(w){const N=v();w.__bindingPointIndex=N;const L=r.createBuffer(),z=w.__size,T=w.usage;return r.bindBuffer(r.UNIFORM_BUFFER,L),r.bufferData(r.UNIFORM_BUFFER,z,T),r.bindBuffer(r.UNIFORM_BUFFER,null),r.bindBufferBase(r.UNIFORM_BUFFER,N,L),L}function v(){for(let w=0;w<h;w++)if(f.indexOf(w)===-1)return f.push(w),w;return Zt("WebGLRenderer: Maximum number of simultaneously usable uniforms groups reached."),0}function x(w){const N=l[w.id],L=w.uniforms,z=w.__cache;r.bindBuffer(r.UNIFORM_BUFFER,N);for(let T=0,O=L.length;T<O;T++){const I=L[T];if(Array.isArray(I))for(let W=0,J=I.length;W<J;W++)_(I[W],T,W,z);else _(I,T,0,z)}r.bindBuffer(r.UNIFORM_BUFFER,null)}function _(w,N,L,z){if(R(w,N,L,z)===!0){const T=w.__offset,O=w.value;if(Array.isArray(O)){let I=0;for(let W=0;W<O.length;W++){const J=O[W],re=S(J);E(J,w.__data,I),typeof J!="number"&&typeof J!="boolean"&&!J.isMatrix3&&!ArrayBuffer.isView(J)&&(I+=re.storage/Float32Array.BYTES_PER_ELEMENT)}}else E(O,w.__data,0);r.bufferSubData(r.UNIFORM_BUFFER,T,w.__data)}}function E(w,N,L){typeof w=="number"||typeof w=="boolean"?N[0]=w:w.isMatrix3?(N[0]=w.elements[0],N[1]=w.elements[1],N[2]=w.elements[2],N[3]=0,N[4]=w.elements[3],N[5]=w.elements[4],N[6]=w.elements[5],N[7]=0,N[8]=w.elements[6],N[9]=w.elements[7],N[10]=w.elements[8],N[11]=0):ArrayBuffer.isView(w)?N.set(new w.constructor(w.buffer,w.byteOffset,N.length)):w.toArray(N,L)}function R(w,N,L,z){const T=w.value,O=N+"_"+L;if(z[O]===void 0)return typeof T=="number"||typeof T=="boolean"?z[O]=T:ArrayBuffer.isView(T)?z[O]=T.slice():z[O]=T.clone(),!0;{const I=z[O];if(typeof T=="number"||typeof T=="boolean"){if(I!==T)return z[O]=T,!0}else{if(ArrayBuffer.isView(T))return!0;if(I.equals(T)===!1)return I.copy(T),!0}}return!1}function b(w){const N=w.uniforms;let L=0;const z=16;for(let O=0,I=N.length;O<I;O++){const W=Array.isArray(N[O])?N[O]:[N[O]];for(let J=0,re=W.length;J<re;J++){const k=W[J],K=Array.isArray(k.value)?k.value:[k.value];for(let B=0,V=K.length;B<V;B++){const ee=K[B],oe=S(ee),fe=L%z,D=fe%oe.boundary,se=fe+D;L+=D,se!==0&&z-se<oe.storage&&(L+=z-se),k.__data=new Float32Array(oe.storage/Float32Array.BYTES_PER_ELEMENT),k.__offset=L,L+=oe.storage}}}const T=L%z;return T>0&&(L+=z-T),w.__size=L,w.__cache={},this}function S(w){const N={boundary:0,storage:0};return typeof w=="number"||typeof w=="boolean"?(N.boundary=4,N.storage=4):w.isVector2?(N.boundary=8,N.storage=8):w.isVector3||w.isColor?(N.boundary=16,N.storage=12):w.isVector4?(N.boundary=16,N.storage=16):w.isMatrix3?(N.boundary=48,N.storage=48):w.isMatrix4?(N.boundary=64,N.storage=64):w.isTexture?ht("WebGLRenderer: Texture samplers can not be part of an uniforms group."):ArrayBuffer.isView(w)?(N.boundary=16,N.storage=w.byteLength):ht("WebGLRenderer: Unsupported uniform value type.",w),N}function F(w){const N=w.target;N.removeEventListener("dispose",F);const L=f.indexOf(N.__bindingPointIndex);f.splice(L,1),r.deleteBuffer(l[N.id]),delete l[N.id],delete c[N.id]}function G(){for(const w in l)r.deleteBuffer(l[w]);f=[],l={},c={}}return{bind:m,update:p,dispose:G}}const Ew=new Uint16Array([12469,15057,12620,14925,13266,14620,13807,14376,14323,13990,14545,13625,14713,13328,14840,12882,14931,12528,14996,12233,15039,11829,15066,11525,15080,11295,15085,10976,15082,10705,15073,10495,13880,14564,13898,14542,13977,14430,14158,14124,14393,13732,14556,13410,14702,12996,14814,12596,14891,12291,14937,11834,14957,11489,14958,11194,14943,10803,14921,10506,14893,10278,14858,9960,14484,14039,14487,14025,14499,13941,14524,13740,14574,13468,14654,13106,14743,12678,14818,12344,14867,11893,14889,11509,14893,11180,14881,10751,14852,10428,14812,10128,14765,9754,14712,9466,14764,13480,14764,13475,14766,13440,14766,13347,14769,13070,14786,12713,14816,12387,14844,11957,14860,11549,14868,11215,14855,10751,14825,10403,14782,10044,14729,9651,14666,9352,14599,9029,14967,12835,14966,12831,14963,12804,14954,12723,14936,12564,14917,12347,14900,11958,14886,11569,14878,11247,14859,10765,14828,10401,14784,10011,14727,9600,14660,9289,14586,8893,14508,8533,15111,12234,15110,12234,15104,12216,15092,12156,15067,12010,15028,11776,14981,11500,14942,11205,14902,10752,14861,10393,14812,9991,14752,9570,14682,9252,14603,8808,14519,8445,14431,8145,15209,11449,15208,11451,15202,11451,15190,11438,15163,11384,15117,11274,15055,10979,14994,10648,14932,10343,14871,9936,14803,9532,14729,9218,14645,8742,14556,8381,14461,8020,14365,7603,15273,10603,15272,10607,15267,10619,15256,10631,15231,10614,15182,10535,15118,10389,15042,10167,14963,9787,14883,9447,14800,9115,14710,8665,14615,8318,14514,7911,14411,7507,14279,7198,15314,9675,15313,9683,15309,9712,15298,9759,15277,9797,15229,9773,15166,9668,15084,9487,14995,9274,14898,8910,14800,8539,14697,8234,14590,7790,14479,7409,14367,7067,14178,6621,15337,8619,15337,8631,15333,8677,15325,8769,15305,8871,15264,8940,15202,8909,15119,8775,15022,8565,14916,8328,14804,8009,14688,7614,14569,7287,14448,6888,14321,6483,14088,6171,15350,7402,15350,7419,15347,7480,15340,7613,15322,7804,15287,7973,15229,8057,15148,8012,15046,7846,14933,7611,14810,7357,14682,7069,14552,6656,14421,6316,14251,5948,14007,5528,15356,5942,15356,5977,15353,6119,15348,6294,15332,6551,15302,6824,15249,7044,15171,7122,15070,7050,14949,6861,14818,6611,14679,6349,14538,6067,14398,5651,14189,5311,13935,4958,15359,4123,15359,4153,15356,4296,15353,4646,15338,5160,15311,5508,15263,5829,15188,6042,15088,6094,14966,6001,14826,5796,14678,5543,14527,5287,14377,4985,14133,4586,13869,4257,15360,1563,15360,1642,15358,2076,15354,2636,15341,3350,15317,4019,15273,4429,15203,4732,15105,4911,14981,4932,14836,4818,14679,4621,14517,4386,14359,4156,14083,3795,13808,3437,15360,122,15360,137,15358,285,15355,636,15344,1274,15322,2177,15281,2765,15215,3223,15120,3451,14995,3569,14846,3567,14681,3466,14511,3305,14344,3121,14037,2800,13753,2467,15360,0,15360,1,15359,21,15355,89,15346,253,15325,479,15287,796,15225,1148,15133,1492,15008,1749,14856,1882,14685,1886,14506,1783,14324,1608,13996,1398,13702,1183]);let Ia=null;function Tw(){return Ia===null&&(Ia=new rM(Ew,16,16,Ps,Wa),Ia.name="DFG_LUT",Ia.minFilter=mi,Ia.magFilter=mi,Ia.wrapS=_r,Ia.wrapT=_r,Ia.generateMipmaps=!1,Ia.needsUpdate=!0),Ia}class K_{constructor(e={}){const{canvas:i=yb(),context:s=null,depth:l=!0,stencil:c=!1,alpha:f=!1,antialias:h=!1,premultipliedAlpha:m=!0,preserveDrawingBuffer:p=!1,powerPreference:g="default",failIfMajorPerformanceCaveat:v=!1,reversedDepthBuffer:x=!1,outputBufferType:_=fa}=e;this.isWebGLRenderer=!0;let E;if(s!==null){if(typeof WebGLRenderingContext<"u"&&s instanceof WebGLRenderingContext)throw new Error("THREE.WebGLRenderer: WebGL 1 is not supported since r163.");E=s.getContextAttributes().alpha}else E=f;const R=_,b=new Set([kp,Vp,Gp]),S=new Set([fa,Xa,Yl,jl,Ip,Hp]),F=new Uint32Array(4),G=new Int32Array(4),w=new Q;let N=null,L=null;const z=[],T=[];let O=null;this.domElement=i,this.debug={checkShaderErrors:!0,diagnostics:{keywords:!1},onShaderError:null},this.autoClear=!0,this.autoClearColor=!0,this.autoClearDepth=!0,this.autoClearStencil=!0,this.sortObjects=!0,this.clippingPlanes=[],this.localClippingEnabled=!1,this.toneMapping=ka,this.toneMappingExposure=1,this.transmissionResolutionScale=1;const I=this;let W=!1,J=null,re=null,k=null,K=null;this._outputColorSpace=Ei;let B=0,V=0,ee=null,oe=-1,fe=null;const D=new Ln,se=new Ln;let _e=null;const De=new wt(0);let ze=0,Xe=i.width,ue=i.height,Se=1,Re=null,at=null;const Ge=new Ln(0,0,Xe,ue),mt=new Ln(0,0,Xe,ue);let un=!1;const ut=new P_;let xt=!1,bt=!1;const pt=new En,vt=new Q,Gt=new Ln,vn={background:null,fog:null,environment:null,overrideMaterial:null,isScene:!0};let Xt=!1;function fn(){return ee===null?Se:1}let j=s;function Ft(A,X){return i.getContext(A,X)}let Ut,P,M,Z,ce,xe,ne,Ae,pe,ye,Ne,Ze,He,Fe,rt,lt,dt,q,Oe,be,Pe,Ve,we;try{const A={alpha:!0,depth:l,stencil:c,antialias:h,premultipliedAlpha:m,preserveDrawingBuffer:p,powerPreference:g,failIfMajorPerformanceCaveat:v};if("setAttribute"in i&&i.setAttribute("data-engine",`three.js r${Fp}`),i.addEventListener("webglcontextlost",Qt,!1),i.addEventListener("webglcontextrestored",Nt,!1),i.addEventListener("webglcontextcreationerror",ei,!1),j===null){const X="webgl2";if(j=Ft(X,A),j===null)throw Ft(X)?new Error("THREE.WebGLRenderer: Error creating WebGL context with your selected attributes."):new Error("THREE.WebGLRenderer: Error creating WebGL context.")}et()}catch(A){throw i.removeEventListener("webglcontextlost",Qt,!1),i.removeEventListener("webglcontextrestored",Nt,!1),i.removeEventListener("webglcontextcreationerror",ei,!1),Zt("WebGLRenderer: "+A.message),A}function et(){Ut=new T2(j),Ut.init(),Pe=new gw(j,Ut),P=new m2(j,Ut,e,Pe),M=new pw(j,Ut),P.reversedDepthBuffer&&x&&M.buffers.depth.setReversed(!0),re=j.createFramebuffer(),k=j.createFramebuffer(),K=j.createFramebuffer(),Z=new C2(j),ce=new ew,xe=new mw(j,Ut,M,ce,P,Pe,Z),ne=new E2(I),Ae=new UM(j),Ve=new h2(j,Ae),pe=new A2(j,Ae,Z,Ve),ye=new U2(j,pe,Ae,Ve,Z),q=new R2(j,P,xe),rt=new g2(ce),Ne=new $A(I,ne,Ut,P,Ve,rt),Ze=new bw(I,ce),He=new nw,Fe=new lw(Ut),dt=new d2(I,ne,M,ye,E,m),lt=new hw(I,ye,P),we=new Mw(j,Z,P,M),Oe=new p2(j,Ut,Z),be=new w2(j,Ut,Z),Z.programs=Ne.programs,I.capabilities=P,I.extensions=Ut,I.properties=ce,I.renderLists=He,I.shadowMap=lt,I.state=M,I.info=Z}R!==fa&&(O=new N2(R,i.width,i.height,h,l,c));const Je=new yw(I,j);this.xr=Je,this.getContext=function(){return j},this.getContextAttributes=function(){return j.getContextAttributes()},this.forceContextLoss=function(){const A=Ut.get("WEBGL_lose_context");A&&A.loseContext()},this.forceContextRestore=function(){const A=Ut.get("WEBGL_lose_context");A&&A.restoreContext()},this.getPixelRatio=function(){return Se},this.setPixelRatio=function(A){A!==void 0&&(Se=A,this.setSize(Xe,ue,!1))},this.getSize=function(A){return A.set(Xe,ue)},this.setSize=function(A,X,ge=!0){if(Je.isPresenting){ht("WebGLRenderer: Can't change size while VR device is presenting.");return}Xe=A,ue=X,i.width=Math.floor(A*Se),i.height=Math.floor(X*Se),ge===!0&&(i.style.width=A+"px",i.style.height=X+"px"),O!==null&&O.setSize(i.width,i.height),this.setViewport(0,0,A,X)},this.getDrawingBufferSize=function(A){return A.set(Xe*Se,ue*Se).floor()},this.setDrawingBufferSize=function(A,X,ge){Xe=A,ue=X,Se=ge,i.width=Math.floor(A*ge),i.height=Math.floor(X*ge),this.setViewport(0,0,A,X)},this.setEffects=function(A){if(R===fa){Zt("WebGLRenderer: setEffects() requires outputBufferType set to HalfFloatType or FloatType.");return}if(A){for(let X=0;X<A.length;X++)if(A[X].isOutputPass===!0){ht("WebGLRenderer: OutputPass is not needed in setEffects(). Tone mapping and color space conversion are applied automatically.");break}}O.setEffects(A||[])},this.getCurrentViewport=function(A){return A.copy(D)},this.getViewport=function(A){return A.copy(Ge)},this.setViewport=function(A,X,ge,ie){A.isVector4?Ge.set(A.x,A.y,A.z,A.w):Ge.set(A,X,ge,ie),M.viewport(D.copy(Ge).multiplyScalar(Se).round())},this.getScissor=function(A){return A.copy(mt)},this.setScissor=function(A,X,ge,ie){A.isVector4?mt.set(A.x,A.y,A.z,A.w):mt.set(A,X,ge,ie),M.scissor(se.copy(mt).multiplyScalar(Se).round())},this.getScissorTest=function(){return un},this.setScissorTest=function(A){M.setScissorTest(un=A)},this.setOpaqueSort=function(A){Re=A},this.setTransparentSort=function(A){at=A},this.getClearColor=function(A){return A.copy(dt.getClearColor())},this.setClearColor=function(){dt.setClearColor(...arguments)},this.getClearAlpha=function(){return dt.getClearAlpha()},this.setClearAlpha=function(){dt.setClearAlpha(...arguments)},this.clear=function(A=!0,X=!0,ge=!0){let ie=0;if(A){let ae=!1;if(ee!==null){const Be=ee.texture.format;ae=b.has(Be)}if(ae){const Be=ee.texture.type,We=S.has(Be),Ie=dt.getClearColor(),qe=dt.getClearAlpha(),Ye=Ie.r,gt=Ie.g,Tt=Ie.b;We?(F[0]=Ye,F[1]=gt,F[2]=Tt,F[3]=qe,j.clearBufferuiv(j.COLOR,0,F)):(G[0]=Ye,G[1]=gt,G[2]=Tt,G[3]=qe,j.clearBufferiv(j.COLOR,0,G))}else ie|=j.COLOR_BUFFER_BIT}X&&(ie|=j.DEPTH_BUFFER_BIT,this.state.buffers.depth.setMask(!0)),ge&&(ie|=j.STENCIL_BUFFER_BIT,this.state.buffers.stencil.setMask(4294967295)),ie!==0&&j.clear(ie)},this.clearColor=function(){this.clear(!0,!1,!1)},this.clearDepth=function(){this.clear(!1,!0,!1)},this.clearStencil=function(){this.clear(!1,!1,!0)},this.setNodesHandler=function(A){A.setRenderer(this),J=A},this.dispose=function(){i.removeEventListener("webglcontextlost",Qt,!1),i.removeEventListener("webglcontextrestored",Nt,!1),i.removeEventListener("webglcontextcreationerror",ei,!1),dt.dispose(),He.dispose(),Fe.dispose(),ce.dispose(),ne.dispose(),ye.dispose(),Ve.dispose(),we.dispose(),Ne.dispose(),Je.dispose(),Je.removeEventListener("sessionstart",Sn),Je.removeEventListener("sessionend",In),Kn.stop()};function Qt(A){A.preventDefault(),$x("WebGLRenderer: Context Lost."),W=!0}function Nt(){$x("WebGLRenderer: Context Restored."),W=!1;const A=Z.autoReset,X=lt.enabled,ge=lt.autoUpdate,ie=lt.needsUpdate,ae=lt.type;et(),Z.autoReset=A,lt.enabled=X,lt.autoUpdate=ge,lt.needsUpdate=ie,lt.type=ae}function ei(A){Zt("WebGLRenderer: A WebGL context could not be created. Reason: ",A.statusMessage)}function ti(A){const X=A.target;X.removeEventListener("dispose",ti),Zi(X)}function Zi(A){ls(A),ce.remove(A)}function ls(A){const X=ce.get(A).programs;X!==void 0&&(X.forEach(function(ge){Ne.releaseProgram(ge)}),A.isShaderMaterial&&Ne.releaseShaderCache(A))}this.renderBufferDirect=function(A,X,ge,ie,ae,Be){X===null&&(X=vn);const We=ae.isMesh&&ae.matrixWorld.determinantAffine()<0,Ie=pa(A,X,ge,ie,ae);M.setMaterial(ie,We);let qe=ge.index,Ye=1;if(ie.wireframe===!0){if(qe=pe.getWireframeAttribute(ge),qe===void 0)return;Ye=2}const gt=ge.drawRange,Tt=ge.attributes.position;let $e=gt.start*Ye,Bt=(gt.start+gt.count)*Ye;Be!==null&&($e=Math.max($e,Be.start*Ye),Bt=Math.min(Bt,(Be.start+Be.count)*Ye)),qe!==null?($e=Math.max($e,0),Bt=Math.min(Bt,qe.count)):Tt!=null&&($e=Math.max($e,0),Bt=Math.min(Bt,Tt.count));const dn=Bt-$e;if(dn<0||dn===1/0)return;Ve.setup(ae,ie,Ie,ge,qe);let rn,Mt=Oe;if(qe!==null&&(rn=Ae.get(qe),Mt=be,Mt.setIndex(rn)),ae.isMesh)ie.wireframe===!0?(M.setLineWidth(ie.wireframeLinewidth*fn()),Mt.setMode(j.LINES)):Mt.setMode(j.TRIANGLES);else if(ae.isLine){let Tn=ie.linewidth;Tn===void 0&&(Tn=1),M.setLineWidth(Tn*fn()),ae.isLineSegments?Mt.setMode(j.LINES):ae.isLineLoop?Mt.setMode(j.LINE_LOOP):Mt.setMode(j.LINE_STRIP)}else ae.isPoints?Mt.setMode(j.POINTS):ae.isSprite&&Mt.setMode(j.TRIANGLES);if(ae.isBatchedMesh)if(Ut.get("WEBGL_multi_draw"))Mt.renderMultiDraw(ae._multiDrawStarts,ae._multiDrawCounts,ae._multiDrawCount);else{const Tn=ae._multiDrawStarts,Ke=ae._multiDrawCounts,Rn=ae._multiDrawCount,Et=qe?Ae.get(qe).bytesPerElement:1,Qn=ce.get(ie).currentProgram.getUniforms();for(let ci=0;ci<Rn;ci++)Qn.setValue(j,"_gl_DrawID",ci),Mt.render(Tn[ci]/Et,Ke[ci])}else if(ae.isInstancedMesh)Mt.renderInstances($e,dn,ae.count);else if(ge.isInstancedBufferGeometry){const Tn=ge._maxInstanceCount!==void 0?ge._maxInstanceCount:1/0,Ke=Math.min(ge.instanceCount,Tn);Mt.renderInstances($e,dn,Ke)}else Mt.render($e,dn)};function Ra(A,X,ge,ie){J!==null&&A.isNodeMaterial&&J.setObject(ie,A),xt===!0&&rt.setState(A,ge,!1),A.transparent===!0&&A.side===vr&&A.forceSinglePass===!1?(A.side=Oi,A.needsUpdate=!0,Ki(A,X,ie),A.side=Ls,A.needsUpdate=!0,Ki(A,X,ie),A.side=vr):Ki(A,X,ie)}this.compile=function(A,X,ge=null){ge===null&&(ge=A),J!==null&&J.renderStart(A,X,ge),L=Fe.get(ge),L.init(X),T.push(L),ge.traverseVisible(function(ae){ae.isLight&&ae.layers.test(X.layers)&&(L.pushLight(ae),ae.castShadow&&L.pushShadow(ae))}),A!==ge&&A.traverseVisible(function(ae){ae.isLight&&ae.layers.test(X.layers)&&(L.pushLight(ae),ae.castShadow&&L.pushShadow(ae))}),L.setupLights(),J!==null&&J.updateLights(L.state.lightsArray),bt=this.localClippingEnabled,xt=rt.init(this.clippingPlanes,bt),xt===!0&&rt.setGlobalState(this.clippingPlanes,X),J!==null&&lt.render(L.state.shadowsArray,ge,X);const ie=new Set;return A.traverse(function(ae){if(!(ae.isMesh||ae.isPoints||ae.isLine||ae.isSprite))return;const Be=ae.material;if(Be)if(Array.isArray(Be))for(let We=0;We<Be.length;We++){const Ie=Be[We];Ra(Ie,ge,X,ae),ie.add(Ie)}else Ra(Be,ge,X,ae),ie.add(Be)}),L=T.pop(),J!==null&&J.renderEnd(),ie},this.compileAsync=function(A,X,ge=null){const ie=this.compile(A,X,ge);return new Promise(ae=>{function Be(){if(ie.forEach(function(We){const qe=ce.get(We).currentProgram;(qe===void 0||qe.isReady())&&ie.delete(We)}),ie.size===0){ae(A);return}setTimeout(Be,10)}Ut.get("KHR_parallel_shader_compile")!==null?Be():setTimeout(Be,10)})};let da=null;function vi(A){da&&da(A)}function Sn(){Kn.stop()}function In(){Kn.start()}const Kn=new V_;Kn.setAnimationLoop(vi),typeof self<"u"&&Kn.setContext(self),this.setAnimationLoop=function(A){da=A,Je.setAnimationLoop(A),A===null?Kn.stop():Kn.start()},Je.addEventListener("sessionstart",Sn),Je.addEventListener("sessionend",In),this.render=function(A,X){if(X!==void 0&&X.isCamera!==!0){Zt("WebGLRenderer.render: camera is not an instance of THREE.Camera.");return}if(W===!0)return;J!==null&&J.renderStart(A,X);const ge=Je.enabled===!0&&Je.isPresenting===!0,ie=O!==null&&(ee===null||ge)&&O.begin(I,ee);if(A.matrixWorldAutoUpdate===!0&&A.updateMatrixWorld(),X.parent===null&&X.matrixWorldAutoUpdate===!0&&X.updateMatrixWorld(),Je.enabled===!0&&Je.isPresenting===!0&&(O===null||O.isCompositing()===!1)&&(Je.cameraAutoUpdate===!0&&Je.updateCamera(X),X=Je.getCamera()),A.isScene===!0&&A.onBeforeRender(I,A,X,ee),L=Fe.get(A,T.length),L.init(X),L.state.textureUnits=xe.getTextureUnits(),T.push(L),pt.multiplyMatrices(X.projectionMatrix,X.matrixWorldInverse),ut.setFromProjectionMatrix(pt,Va,X.reversedDepth),bt=this.localClippingEnabled,xt=rt.init(this.clippingPlanes,bt),N=He.get(A,z.length),N.init(),z.push(N),Je.enabled===!0&&Je.isPresenting===!0){const We=I.xr.getDepthSensingMesh();We!==null&&Wt(We,X,-1/0,I.sortObjects)}Wt(A,X,0,I.sortObjects),N.finish(),J!==null&&J.updateLights(L.state.lightsArray),I.sortObjects===!0&&N.sort(Re,at),Xt=Je.enabled===!1||Je.isPresenting===!1||Je.hasDepthSensing()===!1,Xt&&dt.addToRenderList(N,A),this.info.render.frame++,this.info.autoReset===!0&&this.info.reset(),xt===!0&&rt.beginShadows();const ae=L.state.shadowsArray;if(lt.render(ae,A,X),xt===!0&&rt.endShadows(),(ie&&O.hasRenderPass())===!1){const We=N.opaque,Ie=N.transmissive;if(L.setupLights(),X.isArrayCamera){const qe=X.cameras;if(Ie.length>0)for(let Ye=0,gt=qe.length;Ye<gt;Ye++){const Tt=qe[Ye];Er(We,Ie,A,Tt)}Xt&&dt.render(A);for(let Ye=0,gt=qe.length;Ye<gt;Ye++){const Tt=qe[Ye];bn(N,A,Tt,Tt.viewport)}}else Ie.length>0&&Er(We,Ie,A,X),Xt&&dt.render(A),bn(N,A,X)}ee!==null&&V===0&&(xe.updateMultisampleRenderTarget(ee),xe.updateRenderTargetMipmap(ee)),ie&&O.end(I),A.isScene===!0&&A.onAfterRender(I,A,X),Ve.resetDefaultState(),oe=-1,fe=null,T.pop(),T.length>0?(L=T[T.length-1],xe.setTextureUnits(L.state.textureUnits),xt===!0&&rt.setGlobalState(I.clippingPlanes,L.state.camera)):L=null,z.pop(),z.length>0?N=z[z.length-1]:N=null,J!==null&&J.renderEnd()};function Wt(A,X,ge,ie){if(A.visible===!1)return;if(A.layers.test(X.layers)){if(A.isGroup)ge=A.renderOrder;else if(A.isLOD)A.autoUpdate===!0&&A.update(X);else if(A.isLightProbeGrid)L.pushLightProbeGrid(A);else if(A.isLight)L.pushLight(A),A.castShadow&&L.pushShadow(A);else if(A.isSprite){if(!A.frustumCulled||A.intersectsFrustum(ut)){ie&&Gt.setFromMatrixPosition(A.matrixWorld).applyMatrix4(pt);const We=ye.update(A),Ie=A.material;Ie.visible&&N.push(A,We,Ie,ge,Gt.z,null,X)}}else if((A.isMesh||A.isLine||A.isPoints)&&(!A.frustumCulled||A.intersectsFrustum(ut))){const We=ye.update(A),Ie=A.material;if(ie&&(A.boundingSphere!==void 0?(A.boundingSphere===null&&A.computeBoundingSphere(),Gt.copy(A.boundingSphere.center)):(We.boundingSphere===null&&We.computeBoundingSphere(),Gt.copy(We.boundingSphere.center)),Gt.applyMatrix4(A.matrixWorld).applyMatrix4(pt)),Array.isArray(Ie)){const qe=We.groups;for(let Ye=0,gt=qe.length;Ye<gt;Ye++){const Tt=qe[Ye],$e=Ie[Tt.materialIndex];$e&&$e.visible&&N.push(A,We,$e,ge,Gt.z,Tt,X)}}else Ie.visible&&N.push(A,We,Ie,ge,Gt.z,null,X)}}const Be=A.children;for(let We=0,Ie=Be.length;We<Ie;We++)Wt(Be[We],X,ge,ie)}function bn(A,X,ge,ie){const{opaque:ae,transmissive:Be,transparent:We}=A;L.setupLightsView(ge),xt===!0&&rt.setGlobalState(I.clippingPlanes,ge),ie&&M.viewport(D.copy(ie)),ae.length>0&&Ua(ae,X,ge),Be.length>0&&Ua(Be,X,ge),We.length>0&&Ua(We,X,ge),M.buffers.depth.setTest(!0),M.buffers.depth.setMask(!0),M.buffers.color.setMask(!0),M.setPolygonOffset(!1)}function Er(A,X,ge,ie){if((ge.isScene===!0?ge.overrideMaterial:null)!==null)return;if(L.state.transmissionRenderTarget[ie.id]===void 0){const $e=Ut.has("EXT_color_buffer_half_float")||Ut.has("EXT_color_buffer_float");L.state.transmissionRenderTarget[ie.id]=new wa(1,1,{generateMipmaps:!0,type:$e?Wa:fa,minFilter:Rs,samples:Math.max(4,P.samples),stencilBuffer:c,resolveDepthBuffer:!1,resolveStencilBuffer:!1,storeMultisampledDepthBuffer:!1,storeMultisampledStencilBuffer:!1,colorSpace:kt.workingColorSpace})}const Be=L.state.transmissionRenderTarget[ie.id],We=ie.viewport||D;Be.setSize(We.z*I.transmissionResolutionScale,We.w*I.transmissionResolutionScale);const Ie=I.getRenderTarget(),qe=I.getActiveCubeFace(),Ye=I.getActiveMipmapLevel();I.setRenderTarget(Be),I.getClearColor(De),ze=I.getClearAlpha(),ze<1&&I.setClearColor(16777215,.5),I.clear(),Xt&&dt.render(ge);const gt=I.toneMapping;I.toneMapping=ka;const Tt=ie.viewport;if(ie.viewport!==void 0&&(ie.viewport=void 0),L.setupLightsView(ie),xt===!0&&rt.setGlobalState(I.clippingPlanes,ie),Ua(A,ge,ie),xe.updateMultisampleRenderTarget(Be),xe.updateRenderTargetMipmap(Be),Ut.has("WEBGL_multisampled_render_to_texture")===!1){let $e=!1;for(let Bt=0,dn=X.length;Bt<dn;Bt++){const rn=X[Bt],{object:Mt,geometry:Tn,material:Ke,group:Rn}=rn;if(Ke.side===vr&&Mt.layers.test(ie.layers)){const Et=Ke.side;Ke.side=Oi,Ke.needsUpdate=!0,qt(Mt,ge,ie,Tn,Ke,Rn),Ke.side=Et,Ke.needsUpdate=!0,$e=!0}}$e===!0&&(xe.updateMultisampleRenderTarget(Be),xe.updateRenderTargetMipmap(Be))}I.setRenderTarget(Ie,qe,Ye),I.setClearColor(De,ze),Tt!==void 0&&(ie.viewport=Tt),I.toneMapping=gt}function Ua(A,X,ge){const ie=X.isScene===!0?X.overrideMaterial:null;for(let ae=0,Be=A.length;ae<Be;ae++){const We=A[ae],{object:Ie,geometry:qe,group:Ye}=We;let gt=We.material;gt.allowOverride===!0&&ie!==null&&(gt=ie),Ie.layers.test(ge.layers)&&qt(Ie,X,ge,qe,gt,Ye)}}function qt(A,X,ge,ie,ae,Be){J!==null&&ae.isNodeMaterial&&J.setObject(A,ae),A.onBeforeRender(I,X,ge,ie,ae,Be),A.modelViewMatrix.multiplyMatrices(ge.matrixWorldInverse,A.matrixWorld),A.normalMatrix.getNormalMatrix(A.modelViewMatrix),ae.onBeforeRender(I,X,ge,ie,A,Be),ae.transparent===!0&&ae.side===vr&&ae.forceSinglePass===!1?(ae.side=Oi,ae.needsUpdate=!0,I.renderBufferDirect(ge,X,ie,ae,A,Be),ae.side=Ls,ae.needsUpdate=!0,I.renderBufferDirect(ge,X,ie,ae,A,Be),ae.side=vr):I.renderBufferDirect(ge,X,ie,ae,A,Be),A.onAfterRender(I,X,ge,ie,ae,Be)}function Ki(A,X,ge){X.isScene!==!0&&(X=vn);const ie=ce.get(A),ae=L.state.lights,Be=L.state.shadowsArray,We=ae.state.version,Ie=Ne.getParameters(A,ae.state,Be,X,ge,L.state.lightProbeGridArray),qe=Ne.getProgramCacheKey(Ie);let Ye=ie.programs;ie.environment=A.isMeshStandardMaterial||A.isMeshLambertMaterial||A.isMeshPhongMaterial?X.environment:null,ie.fog=X.fog;const gt=A.isMeshStandardMaterial||A.isMeshLambertMaterial&&!A.envMap||A.isMeshPhongMaterial&&!A.envMap;ie.envMap=ne.get(A.envMap||ie.environment,gt),ie.envMapRotation=ie.environment!==null&&A.envMap===null?X.environmentRotation:A.envMapRotation,Ye===void 0&&(A.addEventListener("dispose",ti),Ye=new Map,ie.programs=Ye);let Tt=Ye.get(qe);if(Tt!==void 0){if(ie.currentProgram===Tt&&ie.lightsStateVersion===We)return zi(A,Ie),Tt}else Ie.uniforms=Ne.getUniforms(A),J!==null&&A.isNodeMaterial&&J.build(A,ge,Ie),A.onBeforeCompile(Ie,I),Tt=Ne.acquireProgram(Ie,qe),Ye.set(qe,Tt),ie.uniforms=Ie.uniforms;const $e=ie.uniforms;return(!A.isShaderMaterial&&!A.isRawShaderMaterial||A.clipping===!0)&&($e.clippingPlanes=rt.uniform),zi(A,Ie),ie.needsLights=Da(A),ie.lightsStateVersion=We,ie.needsLights&&($e.ambientLightColor.value=ae.state.ambient,$e.lightProbe.value=ae.state.probe,$e.sunLights.value=ae.state.sun,$e.sunLightShadows.value=ae.state.sunShadow,$e.directionalLights.value=ae.state.directional,$e.directionalLightShadows.value=ae.state.directionalShadow,$e.spotLights.value=ae.state.spot,$e.spotLightShadows.value=ae.state.spotShadow,$e.rectAreaLights.value=ae.state.rectArea,$e.ltc_1.value=ae.state.rectAreaLTC1,$e.ltc_2.value=ae.state.rectAreaLTC2,$e.pointLights.value=ae.state.point,$e.pointLightShadows.value=ae.state.pointShadow,$e.hemisphereLights.value=ae.state.hemi,$e.sunShadowMatrix.value=ae.state.sunShadowMatrix,$e.sunShadowCascade.value=ae.state.sunShadowCascade,$e.directionalShadowMatrix.value=ae.state.directionalShadowMatrix,$e.spotLightMatrix.value=ae.state.spotLightMatrix,$e.spotLightMap.value=ae.state.spotLightMap,$e.pointShadowMatrix.value=ae.state.pointShadowMatrix),ie.lightProbeGrid=L.state.lightProbeGridArray.length>0,ie.currentProgram=Tt,ie.uniformsList=null,Tt}function Pi(A){if(A.uniformsList===null){const X=A.currentProgram.getUniforms();A.uniformsList=Fu.seqWithValue(X.seq,A.uniforms)}return A.uniformsList}function zi(A,X){const ge=ce.get(A);ge.outputColorSpace=X.outputColorSpace,ge.batching=X.batching,ge.batchingColor=X.batchingColor,ge.instancing=X.instancing,ge.instancingColor=X.instancingColor,ge.instancingMorph=X.instancingMorph,ge.skinning=X.skinning,ge.morphTargets=X.morphTargets,ge.morphNormals=X.morphNormals,ge.morphColors=X.morphColors,ge.morphTargetsCount=X.morphTargetsCount,ge.numClippingPlanes=X.numClippingPlanes,ge.numIntersection=X.numClipIntersection,ge.vertexAlphas=X.vertexAlphas,ge.vertexTangents=X.vertexTangents,ge.toneMapping=X.toneMapping}function ha(A,X){if(A.length===0)return null;if(A.length===1)return A[0].texture!==null?A[0]:null;w.setFromMatrixPosition(X.matrixWorld);for(let ge=0,ie=A.length;ge<ie;ge++){const ae=A[ge];if(ae.texture!==null&&ae.boundingBox.containsPoint(w))return ae}return null}function pa(A,X,ge,ie,ae){X.isScene!==!0&&(X=vn),xe.resetTextureUnits();const Be=X.fog,We=ie.isMeshStandardMaterial||ie.isMeshLambertMaterial||ie.isMeshPhongMaterial?X.environment:null,Ie=ee===null?I.outputColorSpace:ee.isXRRenderTarget===!0?ee.texture.colorSpace:kt.workingColorSpace,qe=ie.isMeshStandardMaterial||ie.isMeshLambertMaterial&&!ie.envMap||ie.isMeshPhongMaterial&&!ie.envMap,Ye=ne.get(ie.envMap||We,qe),gt=ie.vertexColors===!0&&!!ge.attributes.color&&ge.attributes.color.itemSize===4,Tt=!!ge.attributes.tangent&&(!!ie.normalMap||ie.anisotropy>0),$e=!!ge.morphAttributes.position,Bt=!!ge.morphAttributes.normal,dn=!!ge.morphAttributes.color;let rn=ka;ie.toneMapped&&(ee===null||ee.isXRRenderTarget===!0)&&(rn=I.toneMapping);const Mt=ge.morphAttributes.position||ge.morphAttributes.normal||ge.morphAttributes.color,Tn=Mt!==void 0?Mt.length:0,Ke=ce.get(ie),Rn=L.state.lights;if(xt===!0&&(bt===!0||A!==fe)){const en=A===fe&&ie.id===oe;rt.setState(ie,A,en)}let Et=!1;ie.version===Ke.__version?(Ke.needsLights&&Ke.lightsStateVersion!==Rn.state.version||Ke.outputColorSpace!==Ie||ae.isBatchedMesh&&Ke.batching===!1||!ae.isBatchedMesh&&Ke.batching===!0||ae.isBatchedMesh&&Ke.batchingColor===!0&&ae._colorsTexture===null||ae.isBatchedMesh&&Ke.batchingColor===!1&&ae._colorsTexture!==null||ae.isInstancedMesh&&Ke.instancing===!1||!ae.isInstancedMesh&&Ke.instancing===!0||ae.isSkinnedMesh&&Ke.skinning===!1||!ae.isSkinnedMesh&&Ke.skinning===!0||ae.isInstancedMesh&&Ke.instancingColor===!0&&ae.instanceColor===null||ae.isInstancedMesh&&Ke.instancingColor===!1&&ae.instanceColor!==null||ae.isInstancedMesh&&Ke.instancingMorph===!0&&ae.morphTexture===null||ae.isInstancedMesh&&Ke.instancingMorph===!1&&ae.morphTexture!==null||Ke.envMap!==Ye||ie.fog===!0&&Ke.fog!==Be||Ke.numClippingPlanes!==void 0&&(Ke.numClippingPlanes!==rt.numPlanes||Ke.numIntersection!==rt.numIntersection)||Ke.vertexAlphas!==gt||Ke.vertexTangents!==Tt||Ke.morphTargets!==$e||Ke.morphNormals!==Bt||Ke.morphColors!==dn||Ke.toneMapping!==rn||Ke.morphTargetsCount!==Tn||!!Ke.lightProbeGrid!=L.state.lightProbeGridArray.length>0)&&(Et=!0):(Et=!0,Ke.__version=ie.version);let Qn=Ke.currentProgram;Et===!0&&(Qn=Ki(ie,X,ae),J&&ie.isNodeMaterial&&J.onUpdateProgram(ie,Qn,Ke));let ci=!1,ni=!1,Qi=!1;const jt=Qn.getUniforms(),gn=Ke.uniforms;if(M.useProgram(Qn.program)&&(ci=!0,ni=!0,Qi=!0),ie.id!==oe&&(oe=ie.id,ni=!0),Ke.needsLights){const en=ha(L.state.lightProbeGridArray,ae);Ke.lightProbeGrid!==en&&(Ke.lightProbeGrid=en,ni=!0)}if(ci||fe!==A){M.buffers.depth.getReversed()&&A.reversedDepth!==!0&&(A._reversedDepth=!0,A.updateProjectionMatrix()),jt.setValue(j,"projectionMatrix",A.projectionMatrix),jt.setValue(j,"viewMatrix",A.matrixWorldInverse);const Ji=jt.map.cameraPosition;Ji!==void 0&&Ji.setValue(j,vt.setFromMatrixPosition(A.matrixWorld)),P.logarithmicDepthBuffer&&jt.setValue(j,"logDepthBufFC",2/(Math.log(A.far+1)/Math.LN2)),(ie.isMeshPhongMaterial||ie.isMeshToonMaterial||ie.isMeshLambertMaterial||ie.isMeshBasicMaterial||ie.isMeshStandardMaterial||ie.isShaderMaterial)&&jt.setValue(j,"isOrthographic",A.isOrthographicCamera===!0),fe!==A&&(fe=A,ni=!0,Qi=!0)}if(Ke.needsLights&&(Rn.state.sunShadowMap.length>0&&jt.setValue(j,"sunShadowMap",Rn.state.sunShadowMap,xe),Rn.state.directionalShadowMap.length>0&&jt.setValue(j,"directionalShadowMap",Rn.state.directionalShadowMap,xe),Rn.state.spotShadowMap.length>0&&jt.setValue(j,"spotShadowMap",Rn.state.spotShadowMap,xe),Rn.state.pointShadowMap.length>0&&jt.setValue(j,"pointShadowMap",Rn.state.pointShadowMap,xe)),ae.isSkinnedMesh){jt.setOptional(j,ae,"bindMatrix"),jt.setOptional(j,ae,"bindMatrixInverse");const en=ae.skeleton;en&&(en.boneTexture===null&&en.computeBoneTexture(),jt.setValue(j,"boneTexture",en.boneTexture,xe))}ae.isBatchedMesh&&(jt.setOptional(j,ae,"batchingTexture"),jt.setValue(j,"batchingTexture",ae._matricesTexture,xe),jt.setOptional(j,ae,"batchingIdTexture"),jt.setValue(j,"batchingIdTexture",ae._indirectTexture,xe),jt.setOptional(j,ae,"batchingColorTexture"),ae._colorsTexture!==null&&jt.setValue(j,"batchingColorTexture",ae._colorsTexture,xe));const Ai=ge.morphAttributes;if((Ai.position!==void 0||Ai.normal!==void 0||Ai.color!==void 0)&&q.update(ae,ge,Qn),(ni||Ke.receiveShadow!==ae.receiveShadow)&&(Ke.receiveShadow=ae.receiveShadow,jt.setValue(j,"receiveShadow",ae.receiveShadow)),(ie.isMeshStandardMaterial||ie.isMeshLambertMaterial||ie.isMeshPhongMaterial)&&ie.envMap===null&&X.environment!==null&&(gn.envMapIntensity.value=X.environmentIntensity),gn.dfgLUT!==void 0&&(gn.dfgLUT.value=Tw()),ni){if(jt.setValue(j,"toneMappingExposure",I.toneMappingExposure),Ke.needsLights&&sn(gn,Qi),Be&&ie.fog===!0&&Ze.refreshFogUniforms(gn,Be),Ze.refreshMaterialUniforms(gn,ie,Se,ue,L.state.transmissionRenderTarget[A.id]),Ke.needsLights&&Ke.lightProbeGrid){const en=Ke.lightProbeGrid;gn.probesSH.value=en.texture,gn.probesMin.value.copy(en.boundingBox.min),gn.probesMax.value.copy(en.boundingBox.max),gn.probesResolution.value.copy(en.resolution)}Fu.upload(j,Pi(Ke),gn,xe)}if(ie.isShaderMaterial&&ie.uniformsNeedUpdate===!0&&(Fu.upload(j,Pi(Ke),gn,xe),ie.uniformsNeedUpdate=!1),ie.isSpriteMaterial&&jt.setValue(j,"center",ae.center),jt.setValue(j,"modelViewMatrix",ae.modelViewMatrix),jt.setValue(j,"normalMatrix",ae.normalMatrix),jt.setValue(j,"modelMatrix",ae.matrixWorld),ie.uniformsGroups!==void 0){const en=ie.uniformsGroups;for(let Ji=0,Fi=en.length;Ji<Fi;Ji++){const yi=en[Ji];we.update(yi,Qn),we.bind(yi,Qn)}}return Qn}function sn(A,X){A.ambientLightColor.needsUpdate=X,A.lightProbe.needsUpdate=X,A.sunLights.needsUpdate=X,A.sunLightShadows.needsUpdate=X,A.directionalLights.needsUpdate=X,A.directionalLightShadows.needsUpdate=X,A.pointLights.needsUpdate=X,A.pointLightShadows.needsUpdate=X,A.spotLights.needsUpdate=X,A.spotLightShadows.needsUpdate=X,A.rectAreaLights.needsUpdate=X,A.hemisphereLights.needsUpdate=X}function Da(A){return A.isMeshLambertMaterial||A.isMeshToonMaterial||A.isMeshPhongMaterial||A.isMeshStandardMaterial||A.isShadowMaterial||A.isShaderMaterial&&A.lights===!0}this.getActiveCubeFace=function(){return B},this.getActiveMipmapLevel=function(){return V},this.getRenderTarget=function(){return ee},this.setRenderTargetTextures=function(A,X,ge){const ie=ce.get(A);ie.__autoAllocateDepthBuffer=A.resolveDepthBuffer===!1,ie.__autoAllocateDepthBuffer===!1&&(ie.__useRenderToTexture=!1),ce.get(A.texture).__webglTexture=X,ce.get(A.depthTexture).__webglTexture=ie.__autoAllocateDepthBuffer?void 0:ge,ie.__hasExternalTextures=!0},this.setRenderTargetFramebuffer=function(A,X){const ge=ce.get(A);ge.__webglFramebuffer=X,ge.__useDefaultFramebuffer=X===void 0},this.setRenderTarget=function(A,X=0,ge=0){ee=A,B=X,V=ge;let ie=null,ae=!1,Be=!1;if(A){const Ie=ce.get(A);if(Ie.__useDefaultFramebuffer!==void 0){M.bindFramebuffer(j.FRAMEBUFFER,Ie.__webglFramebuffer),D.copy(A.viewport),se.copy(A.scissor),_e=A.scissorTest,M.viewport(D),M.scissor(se),M.setScissorTest(_e),oe=-1;return}else if(Ie.__webglFramebuffer===void 0)xe.setupRenderTarget(A);else if(Ie.__hasExternalTextures)xe.rebindTextures(A,ce.get(A.texture).__webglTexture,ce.get(A.depthTexture).__webglTexture);else if(A.depthBuffer){const gt=A.depthTexture;if(Ie.__boundDepthTexture!==gt){if(gt!==null&&ce.has(gt)&&(A.width!==gt.image.width||A.height!==gt.image.height))throw new Error("THREE.WebGLRenderer: Attached DepthTexture is initialized to the incorrect size.");xe.setupDepthRenderbuffer(A)}}const qe=A.texture;(qe.isData3DTexture||qe.isDataArrayTexture||qe.isCompressedArrayTexture)&&(Be=!0);const Ye=ce.get(A).__webglFramebuffer;A.isWebGLCubeRenderTarget?(Array.isArray(Ye[X])?ie=Ye[X][ge]:ie=Ye[X],ae=!0):A.samples>0&&xe.useMultisampledRTT(A)===!1?ie=ce.get(A).__webglMultisampledFramebuffer:Array.isArray(Ye)?ie=Ye[ge]:ie=Ye,D.copy(A.viewport),se.copy(A.scissor),_e=A.scissorTest}else D.copy(Ge).multiplyScalar(Se).floor(),se.copy(mt).multiplyScalar(Se).floor(),_e=un;if(ge!==0&&(ie=re),M.bindFramebuffer(j.FRAMEBUFFER,ie)&&M.drawBuffers(A,ie),M.viewport(D),M.scissor(se),M.setScissorTest(_e),ae){const Ie=ce.get(A.texture);j.framebufferTexture2D(j.FRAMEBUFFER,j.COLOR_ATTACHMENT0,j.TEXTURE_CUBE_MAP_POSITIVE_X+X,Ie.__webglTexture,ge)}else if(Be){const Ie=X;for(let qe=0;qe<A.textures.length;qe++){const Ye=ce.get(A.textures[qe]);j.framebufferTextureLayer(j.FRAMEBUFFER,j.COLOR_ATTACHMENT0+qe,Ye.__webglTexture,ge,Ie)}}else if(A!==null&&ge!==0){const Ie=ce.get(A.texture);j.framebufferTexture2D(j.FRAMEBUFFER,j.COLOR_ATTACHMENT0,j.TEXTURE_2D,Ie.__webglTexture,ge)}oe=-1};function _i(A){const X=ce.get(A);return(X.__readFormat!==A.format||X.__readType!==A.type)&&(X.__readFormat=A.format,X.__readType=A.type,X.__formatReadable=P.textureFormatReadable(A.format),X.__typeReadable=P.textureTypeReadable(A.type)),X}this.readRenderTargetPixels=function(A,X,ge,ie,ae,Be,We,Ie=0){if(!(A&&A.isWebGLRenderTarget)){Zt("WebGLRenderer.readRenderTargetPixels: renderTarget is not THREE.WebGLRenderTarget.");return}let qe=ce.get(A).__webglFramebuffer;if(A.isWebGLCubeRenderTarget&&We!==void 0&&(qe=qe[We]),qe){M.bindFramebuffer(j.FRAMEBUFFER,qe);try{const Ye=A.textures[Ie],gt=Ye.format,Tt=Ye.type;A.textures.length>1&&j.readBuffer(j.COLOR_ATTACHMENT0+Ie);const $e=_i(Ye);if($e.__formatReadable===!1){Zt("WebGLRenderer.readRenderTargetPixels: renderTarget is not in RGBA or implementation defined format.");return}if($e.__typeReadable===!1){Zt("WebGLRenderer.readRenderTargetPixels: renderTarget is not in UnsignedByteType or implementation defined type.");return}X>=0&&X<=A.width-ie&&ge>=0&&ge<=A.height-ae&&j.readPixels(X,ge,ie,ae,Pe.convert(gt),Pe.convert(Tt),Be)}finally{const Ye=ee!==null?ce.get(ee).__webglFramebuffer:null;M.bindFramebuffer(j.FRAMEBUFFER,Ye)}}},this.readRenderTargetPixelsAsync=async function(A,X,ge,ie,ae,Be,We,Ie=0){if(!(A&&A.isWebGLRenderTarget))throw new Error("THREE.WebGLRenderer.readRenderTargetPixels: renderTarget is not THREE.WebGLRenderTarget.");let qe=ce.get(A).__webglFramebuffer;if(A.isWebGLCubeRenderTarget&&We!==void 0&&(qe=qe[We]),qe)if(X>=0&&X<=A.width-ie&&ge>=0&&ge<=A.height-ae){M.bindFramebuffer(j.FRAMEBUFFER,qe);const Ye=A.textures[Ie],gt=Ye.format,Tt=Ye.type;A.textures.length>1&&j.readBuffer(j.COLOR_ATTACHMENT0+Ie);const $e=_i(Ye);if($e.__formatReadable===!1)throw new Error("THREE.WebGLRenderer.readRenderTargetPixelsAsync: renderTarget is not in RGBA or implementation defined format.");if($e.__typeReadable===!1)throw new Error("THREE.WebGLRenderer.readRenderTargetPixelsAsync: renderTarget is not in UnsignedByteType or implementation defined type.");const Bt=j.createBuffer();j.bindBuffer(j.PIXEL_PACK_BUFFER,Bt),j.bufferData(j.PIXEL_PACK_BUFFER,Be.byteLength,j.STREAM_READ),j.readPixels(X,ge,ie,ae,Pe.convert(gt),Pe.convert(Tt),0),j.bindBuffer(j.PIXEL_PACK_BUFFER,null);const dn=ee!==null?ce.get(ee).__webglFramebuffer:null;M.bindFramebuffer(j.FRAMEBUFFER,dn);const rn=j.fenceSync(j.SYNC_GPU_COMMANDS_COMPLETE,0);return j.flush(),await Sb(j,rn,4),j.bindBuffer(j.PIXEL_PACK_BUFFER,Bt),j.getBufferSubData(j.PIXEL_PACK_BUFFER,0,Be),j.bindBuffer(j.PIXEL_PACK_BUFFER,null),j.deleteBuffer(Bt),j.deleteSync(rn),Be}else throw new Error("THREE.WebGLRenderer.readRenderTargetPixelsAsync: requested read bounds are out of range.")},this.copyFramebufferToTexture=function(A,X=null,ge=0){const ie=Math.pow(2,-ge),ae=Math.floor(A.image.width*ie),Be=Math.floor(A.image.height*ie),We=X!==null?X.x:0,Ie=X!==null?X.y:0;xe.setTexture2D(A,0),j.copyTexSubImage2D(j.TEXTURE_2D,ge,0,0,We,Ie,ae,Be),M.unbindTexture()},this.copyTextureToTexture=function(A,X,ge=null,ie=null,ae=0,Be=0){let We,Ie,qe,Ye,gt,Tt,$e,Bt,dn;const rn=A.isCompressedTexture?A.mipmaps[Be]:A.image;if(ge!==null)We=ge.max.x-ge.min.x,Ie=ge.max.y-ge.min.y,qe=ge.isBox3?ge.max.z-ge.min.z:1,Ye=ge.min.x,gt=ge.min.y,Tt=ge.isBox3?ge.min.z:0;else{const gn=Math.pow(2,-ae);We=Math.floor(rn.width*gn),Ie=Math.floor(rn.height*gn),A.isDataArrayTexture?qe=rn.depth:A.isData3DTexture?qe=Math.floor(rn.depth*gn):qe=1,Ye=0,gt=0,Tt=0}ie!==null?($e=ie.x,Bt=ie.y,dn=ie.z):($e=0,Bt=0,dn=0);const Mt=Pe.convert(X.format),Tn=Pe.convert(X.type);let Ke;X.isData3DTexture?(xe.setTexture3D(X,0),Ke=j.TEXTURE_3D):X.isDataArrayTexture||X.isCompressedArrayTexture?(xe.setTexture2DArray(X,0),Ke=j.TEXTURE_2D_ARRAY):(xe.setTexture2D(X,0),Ke=j.TEXTURE_2D),M.activeTexture(j.TEXTURE0),M.pixelStorei(j.UNPACK_FLIP_Y_WEBGL,X.flipY),M.pixelStorei(j.UNPACK_PREMULTIPLY_ALPHA_WEBGL,X.premultiplyAlpha),M.pixelStorei(j.UNPACK_ALIGNMENT,X.unpackAlignment);const Rn=M.getParameter(j.UNPACK_ROW_LENGTH),Et=M.getParameter(j.UNPACK_IMAGE_HEIGHT),Qn=M.getParameter(j.UNPACK_SKIP_PIXELS),ci=M.getParameter(j.UNPACK_SKIP_ROWS),ni=M.getParameter(j.UNPACK_SKIP_IMAGES);M.pixelStorei(j.UNPACK_ROW_LENGTH,rn.width),M.pixelStorei(j.UNPACK_IMAGE_HEIGHT,rn.height),M.pixelStorei(j.UNPACK_SKIP_PIXELS,Ye),M.pixelStorei(j.UNPACK_SKIP_ROWS,gt),M.pixelStorei(j.UNPACK_SKIP_IMAGES,Tt);const Qi=A.isDataArrayTexture||A.isData3DTexture,jt=X.isDataArrayTexture||X.isData3DTexture;if(A.isDepthTexture){const gn=ce.get(A),Ai=ce.get(X),en=ce.get(gn.__renderTarget),Ji=ce.get(Ai.__renderTarget);M.bindFramebuffer(j.READ_FRAMEBUFFER,en.__webglFramebuffer),M.bindFramebuffer(j.DRAW_FRAMEBUFFER,Ji.__webglFramebuffer);for(let Fi=0;Fi<qe;Fi++)Qi&&(j.framebufferTextureLayer(j.READ_FRAMEBUFFER,j.COLOR_ATTACHMENT0,ce.get(A).__webglTexture,ae,Tt+Fi),j.framebufferTextureLayer(j.DRAW_FRAMEBUFFER,j.COLOR_ATTACHMENT0,ce.get(X).__webglTexture,Be,dn+Fi)),j.blitFramebuffer(Ye,gt,We,Ie,$e,Bt,We,Ie,j.DEPTH_BUFFER_BIT,j.NEAREST);M.bindFramebuffer(j.READ_FRAMEBUFFER,null),M.bindFramebuffer(j.DRAW_FRAMEBUFFER,null)}else if(ae!==0||A.isRenderTargetTexture||ce.has(A)){const gn=ce.get(A),Ai=ce.get(X);M.bindFramebuffer(j.READ_FRAMEBUFFER,k),M.bindFramebuffer(j.DRAW_FRAMEBUFFER,K);for(let en=0;en<qe;en++)Qi?j.framebufferTextureLayer(j.READ_FRAMEBUFFER,j.COLOR_ATTACHMENT0,gn.__webglTexture,ae,Tt+en):j.framebufferTexture2D(j.READ_FRAMEBUFFER,j.COLOR_ATTACHMENT0,j.TEXTURE_2D,gn.__webglTexture,ae),jt?j.framebufferTextureLayer(j.DRAW_FRAMEBUFFER,j.COLOR_ATTACHMENT0,Ai.__webglTexture,Be,dn+en):j.framebufferTexture2D(j.DRAW_FRAMEBUFFER,j.COLOR_ATTACHMENT0,j.TEXTURE_2D,Ai.__webglTexture,Be),ae!==0?j.blitFramebuffer(Ye,gt,We,Ie,$e,Bt,We,Ie,j.COLOR_BUFFER_BIT,j.NEAREST):jt?j.copyTexSubImage3D(Ke,Be,$e,Bt,dn+en,Ye,gt,We,Ie):j.copyTexSubImage2D(Ke,Be,$e,Bt,Ye,gt,We,Ie);M.bindFramebuffer(j.READ_FRAMEBUFFER,null),M.bindFramebuffer(j.DRAW_FRAMEBUFFER,null)}else jt?A.isDataTexture||A.isData3DTexture?j.texSubImage3D(Ke,Be,$e,Bt,dn,We,Ie,qe,Mt,Tn,rn.data):X.isCompressedArrayTexture?j.compressedTexSubImage3D(Ke,Be,$e,Bt,dn,We,Ie,qe,Mt,rn.data):j.texSubImage3D(Ke,Be,$e,Bt,dn,We,Ie,qe,Mt,Tn,rn):A.isDataTexture?j.texSubImage2D(j.TEXTURE_2D,Be,$e,Bt,We,Ie,Mt,Tn,rn.data):A.isCompressedTexture?j.compressedTexSubImage2D(j.TEXTURE_2D,Be,$e,Bt,rn.width,rn.height,Mt,rn.data):j.texSubImage2D(j.TEXTURE_2D,Be,$e,Bt,We,Ie,Mt,Tn,rn);M.pixelStorei(j.UNPACK_ROW_LENGTH,Rn),M.pixelStorei(j.UNPACK_IMAGE_HEIGHT,Et),M.pixelStorei(j.UNPACK_SKIP_PIXELS,Qn),M.pixelStorei(j.UNPACK_SKIP_ROWS,ci),M.pixelStorei(j.UNPACK_SKIP_IMAGES,ni),Be===0&&X.generateMipmaps&&j.generateMipmap(Ke),M.unbindTexture()},this.initRenderTarget=function(A){ce.get(A).__webglFramebuffer===void 0&&xe.setupRenderTarget(A)},this.initTexture=function(A){A.isCubeTexture?xe.setTextureCube(A,0):A.isData3DTexture?xe.setTexture3D(A,0):A.isDataArrayTexture||A.isCompressedArrayTexture?xe.setTexture2DArray(A,0):xe.setTexture2D(A,0),M.unbindTexture()},this.resetState=function(){B=0,V=0,ee=null,M.reset(),Ve.reset()},typeof __THREE_DEVTOOLS__<"u"&&__THREE_DEVTOOLS__.dispatchEvent(new CustomEvent("observe",{detail:this}))}get coordinateSystem(){return Va}get outputColorSpace(){return this._outputColorSpace}set outputColorSpace(e){this._outputColorSpace=e;const i=this.getContext();i.drawingBufferColorSpace=kt._getDrawingBufferColorSpace(e),i.unpackColorSpace=kt._getUnpackColorSpace()}}const $v=[{key:"short",label:"สั้น",timeframe:"M15–H1",ring:"วงใน"},{key:"medium",label:"กลาง",timeframe:"H1–D1",ring:"วงกลาง"},{key:"long",label:"ยาว",timeframe:"D1–W1",ring:"วงนอก"}],e_={AUD:"AUSTRALIAN DOLLAR",CAD:"CANADIAN DOLLAR",CHF:"SWISS FRANC",EUR:"EURO",GBP:"BRITISH POUND",JPY:"JAPANESE YEN",NZD:"NEW ZEALAND DOLLAR",USD:"US DOLLAR"},Aw=["AUDCAD","AUDCHF","AUDJPY","AUDNZD","AUDUSD","CADCHF","CADJPY","CHFJPY","EURAUD","EURCAD","EURCHF","EURGBP","EURJPY","EURNZD","EURUSD","GBPAUD","GBPCAD","GBPCHF","GBPJPY","GBPNZD","GBPUSD","NZDCAD","NZDCHF","NZDJPY","NZDUSD","USDCAD","USDCHF","USDJPY"],ww=["EUR","GBP","AUD","NZD","USD","CAD","CHF"],Cw=[...Aw.map(r=>({symbol:r,name:`${e_[r.slice(0,3)]} / ${e_[r.slice(3)]}`,kind:r.includes("USD")?"MAJOR":"CROSS",assetClass:"forex",clusterId:ww.find(e=>r.slice(0,3)===e||r.slice(3)===e)})),{symbol:"XAUUSD",name:"GOLD",kind:"METALS",assetClass:"metals",clusterId:"METALS"},{symbol:"XAGUSD",name:"SILVER",kind:"METALS",assetClass:"metals",clusterId:"METALS"},{symbol:"WTI",name:"WEST TEXAS INTERMEDIATE",kind:"OIL",assetClass:"oil",clusterId:"OIL"},{symbol:"BRENT",name:"BRENT CRUDE OIL",kind:"OIL",assetClass:"oil",clusterId:"OIL"}],Rw=new Set(["AUDNZD:long","CADCHF:short","EURCHF:medium","GBPCHF:long","NZDCAD:medium"]);function Q_(r){let e=2166136261;for(const i of r)e=Math.imul(e^i.charCodeAt(0),16777619);return e>>>0}function Uw(r){let e=r>>>0;return()=>{e=e+1831565813>>>0;let i=Math.imul(e^e>>>15,1|e);return i^=i+Math.imul(i^i>>>7,61|i),((i^i>>>14)>>>0)/4294967296}}function Dw(r,e,i){if(i==="unknown")return[];const s=Uw(Q_(`${r}:${e}:${i}`)),l=s()*Math.PI*2,c=2+Math.floor(s()*3),f=i==="up"?9:i==="down"?-9:0,h=i==="range"?1.25:.9;return Array.from({length:70},(m,p)=>{const g=p/69,v=Math.sin(Math.PI*g),x=Math.sin(g*Math.PI*2*c+l),_=(s()-.5)*.45;return Number((100+f*g+(x*h+_)*v).toFixed(4))})}const yr=Cw.map(r=>{const{symbol:e}=r,i=$v.map(({key:s})=>Rw.has(`${e}:${s}`)?"unknown":["up","range","down"][Q_(`${e}:${s}`)%3]);return e==="EURUSD"&&i.splice(0,3,"up","range","down"),e==="XAUUSD"&&i.splice(0,3,"up","range","up"),{...r,states:i,series:$v.map(({key:s},l)=>Dw(e,s,i[l]))}}),Nw=[{id:"EUR",label:"EUR",assetClass:"forex",color:"#56d9ed"},{id:"GBP",label:"GBP",assetClass:"forex",color:"#dc91db"},{id:"AUD",label:"AUD",assetClass:"forex",color:"#e4bd72"},{id:"NZD",label:"NZD",assetClass:"forex",color:"#67d9d2"},{id:"USD",label:"USD",assetClass:"forex",color:"#71abef"},{id:"CAD",label:"CAD",assetClass:"forex",color:"#a89be0"},{id:"CHF",label:"CHF",assetClass:"forex",color:"#bacbd8"},{id:"METALS",label:"METALS",assetClass:"metals",color:"#e4c46f"},{id:"OIL",label:"OIL",assetClass:"oil",color:"#da9b56"}].map(r=>({...r,count:yr.filter(({clusterId:e})=>e===r.id).length})),Lw=[.5,1,1.8];function Ow(r,e,{playing:i,hidden:s=!1,dragging:l=!1,speed:c=1}){if(!i||s||l)return r;const f=Lw.includes(c)?c:1;return r+Math.max(0,Math.min(.05,Number.isFinite(e)?e:0))*f}function t_(r,e,i,s,l,c){const f=e+l*c,h=r*(1+.075*Math.sin(l*.32+s));return[Math.cos(f)*h,Math.sin(f)*h*i,.14+Math.sin(f*2+s)*.18]}function Pw(r,e,i,{rate:s=.13,phase:l=0,meteor:c=!1}={}){const f=r.getPoints(180),h=new Bn().setFromPoints(f);h.setAttribute("aProgress",new Cn(f.map((p,g)=>g/180),1));const m=new Yn({transparent:!0,depthWrite:!1,blending:Aa,uniforms:{time:i,tint:{value:new wt(e)},rate:{value:s},phase:{value:l},pixelScale:{value:1},meteor:{value:c?1:0}},vertexShader:`attribute float aProgress; uniform float time; uniform float rate;
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
      }`,fragmentShader:`uniform vec3 tint; varying float vLight; varying float vHead;
      void main() {
        float r = length(gl_PointCoord - 0.5) * 2.0;
        if (r > 1.0 || vLight < 0.008) discard;
        gl_FragColor = vec4(mix(tint, vec3(0.9, 0.97, 1.0), vHead * 0.8), pow(1.0-r, 1.6) * vLight);
        #include <tonemapping_fragment>
        #include <colorspace_fragment>
      }`});return new Ds(h,m)}const zw={unavailable:"#65656b"},J_=Math.PI*2;function Vh(r,e,i){const s=Math.max(0,Math.min(1,i));return`#${[1,3,5].map(c=>{const f=Number.parseInt(r.slice(c,c+2),16),h=Number.parseInt(e.slice(c,c+2),16);return Math.round(f+(h-f)*s).toString(16).padStart(2,"0")}).join("")}`}const Fw=["#8c9bb5","#7fbaa4","#3fc991","#13d976","#05b85c","#009e4c"],Bw=["#8c9bb5","#ba8e99","#db6678","#cf1732","#ad1028","#940b20"];function tf(r){const e=(r==null?void 0:r.long)+(r==null?void 0:r.short);if(!((r==null?void 0:r.available)===!0&&Number.isFinite(r.long)&&Number.isFinite(r.short)&&r.long>=0&&r.long<=100&&r.short>=0&&r.short<=100&&e>0&&Math.abs(e-100)<=2))return{available:!1,bias:"unavailable",strength:0,dominance:null,color:zw.unavailable,core:"#74747a",corona:"#65656b",particles:"#77777e",highlight:"#98989f",brightness:.4};const s=r.long/e*100,l=r.long===r.short?"neutral":r.long>r.short?"long":"short",c=Math.abs(s-50)/50,f=Math.min(5,c*5),h=Math.min(4,Math.floor(f)),m=l==="short"?Bw:Fw,p=Vh(m[h],m[h+1],f-h);return{available:!0,bias:l,strength:c,dominance:Math.max(s,100-s),color:p,core:Vh(p,"#ffffff",.09),corona:p,particles:p,highlight:Vh(p,"#ffffff",.25),brightness:.62+c*.38}}function $p(r){return{coreTint:{value:new wt(r.core)},coronaTint:{value:new wt(r.corona)},particleTint:{value:new wt(r.particles)},highlightTint:{value:new wt(r.highlight)},brightness:{value:r.brightness}}}function $_(r=""){let e=2166136261;for(const i of String(r).trim().toUpperCase())e=Math.imul(e^i.charCodeAt(0),16777619);return(e>>>0)/4294967296*J_}function Iw(r){let e=r>>>0;return()=>(e=Math.imul(e,1664525)+1013904223>>>0,e/4294967296)}function n_(r,e=!1){const i=Iw(e?76183:42851),s=[],l=[],c=[];for(let h=0;h<r;h++){const m=i()*J_;if(e){const p=.22+i()*.27;s.push(Math.cos(m)*p,Math.sin(m)*p*.56,(i()-.5)*.09+Math.sin(m*3)*.045)}else{const p=.135+Math.pow(i(),2.1)*.42,g=i()*2-1,v=Math.sqrt(1-g*g);s.push(Math.cos(m)*v*p,Math.sin(m)*v*p,g*p)}l.push((e?.005:.007)+i()*(e?.011:.021)),c.push(i())}const f=new Bn;return f.setAttribute("position",new Cn(s,3)),f.setAttribute("aSize",new Cn(l,1)),f.setAttribute("aSeed",new Cn(c,1)),f.computeBoundingSphere(),f}function ey(){return{core:new Jl(.148,28,20),bead:new Jl(.012,8,6),particles:n_(480),flow:n_(130,!0),filamentMaterials:new Map,glow:new Bn().setAttribute("position",new Cn([0,0,0],3))}}function Hw(r){return new Yn({uniforms:{time:{value:0},phase:{value:0},muted:{value:r.available?0:1},...$p(r)},vertexShader:`uniform float time; uniform float phase; varying vec3 surface; varying vec3 viewNormal; varying vec3 viewPosition;
      void main(){surface=position;
        float wave=sin(position.x*42.0+time*.8+phase)*sin(position.y*38.0-time*.61)*sin(position.z*45.0+time*.43);
        vec3 p=position+normal*(wave*.006); vec4 mv=modelViewMatrix*vec4(p,1.0);
        viewNormal=normalize(normalMatrix*normal);viewPosition=-mv.xyz;gl_Position=projectionMatrix*mv;}`,fragmentShader:`uniform float time;uniform float phase;uniform float muted;uniform float brightness;uniform vec3 coreTint;uniform vec3 coronaTint;uniform vec3 highlightTint;varying vec3 surface;varying vec3 viewNormal;varying vec3 viewPosition;
      void main(){float facing=max(0.0,dot(normalize(viewNormal),normalize(viewPosition)));
        float cells=sin(surface.x*68.0+sin(surface.z*41.0+time*.6))*sin(surface.y*59.0-time*.7+phase);
        float veins=pow(1.0-abs(sin(surface.x*31.0+surface.y*36.0+sin(surface.z*53.0+time*.3))),8.0);
        vec3 tint=mix(coronaTint*.55,coreTint,pow(facing,.8));
        tint=mix(tint,highlightTint,clamp(cells*.10+veins*.22+.08,0.0,.4));
        tint*=.65+brightness*.35;gl_FragColor=vec4(tint,1.0);
        #include <tonemapping_fragment>
        #include <colorspace_fragment>
      }`})}function i_(r,e,i){return new Yn({transparent:!0,depthWrite:!1,blending:Aa,uniforms:{time:{value:0},phase:{value:0},viewportHeight:{value:900},alpha:{value:i},available:{value:r.available?1:0},longFraction:{value:e},...$p(r)},vertexShader:`attribute float aSize;attribute float aSeed;uniform float time;uniform float phase;uniform float viewportHeight;varying float seed;varying float radius;
      void main(){seed=aSeed;radius=length(position);vec3 p=position*(1.0+sin(time*.46+aSeed*15.0+phase)*.045);
        p+=vec3(sin(time*.16+aSeed*22.0),cos(time*.19+aSeed*17.0),sin(time*.13+aSeed*31.0))*.009;
        vec4 mv=modelViewMatrix*vec4(p,1.0);float divisor=projectionMatrix[2][3]<-.5?max(.1,-mv.z):1.0;
        gl_PointSize=clamp(aSize*viewportHeight*projectionMatrix[1][1]/divisor,1.0,26.0);gl_Position=projectionMatrix*mv;}`,fragmentShader:`uniform float time;uniform float alpha;uniform float brightness;uniform vec3 particleTint;uniform vec3 highlightTint;varying float seed;varying float radius;
      void main(){float r=length(gl_PointCoord-.5)*2.0;if(r>1.0)discard;
        vec3 stellar=mix(highlightTint,particleTint,smoothstep(.13,.32,radius));
        float envelope=pow(1.0-r,2.0)*(0.66+.34*sin(seed*31.0+time*.7));gl_FragColor=vec4(stellar,envelope*alpha*(.55+brightness*.45));
        #include <tonemapping_fragment>
        #include <colorspace_fragment>
      }`})}function Gw(r){return new Yn({transparent:!0,depthWrite:!1,blending:Aa,uniforms:{viewportHeight:{value:900},time:{value:0},available:{value:r.available?1:0},...$p(r)},vertexShader:"uniform float viewportHeight;void main(){vec4 mv=modelViewMatrix*vec4(position,1.0);float divisor=projectionMatrix[2][3]<-.5?max(.1,-mv.z):1.0;gl_PointSize=1.26*viewportHeight*projectionMatrix[1][1]/divisor;gl_Position=projectionMatrix*mv;}",fragmentShader:`uniform float time;uniform float brightness;uniform vec3 coronaTint;uniform vec3 coreTint;void main(){vec2 p=(gl_PointCoord-.5)*2.0;float r=length(p);if(r>1.0)discard;
      float angle=atan(p.y,p.x);float wisps=1.0+sin(angle*5.0+time*.12)*.12+sin(angle*9.0-time*.09)*.06;
      float haze=exp(-r*r*12.0)*pow(1.0-r,1.3)*wisps;vec3 color=mix(coronaTint,coreTint,exp(-r*r*36.0));
      gl_FragColor=vec4(color,haze*(.30+brightness*.24));
      #include <tonemapping_fragment>
      #include <colorspace_fragment>
    }`})}function Vw(r,e,i){const s=new Bn;s.setAttribute("position",new Cn(new Float32Array(147),3));const l=r%3?e.corona:e.highlight,c=`${l}:${r%2}`;i.filamentMaterials.has(c)||i.filamentMaterials.set(c,new Zp({color:l,transparent:!0,opacity:(r%2?.12:.2)*e.brightness,depthWrite:!1,blending:Aa}));const f=i.filamentMaterials.get(c),h=new Kp(s,f);return h.rotation.set(r*.93,r*.71,r*1.13),{mesh:h,index:r}}function ty(r,e,i=0){const s=new ua,l=new ua;s.add(l);const c=tf(r),f=c.available,h=f?r.long/(r.long+r.short):.5,m=new ji(e.core,Hw(c)),p=new Ds(e.glow,Gw(c)),g=new Ds(e.particles,i_(c,h,.72)),v=new Ds(e.flow,i_(c,h,.3));v.rotation.x=.65;const x=Array.from({length:6},(R,b)=>Vw(b,c,e)),_=new ji(e.bead,new Ju({color:c.highlight,transparent:!0,opacity:.65,depthWrite:!1,blending:Aa}));_.visible=f,l.add(p,m,g,v,...x.map(R=>R.mesh),_);const E={group:s,plane:l,core:m,glow:p,particles:g,flow:v,filaments:x,bead:_,phase:i,appearance:c,available:f,ringCount:0,segments:[],composition:f?{long:r.long,short:r.short}:null};return em(E,0),E}function ny(r,e){const i=tf(e),s=i.available;r.ownsFilamentMaterials||(r.filaments.forEach(({mesh:c})=>{c.material=c.material.clone()}),r.ownsFilamentMaterials=!0),r.appearance=i,r.available=s,r.composition=s?{long:e.long,short:e.short}:null;const l={coreTint:i.core,coronaTint:i.corona,particleTint:i.particles,highlightTint:i.highlight};for(const c of[r.core,r.glow,r.particles,r.flow]){const f=c.material.uniforms;for(const[h,m]of Object.entries(l))f[h]&&f[h].value.set(m);f.brightness&&(f.brightness.value=i.brightness),f.available&&(f.available.value=s?1:0),f.muted&&(f.muted.value=s?0:1),f.longFraction&&(f.longFraction.value=s?e.long/(e.long+e.short):.5)}r.bead.visible=s,r.bead.material.color.set(i.highlight),r.filaments.forEach(({mesh:c,index:f})=>{c.material.color.set(f%3?i.corona:i.highlight),c.material.opacity=(f%2?.12:.2)*i.brightness})}function em(r,e){const i=Number.isFinite(e)?e:0,s=Number.isFinite(r.phase)?r.phase:0;r.plane.rotation.set(.16+Math.sin(i*.09+s)*.06,i*.055+s,-.16),r.core.rotation.set(i*.047,i*.09+s,0),r.particles.rotation.set(i*.035,i*-.067,i*.045),r.flow.rotation.z=i*.13+s;for(const f of[r.core,r.glow,r.particles,r.flow])f.material.uniforms.time.value=i,f.material.uniforms.phase&&(f.material.uniforms.phase.value=s);for(const{mesh:f,index:h}of r.filaments){const m=f.geometry.attributes.position,p=.12+h*.021;for(let g=0;g<m.count;g++){const v=g/(m.count-1),x=v*Math.PI,_=Math.sin(x),E=Math.sin(v*17+i*.21+s+h)*.009*_;m.setXYZ(g,Math.cos(x)*(.085+h*.004),.09+_*p+E,Math.sin(v*8+h+i*.13)*.025*_)}m.needsUpdate=!0,f.geometry.boundingSphere||(f.geometry.boundingSphere=new Bs(new Q,.4))}const l=i*.35+s,c=.21+Math.sin(i*.17+s)*.025;r.bead.position.set(Math.cos(l)*c,Math.sin(l)*c*.52,Math.sin(l*1.7)*.06)}function iy(r,e){const i=Number.isFinite(e)&&e>0?e:900;for(const s of[r.glow,r.particles,r.flow])s.material.uniforms.viewportHeight.value=i}function ay(r,e){var l;const i=new Set,s=new Set;r.traverse(c=>{c.geometry&&i.add(c.geometry),c.material&&(Array.isArray(c.material)?c.material:[c.material]).forEach(f=>s.add(f))}),e&&(Object.values(e).forEach(c=>{c!=null&&c.isBufferGeometry&&i.add(c)}),(l=e.filamentMaterials)==null||l.forEach(c=>s.add(c))),i.forEach(c=>c.dispose()),s.forEach(c=>c.dispose())}const Ns=new Map(yr.map(r=>[r.symbol,r])),kw=()=>({available:!1,long:null,short:null,avgLong:null,avgShort:null,asOf:null});let Ca={schemaVersion:1,mode:"live",generatedAt:null,connection:"loading",revision:0,sentiment:{source:"Myfxbook",status:"loading",items:[]},correlations:{source:"MT5",status:"loading",items:[]},news:{source:"Forex Factory",status:"loading",events:[],calendarEvents:[]}};const ju=new Set,Xw=r=>(ju.add(r),()=>ju.delete(r)),Ww=()=>Ca,tm=r=>typeof r=="number"&&Number.isFinite(r)&&Math.abs(r)<=1,Uu=r=>typeof r=="number"&&Number.isFinite(r)?r:null,qw=r=>{try{const e=new URL(r);return e.protocol==="https:"&&!e.username&&!e.password?e.href:null}catch{return null}};function Yw(r,e=Date.now(),i=!1){var c;const s=(c=r==null?void 0:r.mirror)==null?void 0:c.publishedAt;if(!i&&!s)return{connection:"online",heartbeatAt:null};const l=typeof s=="string"&&/(Z|[+-]\d{2}:\d{2})$/.test(s)?Date.parse(s):NaN;return{connection:Number.isFinite(l)&&e-l<=12e4&&l-e<=3e4?"online":"stale",heartbeatAt:Number.isFinite(l)?s:null}}function jw(r,{requireHeartbeat:e=!1,now:i=Date.now()}={}){var h,m,p;if((r==null?void 0:r.schemaVersion)!==1||(r==null?void 0:r.mode)!=="live"||!Array.isArray((h=r.sentiment)==null?void 0:h.items)||!Array.isArray((m=r.correlations)==null?void 0:m.items)||!Array.isArray((p=r.news)==null?void 0:p.events))throw new Error("invalid_market_snapshot");const s=r.sentiment.items.filter(g=>Ns.has(g.symbol)).map(g=>{const v=Uu(g.long),x=Uu(g.short),_=g.available===!0&&v!==null&&x!==null&&v>=0&&v<=100&&x>=0&&x<=100&&Math.abs(v+x-100)<=2;return{...g,available:_,long:_?v:null,short:_?x:null,avgLong:Uu(g.avgLong),avgShort:Uu(g.avgShort)}}),l=new Set,c=r.correlations.items.filter(g=>Ns.has(g.source)&&Ns.has(g.target)&&g.source!==g.target).filter(g=>{const v=[g.source,g.target].sort().join("|");return l.has(v)?!1:(l.add(v),!0)}).map(g=>({...g,value:tm(g.value)?g.value:null})),f=g=>Array.isArray(g)?g.filter(v=>v&&typeof v.id=="string"&&typeof v.title=="string"&&!v.mock).map(v=>({...v,currency:String(v.currency||"").toUpperCase(),sourceUrl:qw(v.sourceUrl),forecast:v.forecast??"—",previous:v.previous??"—",actual:v.actual??null,mock:!1})):[];Ca={...r,...Yw(r,i,e),revision:Ca.revision+1,sentiment:{...r.sentiment,items:s},correlations:{...r.correlations,items:c},news:{...r.news,events:f(r.news.events),calendarEvents:f(r.news.calendarEvents)}},ju.forEach(g=>g())}function Zw(){Ca={...Ca,connection:"offline"},ju.forEach(r=>r())}function is(r){return Ca.sentiment.items.find(e=>e.symbol===r)||kw()}function Lp(r){return Ca.correlations.items.filter(e=>tm(e.value)&&(e.source===r||e.target===r)).map(e=>({...e,symbol:e.source===r?e.target:e.source})).sort((e,i)=>Math.abs(i.value)-Math.abs(e.value)||e.symbol.localeCompare(i.symbol))}function Kw(r="all"){return Ca.correlations.items.filter(e=>{var i,s;return tm(e.value)&&(r==="all"||((i=Ns.get(e.source))==null?void 0:i.assetClass)===r&&((s=Ns.get(e.target))==null?void 0:s.assetClass)===r)})}function rs(r=new Date().toISOString()){const e=new Date(r);return Number.isFinite(e.getTime())?new Intl.DateTimeFormat("en-CA",{timeZone:"Asia/Bangkok",year:"numeric",month:"2-digit",day:"2-digit"}).format(e):""}function Qw(r){if(typeof r!="string"||!/(Z|[+-]\d{2}:\d{2})$/.test(r))return"—";const e=new Date(r);return Number.isFinite(e.getTime())?new Intl.DateTimeFormat("en-GB",{timeZone:"Asia/Bangkok",hour:"2-digit",minute:"2-digit",hourCycle:"h23"}).format(e):"—"}function os(r){if(!r)return"ยังไม่มี";const e=new Date(r);return Number.isFinite(e.getTime())?new Intl.DateTimeFormat("th-TH",{timeZone:"Asia/Bangkok",day:"numeric",month:"short",hour:"2-digit",minute:"2-digit",hourCycle:"h23"}).format(e):"ยังไม่มี"}function Op(r){const e=r.timePrecision||r.timeKind;return e==="date"||e==="all_day"?"ทั้งวัน":e==="tentative"?"รอยืนยันเวลา":r.timeLabel||Qw(r.time)}function ry(r,e=rs()){const i=Ca.news.calendarEvents.length?Ca.news.calendarEvents:Ca.news.events,s=Ns.get(r),l=(s==null?void 0:s.assetClass)==="forex"?[r.slice(0,3),r.slice(3)]:["USD"];return i.filter(c=>(c.dayThai||rs(c.time))===e&&(!r||l.includes(c.currency)||c.currency==="ALL")).sort((c,f)=>(c.time||"9999").localeCompare(f.time||"9999")||c.id.localeCompare(f.id))}function Jw(r,e){const i=Ns.get(e);if(!i||i.assetClass!=="forex"||!["activity","employment","unemployment","inflation","confidence","growth","rates","retail"].includes(r.metric)||!Number.isFinite(r.forecastValue)||!r.numeric)return[];const s=r.currency===e.slice(0,3)?1:r.currency===e.slice(3)?-1:0;if(!s)return[];const l=r.metric==="unemployment"?-1:1;return[{key:"below",label:"ต่ำกว่าคาด",delta:-1},{key:"inline",label:"ใกล้เคียงคาด",delta:0},{key:"above",label:"สูงกว่าคาด",delta:1}].map(({delta:c,...f})=>{const h=c*l*s;return{...f,direction:h>0?"up":h<0?"down":"neutral",summary:h>0?`อาจหนุน ${e} ↑`:h<0?`อาจกดดัน ${e} ↓`:"ยังไม่ชี้ทิศ ต้องดูรายละเอียดและข่าวอื่นร่วมด้วย",note:r.metric==="inflation"?"ขึ้นกับการปรับคาดการณ์ดอกเบี้ย ไม่ใช่ผลตายตัว":"ฉากทัศน์พื้นฐานตามเงื่อนไข ไม่ใช่คำแนะนำซื้อขาย"}})}function as(r){const e=r==null?void 0:r.status;return{loading:"กำลังเชื่อมต่อ",ready:"พร้อม",ok:"พร้อม",fresh:"พร้อม",empty:"ไม่มีข่าววันนี้ในปฏิทิน",partial:"ข้อมูลบางส่วน",stale:"ข้อมูลเก่า",error:"เชื่อมต่อไม่สำเร็จ",needs_configuration:"รอเชื่อมบัญชี",auth_error:"ตรวจบัญชีอีกครั้ง",auth_failed:"ตรวจบัญชีอีกครั้ง",authentication_failed:"ตรวจบัญชีอีกครั้ง",rate_limited:"รอรอบโควต้า",provider_unavailable:"แหล่งข้อมูลยังไม่พร้อม",unavailable:"ยังไม่มีข้อมูล",market_closed:"ตลาดปิด",not_covered:"วันที่อยู่นอกช่วงข้อมูล",cached:"ข้อมูลจากรอบล่าสุด"}[e]||e||"ยังไม่มีข้อมูล"}const Bu=20,$w=.7,Iu=.6,nm=.3,sy=.1,oy=.8,gr={brightYellow:"#ffe66d",gold:"#dfb64f",positive:"#66dda0",deepPositive:"#18985b",negative:"#ff9292",deepNegative:"#c9384a",unavailable:"#778593"},nf=r=>Number.isFinite(r)&&Math.abs(r)<=1;function kh(r,e,i){const s=Math.max(0,Math.min(1,i)),l=c=>Math.round(parseInt(r.slice(c,c+2),16)*(1-s)+parseInt(e.slice(c,c+2),16)*s).toString(16).padStart(2,"0");return`#${l(1)}${l(3)}${l(5)}`}function kl(r){return nf(r)?Math.abs(r)<=nm?"neutral":r>0?"positive":"negative":"unavailable"}function pi(r){if(!nf(r))return gr.unavailable;const e=Math.abs(r);if(e<=sy)return gr.brightYellow;if(e<=nm)return kh(gr.brightYellow,gr.gold,(e-.1)/.2);const i=r>0?gr.positive:gr.negative,s=r>0?gr.deepPositive:gr.deepNegative;return e<.4?kh(gr.gold,i,(e-.3)/.1):e<oy?kh(i,s,(e-.4)/.4):s}function a_(r){if(!nf(r))return{strength:null,emphasized:!1,opacity:0};const e=Math.abs(r),i=e>=Iu,s=i?.3+.26*(e-Iu)/(1-Iu):e<=.1?.24:e<=.3?.16+.08*(.3-e)/.2:.16+.03*(e-.3)/.3;return{strength:e,emphasized:i,opacity:s}}function ly(r,e){return!r||!e?null:r.source===e?r.target:r.target===e?r.source:null}function e3(r,e){const i=ly(r,e);return i&&!nf(r.value)?`${i} ไม่มีข้อมูล`:i?`${i} ${r.value>0?"+":""}${Math.round(r.value*100)}%`:""}function Oo(r,e){return[r,e].sort().join("|")}function r_(r,e=()=>[]){const i=[...new Map(r.map(l=>[l.symbol,l])).values()],s=[];for(let l=0;l<i.length;l++){const c=i[l],f=new Map(e(c.symbol).map(h=>[h.symbol,h.value]));for(let h=l+1;h<i.length;h++){const m=i[h],p=f.get(m.symbol);!Number.isFinite(p)||p<-1||p>1||s.push({source:c.symbol,target:m.symbol,value:p,sourceClass:c.assetClass,targetClass:m.assetClass,key:Oo(c.symbol,m.symbol),index:s.length})}}return s}function t3(r,e="all"){return e==="all"?r:r.filter(i=>i.sourceClass===e&&i.targetClass===e)}function n3(r,e){return e?r.filter(i=>i.source===e||i.target===e):[]}function s_(r){return r.filter(e=>Math.abs(e.value)>$w)}function o_(r,e=0){const i=e*.173;return((r*(.12+e%5*.013)+i)%1+1)%1}function i3(r,e,i=0){const s=e.x-r.x,l=e.y-r.y,c=e.z-r.z,f=Math.max(.01,Math.hypot(s,l)),h=Math.min(4.6,Math.hypot(s,l,c)*(.15+i%4*.025)),m=i%2?1:-1;return{x:(r.x+e.x)*.5-l/f*h*m,y:(r.y+e.y)*.5+s/f*h*m,z:(r.z+e.z)*.5+.45+Math.sin(i*1.31)*h*.72}}function l_(r,e,i,s,l={}){const c=Math.max(0,Math.min(1,s)),f=1-c,h=f*f,m=2*f*c,p=c*c;return l.x=h*r.x+m*i.x+p*e.x,l.y=h*r.y+m*i.y+p*e.y,l.z=h*r.z+m*i.z+p*e.z,l}function a3(r,e,i=Bu){return!Number.isInteger(e)||e<0?null:r[Math.floor(e/(i*2))]??null}function cy(r="/",e){return`${String(r).replace(/\/+$/,"")}/assets/${e}`}const r3={CHF:{center:[-9.6,3.7,-.5],radius:1.6,tilt:.95,turn:-.25},EUR:{center:[.6,1.1,.5],radius:3.9,tilt:.92,turn:.18},GBP:{center:[-7.5,-3,.4],radius:2.9,tilt:.98,turn:.08},USD:{center:[-1.1,6.3,-.4],radius:2.9,tilt:.96,turn:-.1},AUD:{center:[11.5,4.8,-.6],radius:3.2,tilt:.93,turn:-.15},CAD:{center:[14.3,-.2,.1],radius:1.8,tilt:.94,turn:.2},NZD:{center:[12.8,-5.2,.3],radius:2.9,tilt:.95,turn:-.15},METALS:{center:[5.2,-10.4,1],radius:2.7,tilt:.98,turn:-.1},OIL:{center:[-1.9,-9.2,.2],radius:2.2,tilt:.98,turn:.04}},c_=new Set(["CHFJPY","EURUSD","EURGBP","GBPUSD","USDJPY","USDCAD","AUDUSD","CADJPY","NZDUSD","XAUUSD","XAGUSD","WTI","BRENT"]),s3={EUR:[-4.8,10.5,.5],GBP:[4.8,10.5,.4],USD:[-4.8,5.2,-.4],AUD:[4.8,5.2,-.6],METALS:[0,0,1],CHF:[-4.1,-4.8,-.5],CAD:[4.8,-5.4,.1],NZD:[-4.8,-10.7,.3],OIL:[4.8,-10.7,.2]},o3={CHF:[-6.2,1,-.5],EUR:[0,6.8,.5],USD:[7.4,6.8,-.4],GBP:[-9.5,-2.7,.4],METALS:[0,0,1],AUD:[7.4,.1,-.6],OIL:[-7.1,-6.8,.2],NZD:[0,-6.8,.3],CAD:[7.4,-6.8,.1]},Bl=Math.PI*2;function l3(r){return()=>(r=r*1664525+1013904223>>>0,r/4294967296)}function c3(r,e,i,s=1,l=48,c={value:0},f=0){const h=new Bn;h.setAttribute("position",new Cn(r,3)),h.setAttribute("color",new Cn(e,3)),h.setAttribute("aSize",new Cn(i,1));const m=new Yn({transparent:!0,depthWrite:!1,blending:Aa,vertexColors:!0,uniforms:{opacity:{value:s},pixelScale:{value:1},maxSize:{value:l},time:c,shear:{value:f}},vertexShader:`attribute float aSize; varying vec3 vColor; varying float vShimmer;
      uniform float pixelScale; uniform float maxSize; uniform float time; uniform float shear;
      void main(){ vColor=color;
      float a=sin(time*0.14)*shear*5.0/(0.8+length(position.xy)*0.55);
      vec3 warped=vec3(mat2(cos(a),sin(a),-sin(a),cos(a))*position.xy,position.z);
      warped.z+=sin(time*0.38+length(position.xy)*2.0)*abs(shear)*2.5;
      vShimmer=0.82+0.18*sin(time*0.9+position.x*4.0+position.y*7.0);
      vec4 p=modelViewMatrix*vec4(warped,1.0);
      gl_PointSize=clamp(aSize*pixelScale*420.0/max(2.0,-p.z),0.65,maxSize);
      gl_Position=projectionMatrix*p; }`,fragmentShader:`varying vec3 vColor; varying float vShimmer; uniform float opacity;
      void main(){ float r=length(gl_PointCoord-0.5)*2.0;
      if(r>1.0) discard; float glow=pow(1.0-r,2.4);
      gl_FragColor=vec4(vColor,glow*opacity*vShimmer);
      #include <tonemapping_fragment>
      #include <colorspace_fragment>
      }`});return new Ds(h,m)}function u3(r,e,i=.2){return new Kp(new Bn().setFromPoints(r),new Zp({color:e,transparent:!0,opacity:i,depthWrite:!1}))}function f3({assetBase:r="/",pairs:e,selectedSymbol:i,axis:s="free",playing:l=!0,reducedMotion:c=!1,motionSpeed:f=1,motionClock:h,filter:m="all",correlationsVisible:p=!0,selectedCorrelation:g=null,resetKey:v=0,focusKey:x=0,dataRevision:_=0,onSelect:E,onCorrelationSelect:R,onReady:b,onError:S}){const F=nt.useRef(null),G=nt.useRef(null),w=nt.useRef(null);return w.current={selectedSymbol:i,axis:s,playing:l,reducedMotion:c,motionSpeed:f,filter:m,correlationsVisible:p,selectedCorrelation:g,dataRevision:_,onSelect:E,onCorrelationSelect:R,onReady:b,onError:S},nt.useEffect(()=>{var Hs,qa,Ya,Wo;const N=F.current;if(!N)return;let L;try{L=new K_({antialias:!0,alpha:!0,powerPreference:"high-performance"})}catch{(qa=(Hs=w.current).onError)==null||qa.call(Hs,"เบราว์เซอร์นี้เปิด WebGL ไม่สำเร็จ กรุณาลอง Chrome หรือ Edge");return}L.setClearColor("#020810",1),L.setPixelRatio(Math.min(window.devicePixelRatio||1,1.6)),L.outputColorSpace=Ei;const z=L.domElement;z.className="orbital-webgl",z.tabIndex=0,z.setAttribute("aria-label","จักรวาล 32 สินทรัพย์ ลากซ้ายเพื่อหมุน ลากขวาเพื่อเลื่อนมุมมอง เลื่อนล้อเพื่อซูม"),z.setAttribute("role","application"),N.appendChild(z);const T=document.createElement("canvas");T.className="orbital-leaders",T.setAttribute("aria-hidden","true"),N.appendChild(T);const O=T.getContext("2d"),I=document.createElement("div");I.className="orbital-label-layer",N.appendChild(I);const W=(le,te)=>{le.addEventListener("pointerdown",Ue=>{Ue.button===0&&(Ue.preventDefault(),Ue.stopPropagation(),le.focus({preventScroll:!0}),te())}),le.addEventListener("click",Ue=>{Ue.detail===0&&te()})},J=(le,te)=>W(le,()=>{var Ce,Qe;const Ue=te();Ue&&((Qe=(Ce=w.current).onSelect)==null||Qe.call(Ce,Ue))}),re=new N_,k=new ua;re.add(k);const K=new Yi(43,1,.1,220);K.position.set(0,0,37),K.lookAt(0,0,0);const B=[],V=[],ee=[],oe=(h==null?void 0:h.current)||{value:0},fe=l3(20261024),D=(le,te,Ue,Ce,Qe,Lt,Le=0)=>{const st=c3(te,Ue,Ce,Qe,Lt,oe,Le);return le.add(st),B.push(st.material),st},se=(le,te,Ue,Ce)=>{const Qe=Pw(te,Ue,oe,Ce);return le.add(Qe),B.push(Qe.material),Qe},_e=[],De=[],ze=[];for(let le=0;le<16e3;le++){_e.push((fe()-.5)*75,(fe()-.5)*42,-9-fe()*25);const te=.1+Math.pow(fe(),5)*.8;De.push(.3*te,.58*te,te),ze.push(.065+Math.pow(fe(),8)*1.08)}D(re,_e,De,ze,.86);const Xe=[],ue=[],Se=[];for(let le=0;le<2800;le++){const te=fe()*Bl,Ue=le%3;Xe.push(Math.sin(te)*(17+fe()*2),Math.cos(te*1.4+Ue)*8+(fe()-.5)*2,-8-fe()*8),ue.push(.06,.13,.28),Se.push(.6+fe()*2.8)}D(re,Xe,ue,Se,.15,100);let Re=!1;const at=new TM().load(cy(r,"nebula-depth-v1.png"),()=>{Re?at.dispose():N.dataset.nebula="ready"},void 0,()=>{N.dataset.nebula="unavailable"});at.colorSpace=Ei;const Ge=[{z:-20,w:84,h:48,x:-2,y:2,angle:-.12,opacity:1},{z:-12,w:66,h:40,x:7,y:-4,angle:.22,opacity:.56},{z:-6,w:42,h:26,x:-11,y:3,angle:-.48,opacity:.225}].map((le,te)=>{const Ue=new Yn({transparent:!0,depthWrite:!1,blending:Aa,uniforms:{map:{value:at},opacity:{value:le.opacity}},vertexShader:"varying vec2 vUv; void main(){vUv=uv;gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.0);}",fragmentShader:`varying vec2 vUv; uniform sampler2D map; uniform float opacity;
          void main(){vec3 c=texture2D(map,vUv).rgb;float edge=smoothstep(0.0,.15,vUv.x)*smoothstep(0.0,.15,vUv.y)*(1.0-smoothstep(.85,1.0,vUv.x))*(1.0-smoothstep(.85,1.0,vUv.y));gl_FragColor=vec4(c,opacity*edge);
          #include <tonemapping_fragment>
          #include <colorspace_fragment>
          }`}),Ce=new ji(new ec(le.w,le.h),Ue);return Ce.position.set(le.x,le.y,le.z),Ce.rotation.z=le.angle,re.add(Ce),{mesh:Ce,spec:le,index:te}}),mt=new Jl(.46,8,6),un=new Ju({visible:!1}),ut=ey();Nw.forEach((le,te)=>{const Ue=r3[le.id],Ce=e.filter(nn=>nn.clusterId===le.id),Qe=new ua;Qe.position.fromArray(Ue.center),k.add(Qe);const Lt=new ua;Lt.rotation.set(Ue.tilt,0,Ue.turn),Qe.add(Lt);const Le=new ua;Lt.add(Le);const st=.72+te%3*.09,_t=(.036+te%4*.009)*(te%3===1?-1:1),Ot=new wt(le.color),Yt=new wt("#d8e7ff"),Wn=new wt("#8bbaff"),it=[],ke=[],tn=[],An=[],wn=[],ma=[],Un=Math.round(2700+Ue.radius*1250);for(let nn=0;nn<Un;nn++){const ui=Math.pow(fe(),.68)*Ue.radius,$i=nn%3,ga=ui/Ue.radius*4.9+$i*Bl/3+(fe()-.5)*(.3+ui*.12),xa=1+.13*Math.sin(ga*2+te),ea=nn%5===0?.7:.22,Za=Math.cos(ga)*ui*xa+(fe()-.5)*ea,Tr=Math.sin(ga)*ui*st+(fe()-.5)*ea,Ci=(fe()-.5)*.22+Math.sin(ga*2+ui)*.12;it.push(Za,Tr,Ci);const Ar=nn%29===0,wr=.24+fe()*.67,ii=le.id==="METALS"&&Za>.3?Yt:le.id==="OIL"&&Za>.2?Wn:Ot;ke.push((Ar?.85:ii.r)*wr,(Ar?.94:ii.g)*wr,(Ar?1:ii.b)*wr),tn.push(.045+Math.pow(fe(),5)*.32+(nn%181===0?.75:0)),nn%9===0&&(An.push(Za,Tr,Ci-.1),wn.push(ii.r,ii.g,ii.b),ma.push(.7+fe()*1.1))}D(Le,it,ke,tn,1.04,48,_t*.65),D(Le,An,wn,ma,.07,85,_t*.65);for(let nn=0;nn<3;nn++){const ui=Array.from({length:100},($i,ga)=>{const xa=(.16+ga/99*.84)*Ue.radius,ea=xa/Ue.radius*4.9+nn*Bl/3;return new Q(Math.cos(ea)*xa*(1+.13*Math.sin(ea*2+te)),Math.sin(ea)*xa*st,Math.sin(ea*2+xa)*.12)});Le.add(u3(ui,le.color,.16)),se(Le,new uM(ui),le.color,{rate:.11+nn*.025,phase:nn/3+te*.07})}const On=document.createElement("div");On.className="galaxy-cluster-label",On.style.setProperty("--cluster-color",le.color);const wi=document.createElement("strong");wi.textContent=le.label;const Na=document.createElement("span");Na.textContent=` · ${Ce.length}`,On.append(wi,Na),I.appendChild(On);const La=new Q(Ue.radius*-.15,le.id==="METALS"?1:Ue.radius*.62+.35,.1),ja={meta:le,layout:Ue,group:Qe,layoutTarget:Qe.position.clone(),plane:Lt,spin:Le,spinRate:_t,phase:te*.8,caption:On,labelPoint:La,members:Ce,visible:!0};V.push(ja),Ce.forEach((nn,ui)=>{const $i=new ua,ga=ui/Math.max(1,Ce.length)*Bl+.38+te*.3,xa=Ue.radius*(Ce.length===1?.3:Ce.length===2?.65:.62+ui%2*.23),ea=ui*1.7+te,Za=(.019+ui%3*.009)*(_t<0?-1:1);$i.position.fromArray(t_(xa,ga,st,ea,0,Za)),Le.add($i);const Tr=new ji(mt,un);Tr.userData.symbol=nn.symbol,$i.add(Tr);const Ci=is(nn.symbol),Ar=ty(Ci,ut,$_(nn.symbol)),wr=Ar.group;$i.add(wr);const ii=document.createElement("button");ii.className="orbital-node-label",ii.textContent=nn.symbol,ii.setAttribute("aria-label",`เลือกสินทรัพย์ ${nn.symbol} ${Ci.available?`Short ${Ci.short}% Long ${Ci.long}%`:"ไม่มีข้อมูล Sentiment"}`),ii.dataset.symbol=nn.symbol,ii.title=Ci.available?`${nn.symbol} · Short ${Ci.short}% / Long ${Ci.long}% · Myfxbook`:`${nn.symbol} · ยังไม่มีข้อมูล Myfxbook`,J(ii,()=>nn.symbol),I.appendChild(ii),ee.push({pair:nn,cluster:ja,group:$i,rings:wr,nucleus:Ar,sentiment:Ci,hit:Tr,label:ii,radius:xa,angle:ga,eccentricity:st,phase:ea,rate:Za,depthOffset:Math.sin(ui*2.4)*.4,point:new Q})})});let xt=r_(e,Lp);const bt=e.length*(e.length-1)/2,pt=new Map(ee.map(le=>[le.pair.symbol,le])),vt=Bu*2,Gt=new Bn,vn=new Fn(new Float32Array(bt*vt*3),3).setUsage(ch),Xt=new Fn(new Float32Array(bt*vt),1),fn=new Fn(new Float32Array(bt*vt),1),j=new Fn(new Float32Array(bt*vt),1),Ft=new Fn(new Float32Array(bt*vt),1),Ut=new Fn(new Float32Array(bt*vt*3),3);Gt.setAttribute("position",vn),Gt.setAttribute("aValue",Xt),Gt.setAttribute("aEdge",fn),Gt.setAttribute("aIncident",j),Gt.setAttribute("aOverviewOpacity",Ft),Gt.setAttribute("aCorrelationColor",Ut),Gt.boundingSphere=new Bs(new Q,180);const P=new Yn({transparent:!0,depthWrite:!1,blending:zo,uniforms:{selectedEdge:{value:-1},hasSelection:{value:0}},vertexShader:`attribute float aValue;attribute float aEdge;attribute float aIncident;attribute float aOverviewOpacity;attribute vec3 aCorrelationColor;uniform float selectedEdge;varying float vValue;varying float vSelected;varying float vIncident;varying float vOverviewOpacity;varying vec3 vCorrelationColor;
        void main(){vValue=aValue;vIncident=aIncident;vOverviewOpacity=aOverviewOpacity;vCorrelationColor=aCorrelationColor;vSelected=1.-step(.5,abs(aEdge-selectedEdge));gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.0);}`,fragmentShader:`varying float vValue;varying float vSelected;varying float vIncident;varying float vOverviewOpacity;varying vec3 vCorrelationColor;uniform float hasSelection;
        void main(){float strength=abs(vValue);vec3 tint=vCorrelationColor;
          float alpha=vOverviewOpacity*mix(1.,.13,hasSelection);
          alpha=mix(alpha,.24+pow(strength,1.4)*.52,vIncident);
          gl_FragColor=vec4(tint,mix(alpha,.94,vSelected));
          #include <tonemapping_fragment>
          #include <colorspace_fragment>
        }`}),M=new oM(Gt,P);M.frustumCulled=!1,re.add(M);let Z=[],ce=[],xe=[],ne={neutral:0,positive:0,negative:0,minOpacity:0,maxOpacity:0};const Ae=new Map,pe=new Map,ye=Array.from({length:Math.max(0,e.length-1)},()=>{const le=document.createElement("button");return le.className="orbital-correlation-label",le.hidden=!0,I.appendChild(le),le.type="button",{label:le,edge:null,progress:null,offset:null,width:104}});let Ne=null,Ze=0;const He=le=>{var Ue,Ce;const te=(Ce=(Ue=le.target).closest)==null?void 0:Ce.call(Ue,".orbital-correlation-label");return te&&I.contains(te)&&!te.hidden?te:null},Fe=(le,te)=>{var Qe,Lt;const Ue=Oo(le.dataset.source,le.dataset.target),Ce=Z.find(Le=>Le.key===Ue);N.dataset.correlationLabelEvent=te.type,N.dataset.correlationLabelCallback=String(typeof w.current.onCorrelationSelect=="function"),Ce&&(N.dataset.lastPickedCorrelation=Ce.key,N.dataset.correlationActivationCount=String(++Ze),(Lt=(Qe=w.current).onCorrelationSelect)==null||Lt.call(Qe,{source:Ce.source,target:Ce.target,value:Ce.value}))},rt=le=>{const te=He(le);!te||le.button!==0||(le.preventDefault(),le.stopPropagation(),te.focus({preventScroll:!0}),Ne=te,Fe(te,le))},lt=le=>{const te=He(le);if(!te)return;le.preventDefault(),le.stopPropagation();const Ue=le.detail>0&&Ne===te;Ne=null,Ue||Fe(te,le)},dt=le=>{const te=He(le);!te||!["Enter"," "].includes(le.key)||le.repeat||(le.preventDefault(),le.stopPropagation(),Ne=null,Fe(te,le))};I.addEventListener("pointerdown",rt,!0),I.addEventListener("click",lt,!0),I.addEventListener("keydown",dt,!0);const q=new Bn,Oe=new Fn(new Float32Array(bt*3),3).setUsage(ch),be=new Fn(new Float32Array(bt),1),Pe=new Fn(new Float32Array(bt),1),Ve=new Fn(new Float32Array(bt*3),3);q.setAttribute("position",Oe),q.setAttribute("aValue",be),q.setAttribute("aEmphasis",Pe),q.setAttribute("aCorrelationColor",Ve);const we=new Yn({transparent:!0,depthWrite:!1,blending:Aa,uniforms:{pixelScale:{value:1}},vertexShader:`attribute float aEmphasis;attribute vec3 aCorrelationColor;uniform float pixelScale;varying float vEmphasis;varying vec3 vCorrelationColor;
        void main(){vCorrelationColor=aCorrelationColor;vEmphasis=aEmphasis;vec4 p=modelViewMatrix*vec4(position,1.);gl_Position=projectionMatrix*p;gl_PointSize=clamp((4.+aEmphasis*4.)*pixelScale,3.,18.);}`,fragmentShader:`varying vec3 vCorrelationColor;varying float vEmphasis;void main(){float r=length(gl_PointCoord-.5)*2.;if(r>1.)discard;
        vec3 tint=vCorrelationColor;float core=pow(1.-r,2.);
        gl_FragColor=vec4(mix(tint,vec3(1.,.97,.8),pow(1.-r,5.)*.25),core*vEmphasis);
        #include <tonemapping_fragment>
        #include <colorspace_fragment>
      }`}),et=new Ds(q,we);et.frustumCulled=!1,re.add(et),B.push(we);const Je=new Bn,Qt=new Fn(new Float32Array(ee.length*3),3).setUsage(ch),Nt=new Fn(new Float32Array(ee.length),1);Je.setAttribute("position",Qt),Je.setAttribute("aStrength",Nt);const ei=new Yn({transparent:!0,depthWrite:!1,blending:Aa,uniforms:{pixelScale:{value:1}},vertexShader:"attribute float aStrength;uniform float pixelScale;varying float vStrength;void main(){vStrength=aStrength;gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.);gl_PointSize=(7.+aStrength*4.)*pixelScale;}",fragmentShader:`varying float vStrength;void main(){float r=length(gl_PointCoord-.5)*2.;if(r>1.||vStrength<.01)discard;gl_FragColor=vec4(1.,.75,.27,pow(1.-r,2.7)*vStrength*.7);
        #include <tonemapping_fragment>
        #include <colorspace_fragment>
      }`}),ti=new Ds(Je,ei);ti.frustumCulled=!1,re.add(ti),B.push(ei);const Zi=new ua;k.add(Zi);const ls=Array.from({length:5},(le,te)=>{const Ue=new pM(new Q(-19+te*1.8,7-te*3,-4-te),new Q(-2+te*2,5-te*2,-2-te),new Q(18-te,3-te*2,-4-te));return se(Zi,Ue,te%2?"#8facf9":"#62c9f2",{rate:.06+te*.008,phase:.07+te*.19,meteor:!0})}),Ra=new CM,da=new Kt,vi={x:new Q(1,0,0),y:new Q(0,1,0),z:new Q(0,0,1)},Sn=new ss,In=new ss,Kn=new Q;let Wt=1,bn=1,Er=0,Ua=!1,qt=null,Ki=null,Pi=!1;const zi=new Q(1,1,1);let ha=performance.now(),pa=0,sn=1,Da=null,_i=null,A=!1,X="",ge=null;const ie=new Q,ae=new Q,Be=new Q;let We=37,Ie=!0;const qe=(le,te)=>{const Ue=w.current.axis;Ue==="free"?(k.quaternion.premultiply(Sn.setFromAxisAngle(vi.y,le*.004)),k.quaternion.premultiply(Sn.setFromAxisAngle(vi.x,te*.004))):k.quaternion.premultiply(Sn.setFromAxisAngle(vi[Ue]||vi.z,(le+te*.65)*.005)),k.quaternion.normalize()},Ye=(le,te)=>{const Ue=2*Math.tan(xo.degToRad(K.fov*.5))*K.position.distanceTo(ie)/bn;Be.x-=le*Ue,Be.y+=te*Ue},gt=le=>{const te=z.getBoundingClientRect();da.set((le.clientX-te.left)/te.width*2-1,-((le.clientY-te.top)/te.height)*2+1),Ra.setFromCamera(da,K)},Tt=le=>{var te;return gt(le),((te=Ra.intersectObjects(ee.filter(Ue=>Ue.cluster.visible).map(Ue=>Ue.hit),!1)[0])==null?void 0:te.object.userData.symbol)||null},$e=le=>{if(!M.visible||!Z.length)return null;gt(le);const te=2*Math.tan(xo.degToRad(K.fov*.5))*K.position.distanceTo(ie)/bn;Ra.params.Line.threshold=te*4;const Ue=Ra.intersectObject(M,!1);let Ce=null,Qe=5;for(const Lt of Ue){Kn.copy(Lt.point).project(K);const Le=Math.hypot((Kn.x-da.x)*Wt*.5,(Kn.y-da.y)*bn*.5);Le<Qe&&(Qe=Le,Ce=a3(Z,Lt.index))}return Ce},Bt=le=>{var Ue,Ce;if(le.button!==0&&le.button!==2&&le.pointerType!=="touch"||le.button===0&&((Ce=(Ue=le.target).closest)!=null&&Ce.call(Ue,"button")))return;le.preventDefault(),z.focus({preventScroll:!0});const te=le.button===0?Tt(le):null;qt={id:le.pointerId,x:le.clientX,y:le.clientY,button:le.button,travel:0,symbol:te,correlation:le.button===0&&!te?$e(le):null},z.setPointerCapture(le.pointerId),z.classList.add("is-dragging")},dn=le=>{if(qt&&le.pointerId===qt.id){const te=le.clientX-qt.x,Ue=le.clientY-qt.y;qt.travel+=Math.abs(te)+Math.abs(Ue),qt.button===2?Ye(te,Ue):qe(te,Ue),qt.x=le.clientX,qt.y=le.clientY}else Ki=Tt(le),z.style.cursor=Ki?"pointer":w.current.correlationsVisible?"crosshair":"grab"},rn=le=>{var te,Ue,Ce,Qe;if(!(!qt||le.pointerId!==qt.id)){if(qt.button===0&&qt.travel<6){if(qt.symbol)(Ue=(te=w.current).onSelect)==null||Ue.call(te,qt.symbol);else if(qt.correlation){const{source:Lt,target:Le,value:st}=qt.correlation;N.dataset.lastPickedCorrelation=Oo(Lt,Le),(Qe=(Ce=w.current).onCorrelationSelect)==null||Qe.call(Ce,{source:Lt,target:Le,value:st})}}z.hasPointerCapture(le.pointerId)&&z.releasePointerCapture(le.pointerId),qt=null,z.classList.remove("is-dragging")}},Mt=()=>{qt=null,z.classList.remove("is-dragging")},Tn=le=>le.preventDefault(),Ke=le=>{le.preventDefault(),sn=xo.clamp(sn*Math.exp(le.deltaY*7e-4),.42,1.7)},Rn=le=>{const te={ArrowLeft:[-14,0],ArrowRight:[14,0],ArrowUp:[0,-14],ArrowDown:[0,14]};te[le.key]?(le.preventDefault(),le.shiftKey?Ye(...te[le.key]):qe(...te[le.key])):["+","=","-"].includes(le.key)&&(le.preventDefault(),sn=xo.clamp(sn*(le.key==="-"?1.08:.92),.42,1.7))},Et=le=>{var te,Ue;le.preventDefault(),(Ue=(te=w.current).onError)==null||Ue.call(te,"ฉากสามมิติหยุดชั่วคราว กรุณาโหลดหน้าใหม่เพื่อเชื่อมต่อกราฟิกอีกครั้ง")};N.addEventListener("pointerdown",Bt),N.addEventListener("pointermove",dn),N.addEventListener("pointerup",rn),N.addEventListener("pointercancel",Mt),N.addEventListener("contextmenu",Tn),N.addEventListener("wheel",Ke,{passive:!1}),z.addEventListener("keydown",Rn),z.addEventListener("webglcontextlost",Et);const Qn=()=>{const le=N.getBoundingClientRect();Wt=Math.max(1,le.width),bn=Math.max(1,le.height);const te=Wt>=640&&Wt/bn<1.24;N.dataset.framing=Wt<640?"portrait":te?"compact":"wide",V.forEach(Ce=>{Ce.layoutTarget.fromArray(Wt<640?s3[Ce.meta.id]:te?o3[Ce.meta.id]:Ce.layout.center),(!Pi||w.current.reducedMotion)&&Ce.group.position.copy(Ce.layoutTarget)}),zi.set(Wt<640?.5:1,Wt<640?1.7:1,1),(!Pi||w.current.reducedMotion)&&Zi.scale.copy(zi),Pi=!0,L.setSize(Wt,bn,!1),K.aspect=Wt/bn,K.updateProjectionMatrix();const Ue=Math.min(window.devicePixelRatio||1,1.6);T.width=Wt*Ue,T.height=bn*Ue,T.style.width=`${Wt}px`,T.style.height=`${bn}px`,O==null||O.setTransform(Ue,0,0,Ue,0,0),B.forEach(Ce=>{Ce.uniforms.pixelScale.value=bn/720*Ue}),ee.forEach(Ce=>iy(Ce.nucleus,bn*Ue))},ci=new ResizeObserver(Qn);ci.observe(N),Qn();const ni=()=>{const le=new Vo,te=new Q;if(V.filter(st=>st.visible&&(!_i||st.meta.id===_i)).forEach(st=>{const _t=st.layout.radius;for(const Ot of[-_t*1.12,_t*1.12])for(const Yt of[-_t*.7,_t*.74+.35])for(const Wn of[-_t*.65,_t*.65])te.set(Ot,Yt,Wn),st.group.localToWorld(te),le.expandByPoint(te)}),le.isEmpty())return;const Ue=le.getSize(new Q);le.getCenter(ae),Wt>=640&&w.current.filter==="all"&&!_i&&(ae.y+=1.05),ae.add(Be);const Ce=Math.tan(xo.degToRad(K.fov*.5)),Qe=bn/Math.max(240,bn-160),Lt=Wt/Math.max(240,Wt-40);We=(Math.max(Ue.y/(2*Ce)*Qe,Ue.x/(2*Ce*K.aspect)*Lt)*(Wt<640?1.08:1.025)+Ue.z*.5)*sn,Ie&&(ie.copy(ae),K.position.set(ae.x,ae.y,ae.z+We),Ie=!1)},Qi=le=>({x:(le.x*.5+.5)*Wt,y:(-le.y*.5+.5)*bn});function jt(){O==null||O.clearRect(0,0,Wt,bn);const le=[],te=new Q,Ue=(Le,st,_t,Ot)=>Le>=8&&Le+_t<=Wt-8&&st>=65&&st+Ot<=bn-124&&!le.some(Yt=>Le<Yt.x+Yt.w+4&&Le+_t>Yt.x-4&&st<Yt.y+Yt.h+3&&st+Ot>Yt.y-3),Ce=(Le,st,_t)=>{if(!O)return;const Ot=Math.max(st.x,Math.min(st.x+st.w,Le.x)),Yt=Math.max(st.y,Math.min(st.y+st.h,Le.y));Math.hypot(Ot-Le.x,Yt-Le.y)<12||(O.beginPath(),O.strokeStyle=_t,O.lineWidth=.7,O.moveTo(Le.x,Le.y),O.lineTo(Ot,Yt),O.stroke())};V.forEach(Le=>{te.copy(Le.labelPoint),Le.group.localToWorld(te),te.project(K);const st=Qi(te),_t=Wt<640?72:108,Ot=Le.visible&&te.z<1&&st.x>12&&st.x<Wt-12&&st.y>70&&st.y<bn-120;if(Le.caption.hidden=!Ot,Ot){const Yt=Math.min(st.x,Wt-_t-8);Le.caption.style.transform=`translate3d(${Yt.toFixed(1)}px,${(st.y-20).toFixed(1)}px,0)`,le.push({x:Yt,y:st.y-20,w:_t,h:30})}});const Qe=w.current.selectedSymbol;[...ee].sort((Le,st)=>Le.pair.symbol===Qe?-1:st.pair.symbol===Qe?1:0).forEach(Le=>{Le.group.getWorldPosition(Le.point),te.copy(Le.point).project(K);const st=Qi(te),_t=Le.pair.symbol===Qe,Ot=w.current.selectedCorrelation,Yt=pe.has(Le.pair.symbol),Wn=_t||Yt||Le.pair.symbol===Ki||(Ot==null?void 0:Ot.source)===Le.pair.symbol||(Ot==null?void 0:Ot.target)===Le.pair.symbol||Wt>=640&&c_.has(Le.pair.symbol)||_i||w.current.filter!=="all",it=Le.cluster.visible&&Wn&&te.z<1&&st.x>6&&st.x<Wt-8&&st.y>65&&st.y<bn-110;if(Le.label.hidden=!it,!it)return;const ke=_t?82:Wt<640?58:66,tn=_t?27:24,An=[...Le.labelOffset?[Le.labelOffset]:[],{x:17,y:-29},{x:-ke-17,y:-29},{x:17,y:13},{x:-ke-17,y:13}];for(const Un of[36,58,84,112,144])for(let On=0;On<8;On++){const wi=On*Bl/8;An.push({x:Math.cos(wi)*Un-ke*.5,y:Math.sin(wi)*Un-tn*.5})}const wn=An.find(Un=>Ue(st.x+Un.x,st.y+Un.y,ke,tn));if(Le.label.hidden=!wn,!wn)return;Le.labelOffset=wn;const ma={x:st.x+wn.x,y:st.y+wn.y,w:ke,h:tn};le.push(ma),Ce(st,ma,Yt?"#d7b77366":"#93b3c74d"),Le.label.style.transform=`translate3d(${ma.x.toFixed(1)}px,${ma.y.toFixed(1)}px,0)`,Le.label.classList.toggle("is-selected",_t),Le.label.classList.toggle("is-connected",Yt&&!_t),Le.label.setAttribute("aria-pressed",String(_t))}),ye.forEach((Le,st)=>{const{label:_t,edge:Ot}=Le;if(!Ot){_t.hidden=!0;return}const Yt=pt.get(Ot.source).point,Wn=pt.get(Ot.target).point,it=Ae.get(Ot.key);if(!it){_t.hidden=!0;return}const tn=.5+(Ot.source===Qe?1:-1)*(.08+st%5*.055),An=Le.width,wn=22,ma=[...Le.offset?[Le.offset]:[],{x:0,y:0},{x:0,y:-24},{x:0,y:24},{x:-An*.45,y:-24},{x:An*.45,y:24},{x:-An*.45,y:24},{x:An*.45,y:-24}];let Un=null;for(let On=0;On<16;On++){const wi=On-1,Na=On===0&&Le.progress!==null?Le.progress:xo.clamp(tn+(wi%2?1:-1)*Math.ceil(Math.max(0,wi)/2)*.045,.14,.86);l_(Yt,Wn,it,Na,te),te.project(K);const La=Qi(te);if(te.z>=1)continue;const ja=ma.find(nn=>Ue(La.x-An*.5+nn.x,La.y-wn*.5+nn.y,An,wn));if(ja){Un={x:La.x-An*.5+ja.x,y:La.y-wn*.5+ja.y,progress:Na,offset:ja,anchor:La};break}}if(_t.hidden=!Un,Un){Le.progress=Un.progress,Le.offset=Un.offset,_t.style.transform=`translate3d(${Un.x.toFixed(1)}px,${Un.y.toFixed(1)}px,0)`;const On={x:Un.x,y:Un.y,w:An,h:wn};le.push(On),Ce(Un.anchor,On,`${pi(Ot.value)}66`)}_t.classList.toggle("is-selected",w.current.selectedCorrelation&&Ot.key===Oo(w.current.selectedCorrelation.source,w.current.selectedCorrelation.target))})}function gn(){Z=w.current.correlationsVisible?t3(xt,w.current.filter):[],ce=n3(Z,w.current.selectedSymbol);const le=new Set(ce.map(te=>te.key));xe=s_(Z),P.uniforms.hasSelection.value=ce.length?1:0,pe.clear(),ce.forEach(te=>pe.set(te.source===w.current.selectedSymbol?te.target:te.source,Math.abs(te.value))),M.visible=Z.length>0,Gt.setDrawRange(0,Z.length*vt),ne={neutral:0,positive:0,negative:0,minOpacity:Z.length?1/0:0,maxOpacity:0},Z.forEach((te,Ue)=>{const Ce=Ue*vt,Qe=a_(te.value),Lt=new wt(pi(te.value));ne[kl(te.value)]++,ne.minOpacity=Math.min(ne.minOpacity,Qe.opacity),ne.maxOpacity=Math.max(ne.maxOpacity,Qe.opacity),Xt.array.fill(te.value,Ce,Ce+vt),fn.array.fill(te.index,Ce,Ce+vt),j.array.fill(le.has(te.key)?1:0,Ce,Ce+vt),Ft.array.fill(Qe.opacity,Ce,Ce+vt);for(let Le=Ce;Le<Ce+vt;Le++)Ut.setXYZ(Le,Lt.r,Lt.g,Lt.b)}),Xt.needsUpdate=!0,fn.needsUpdate=!0,j.needsUpdate=!0,Ft.needsUpdate=!0,Ut.needsUpdate=!0,ye.forEach((te,Ue)=>{var Qe;const Ce=ce[Ue];((Qe=te.edge)==null?void 0:Qe.key)!==(Ce==null?void 0:Ce.key)&&(te.progress=null,te.offset=null),te.edge=Ce||null,te.label.hidden=!Ce,Ce&&(te.label.textContent=e3(Ce,w.current.selectedSymbol),O&&(O.font="600 12px Rajdhani, sans-serif"),te.width=Math.max(94,Math.ceil((O==null?void 0:O.measureText(te.label.textContent).width)||te.label.textContent.length*6.2)+14),te.label.style.setProperty("--correlation-color",pi(Ce.value)),te.label.dataset.tone=kl(Ce.value),te.label.title=`${Ce.source} ↔ ${Ce.target} · ${Math.round(Ce.value*100)}% · คำนวณจากราคาปิด MT5`,te.label.setAttribute("aria-label",te.label.title),te.label.dataset.source=Ce.source,te.label.dataset.target=Ce.target,te.label.dataset.correlation=String(Ce.value),te.label.dataset.counterpart=ly(Ce,w.current.selectedSymbol))}),et.visible=xe.length>0,q.setDrawRange(0,xe.length),xe.forEach((te,Ue)=>{const Ce=new wt(pi(te.value));Ve.setXYZ(Ue,Ce.r,Ce.g,Ce.b),be.setX(Ue,te.value),Pe.setX(Ue,ce.length?le.has(te.key)?1:.14:.75)}),be.needsUpdate=!0,Pe.needsUpdate=!0,Ve.needsUpdate=!0,ee.forEach((te,Ue)=>{const Ce=pe.get(te.pair.symbol),Qe=te.pair.symbol===w.current.selectedSymbol&&ce.length>0;Nt.setX(Ue,te.cluster.visible?Qe?.95:Ce===void 0?0:.45+Ce*.5:0)}),Nt.needsUpdate=!0,ti.visible=ce.length>0}function Ai(le){if(!Z.length)return;ee.forEach(Qe=>Qe.group.getWorldPosition(Qe.point));const te=vn.array;Z.forEach((Qe,Lt)=>{const Le=pt.get(Qe.source).point,st=pt.get(Qe.target).point,_t=i3(Le,st,Qe.index);Ae.set(Qe.key,_t);let Ot=Lt*vt*3;for(let Yt=0;Yt<Bu;Yt++)for(let Wn=0;Wn<2;Wn++){const it=(Yt+Wn)/Bu,ke=1-it,tn=ke*ke,An=2*ke*it,wn=it*it;te[Ot++]=tn*Le.x+An*_t.x+wn*st.x,te[Ot++]=tn*Le.y+An*_t.y+wn*st.y,te[Ot++]=tn*Le.z+An*_t.z+wn*st.z}}),vn.needsUpdate=!0;const Ue=new Q;xe.forEach((Qe,Lt)=>{l_(pt.get(Qe.source).point,pt.get(Qe.target).point,Ae.get(Qe.key),o_(le,Qe.index),Ue),Oe.setXYZ(Lt,Ue.x,Ue.y,Ue.z)}),Oe.needsUpdate=!0;const Ce=new Q(.4,.32,.04).applyQuaternion(K.quaternion);ee.forEach((Qe,Lt)=>Qt.setXYZ(Lt,Qe.point.x+Ce.x,Qe.point.y+Ce.y,Qe.point.z+Ce.z)),Qt.needsUpdate=!0}function en(){ee.forEach(le=>{const te=is(le.pair.symbol);le.sentiment=te,ny(le.nucleus,te),le.label.setAttribute("aria-label",`เลือกสินทรัพย์ ${le.pair.symbol} ${te.available?`Short ${te.short}% Long ${te.long}%`:"ยังไม่มีข้อมูล Myfxbook"}`),le.label.title=te.available?`${le.pair.symbol} · Short ${te.short}% / Long ${te.long}% · Myfxbook${te.asOf?` · รับข้อมูล ${te.asOf}`:""}`:`${le.pair.symbol} · ยังไม่มีข้อมูล Myfxbook`,le.label.dataset.sentimentAvailable=String(te.available),le.label.dataset.sentimentColor=le.nucleus.appearance.color}),xt=r_(e,Lp),Ae.clear(),qt!=null&&qt.correlation&&(qt.correlation=xt.find(le=>le.key===qt.correlation.key)||null),gn(),X="",ge=w.current.dataRevision,N.dataset.dataRevision=String(ge)}const Ji=()=>{k.quaternion.identity(),Be.set(0,0,0),_i=null,A=!1,sn=1},Fi=()=>{A=!0};G.current={reset:Ji,focus:Fi,refreshData:en};const yi=()=>{ha=performance.now()};document.addEventListener("visibilitychange",yi);function Is(le){var st,_t,Ot,Yt,Wn;if(Ua)return;Er=requestAnimationFrame(Is);const te=Math.max(0,Math.min(.05,(le-ha)/1e3));if(ha=le,document.hidden||Wt<2||bn<2)return;Da!==w.current.filter&&(Da=w.current.filter,_i=null,sn=1,V.forEach(it=>{it.visible=Da==="all"||it.meta.assetClass===Da,it.group.visible=it.visible}),Zi.visible=Da==="all"),ge!==w.current.dataRevision&&en();const Ue=`${w.current.filter}:${w.current.correlationsVisible}:${w.current.selectedSymbol}`;Ue!==X&&(gn(),X=Ue);const Ce=w.current.selectedCorrelation;P.uniforms.selectedEdge.value=Ce?((st=xt.find(it=>it.key===Oo(Ce.source,Ce.target)))==null?void 0:st.index)??-1:-1,A&&(_i=((_t=ee.find(it=>it.pair.symbol===w.current.selectedSymbol))==null?void 0:_t.pair.clusterId)||null,sn=1,A=!1),w.current.selectedSymbol||(_i=null),oe.value=Ow(oe.value,te,{playing:w.current.playing&&!w.current.reducedMotion,dragging:!!qt,speed:w.current.motionSpeed});const Qe=oe.value,Lt=w.current.reducedMotion?1:1-Math.exp(-te*9);Zi.scale.lerp(zi,Lt),Ge.forEach(({mesh:it,spec:ke,index:tn})=>{it.position.x=ke.x+Math.sin(Qe*.018+tn)*1.2+k.quaternion.y*(tn+1)*1.3,it.position.y=ke.y+Math.sin(Qe*.012+tn)*.65-k.quaternion.x*(tn+1)*.9,it.rotation.z=ke.angle+Math.sin(Qe*.009+tn)*.025}),V.forEach(it=>{it.group.position.lerp(it.layoutTarget,Lt),it.group.position.distanceToSquared(it.layoutTarget)<1e-6&&it.group.position.copy(it.layoutTarget),it.spin.rotation.z=Qe*it.spinRate,it.plane.rotation.x=it.layout.tilt+Math.sin(Qe*.17+it.phase)*.055,it.plane.rotation.z=it.layout.turn+Math.sin(Qe*.12+it.phase)*.035}),ee.forEach(it=>{it.group.position.fromArray(t_(it.radius,it.angle,it.eccentricity,it.phase,Qe,it.rate)),it.group.position.z+=it.depthOffset}),k.updateMatrixWorld(!0),ni();const Le=w.current.reducedMotion?1:1-Math.exp(-te*6);if(ie.lerp(ae,Le),K.position.x+=(ie.x-K.position.x)*Le,K.position.y+=(ie.y-K.position.y)*Le,K.position.z+=(ie.z+We-K.position.z)*Le,K.lookAt(ie),K.updateMatrixWorld(),ee.forEach(it=>{const ke=it.pair.symbol===w.current.selectedSymbol,tn=c_.has(it.pair.symbol);it.rings.scale.setScalar(ke?1.22:tn?1.08:.92),it.hit.scale.setScalar(ke?1.2:1),it.group.getWorldQuaternion(In),it.rings.quaternion.copy(In.invert()).multiply(K.quaternion),em(it.nucleus,Qe)}),re.updateMatrixWorld(!0),Ai(Qe),L.render(re,K),jt(),le-pa>160){const it=new Set(ee.filter(ke=>!ke.label.hidden&&pe.has(ke.pair.symbol)).map(ke=>ke.pair.symbol));ye.filter(ke=>!ke.label.hidden).forEach(ke=>it.add(ke.label.dataset.counterpart)),Object.assign(N.dataset,{rotation:k.quaternion.toArray().map(ke=>ke.toFixed(5)).join(","),orbit:V[1].spin.rotation.z.toFixed(6),motionTime:Qe.toFixed(6),motionSpeed:String(w.current.motionSpeed),distance:K.position.z.toFixed(3),selected:w.current.selectedSymbol||"",selectionMode:w.current.selectedSymbol?"selected":"overview",axis:w.current.axis,playing:String(w.current.playing),visibleCount:String(ee.filter(ke=>ke.cluster.visible).length),clusterCount:String(V.filter(ke=>ke.visible).length),focus:_i||"overview",reducedMotion:String(w.current.reducedMotion),layoutMoving:String(V.some(ke=>ke.group.position.distanceToSquared(ke.layoutTarget)>1e-6)),layoutDistance:V.reduce((ke,tn)=>ke+tn.group.position.distanceTo(tn.layoutTarget),0).toFixed(4),chfCenter:V.find(ke=>ke.meta.id==="CHF").group.position.toArray().map(ke=>ke.toFixed(4)).join(","),connectionCount:String(Z.length),correlationCount:String(Z.length),correlationTotal:String(xt.length),correlationDrawCalls:String(M.visible?1:0),selectedCorrelation:Ce?Oo(Ce.source,Ce.target):"",cometCount:String(Zi.visible?ls.length:0),starPosition:ee[0].group.position.toArray().map(ke=>ke.toFixed(5)).join(","),selectedEdgeCount:String(ce.length),correlationLabelCount:String(ye.filter(ke=>!ke.label.hidden).length),correlationLabelTotal:String(ce.length),highlightedEndpointCount:String(pe.size),flowCount:String(xe.length),selectedFlowCount:String(s_(ce).length),flowProgress:xe.length?o_(Qe,xe[0].index).toFixed(6):"",flowDrawCalls:String(et.visible?1:0),pan:Be.toArray().map(ke=>ke.toFixed(4)).join(","),panX:Be.x.toFixed(4),panY:Be.y.toFixed(4),cameraControls:"left-rotate,right-pan",overviewThreshold:String(Iu),overviewStrongCount:String(Z.filter(ke=>a_(ke.value).emphasized).length),visibleNameCount:String(ee.filter(ke=>!ke.label.hidden).length),connectedNameCount:String(it.size),neutralThreshold:String(nm),correlationNeutralCount:String(ne.neutral),correlationPositiveCount:String(ne.positive),correlationNegativeCount:String(ne.negative),correlationOpacityMin:ne.minOpacity.toFixed(4),correlationOpacityMax:ne.maxOpacity.toFixed(4),correlationBrightYellowCount:String(Z.filter(ke=>Math.abs(ke.value)<=sy).length),correlationDeepCount:String(Z.filter(ke=>Math.abs(ke.value)>=oy).length),correlationBlending:"normal",nucleusOrbits:String(((Ot=ee[0])==null?void 0:Ot.nucleus.ringCount)??0),sentimentRings:String(((Yt=ee[0])==null?void 0:Yt.nucleus.ringCount)??0),selectedLong:String(is(w.current.selectedSymbol).long??""),selectedShort:String(is(w.current.selectedSymbol).short??""),beadPosition:((Wn=ee.find(ke=>ke.pair.symbol===w.current.selectedSymbol))==null?void 0:Wn.nucleus.bead.position.toArray().map(ke=>ke.toFixed(5)).join(","))||"",nebulaLayers:String(Ge.length)}),pa=le}}return Er=requestAnimationFrame(Is),N.dataset.ready="true",N.dataset.nodeCount=String(ee.length),(Wo=(Ya=w.current).onReady)==null||Wo.call(Ya),()=>{Ua=!0,cancelAnimationFrame(Er),ci.disconnect(),document.removeEventListener("visibilitychange",yi),N.removeEventListener("pointerdown",Bt),N.removeEventListener("pointermove",dn),N.removeEventListener("pointerup",rn),N.removeEventListener("pointercancel",Mt),N.removeEventListener("wheel",Ke),N.removeEventListener("contextmenu",Tn),z.removeEventListener("keydown",Rn),z.removeEventListener("webglcontextlost",Et),I.removeEventListener("pointerdown",rt,!0),I.removeEventListener("click",lt,!0),I.removeEventListener("keydown",dt,!0),Re=!0,at.dispose(),ay(re,ut),L.dispose(),L.forceContextLoss(),z.remove(),T.remove(),I.remove(),G.current=null,delete N.dataset.ready}},[e]),nt.useEffect(()=>{var N;v&&((N=G.current)==null||N.reset())},[v]),nt.useEffect(()=>{var N;x&&((N=G.current)==null||N.focus())},[x]),U.jsx("div",{ref:F,className:"orbital-canvas-wrap","data-testid":"orbital-scene"})}function d3({symbol:r,playing:e,motionClock:i,motionSpeed:s=1,dataRevision:l=0,className:c=""}){const f=nt.useRef(null),h=nt.useRef(null),m=nt.useRef({playing:e,motionSpeed:s});m.current={playing:e,motionSpeed:s},nt.useEffect(()=>{var J;const g=f.current;if(!g)return;let v;try{v=new K_({antialias:!0,alpha:!0,powerPreference:"low-power"})}catch{g.dataset.ready="false";return}const x=Math.min(window.devicePixelRatio||1,1.75);v.setPixelRatio(x),v.setClearColor(0,0),v.outputColorSpace=Ei,v.domElement.setAttribute("aria-hidden","true"),g.prepend(v.domElement);const _=new N_,E=new Yi(32,1,.1,20);E.position.set(0,.05,2.65),E.lookAt(0,0,0);const R=ey(),b=ty(is(r),R,$_(r));_.add(b.group);let S=0,F=0,G=0,w=!0,N=null,L=Number.isFinite((J=i==null?void 0:i.current)==null?void 0:J.value)?i.current.value:0;const z=()=>{ny(b,is(r)),w=!0,g.dataset.sentimentColor=b.appearance.color,g.dataset.sentimentBias=b.appearance.bias,g.dataset.sentimentDominance=String(b.appearance.dominance??""),g.dataset.sentimentAvailable=String(b.available)};h.current=z;const T=()=>{const re=g.getBoundingClientRect();F=re.width,G=re.height,!(F<1||G<1)&&(v.setSize(F,G,!1),E.aspect=F/G,E.updateProjectionMatrix(),iy(b,G*x),w=!0)},O=new ResizeObserver(T);O.observe(g),T();function I(){var k;if(S=requestAnimationFrame(I),document.hidden||F<1||G<1)return;const re=(k=i==null?void 0:i.current)==null?void 0:k.value;m.current.playing&&Number.isFinite(re)&&(L=re),!(!w&&L===N)&&(N=L,w=!1,em(b,L),v.render(_,E),g.dataset.motionTime=L.toFixed(6),g.dataset.beadPosition=b.bead.position.toArray().map(K=>K.toFixed(5)).join(","))}S=requestAnimationFrame(I),g.dataset.ready="true",g.dataset.orbits="0",g.dataset.sentimentColor=b.appearance.color,g.dataset.sentimentBias=b.appearance.bias,g.dataset.sentimentDominance=String(b.appearance.dominance??"");const W=re=>{re.preventDefault(),g.dataset.ready="false"};return v.domElement.addEventListener("webglcontextlost",W),()=>{h.current=null,cancelAnimationFrame(S),O.disconnect(),v.domElement.removeEventListener("webglcontextlost",W),ay(_,R),v.dispose(),v.forceContextLoss(),v.domElement.remove(),delete g.dataset.ready}},[r,i]),nt.useEffect(()=>{var g;(g=h.current)==null||g.call(h)},[l]);const p=is(r);return U.jsx("div",{ref:f,className:`sentiment-preview ${c}`,"data-symbol":r,"data-data-revision":l,role:"img","aria-label":`ดาวพลาสมาสามมิติ ${r} ${p.available?`Myfxbook Short ${p.short}% Long ${p.long}%`:"ยังไม่มีข้อมูล Myfxbook"}`,children:U.jsx("span",{className:"sentiment-preview-fallback",children:"เปิดภาพดาว 3D ไม่สำเร็จ"})})}function h3({url:r,onData:e,onFailure:i,fetchImpl:s=globalThis.fetch,intervalMs:l=3e4,timeoutMs:c=1e4,schedule:f=setTimeout,cancel:h=clearTimeout}){let m=!1,p,g,v;const x=async()=>{g=new AbortController,v=f(()=>g.abort(),c);try{const _=await s(r,{cache:"no-store",credentials:"omit",signal:g.signal});if(!_.ok)throw new Error("market_unavailable");const E=await _.json();m||e(E)}catch{m||i()}finally{h(v),m||(p=f(x,l))}};return x(),()=>{m=!0,h(p),h(v),g==null||g.abort()}}function p3({marketUrl:r="/api/market",requireHeartbeat:e=!1}={}){const i=nt.useSyncExternalStore(Xw,Ww);return nt.useEffect(()=>h3({url:r,onData:s=>jw(s,{requireHeartbeat:e}),onFailure:Zw}),[r,e]),i}function m3(r){return[...r.querySelectorAll('button:not(:disabled),a[href],input:not(:disabled),select:not(:disabled),textarea:not(:disabled),[tabindex="0"]')].filter(e=>!e.closest("[inert]")&&e.getClientRects().length)}function g3(r,e){var i,s,l;if(r.key==="Escape"){const c=e.explainerOpen?e.closeExplainer:e.eventOpen?e.closeNews:e.settingsOpen?e.closeSettings:e.inspectorOpen?e.closeInspector:null;return c?(c(),r.preventDefault(),r.stopPropagation(),!0):!1}if(e.embedded&&r.key==="Tab"){const c=m3(e.root),f=e.root.getRootNode().activeElement;return r.shiftKey&&f===c[0]?(r.preventDefault(),(i=c.at(-1))==null||i.focus()):!r.shiftKey&&f===c.at(-1)&&(r.preventDefault(),(s=c[0])==null||s.focus()),r.stopPropagation(),!0}return e.explainerOpen||/INPUT|SELECT|TEXTAREA|BUTTON|A/.test((l=r.target)==null?void 0:l.tagName)?!1:r.key===" "?(r.preventDefault(),r.stopPropagation(),e.toggleMotion(),!0):!1}const x3={pmi:{title:"PMI · ดัชนีผู้จัดการฝ่ายจัดซื้อ",lines:["สำรวจภาวะธุรกิจ เป็นค่าดัชนี ไม่ใช่ % การเติบโต","50 = คงเดิม; สูงกว่า = ขยาย; ต่ำกว่า = หดจากเดือนก่อน","ดีขึ้นแต่ยังต่ำกว่า 50 = ยังหดตัว; เทียบค่าคาดด้วย","ค่าเงินอาจตอบสนองผ่านมุมมองเศรษฐกิจและดอกเบี้ย"],sourceName:"S&P Global · PMI FAQ",sourceUrl:"https://www.spglobal.com/market-intelligence/en/solutions/products/resources/pmi-faq"},consumerConfidence:{title:"ความเชื่อมั่นผู้บริโภค",lines:["สำรวจมุมมองต่อการเงิน เศรษฐกิจ และการใช้จ่าย","เป็นดุลคำตอบเชิงบวก–ลบ ไม่ใช่อัตราโตของยอดขาย","สูงขึ้นคือมุมมองดีขึ้น; เทียบคาดการณ์และครั้งก่อน","อาจหนุนมุมมองเศรษฐกิจ แต่ไม่ยืนยันทิศค่าเงิน"],sourceName:"European Commission · วิธีอ่านแบบสำรวจ",sourceUrl:"https://economy-finance.ec.europa.eu/economic-forecast-and-surveys/business-and-consumer-surveys/methodology-business-and-consumer-surveys/methodological-concepts_en"},businessConfidence:{title:"ANZ · ความเชื่อมั่นธุรกิจ",lines:["สำรวจมุมมองธุรกิจนิวซีแลนด์ต่อเศรษฐกิจข้างหน้า","ดุลสุทธิคือฝั่งมองดีหักฝั่งมองแย่ ไม่ใช่ GDP","แยกความมั่นใจรวมจากแนวโน้มกิจการของผู้ตอบ","เทียบคาดและครั้งก่อน; ค่าเงินยังขึ้นกับปัจจัยอื่น"],sourceName:"ANZ · Business Outlook",sourceUrl:"https://www.anz.co.nz/about-us/economic-markets-research/business-outlook/"},cpi:{title:"CPI · เงินเฟ้อผู้บริโภค",lines:["วัดการเปลี่ยนราคาสินค้าและบริการของผู้บริโภค","m/m เทียบเดือนก่อน; y/y เทียบเดือนเดียวกันปีก่อน","เงินเฟ้อลดลง อาจแค่ราคาเพิ่มช้าลง ไม่ใช่ราคาลด","เกินคาดอาจดันมุมมองดอกเบี้ยขึ้น ค่าเงินไม่แน่นอน"],sourceName:"BLS · CPI FAQ",sourceUrl:"https://www.bls.gov/cpi/questions-and-answers.htm"},coreCpi:{title:"Core CPI · เงินเฟ้อพื้นฐานสหรัฐฯ",lines:["CPI สหรัฐฯ ที่ไม่นับอาหารและพลังงาน","ช่วยดูแรงกดดันราคาพื้นฐาน โดยยังต้องอ่าน CPI รวม","เทียบคาดและครั้งก่อนในช่วงเวลาเดียวกัน เช่น m/m","เกินคาดอาจหนุนดอกเบี้ยสูงนาน แต่ไม่ยืนยันทิศกราฟ"],sourceName:"BLS · Headline และ Core CPI",sourceUrl:"https://www.bls.gov/cpi/factsheets/common-misconceptions-about-cpi.htm"},canadaCpi:{title:"CPI · เงินเฟ้อแคนาดา",lines:["วัดการเปลี่ยนราคาตะกร้าสินค้าและบริการผู้บริโภค","m/m เทียบเดือนก่อน; y/y เทียบเดือนเดียวกันปีก่อน","อ่านผลเทียบคาด ไม่สรุปจากตัวเลขสูงขึ้นอย่างเดียว","CAD อาจตอบสนองผ่านมุมมองดอกเบี้ยและปัจจัยอื่น"],sourceName:"Statistics Canada · CPI FAQ",sourceUrl:"https://www.statcan.gc.ca/en/subjects-start/prices_and_price_indexes/consumer_price_indexes/faq"},japanCpi:{title:"CPI · เงินเฟ้อญี่ปุ่นรายปี",lines:["วัดการเปลี่ยนราคาสินค้าและบริการที่ครัวเรือนซื้อ","รายปีเทียบเดือนเดียวกันปีก่อน ไม่ใช่เดือนก่อน","เทียบคาดการณ์ และแยกเงินเฟ้อรวมจากดัชนีพื้นฐาน","JPY อาจตอบสนองผ่านมุมมอง BOJ ไม่ใช่ตัวเลขเดียว"],sourceName:"Statistics Bureau Japan · CPI Q&A",sourceUrl:"https://www.stat.go.jp/english/data/cpi/1585.htm"},unemployment:{title:"อัตราว่างงาน",lines:["ผู้ว่างงานหารกำลังแรงงาน ไม่ใช่ประชากรทั้งหมด","สูงขึ้นอาจสะท้อนแรงงานอ่อนลง ไม่ใช่ข่าวดีเสมอ","เทียบคาด พร้อมดูค่าจ้างและการมีส่วนร่วมแรงงาน","ค่าเงินอาจอ่อนหากตลาดคาดลดดอกเบี้ย แต่ไม่เสมอ"],sourceName:"ONS · คู่มือสถิติตลาดแรงงาน",sourceUrl:"https://www.ons.gov.uk/employmentandlabourmarket/peopleinwork/employmentandemployeetypes/methodologies/aguidetolabourmarketstatistics/"},employment:{title:"การเปลี่ยนแปลงการจ้างงาน",lines:["จำนวนผู้มีงานทำที่เปลี่ยนจากเดือนก่อน","ครอบคลุมงานเต็มเวลาและพาร์ตไทม์ ไม่ใช่ค่าจ้าง","เทียบคาด พร้อมดูชั่วโมงทำงานและอัตราว่างงาน","เกินคาดอาจหนุน AUD หากมุมมองเศรษฐกิจดีขึ้น"],sourceName:"ABS · Labour force framework",sourceUrl:"https://www.abs.gov.au/statistics/detailed-methodology-information/concepts-sources-methods/labour-statistics-concepts-sources-and-methods/2023/concepts-and-sources/labour-force-framework"},ecbSpeech:{title:"ถ้อยแถลง ECB",lines:["ติดตามมุมมองเงินเฟ้อและแนวทางดอกเบี้ยของ ECB","เข้มขึ้นเน้นคุมเงินเฟ้อ; ผ่อนคลายเน้นหนุนเศรษฐกิจ","ดูว่าต่างจากตลาดคาดอย่างไร ไม่มีค่าคาดแบบตัวเลข","อาจเปลี่ยนมุมมองต่อ EUR แต่ยังไม่ใช่มติขึ้นดอกเบี้ย"],sourceName:"ECB · นโยบายการเงินคืออะไร",sourceUrl:"https://www.ecb.europa.eu/ecb-and-you/explainers/tell-me/html/what-is-monetary-policy.en.html"},fedSpeech:{title:"ถ้อยแถลง Fed",lines:["ติดตามมุมมองเศรษฐกิจ เงินเฟ้อ และดอกเบี้ยสหรัฐฯ","เข้มขึ้นอาจชี้ดอกเบี้ยสูงนาน; ผ่อนคลายอาจตรงข้าม","ดูสิ่งที่ต่างจากตลาดคาด ไม่ใช่ทุกคำพูดคือมติ Fed","USD อาจขยับผ่านคาดการณ์ดอกเบี้ยและปัจจัยอื่น"],sourceName:"Federal Reserve · ดอกเบี้ยคาดการณ์กับค่าเงิน",sourceUrl:"https://www.federalreserve.gov/econres/notes/ifdp-notes/the-sensitivity-of-the-us-dollar-exchange-rate-to-changes-in-monetary-policy-expectations-20170922.htm"},snbSpeech:{title:"ถ้อยแถลง SNB",lines:["ติดตามนโยบายเงินเฟ้อและดอกเบี้ยสวิตเซอร์แลนด์","มองหาท่าทีที่เปลี่ยนจากเดิมและจากตลาดคาด","ไม่มีผลตัวเลขเทียบคาด และไม่ใช่มตินโยบายเสมอไป","CHF อาจตอบสนอง แต่ยังขึ้นกับเศรษฐกิจและความเสี่ยง"],sourceName:"SNB · นโยบายการเงิน",sourceUrl:"https://www.snb.ch/en/the-snb/mandates-goals/monetary-policy"},generic:{title:"อ่านข่าวเศรษฐกิจอย่างไร",lines:["เริ่มจากชื่อ หน่วย และช่วงเวลาที่ตัวเลขครอบคลุม","แยกการเทียบคาดการณ์ออกจากการเทียบครั้งก่อน","ยังไม่มีผลจริง ให้อ่านเพียงฉากทัศน์ตามเงื่อนไข","ข่าวเดียวไม่ยืนยันทิศกราฟหรือแนวโน้มระยะยาว"],sourceName:"Federal Reserve · ความคาดหวังกับค่าเงิน",sourceUrl:"https://www.federalreserve.gov/econres/notes/ifdp-notes/the-sensitivity-of-the-us-dollar-exchange-rate-to-changes-in-monetary-policy-expectations-20170922.htm"}};function v3(r){if(!r||typeof r!="object")return"generic";const e=typeof r.title=="string"?r.title:"";if(/\bPMI\b/i.test(e))return"pmi";if(r.metric==="inflation"){if(r.currency==="JPY")return"japanCpi";if(r.currency==="CAD")return"canadaCpi";if(r.currency==="USD")return/\bcore\b/i.test(e)?"coreCpi":"cpi"}if(r.metric==="confidence"){if(r.currency==="EUR")return"consumerConfidence";if(r.currency==="NZD")return"businessConfidence"}if(r.metric==="unemployment")return"unemployment";if(r.metric==="employment"&&r.currency==="AUD")return"employment";if(r.kind==="speech"){if(r.currency==="EUR")return"ecbSpeech";if(r.currency==="USD")return"fedSpeech";if(r.currency==="CHF")return"snbSpeech"}return"generic"}function _3(r){const e=x3[v3(r)];return{...e,lines:[...e.lines]}}const y3=460;function S3(r,e,i){const[s,l]=nt.useState(null),[c,f]=nt.useState(!1);return nt.useEffect(()=>{let h,m,p;return r&&e?(l(e),i?f(!0):h=requestAnimationFrame(()=>{m=requestAnimationFrame(()=>f(!0))})):(f(!1),i?l(null):p=setTimeout(()=>l(null),y3)),()=>{cancelAnimationFrame(h),cancelAnimationFrame(m),clearTimeout(p)}},[r,e,i]),{displayPair:s,expanded:c}}const b3=[["all","ทั้งหมด",32],["forex","Forex",28],["metals","Metals",2],["oil","Oil",2]],M3=`linear-gradient(90deg,${[0,10,20,35,50,65,80,90,100].map(r=>`${tf({available:!0,long:r,short:100-r}).color} ${r}%`).join(",")})`;function E3({symbol:r,onSelect:e}){const[i,s]=nt.useState(""),[l,c]=nt.useState(!1),[f,h]=nt.useState(0),m=nt.useRef(null),p=nt.useRef(null),g=yr.filter(x=>`${x.symbol} ${x.name}`.toLowerCase().includes(i.trim().toLowerCase()));nt.useEffect(()=>{const x=_=>{_.composedPath().includes(m.current)||c(!1)};return document.addEventListener("pointerdown",x),()=>document.removeEventListener("pointerdown",x)},[]);const v=x=>{var _;e(x),c(!1),s(""),(_=p.current)==null||_.focus()};return U.jsxs("div",{className:"asset-search",ref:m,children:[U.jsx(O1,{size:18}),U.jsx("input",{ref:p,value:i,role:"combobox","aria-label":"ค้นหาสินทรัพย์ 32 รายการ","aria-expanded":l,"aria-controls":l?"asset-options":void 0,"aria-autocomplete":"list","aria-activedescendant":l&&g[f]?`asset-${g[f].symbol}`:void 0,placeholder:"ค้นหาสินทรัพย์ เช่น EURUSD",onFocus:()=>c(!0),onChange:x=>{s(x.target.value),h(0),c(!0)},onKeyDown:x=>{x.key==="Escape"&&(x.stopPropagation(),c(!1)),(x.key==="ArrowDown"||x.key==="ArrowUp")&&(x.preventDefault(),c(!0),h(_=>Math.max(0,Math.min(g.length-1,_+(x.key==="ArrowDown"?1:-1))))),x.key==="Enter"&&l&&g[f]&&(x.preventDefault(),v(g[f].symbol))}}),l&&U.jsxs("div",{className:"asset-results",id:"asset-options",role:"listbox","aria-label":"ผลค้นหาสินทรัพย์",children:[U.jsxs("div",{className:"result-heading",children:[g.length," สินทรัพย์"]}),g.map((x,_)=>U.jsxs("button",{id:`asset-${x.symbol}`,role:"option","aria-selected":x.symbol===r,className:_===f?"active":"",onPointerMove:()=>h(_),onClick:()=>v(x.symbol),children:[U.jsx("strong",{children:x.symbol}),U.jsx("small",{children:x.assetClass.toUpperCase()})]},x.symbol)),!g.length&&U.jsx("p",{className:"empty-search",children:"ไม่พบสินทรัพย์ ลองค้นหาด้วยชื่อคู่เงิน"})]})]})}function T3({symbol:r,news:e,eventId:i,onEvent:s,highOnly:l,setHighOnly:c,inactive:f,day:h,onDay:m,source:p}){var N,L,z,T,O;const g=l?e.filter(I=>I.impact==="high"):e,v=Object.values(g.reduce((I,W)=>{const J=`${W.dayThai||rs(W.time)}|${W.timeKind||W.timePrecision||"timed"}|${Op(W)}`;return I[J]??(I[J]={key:J,event:W,events:[]}),I[J].events.push(W),I},{})),x=(N=p.availableDays)==null?void 0:N.find(I=>I.dayThai===h),_=!!p.lastSuccessAt,E=!["ready","ok","fresh","empty","cached","partial"].includes(p.status),R=(x==null?void 0:x.fullyCovered)===!0,b=(x==null?void 0:x.count)??ry(null,h).length,S=((L=p.coverage)==null?void 0:L.cachedSourceCount)??((z=p.coverage)==null?void 0:z.sourceCount)??((T=p.calendarEvents)==null?void 0:T.length)??0,F=_?x?R?"ครอบคลุมวันที่เลือก":"ครอบคลุมวันบางส่วน":"อยู่นอกช่วงข้อมูล":as(p),G=_?x?E?"ยังยืนยันข่าวรอบล่าสุดไม่ได้":R?l&&e.length?"ไม่มีข่าวสำคัญในตัวกรองนี้":r&&b?"ไม่มีข่าวตรงกับสินทรัพย์ที่เลือก":"ไม่มีเหตุการณ์ในวันที่เลือก":"ยังยืนยันข่าวครบวันไม่ได้":"วันที่นี้อยู่นอกช่วงข้อมูล":"ยังโหลดปฏิทินไม่สำเร็จ",w=_?x?E?"แสดงเฉพาะข้อมูลรอบที่เก็บไว้ ตรวจสถานะแหล่งข่าวด้านบน":R?l&&e.length?"ปิดตัวกรองเพื่อดูทุกระดับความสำคัญ":r&&b?"เลือกภาพรวมเพื่อดูข่าวทั้งหมดของวันนี้":"แหล่งข่าวส่งปฏิทินมาแล้ว และไม่มีรายการสำหรับวันนี้":"แหล่งข้อมูลครอบคลุมวันนี้เพียงบางช่วง จึงไม่ถือว่าไม่มีข่าวทั้งวัน":"เลือกวันอื่นจากปฏิทิน โดยข้อมูลที่ดึงไว้ยังคงเปิดอ่านได้":"รอการเชื่อมต่อแหล่งข่าว";return U.jsxs("aside",{className:"news-rail","aria-label":"ข่าวที่เกี่ยวข้อง",inert:f,children:[U.jsxs("header",{className:"news-heading",children:[U.jsx("p",{className:"eyebrow",children:"YOUR DAILY BRIEFING"}),U.jsxs("h1",{children:[r?"ข่าวที่เกี่ยวข้อง":"ข่าวภาพรวม"," ",U.jsxs("span",{children:[g.length," เหตุการณ์"]})]}),U.jsxs("h2",{children:[r||"MARKET BRIEF",U.jsx("small",{children:r?((O=yr.find(I=>I.symbol===r))==null?void 0:O.assetClass)==="forex"?`${r.slice(0,3)} + ${r.slice(3)}`:"ข่าว USD ที่เกี่ยวข้อง":"เลือกดาวเพื่อกรองข่าว"})]}),U.jsxs("p",{className:"time-zone",children:[U.jsx(Wx,{size:15}),"เวลาไทย · Asia/Bangkok"]}),U.jsxs("div",{className:"news-date-controls",children:[U.jsx("label",{htmlFor:"calendar-day",className:"sr-only",children:"วันที่ปฏิทินข่าว เวลาไทย"}),U.jsx("input",{id:"calendar-day",type:"date",value:h,onChange:I=>I.target.value&&m(I.target.value)}),U.jsx("button",{onClick:()=>m(rs()),children:"วันนี้"})]}),U.jsxs("div",{className:"news-filter",children:[U.jsx("span",{className:"sample-mini",children:l?"ข่าวสำคัญ":"ทุกระดับความสำคัญ"}),U.jsx("button",{"aria-pressed":l,onClick:()=>c(I=>!I),children:"เฉพาะข่าวสำคัญ"})]}),U.jsxs("div",{className:"news-source-status",role:"status",children:[U.jsxs("a",{href:p.sourceUrl||"https://www.forexfactory.com/calendar",target:"_blank",rel:"noopener noreferrer",children:[p.source||"Forex Factory",U.jsx(Xl,{size:11})]}),U.jsxs("span",{children:[F,E&&_?` · ${as(p)}`:""]}),U.jsxs("small",{children:["วันที่เลือก ",b," · ในช่วงที่ดึงไว้ ",S," รายการ",U.jsx("br",{}),"เป็นรายการจากแหล่งนี้ อาจไม่ครอบคลุมทุกข่าวตลาด"]})]}),p.error==="http_429"&&U.jsxs("p",{className:"news-retry-notice",children:["ต้นทางจำกัดการเรียก · ใช้ปฏิทินรอบที่เก็บไว้",U.jsx("br",{}),"ลองใหม่ ",os(p.nextAttemptAt)," เวลาไทย"]})]}),U.jsxs("div",{className:"news-list",children:[v.map(I=>U.jsxs("section",{className:"news-time-group",children:[U.jsxs("div",{className:"time-heading",children:[U.jsx(qx,{size:10}),U.jsx("time",{dateTime:I.event.time||void 0,children:Op(I.event)}),U.jsx("span",{children:I.events.length>1?`${I.events.length} เหตุการณ์`:I.events[0].currency})]}),U.jsx("div",{className:"events-at-time",children:I.events.map(W=>U.jsxs("button",{id:`news-${W.id}`,className:`news-event ${W.id===i?"selected":""}`,"aria-expanded":W.id===i,"aria-controls":W.id===i?"news-popover":void 0,onClick:()=>s(W.id),children:[U.jsx("span",{className:"event-currency",children:W.currency}),U.jsx("span",{className:"event-title",children:W.title}),U.jsxs("span",{className:`impact ${W.impact}`,title:`ความสำคัญ ${W.impactLabel||"ไม่ระบุ"}`,children:[U.jsx(qx,{size:8}),U.jsx("span",{className:"sr-only",children:W.impactLabel||"ไม่ระบุ"})]})]},W.id))})]},I.key)),!g.length&&U.jsxs("div",{className:"empty-news",children:[U.jsx(A1,{size:28}),U.jsx("h3",{children:G}),U.jsx("p",{children:w})]})]}),U.jsxs("footer",{className:"news-round",children:[U.jsx(Wx,{size:19}),U.jsxs("div",{children:["ปฏิทินอัปเดตวันละครั้ง",U.jsxs("small",{children:["ดึงสำเร็จ ",os(p.lastSuccessAt),U.jsx("br",{}),"กำหนดการที่เก็บไว้ อาจมีการเปลี่ยนภายหลัง"]})]})]})]})}function A3({event:r,symbol:e,onClose:i,onLearnMore:s,explainerOpen:l}){const c=nt.useRef(null);nt.useEffect(()=>{var m;(m=c.current)==null||m.focus({preventScroll:!0})},[r.id]);const f=e?Jw(r,e):[],h=r.numeric||[r.forecast,r.previous].some(m=>m!=null&&m!=="—");return U.jsxs("section",{className:"news-popover",id:"news-popover",role:l?"region":"dialog","aria-modal":l?void 0:!1,"aria-labelledby":"news-title",children:[U.jsxs("header",{children:[U.jsxs("div",{className:"popup-meta",children:[U.jsx("span",{className:"currency-tag",children:r.currency}),U.jsxs("time",{dateTime:r.time||void 0,children:[r.dayThai||rs(r.time)," · ",Op(r)," · ไทย"]})]}),U.jsx("button",{ref:c,className:"icon-button","aria-label":"ปิดบทวิเคราะห์ข่าว",onClick:i,children:U.jsx(Wl,{size:20})})]}),U.jsxs("div",{className:"popup-scroll",children:[U.jsx("h2",{id:"news-title",children:r.title}),r.summary&&U.jsx("p",{className:"news-summary",children:r.summary}),U.jsxs("button",{id:"news-learn-more",className:"news-learn-more","aria-expanded":l,"aria-controls":l?"news-explainer":void 0,onClick:s,children:[U.jsx(zp,{size:16}),"อ่านเพิ่มเติม · ข่าวนี้หมายถึงอะไร"]}),h&&U.jsxs("div",{className:"event-figures",children:[U.jsxs("div",{children:[U.jsx("small",{children:"คาดการณ์"}),U.jsx("strong",{children:r.forecast??"—"})]}),U.jsxs("div",{children:[U.jsx("small",{children:"ครั้งก่อน"}),U.jsx("strong",{children:r.previous??"—"})]})]}),U.jsxs("p",{className:"actual-status",children:["ผลจริง: ",r.actual===null||r.actual===void 0?"แหล่งนี้ไม่ส่งผลจริง":String(r.actual)]}),f.length>0?U.jsxs(U.Fragment,{children:[U.jsxs("div",{className:"scenario-heading",children:["ฉากทัศน์ต่อ ",U.jsx("strong",{children:e}),U.jsx("span",{children:"หากผลออกมา…"})]}),U.jsx("div",{className:"scenario-list",children:f.map(m=>U.jsxs("div",{className:`scenario ${m.direction}`,children:[U.jsxs("div",{children:[U.jsx("span",{className:"scenario-icon",children:m.direction==="up"?U.jsx(v1,{size:18}):m.direction==="down"?U.jsx(g1,{size:18}):U.jsx(E1,{size:18})}),U.jsx("strong",{children:m.label})]}),U.jsx("p",{children:m.summary})]},m.key))}),U.jsxs("p",{className:"scenario-note",children:[f[0].note,U.jsx("br",{}),"ข่าวเดียวไม่พอสรุปทิศทางระยะยาว"]})]}):U.jsx("p",{className:"overview-news-hint",children:e?"ยังไม่มีฉากทัศน์ทิศทางที่รองรับสำหรับข่าวและสินทรัพย์นี้":"เลือกคู่เงินเพื่อดูฉากทัศน์ เมื่อข่าวมีตัวเลขคาดการณ์ที่รองรับ"}),r.datePrecisionNote&&U.jsx("p",{className:"scenario-note",children:r.datePrecisionNote})]}),U.jsxs("footer",{children:[r.sourceUrl?U.jsxs("a",{href:r.sourceUrl,target:"_blank",rel:"noopener noreferrer",children:[r.sourceName,U.jsx(Xl,{size:14})]}):U.jsx("span",{children:r.sourceName||"ไม่ระบุแหล่งข่าว"}),U.jsx("span",{children:"ปฏิทินรอบรายวัน"})]})]})}function w3({event:r,onClose:e}){const i=nt.useRef(null),s=_3(r);return nt.useEffect(()=>{var l,c,f;(l=i.current)==null||l.focus({preventScroll:!0}),matchMedia("(max-width:740px)").matches&&((f=(c=i.current)==null?void 0:c.closest(".news-explainer"))==null||f.scrollIntoView({block:"nearest"}))},[r.id]),U.jsxs("aside",{className:"news-explainer",id:"news-explainer",role:"region","aria-labelledby":"explainer-title",children:[U.jsxs("header",{children:[U.jsxs("div",{children:[U.jsx("p",{className:"eyebrow",children:"UNDERSTAND THE EVENT"}),U.jsx("h2",{id:"explainer-title",children:s.title})]}),U.jsx("button",{ref:i,className:"icon-button","aria-label":"ปิดคำอธิบายข่าว",onClick:e,children:U.jsx(Wl,{size:19})})]}),U.jsx("div",{className:"explainer-points",children:s.lines.map((l,c)=>U.jsxs("p",{children:[U.jsx("span",{children:String(c+1).padStart(2,"0")}),l]},c))}),U.jsxs("footer",{children:[U.jsxs("a",{href:s.sourceUrl,target:"_blank",rel:"noopener noreferrer",children:[s.sourceName,U.jsx(Xl,{size:14})]}),U.jsx("small",{children:"คำอธิบายตัวชี้วัด · ตรวจผลจริงจากแหล่งประกาศ"})]})]})}function C3({event:r,symbol:e,explainerOpen:i,onClose:s,onLearnMore:l,onCloseExplainer:c,embedded:f=!1}){const h=nt.useRef(null);nt.useEffect(()=>{if(!i||f)return;const p=document.body.style.overflow;return document.body.style.overflow="hidden",()=>{document.body.style.overflow=p}},[i,f]);const m=p=>{if(!i||p.key!=="Tab")return;const g=[...h.current.querySelectorAll('button:not(:disabled),a[href],[tabindex="0"]')].filter(_=>_.getClientRects().length),v=g[0],x=g.at(-1);p.shiftKey&&h.current.getRootNode().activeElement===v?(p.preventDefault(),x==null||x.focus()):!p.shiftKey&&h.current.getRootNode().activeElement===x&&(p.preventDefault(),v==null||v.focus())};return U.jsxs("div",{className:`news-reading-layer ${i?"is-expanded":""}`,children:[i&&U.jsx("button",{className:"news-reading-backdrop","aria-label":"ปิดอ่านเพิ่มเติมและกลับสู่ข่าว",tabIndex:-1,onClick:c}),U.jsxs("div",{ref:h,className:"news-reading-panels",role:i?"dialog":void 0,"aria-modal":i||void 0,"aria-label":i?"อ่านข่าวและคำอธิบายเพิ่มเติม":void 0,onKeyDown:m,children:[U.jsx(A3,{event:r,symbol:e,onClose:s,explainerOpen:i,onLearnMore:l}),i&&U.jsx(w3,{event:r,onClose:c})]})]})}function R3({pair:r,source:e}){const i=is(r.symbol),s=tf(i),l=i.long+i.short,c=i.available?i.long/l*100:null,f=h=>typeof h=="number"&&Number.isFinite(h)?h.toFixed(r.assetClass==="metals"||r.assetClass==="oil"?2:r.symbol.endsWith("JPY")?3:5):"—";return U.jsxs("section",{className:"sentiment-card","aria-label":`Sentiment ${r.symbol}`,children:[U.jsxs("header",{children:[U.jsx(z1,{size:19}),U.jsxs("div",{children:[U.jsx("h2",{children:"COMMUNITY SENTIMENT"}),U.jsxs("small",{children:["Myfxbook · ",as(e)]})]})]}),i.available?U.jsxs(U.Fragment,{children:[U.jsxs("div",{className:"sentiment-ratio",children:[U.jsxs("div",{className:"short",children:[U.jsx("small",{children:"SHORT"}),U.jsxs("strong",{children:[i.short,U.jsx("span",{children:"%"})]})]}),U.jsxs("div",{className:"ratio-caption",children:["สัดส่วนสถานะ",U.jsx("br",{}),"ของชุมชน"]}),U.jsxs("div",{className:"long",children:[U.jsx("small",{children:"LONG"}),U.jsxs("strong",{children:[i.long,U.jsx("span",{children:"%"})]})]})]}),U.jsxs("div",{className:"average-prices",children:[U.jsxs("div",{children:[U.jsx("small",{children:"ราคา Short เฉลี่ย"}),U.jsx("strong",{className:"short",children:f(i.avgShort)})]}),U.jsxs("div",{children:[U.jsx("small",{children:"ราคา Long เฉลี่ย"}),U.jsx("strong",{className:"long",children:f(i.avgLong)})]})]})]}):U.jsxs("div",{className:"no-sentiment",children:[U.jsx(zp,{size:22}),U.jsx("strong",{children:"ยังไม่มีข้อมูล Sentiment"}),U.jsx("span",{children:"ไม่แทนค่าที่ขาดหายด้วย Short/Long 50/50"})]}),i.available&&U.jsxs("div",{className:"stellar-color-key","aria-label":"ระดับสีดาวตามสัดส่วน Sentiment",children:[U.jsx("div",{className:"stellar-color-scale",style:{background:M3},children:U.jsx("i",{style:{left:`${c}%`,background:s.color}})}),U.jsxs("div",{children:[U.jsx("span",{children:"SHORT 100%"}),U.jsx("span",{children:"50 / 50"}),U.jsx("span",{children:"LONG 100%"})]})]}),i.available&&Math.abs(l-100)>1e-6&&U.jsxs("p",{className:"rounding-note",children:["ตัวเลขจากแหล่งข้อมูลรวม ",l,"% จากการปัดเศษ · ปรับเฉพาะตำแหน่งสีให้ครบ 100%"]}),U.jsxs("div",{className:"sentiment-source-meta",children:[U.jsxs("span",{children:["ดึงสำเร็จ ",os(e.lastSuccessAt)]}),i.available&&U.jsxs("span",{children:["ข้อมูลรายการนี้ ",os(i.asOf)]}),i.available&&i.avgLong===null&&i.avgShort===null&&U.jsx("span",{children:"แหล่งข้อมูลไม่มีราคาเฉลี่ยของรายการนี้"})]}),U.jsx("p",{children:"สีดาว = สัดส่วนสถานะของชุมชน ไม่ใช่แนวโน้มราคา"})]})}function U3({pair:r,motionClock:e,playing:i,speed:s,connection:l,onClose:c,onClearConnection:f,onSelect:h,relatedCount:m,correlationsVisible:p,filter:g,onConnectionSelect:v,dataRevision:x,market:_}){const E=nt.useRef(null);nt.useEffect(()=>{E.current&&(E.current.scrollTop=0)},[r.symbol]);const R=Lp(r.symbol).filter(S=>{var F;return g==="all"||((F=yr.find(G=>G.symbol===S.symbol))==null?void 0:F.assetClass)===g}),b=l&&(l.source===r.symbol?l.target:l.source);return U.jsxs("aside",{className:"stellar-inspector","aria-label":`รายละเอียด ${r.symbol}`,children:[U.jsxs("header",{className:"inspector-heading",children:[U.jsxs("div",{children:[U.jsx("p",{className:"eyebrow",children:"STELLAR OBSERVATORY"}),U.jsxs("h2",{children:[r.symbol,U.jsx("span",{children:r.assetClass.toUpperCase()})]})]}),U.jsx("button",{className:"icon-button","aria-label":"ปิดรายละเอียดดาว",onClick:c,children:U.jsx(Wl,{size:19})})]}),U.jsxs("div",{className:"inspector-scroll",ref:E,children:[U.jsxs("div",{className:"stellar-hero",children:[U.jsx(d3,{symbol:r.symbol,motionClock:e,playing:i,motionSpeed:s,dataRevision:x}),U.jsx("span",{className:"stellar-caption",children:r.name})]}),U.jsx(R3,{pair:r,source:_.sentiment}),U.jsxs("section",{className:"connection-detail","aria-label":"รายละเอียดเส้น Correlation",children:[U.jsxs("div",{className:"connection-title",children:[U.jsx(Hu,{size:16}),U.jsx("h3",{children:"CORRELATION"}),l&&U.jsx("button",{className:"icon-button","aria-label":"ล้างเส้นที่เลือก",onClick:f,children:U.jsx(Wl,{size:15})})]}),l?U.jsxs(U.Fragment,{children:[U.jsxs("div",{className:"connection-pair",children:[U.jsx("button",{onClick:()=>h(l.source),children:l.source}),U.jsx(Hu,{size:15}),U.jsx("button",{onClick:()=>h(l.target),children:l.target})]}),U.jsxs("div",{className:`connection-value ${kl(l.value)}`,style:{color:pi(l.value)},children:[U.jsxs("strong",{children:[l.value>=0?"+":"",Math.round(l.value*100),U.jsx("small",{children:"%"})]}),U.jsx("span",{children:kl(l.value)==="neutral"?"สัมพันธ์อ่อน / ใกล้ศูนย์":l.value>0?"สัมพันธ์ในทิศทางเดียวกัน":"สัมพันธ์ในทิศทางตรงข้าม"})]}),U.jsxs("p",{children:["MT5 · Pearson จากผลตอบแทน H1 ที่ปิดแล้ว",U.jsx("br",{}),l.samples," ช่วงตรงกัน · สิ้นสุด ",os(l.endAt)]})]}):U.jsx("p",{className:"connection-empty",children:p?U.jsxs(U.Fragment,{children:["เน้น ",m," เส้นที่มีข้อมูลของ ",r.symbol,U.jsx("br",{}),m?"กดชื่อบนเส้น หรือเลือกจากรายการด้านล่าง":"ยังไม่มีราคาที่เพียงพอและตรงช่วงเวลา"]}):U.jsxs(U.Fragment,{children:["ซ่อนเส้นอยู่ · เปิด Correlation",U.jsx("br",{}),"เพื่อดูความสัมพันธ์กับดาวอื่น"]})}),U.jsxs("p",{className:"correlation-source-meta",children:["MT5 · ",as(_.correlations),_.correlations.marketStatus==="market_closed"?" · ตลาดปิด":"",U.jsx("br",{}),"แท่งข้อมูลล่าสุด ",os(_.correlations.asOf)]}),U.jsxs("div",{className:"correlation-list-heading",children:[U.jsxs("strong",{children:["คู่ที่สัมพันธ์ ",U.jsx("span",{children:R.length})]}),U.jsx("small",{children:"เรียงตามความสัมพันธ์มาก → น้อย"})]}),U.jsx("div",{className:"correlation-list",role:"region","aria-label":`รายการ Correlation ของ ${r.symbol}`,tabIndex:0,children:R.map(S=>U.jsxs("button",{className:`correlation-row ${kl(S.value)}`,style:{"--correlation-color":pi(S.value)},"aria-label":`${r.symbol} กับ ${S.symbol} ${S.value>=0?"+":""}${Math.round(S.value*100)}%`,"aria-pressed":b===S.symbol,onClick:()=>v({source:r.symbol,target:S.symbol,value:S.value}),children:[U.jsx("span",{className:"correlation-symbol",children:S.symbol}),U.jsx("span",{className:"correlation-meter",children:U.jsx("i",{style:{width:`${Math.abs(S.value)*100}%`}})}),U.jsxs("strong",{children:[S.value>=0?"+":"",Math.round(S.value*100),"%"]})]},S.symbol))},`${r.symbol}:${g}`),U.jsx("p",{className:"list-scroll-hint",children:R.length?"กดคู่ที่มีข้อมูลเพื่อเน้นเส้นบนกาแล็กซี่":"ไม่มีเส้นที่คำนวณได้สำหรับสินทรัพย์นี้"})]}),U.jsxs("p",{className:"inspector-note",children:[U.jsx("span",{className:"gold-key",children:"จุดสีทอง"})," = ดาวที่เชื่อมกับดาวที่เลือก",U.jsx("br",{}),"แสงวิ่งบนเส้นเมื่อ Correlation > +70% หรือ < −70%",U.jsx("br",{}),"ความสัมพันธ์ย้อนหลัง ไม่ใช่การคาดการณ์ราคา",U.jsx("br",{}),"โมชั่นใช้ประกอบภาพ ไม่ใช่คำสั่งซื้อขาย"]})]})]})}function D3({assetBase:r="/",marketUrl:e="/api/market",setupUrl:i="/connect",embedded:s=!1,requireHeartbeat:l=!1}={}){var xe;const c=nt.useRef(null),f=p3({marketUrl:e,requireHeartbeat:l}),[h,m]=nt.useState(null),[p,g]=nt.useState("all"),[v,x]=nt.useState(null),[_,E]=nt.useState(!1),[R,b]=nt.useState(()=>rs()),S=nt.useRef(rs()),[F,G]=nt.useState(!0),[w,N]=nt.useState(1),[L,z]=nt.useState(()=>matchMedia("(prefers-reduced-motion: reduce)").matches),[T,O]=nt.useState(!0),[I,W]=nt.useState(0),[J,re]=nt.useState("loading"),[k,K]=nt.useState(!1),[B,V]=nt.useState(!1),[ee,oe]=nt.useState(null),[fe,D]=nt.useState(!1),se=nt.useRef({value:0}),_e=yr.find(ne=>ne.symbol===h)||null,De=nt.useMemo(()=>ry(h,R),[h,R,f.revision]),ze=nt.useMemo(()=>Kw(p),[p,f.revision]),Xe=ee&&ze.find(ne=>ne.source===ee.source&&ne.target===ee.target||ne.source===ee.target&&ne.target===ee.source)||null,{displayPair:ue,expanded:Se}=S3(B,_e,L),Re=De.find(ne=>ne.id===v),at=!!(Re&&fe),Ge=yr.filter(ne=>p==="all"||ne.assetClass===p).length,mt=Ge*(Ge-1)/2,un=ze.length,ut=ze.filter(ne=>ne.source===h||ne.target===h).length,xt=(f.correlations.instruments||[]).filter(ne=>ne.status==="missing").map(ne=>ne.symbol),bt=ne=>{b(ne),x(null),D(!1)},pt=nt.useCallback(ne=>{m(ne),V(!0),oe(null),x(null),D(!1),g(Ae=>{var pe;return Ae!=="all"&&((pe=yr.find(ye=>ye.symbol===ne))==null?void 0:pe.assetClass)!==Ae?"all":Ae})},[]),vt=nt.useCallback(ne=>{m(Ae=>Ae===ne.source||Ae===ne.target?Ae:ne.source),oe(ne),V(!0),O(!0),x(null),D(!1)},[]),Gt=nt.useCallback(()=>{const ne=Re==null?void 0:Re.id;x(null),D(!1),requestAnimationFrame(()=>{var Ae,pe;return(pe=(Ae=c.current)==null?void 0:Ae.getRootNode().getElementById(`news-${ne}`))==null?void 0:pe.focus({preventScroll:!0})})},[Re==null?void 0:Re.id]),vn=nt.useCallback(()=>{D(!1),requestAnimationFrame(()=>{var ne,Ae;return(Ae=(ne=c.current)==null?void 0:ne.getRootNode().getElementById("news-learn-more"))==null?void 0:Ae.focus({preventScroll:!0})})},[]),Xt=nt.useCallback(()=>{V(!1),requestAnimationFrame(()=>{var ne,Ae;return(Ae=(ne=c.current)==null?void 0:ne.getRootNode().getElementById("open-stellar-inspector"))==null?void 0:Ae.focus({preventScroll:!0})})},[]),fn=nt.useCallback(()=>re("ready"),[]),j=nt.useCallback(()=>re("error"),[]),Ft=ne=>{g(ne),oe(null),_e&&ne!=="all"&&_e.assetClass!==ne&&(m(null),V(!1),x(null),D(!1))},Ut=()=>{g("all"),m(null),V(!1),oe(null),x(null),D(!1),K(!1),O(!0),W(ne=>ne+1),G(!0)};nt.useEffect(()=>{const ne=rs(),Ae=S.current;ne!==Ae&&(b(pe=>pe===Ae?ne:pe),S.current=ne)},[f.revision]),nt.useEffect(()=>{const ne=matchMedia("(prefers-reduced-motion: reduce)"),Ae=pe=>z(pe.matches);return ne.addEventListener("change",Ae),()=>ne.removeEventListener("change",Ae)},[]),nt.useEffect(()=>{s||(document.title="Metafxclub · Sentiment Universe")},[s]);const P=ne=>g3(ne,{embedded:s,root:c.current,explainerOpen:fe,eventOpen:!!Re,settingsOpen:k,inspectorOpen:B,closeExplainer:vn,closeNews:Gt,closeSettings:()=>K(!1),closeInspector:Xt,toggleMotion:()=>G(Ae=>!Ae)}),M=["offline","stale"].includes(f.connection),Z=[f.sentiment,f.correlations].some(ne=>["needs_configuration","auth_error","auth_failed","authentication_failed"].includes(ne.status)),ce=f.connection==="stale"?"บริการข้อมูลหยุดอัปเดต · แสดงข้อมูลรอบที่เก็บไว้":f.connection==="offline"?"ยังเชื่อมบริการข้อมูลไม่ได้ · แสดงข้อมูลรอบที่เก็บไว้":"เชื่อมบัญชี Myfxbook และเลือก MT5 ของเครื่องนี้ครั้งแรก";return U.jsxs("div",{ref:c,onKeyDown:P,className:`app-shell ${L?"reduce-motion":""}`,children:[U.jsxs("header",{className:"app-header",inert:at,children:[U.jsxs("a",{className:"brand",href:"#universe","aria-label":"Metafxclub กลับภาพรวม",onClick:ne=>{ne.preventDefault(),Ut()},children:[U.jsx("img",{src:cy(r,"metafx-mark.png"),alt:""}),U.jsx("span",{children:"METAFXCLUB"})]}),U.jsx("div",{className:"product-title",children:"SENTIMENT UNIVERSE"}),U.jsx("div",{className:"asset-filters",role:"group","aria-label":"กรองกลุ่มสินทรัพย์",children:b3.map(([ne,Ae,pe])=>U.jsxs("button",{className:p===ne?"current":"","aria-pressed":p===ne,onClick:()=>Ft(ne),children:[Ae," ",U.jsx("span",{children:pe})]},ne))}),U.jsx(E3,{symbol:h,onSelect:pt}),U.jsxs("a",{className:"demo-badge live-connect",href:i,target:"_blank",rel:"noopener noreferrer",title:`Myfxbook · ${as(f.sentiment)}`,children:["ตั้งค่า Myfxbook / MT5 ",U.jsx(Xl,{size:12})]})]}),U.jsxs("main",{className:`app-main ${Se?"has-inspector":""}`,id:"universe",children:[U.jsx(T3,{inactive:at,symbol:h,news:De,eventId:Re==null?void 0:Re.id,onEvent:ne=>{x(ne===(Re==null?void 0:Re.id)?null:ne),D(!1)},highOnly:_,setHighOnly:E,day:R,onDay:bt,source:f.news}),U.jsxs("div",{className:"galaxy-stage",inert:at,children:[U.jsx("div",{className:"scene-host",tabIndex:-1,children:U.jsx(f3,{assetBase:r,pairs:yr,selectedSymbol:h,filter:p,axis:"free",reducedMotion:L,playing:F&&!L,motionSpeed:w,motionClock:se,resetKey:I,correlationsVisible:T,selectedCorrelation:Xe,dataRevision:f.revision,onCorrelationSelect:vt,onSelect:pt,onReady:fn,onError:j})}),(M||Z)&&U.jsxs("section",{className:"connection-notice","aria-label":"สถานะแหล่งข้อมูล",children:[U.jsxs("div",{role:"status",children:[U.jsx("strong",{children:ce}),M&&U.jsxs("small",{children:["ตรวจบริการในเครื่อง · ข้อมูลต้นทางสำเร็จล่าสุด Myfxbook ",os(f.sentiment.lastSuccessAt)]})]}),U.jsxs("a",{href:i,target:"_blank",rel:"noopener noreferrer",children:["เปิดการตั้งค่า ",U.jsx(Xl,{size:13})]})]}),J!=="ready"&&U.jsx("div",{className:"scene-status",role:"status",children:J==="error"?"เปิดมุมมอง 3D ไม่สำเร็จ ยังเลือกสินทรัพย์จากช่องค้นหาได้":"กำลังเตรียมกาแล็กซี่…"}),U.jsxs("div",{className:"scene-topbar",children:[_e?U.jsxs("button",{id:"open-stellar-inspector",className:"view-label","aria-label":`เปิดรายละเอียด ${h}`,"aria-expanded":B,onClick:()=>V(!0),children:[_e.clusterId," / ",U.jsx("strong",{children:h})]}):U.jsxs("div",{className:"view-label overview-label",children:["ภาพรวม ",U.jsxs("strong",{children:[Ge," สินทรัพย์"]})]}),U.jsxs("div",{className:"view-tools",children:[U.jsxs("button",{className:"tool-button","aria-pressed":T,onClick:()=>{O(ne=>!ne),oe(null)},children:[U.jsx(Hu,{size:16}),"Correlation ",U.jsx("span",{children:T?un:0})]}),U.jsx("button",{className:"icon-button","aria-label":F&&!L?"หยุดโมชั่นทั้งหมด":"เริ่มโมชั่น",disabled:L,onClick:()=>G(ne=>!ne),children:F&&!L?U.jsx(C1,{size:19}):U.jsx(U1,{size:19})}),U.jsx("button",{className:"icon-button","aria-label":"ตั้งค่าการเคลื่อนไหว","aria-expanded":k,onClick:()=>K(ne=>!ne),children:U.jsx(p1,{size:19})})]})]}),k&&U.jsxs("section",{className:"view-settings","aria-label":"ตั้งค่าการเคลื่อนไหว",children:[U.jsxs("header",{children:[U.jsx("strong",{children:"การเคลื่อนไหว"}),U.jsx("button",{className:"icon-button","aria-label":"ปิดการตั้งค่า",onClick:()=>K(!1),children:U.jsx(Wl,{size:18})})]}),U.jsxs("label",{children:["ความเร็ว",U.jsxs("select",{"aria-label":"ความเร็วโมชั่น",value:w,onChange:ne=>N(Number(ne.target.value)),children:[U.jsx("option",{value:"0.5",children:"0.5×"}),U.jsx("option",{value:"1",children:"1×"}),U.jsx("option",{value:"1.8",children:"1.8×"})]})]}),U.jsxs("label",{children:["ลดการเคลื่อนไหว",U.jsx("input",{type:"checkbox",checked:L,onChange:ne=>z(ne.target.checked)})]}),U.jsx("p",{children:"โมชั่นเป็นภาพประกอบ ไม่ใช่การส่งคำสั่งเทรด"})]}),U.jsxs("div",{className:"scene-bottom",children:[U.jsx("div",{className:"camera-controls",role:"group","aria-label":"ควบคุมมุมมอง",children:U.jsxs("button",{className:"reset-overview","aria-label":"รีเซต กลับภาพรวมไม่เลือกสินทรัพย์",onClick:Ut,children:[U.jsx(N1,{size:17}),U.jsx("span",{children:"รีเซต"})]})}),U.jsx("span",{className:"scene-hint",children:"ลากซ้ายหมุน · ลากขวาเลื่อน · ล้อเมาส์ซูม"})]}),T&&U.jsxs("div",{className:"correlation-legend","aria-label":"คำอธิบายสีเส้น Correlation",children:[U.jsxs("span",{children:[U.jsx(Hu,{size:14}),h?`${h} · เน้น ${ut} / ${un} เส้น`:`คำนวณได้ ${un} / ${mt} เส้น`]}),U.jsxs("div",{className:"correlation-color-bands",children:[U.jsxs("b",{style:{color:pi(0)},children:[U.jsx("i",{style:{background:pi(0)}}),"เหลือง −30% ถึง +30%"]}),U.jsx("small",{children:"ใกล้ 0% ช่วง ±10% สว่างขึ้น"}),U.jsxs("b",{style:{color:pi(.6)},children:[U.jsx("i",{style:{background:pi(.6)}}),"เขียว +40 ถึง <80%"]}),U.jsxs("b",{style:{color:pi(.9)},children:[U.jsx("i",{style:{background:pi(.9)}}),"เข้ม +80 ถึง +100%"]}),U.jsxs("b",{style:{color:pi(-.6)},children:[U.jsx("i",{style:{background:pi(-.6)}}),"แดง −40 ถึง >−80%"]}),U.jsxs("b",{style:{color:pi(-.9)},children:[U.jsx("i",{style:{background:pi(-.9)}}),"เข้ม −80 ถึง −100%"]})]}),U.jsx("small",{children:"ช่วง ±30–40% ไล่สีต่อเนื่อง"}),U.jsx("small",{children:h?"จุดทอง = ดาวที่เชื่อมกับดาวที่เลือก":"เน้นเส้นที่ความสัมพันธ์ตั้งแต่ ±60%"}),U.jsx("small",{children:"แสงวิ่งเฉพาะ > +70% หรือ < −70%"}),U.jsxs("small",{className:"live-correlation-status",children:["MT5 · ",as(f.correlations),f.correlations.marketStatus==="market_closed"?" · ตลาดปิด":"",U.jsx("br",{}),"H1 ล่าสุด ",os(f.correlations.asOf),xt.length>0&&U.jsxs(U.Fragment,{children:[U.jsx("br",{}),xt.join(", ")," ยังไม่มีข้อมูล H1 ที่ใช้คำนวณจาก MT5"]})]})]})]}),U.jsx("div",{className:`inspector-dock ${Se?"is-open":""}`,"aria-hidden":!B||at,inert:!B||at,"data-state":Se?"open":ue?"closing":"closed",children:ue&&U.jsx(U3,{pair:ue,motionClock:se,playing:F&&!L&&B,speed:w,connection:Xe,dataRevision:f.revision,market:f,onClose:Xt,onClearConnection:()=>oe(null),onSelect:pt,relatedCount:ut,correlationsVisible:T,filter:p,onConnectionSelect:vt})}),Re&&U.jsx(C3,{embedded:s,event:Re,symbol:h,explainerOpen:fe,onClose:Gt,onLearnMore:()=>D(ne=>!ne),onCloseExplainer:vn})]}),U.jsxs("footer",{className:"app-footer",inert:at,children:[U.jsxs("span",{children:[U.jsx(zp,{size:15}),"คลิกดาวดูเส้นเชื่อม · ลากซ้ายหมุน · ลากขวาเลื่อน · ล้อเมาส์ซูม"]}),U.jsxs("span",{className:"live-flow-status",role:"status",children:[M?ce:f.connection==="loading"?"กำลังเชื่อมบริการข้อมูล":`Myfxbook ${as(f.sentiment)} · MT5 ${((xe=f.correlations.coverage)==null?void 0:xe.available)??0}/32 · ปฏิทิน ${f.news.status==="empty"?"พร้อม":as(f.news)}`," · ไม่มีการส่งคำสั่งเทรด"]})]}),U.jsxs("div",{className:"sr-only","aria-live":"polite",children:[h?`เลือก ${h}`:"ภาพรวม ยังไม่เลือกสินทรัพย์"," มีข่าว ",De.length," เหตุการณ์"]})]})}function N3(r={},e){const i=f=>{const h=new URL(f,e);if(h.origin!==new URL(e).origin||h.username||h.password)throw new Error("same_origin_required");return h},s=i(r.assetBase||"/frontend/public/sentiment-universe/");s.pathname.endsWith("/")||(s.pathname+="/"),s.search="",s.hash="";const l=i(r.marketUrl||new URL("market.json",s).href).href,c=new URL(r.setupUrl||"http://127.0.0.1:4197/connect",e);if(c.protocol!=="http:"||c.hostname!=="127.0.0.1"||c.username||c.password||c.pathname!=="/connect"||c.search||c.hash)throw new Error("local_setup_required");return{assetBase:s.href,marketUrl:l,setupUrl:c.href,embedded:!0,requireHeartbeat:!0}}const L3=":root{font-family:Sarabun,sans-serif;color:#e5edf5;background:#020a12;color-scheme:dark;font-synthesis:none;text-rendering:optimizeLegibility;-webkit-font-smoothing:antialiased;--cyan:#17d5ee;--muted:#94acc2;--line:#203c50;--long:#43e4c4;--short:#fa7282}*{box-sizing:border-box}body{margin:0;min-width:360px}button,input,select{font:inherit}button{cursor:pointer;color:inherit;border:0;background:none;transition:background-color .15s,border-color .15s}button:disabled{opacity:.4;cursor:not-allowed}a{color:var(--cyan)}button:focus-visible,a:focus-visible,input:focus-visible,select:focus-visible{outline:2px solid var(--cyan);outline-offset:3px}svg{flex-shrink:0}button,a{touch-action:manipulation}::-webkit-scrollbar{width:5px;height:5px}::-webkit-scrollbar-thumb{background:#28465e;border-radius:5px}::-webkit-scrollbar-track{background:#06111d}.sr-only{position:absolute;width:1px;height:1px;padding:0;margin:-1px;overflow:hidden;clip:rect(0,0,0,0);white-space:nowrap;border:0}.long{color:var(--long)}.short{color:var(--short)}.app-shell{display:grid;grid-template-rows:60px minmax(0,1fr) 32px;height:100dvh;min-height:640px;overflow:hidden}.app-header{display:flex;gap:22px;align-items:center;padding:0 22px;background:#030c14;border-bottom:1px solid var(--line);z-index:30;min-width:0}.brand{display:flex;align-items:center;gap:9px;text-decoration:none;flex-shrink:0}.brand img{width:37px;height:28px;object-fit:contain}.brand span{font:700 27px Rajdhani,sans-serif;letter-spacing:.7px}.product-title{font:600 23px Rajdhani,sans-serif;letter-spacing:.5px;white-space:nowrap;border-left:1px solid var(--line);padding-left:22px}.asset-filters{display:flex;gap:7px;white-space:nowrap;margin-left:auto}.asset-filters button{height:34px;border:1px solid #28485f;border-radius:4px;padding:0 13px;font-size:12px;color:#a9bfd3;background:#04111b}.asset-filters button.current{color:#e8faff;border-color:#16c9e5;background:#073144;box-shadow:0 0 12px #06c5e51c}.asset-filters button:hover{background:#123147}.asset-filters button span{padding-left:3px}.demo-badge{font-size:10px;padding:8px;border:1px solid #a97d33;color:#ffc16a;border-radius:4px;white-space:nowrap}.asset-search{display:flex;gap:8px;position:relative;align-items:center;min-width:160px;width:260px;flex:0 1 260px;border:1px solid #28485f;border-radius:4px;padding:0 10px;height:35px;color:#9ebbd3}.asset-search input{width:100%;min-width:0;background:none;border:0;outline:none;color:#e3edf7;font-size:12px}.asset-search input::placeholder{color:#8ca6bd}.asset-results{position:absolute;right:0;top:43px;width:290px;max-height:450px;overflow:auto;border:1px solid #2f627c;border-radius:6px;background:#061421;box-shadow:0 16px 40px #000a;z-index:100}.result-heading{padding:12px;color:var(--muted);font-size:11px;border-bottom:1px solid var(--line)}.asset-results button{display:flex;justify-content:space-between;padding:10px 14px;width:100%;align-items:center}.asset-results button.active{background:#12334a}.asset-results strong{font:600 19px Rajdhani,sans-serif}.asset-results small{color:var(--muted);font-size:10px}.empty-search{padding:16px;font-size:12px;color:var(--muted)}.app-main{display:grid;grid-template-columns:310px minmax(0,1fr);min-height:0}.news-rail{position:relative;z-index:10;display:flex;flex-direction:column;min-height:0;background:#030f19;border-right:1px solid #254054}.news-heading{padding:22px 20px 16px;border-bottom:1px solid var(--line)}.eyebrow{font:500 11px Rajdhani,sans-serif;letter-spacing:2px;color:#4e9caf;margin:0 0 8px}.news-heading h1{font-size:18px;font-weight:600;margin:0 0 17px;display:flex;align-items:center;justify-content:space-between;gap:8px}.news-heading h1 span{font-size:12px;color:#a5bfd1;font-weight:400}.news-heading h2{display:flex;gap:15px;align-items:center;font:600 25px Rajdhani,sans-serif;margin:0 0 7px}.news-heading h2 small{font:400 12px Sarabun,sans-serif;color:#95b6ce}.time-zone{display:flex;gap:6px;align-items:center;font-size:11px;color:#91acc4;margin:0 0 17px}.news-filter{display:flex;align-items:center;justify-content:space-between;gap:8px}.sample-mini{font-size:10px;border:1px solid #846735;border-radius:3px;padding:4px 6px;color:#e8b866}.news-filter button{font-size:10px;color:#87a8be;padding:4px 0}.news-filter button[aria-pressed=true]{color:var(--cyan)}.news-list{padding:14px 14px 8px 20px;min-height:0;flex:1;overflow:auto}.news-time-group{padding:4px 0 20px 20px;border-left:1px solid #294e63;position:relative}.news-time-group:last-child{border-left-color:transparent;padding-bottom:4px}.time-heading{display:flex;align-items:center;gap:12px;margin-bottom:10px;font:500 18px Rajdhani,sans-serif;color:#c2d7e8}.time-heading>svg{position:absolute;left:-5.5px;color:#31c8e1}.time-heading>span{font:400 10px Sarabun,sans-serif;color:#93abc0}.events-at-time{display:flex;flex-direction:column;gap:6px}.news-event{display:flex;align-items:center;gap:8px;text-align:left;padding:9px 8px;width:100%;border:1px solid transparent;border-radius:4px;position:relative;color:#d7e5ef;background:#06121d;min-height:42px}.news-event:hover{background:#0c2535;border-color:#244d66}.news-event.selected{border-color:#13cce6;background:#052b3a;box-shadow:inset 3px 0 #20d7ed}.event-currency{font:500 13px Rajdhani,sans-serif;color:#6c97ae}.event-title{font-size:12px;line-height:1.5;flex:1}.impact{color:#dba359;display:flex;align-items:center}.impact.high{color:#ff7e81}.news-round{display:flex;align-items:center;gap:10px;margin:0 20px;padding:17px 0;border-top:1px solid var(--line);font-size:11px;color:#aac0d2}.news-round small{display:block;font-size:10px;margin-top:4px;color:#6f91a9}.empty-news{padding:35px 5px;color:#82a4bc;text-align:center}.empty-news h3{font-size:13px}.empty-news p{font-size:11px;line-height:1.7}.galaxy-stage{position:relative;isolation:isolate;overflow:hidden;min-width:0;background:#020a13}.scene-host{position:absolute;top:0;right:0;bottom:0;left:0;width:100%;height:100%}.scene-topbar{position:absolute;top:17px;left:24px;right:20px;display:flex;align-items:center;justify-content:space-between;pointer-events:none;z-index:4}.view-label{font:500 13px Rajdhani,sans-serif;color:#87a8be;letter-spacing:1.1px;padding:8px 11px;background:#04111dc9;border:1px solid #1c3c4a;border-radius:4px}.view-label strong{color:#c7e8f4}.view-tools{display:flex;align-items:center;gap:8px;pointer-events:auto}.tool-button{display:flex;align-items:center;gap:6px;height:32px;padding:0 10px;background:#03121ee6;border:1px solid #294c62;border-radius:4px;font:500 14px Rajdhani,sans-serif;color:#8aa8bf}.tool-button[aria-pressed=true]{color:#c9eff8;border-color:#317088}.icon-button{width:31px;height:31px;display:inline-flex;align-items:center;justify-content:center;border-radius:4px;background:#061522c9;color:#8faec5}.icon-button:hover{background:#173349;color:#dcf5ff}.scene-status{position:absolute;top:0;right:0;bottom:0;left:0;display:grid;place-items:center;pointer-events:none;background:#03101bbb;color:#b4d9e9;z-index:3;font-size:13px}.scene-bottom{position:absolute;bottom:22px;left:24px;display:flex;align-items:center;gap:15px;z-index:5}.camera-controls{display:flex;align-items:center;gap:2px;padding:4px;border:1px solid #28475b;border-radius:5px;background:#04121eea}.camera-controls button{height:30px;min-width:34px;padding:0 8px;font:500 14px Rajdhani,sans-serif;color:#7f9db3;display:flex;align-items:center;justify-content:center;border-radius:3px}.camera-controls button[aria-pressed=true]{background:#123347;color:#cbf7ff}.scene-hint{font-size:10px;color:#9ab3c8;background:#04111bbf;padding:6px 8px;border-radius:3px}.view-settings{position:absolute;right:22px;top:62px;z-index:25;background:#061725;border:1px solid #31556d;border-radius:7px;padding:12px 15px;width:255px;box-shadow:0 15px 30px #0008}.view-settings header{display:flex;align-items:center;justify-content:space-between;font-size:13px;margin-bottom:10px}.view-settings label{display:flex;align-items:center;justify-content:space-between;padding:10px 0;font-size:12px;border-bottom:1px solid var(--line)}.view-settings select{padding:4px 8px;border:1px solid #345365;background:#091f2f;border-radius:3px}.view-settings p{font-size:10px;line-height:1.7;color:#8da7bd}.news-popover{position:absolute;left:24px;top:18%;width:365px;max-height:74%;display:flex;flex-direction:column;z-index:20;border:1px solid #0fa7c7;border-radius:10px;background:#03121ef5;box-shadow:0 16px 60px #0009,0 0 25px #00b4da0a;-webkit-backdrop-filter:blur(15px);backdrop-filter:blur(15px)}.news-popover>header{padding:12px 15px 10px 19px;display:flex;align-items:center;justify-content:space-between;border-bottom:1px solid #1d374a}.popup-meta{display:flex;align-items:center;gap:10px;color:#b2cde0;font-size:12px}.currency-tag{color:#55d1ea;font:600 15px Rajdhani,sans-serif;background:#0d2a3d;border:1px solid #28536b;border-radius:4px;padding:3px 6px}.popup-scroll{padding:16px 19px 8px;overflow:auto;min-height:0}.news-popover h2{font-size:22px;margin:0 0 9px;font-weight:600}.news-summary{font-size:12px;line-height:1.7;color:#a3bcd1;margin:0 0 16px}.event-figures{display:grid;grid-template-columns:1fr 1fr;margin-bottom:11px}.event-figures>div{padding-right:20px}.event-figures>div+div{padding-left:20px;border-left:1px solid #1d3c51}.event-figures small{display:block;font-size:11px;color:#96afc5;margin-bottom:5px}.event-figures strong{font:600 28px Rajdhani,sans-serif}.actual-status{font-size:11px;color:#dfb46d;padding:9px 10px;background:#28231b70;border:1px solid #62513980;border-radius:4px;margin:0 0 15px;line-height:1.6}.scenario-heading{display:flex;gap:5px;align-items:center;font-size:11px;color:#98b4c9;margin:0 0 9px}.scenario-heading strong{font:600 15px Rajdhani,sans-serif;color:#dcf2fa}.scenario-heading span{margin-left:auto;color:#62869e;font-size:10px}.scenario-list{display:flex;flex-direction:column;gap:7px}.scenario{border:1px solid #204356;border-radius:5px;background:#071926;padding:9px 10px}.scenario>div{display:flex;align-items:center;gap:8px;font-size:11px}.scenario strong{font-weight:500;color:#d2e7f3}.scenario-icon{display:flex;align-items:center;color:#b5a47c}.scenario.up .scenario-icon,.scenario.up p{color:var(--long)}.scenario.down .scenario-icon,.scenario.down p{color:var(--short)}.scenario.neutral p,.scenario.uncertain p{color:#9fb8c9}.scenario p{font-size:11px;line-height:1.6;margin:3px 0 0 26px}.scenario-note{font-size:10px;color:#829eb4;line-height:1.8;margin:13px 0 5px}.news-popover>footer{padding:12px 18px;display:flex;justify-content:space-between;align-items:center;border-top:1px solid var(--line);gap:8px}.news-popover>footer a{display:flex;align-items:center;gap:6px;font-size:11px;text-decoration:none}.news-popover>footer span{font-size:10px;color:#63879f}.sentiment-card{position:absolute;top:58%;left:65%;transform:translate(-50%);width:365px;z-index:6;border:1px solid #235b73;border-radius:9px;background:#03131eeb;box-shadow:0 10px 35px #0005;-webkit-backdrop-filter:blur(12px);backdrop-filter:blur(12px)}.sentiment-card>header{display:flex;align-items:center;gap:11px;padding:14px 18px 10px;border-bottom:1px solid #1c3546;color:#53c9e5}.sentiment-card h2{font:600 22px/1.1 Rajdhani,sans-serif;color:#edf5fc;margin:0 0 3px;letter-spacing:.3px}.sentiment-card h2 span{font:500 12px Rajdhani,sans-serif;color:#95bad1;margin-left:5px}.sentiment-card header small{font-size:10px;color:#799aaf}.sentiment-ratio{display:flex;align-items:center;justify-content:space-between;padding:13px 24px 5px}.sentiment-ratio>div{display:flex;flex-direction:column}.sentiment-ratio small{font:600 14px Rajdhani,sans-serif;letter-spacing:1px}.sentiment-ratio strong{font:600 36px/1.1 Rajdhani,sans-serif}.sentiment-ratio strong span{font-size:23px;margin-left:2px}.sentiment-ratio .ratio-caption{font-size:10px;line-height:1.8;text-align:center;color:#728fa5}.average-prices{display:grid;grid-template-columns:1fr 1fr;padding:10px 24px;gap:18px}.average-prices>div+div{border-left:1px solid #203c50;padding-left:18px}.average-prices small{display:block;font-size:10px;color:#9ab4c8;margin-bottom:3px}.average-prices strong{font:600 23px Rajdhani,sans-serif}.sentiment-card>p{text-align:center;font-size:10px;color:#8ba9bd;margin:8px 10px 14px}.no-sentiment{padding:22px;display:flex;align-items:center;flex-direction:column;gap:10px;color:#8ca5b8}.no-sentiment strong{font-size:13px}.no-sentiment span{font-size:11px;line-height:1.6;text-align:center}.correlation-legend{position:absolute;bottom:22px;right:24px;z-index:6;background:#05131edb;padding:10px 13px;border:1px solid #203e50;border-radius:5px;font-size:10px;color:#8aa8bf}.correlation-legend>span{display:flex;gap:6px;align-items:center;margin-bottom:7px;font-size:11px;color:#b7cfe0}.correlation-legend>div{display:flex;gap:13px;margin-bottom:4px}.correlation-legend b{font-weight:400}.correlation-legend small{font-size:9px;color:#66879e}.app-footer{display:flex;align-items:center;justify-content:space-between;padding:0 20px;border-top:1px solid var(--line);font-size:10px;color:#87a6be;background:#030e18;z-index:30;gap:15px}.app-footer span{display:flex;align-items:center;gap:7px}.reduce-motion *{scroll-behavior:auto!important;transition:none!important}.news-popover{width:390px;max-height:71%}.news-summary{font-size:13px;margin-bottom:13px}.popup-scroll{padding-top:14px}.scenario{display:grid;grid-template-columns:110px 1fr;align-items:center;gap:5px;padding:11px 10px}.scenario>div{font-size:12px;gap:5px}.scenario p{font-size:12px;margin:0;line-height:1.65}.scenario-note{font-size:11px}.sentiment-card{left:61%}.event-title{font-size:13px}.news-popover>footer a{font-size:12px}.news-heading h1 span{font-size:12px}.news-time-group{padding-bottom:23px}@media(min-width:1800px){.app-main{grid-template-columns:330px minmax(0,1fr)}.news-popover{width:405px}.sentiment-card{width:400px}.news-heading{padding:25px}.news-list{padding:20px 20px 12px 25px}.news-time-group{padding-bottom:25px}.event-title{font-size:13px}.news-summary,.scenario p{font-size:12px}}@media(max-width:1450px){.app-header{gap:13px;padding:0 15px}.brand span{font-size:23px}.brand img{width:29px}.product-title{font-size:19px;padding-left:14px}.asset-filters button{padding:0 9px;font-size:11px}.asset-search{width:200px;flex-basis:200px}.demo-badge{font-size:9px;padding:6px}.app-main{grid-template-columns:275px minmax(0,1fr)}.news-heading{padding:20px 16px 14px}.news-heading h1{font-size:16px}.news-heading h1 span{font-size:10px}.news-list{padding-left:15px;padding-right:12px}.news-popover{width:320px;left:18px;top:14%;max-height:76%}.popup-scroll{padding:14px}.news-popover h2{font-size:20px}.news-summary{font-size:11px}.sentiment-card{width:315px;left:68%;top:57%}.sentiment-card h2{font-size:20px}.sentiment-card h2 span{font-size:10px}.scene-hint{display:none}.sentiment-ratio{padding:10px 20px 0}.average-prices{padding:8px 20px}.sentiment-ratio strong{font-size:31px}}@media(max-width:1150px){.product-title{display:none}.brand span{font-size:24px}.app-header{gap:12px}.demo-badge{font-size:8px}.asset-filters button{padding:0 8px}.asset-search{min-width:135px;flex-basis:180px}.app-main{grid-template-columns:245px minmax(0,1fr)}.news-heading{padding:16px 14px}.news-heading h1{display:block}.news-heading h1 span{padding-left:8px}.news-filter{align-items:flex-start;flex-direction:column;gap:4px}.news-time-group{padding-left:13px}.event-currency{display:none}.event-title{font-size:11px}.sentiment-card{left:auto;right:18px;transform:none;top:60%;width:275px}.sentiment-card>header{padding:12px}.sentiment-card h2 span{display:block;margin:3px 0 0}.sentiment-card .average-prices{padding:8px 14px;gap:8px}.average-prices>div+div{padding-left:10px}.news-popover{width:305px;max-height:76%;z-index:20}.correlation-legend{bottom:20px;right:18px}.scene-bottom,.scene-topbar{left:18px}.sentiment-card>p{font-size:9px}}@media(max-width:900px){.app-shell{min-height:100vh;height:auto;overflow:visible;grid-template-rows:auto minmax(0,1fr) auto}.app-header{flex-wrap:wrap;padding:13px 16px;gap:12px}.brand{order:0}.demo-badge{order:1;margin-left:auto;font-size:9px}.asset-filters{order:2;margin-left:0;flex:1}.asset-search{order:3;flex:1;min-width:170px}.app-main{grid-template-columns:245px minmax(0,1fr);height:870px}.news-popover{position:fixed;left:auto;right:22px;top:170px;max-height:calc(100dvh - 200px);width:min(370px,calc(100vw - 36px));z-index:45}.sentiment-card{top:auto;bottom:115px;left:20px;right:20px;width:auto;transform:none}.sentiment-card h2 span{display:inline;margin-left:7px}.scene-topbar{gap:10px;right:15px}.view-label{display:none}.view-tools{margin-left:auto}.correlation-legend{bottom:12px;left:20px;right:20px}.scene-bottom{bottom:86px}.scene-hint{display:none}.app-footer{padding:10px 16px;flex-wrap:wrap;gap:7px}.news-round{margin:0 14px}.news-list{padding-top:12px}.view-settings{right:15px}.sentiment-card>p{font-size:10px}}@media(min-width:901px)and (max-width:1450px){.sentiment-card{left:65%;right:auto;transform:translate(-50%)}.scenario{grid-template-columns:85px 1fr;padding:8px}.scenario>div{font-size:11px}.scenario p{margin:0;font-size:11px;line-height:1.5}.news-popover .news-summary{font-size:12px}.news-popover>header{padding-top:8px;padding-bottom:8px}.scenario-note{margin-top:9px;font-size:10px}.actual-status{padding:6px 8px;margin-bottom:10px}.event-figures{margin-bottom:8px}}@media(max-width:900px){.galaxy-stage{isolation:auto}.news-popover{z-index:45}.scenario{grid-template-columns:100px 1fr}}@media(min-width:901px)and (max-width:1150px){.sentiment-card{top:auto;bottom:108px;width:290px}.sentiment-card>header{padding:9px 12px}.sentiment-card h2 span{display:inline;margin-left:5px}.sentiment-ratio{padding:8px 16px 0}.sentiment-ratio strong{font-size:28px}.average-prices strong{font-size:21px}.sentiment-card>p{margin:5px 8px 10px}.correlation-legend{bottom:14px}}@media(max-width:600px){.app-header{gap:11px}.brand span{font-size:22px}.brand img{width:29px}.asset-filters{width:100%;flex-basis:100%;gap:6px}.asset-filters button{flex:1;font-size:11px}.asset-search{width:100%;flex-basis:100%;height:36px}.demo-badge{font-size:8px}.app-main{display:flex;flex-direction:column;height:auto}.galaxy-stage{order:0;height:750px;flex-shrink:0}.news-rail{order:1;border-top:1px solid #294558;border-right:0;height:520px}.news-heading{padding:18px}.news-heading h1{display:flex;font-size:18px}.news-heading h2{margin-top:10px}.news-filter{flex-direction:row;align-items:center}.news-list{padding:16px 18px}.news-time-group{padding-left:23px}.news-event{padding:11px}.event-currency{display:inline}.event-title{font-size:13px}.news-popover{top:auto;bottom:12px;left:12px;right:12px;width:auto;max-height:calc(100dvh - 36px);border-radius:9px;box-shadow:0 0 0 100vmax #0006}.news-summary{font-size:12px}.news-popover h2{font-size:22px}.scenario p{font-size:12px}.sentiment-card{bottom:115px;left:25px;right:25px}.scene-topbar{top:14px}.view-label{display:block;font-size:12px}.view-tools{gap:5px}.tool-button{font-size:12px;padding:0 7px}.sentiment-card h2{font-size:21px}.sentiment-card h2 span{font-size:11px}.sentiment-card>header{padding:14px 18px}.sentiment-ratio strong{font-size:33px}.average-prices strong{font-size:24px}.app-footer{font-size:9px}.empty-news{padding:25px}.asset-results{width:100%;max-height:300px}}.app-main{grid-template-columns:270px minmax(0,1fr)}.app-main.has-inspector{grid-template-columns:270px minmax(0,1fr) 350px}.galaxy-stage,.scene-topbar,.scene-bottom{user-select:none;-webkit-user-select:none}.scene-topbar{left:18px;right:18px;gap:10px}.view-label{pointer-events:auto;white-space:nowrap;text-align:left;cursor:pointer}.view-label:hover{border-color:#38b1ce;color:#c2e9f5}.view-tools{gap:6px}.tool-button span{font:600 13px Rajdhani,sans-serif;color:#4de0dc;margin-left:2px}.scene-bottom{left:18px;bottom:18px}.scene-hint{display:none}.correlation-legend{bottom:18px;right:18px;padding:9px 12px;font-size:10px;max-width:260px}.correlation-legend>span{margin-bottom:5px}.correlation-legend small{display:block;line-height:1.6}.news-popover{top:86px;left:18px;width:min(350px,calc(100% - 36px));max-height:calc(100% - 160px)}.stellar-inspector{min-width:0;min-height:0;display:flex;flex-direction:column;background:#04111b;border-left:1px solid #284455;z-index:12}.inspector-heading{display:flex;align-items:center;justify-content:space-between;padding:21px 21px 15px;border-bottom:1px solid #1b3444;flex-shrink:0}.inspector-heading .eyebrow{font-size:10px;letter-spacing:2.3px;margin-bottom:5px;color:#729bb1}.inspector-heading h2{font:600 29px/1.1 Rajdhani,sans-serif;letter-spacing:.6px;margin:0;color:#e4f4fb}.inspector-heading h2 span{font:500 10px Sarabun,sans-serif;letter-spacing:1px;margin-left:13px;color:#6e9db5}.inspector-scroll{flex:1;min-height:0;overflow:auto;padding-bottom:16px}.stellar-hero{position:relative;height:clamp(185px,29vh,285px);margin:0 8px}.stellar-hero .sentiment-preview{width:100%;height:100%}.stellar-caption{position:absolute;bottom:8px;left:0;right:0;text-align:center;font:500 12px Rajdhani,sans-serif;letter-spacing:1.1px;color:#83acc1;pointer-events:none}.stellar-inspector .sentiment-card{position:relative;inset:auto;transform:none;width:auto;margin:0 20px;border:0;border-top:1px solid #1c3c4e;border-bottom:1px solid #1c3c4e;border-radius:0;background:none;box-shadow:none;-webkit-backdrop-filter:none;backdrop-filter:none}.stellar-inspector .sentiment-card>header{padding:17px 0 11px;border:0;gap:9px}.stellar-inspector .sentiment-card h2{font:600 17px Rajdhani,sans-serif;letter-spacing:.5px;margin:0 0 3px}.stellar-inspector .sentiment-card header small{font-size:10px;line-height:1.5;color:#8aa9bc}.stellar-inspector .sentiment-ratio{padding:8px 0 6px}.stellar-inspector .sentiment-ratio strong{font-size:38px;line-height:1.2}.stellar-inspector .sentiment-ratio small{font-size:12px;letter-spacing:1.8px}.stellar-inspector .sentiment-ratio .ratio-caption{font-size:10px;color:#7799ae}.stellar-inspector .average-prices{padding:10px 0 9px;gap:13px}.stellar-inspector .average-prices strong{font-size:23px}.stellar-inspector .average-prices small{font-size:10px}.stellar-inspector .average-prices>div+div{padding-left:13px}.stellar-inspector .sentiment-card>p{font-size:10px;margin:7px 0 16px;text-align:left;color:#7b9aad}.connection-detail{margin:0 20px;padding:18px 0 6px}.connection-title{display:flex;align-items:center;gap:8px;color:#74bed2}.connection-title h3{font:600 16px Rajdhani,sans-serif;letter-spacing:1px;margin:0;flex:1}.connection-detail p{font-size:10px;color:#6f97af;line-height:1.8;margin:10px 0}.connection-detail .connection-empty{font-size:12px;color:#91afc2}.connection-pair{display:flex;align-items:center;gap:9px;margin-top:14px;color:#729fb5}.connection-pair button{font:600 19px Rajdhani,sans-serif;color:#daeff7;padding:4px 7px;border:1px solid #30536a;border-radius:4px}.connection-pair button:hover{background:#123147;border-color:#4db6d6}.connection-value{display:flex;gap:13px;align-items:center;margin-top:9px}.connection-value strong{font:600 36px Rajdhani,sans-serif}.connection-value span{font-size:11px}.inspector-note{font-size:10px;line-height:1.8;color:#69899d;margin:10px 20px 5px}@media(min-width:1800px){.app-main{grid-template-columns:290px minmax(0,1fr)}.app-main.has-inspector{grid-template-columns:290px minmax(0,1fr) 380px}.stellar-hero{height:290px}}@media(max-width:1450px){.app-main{grid-template-columns:245px minmax(0,1fr)}.app-main.has-inspector{grid-template-columns:245px minmax(0,1fr) 320px}.news-popover{width:min(330px,calc(100% - 36px))}.stellar-inspector .sentiment-ratio strong{font-size:34px}.stellar-inspector .sentiment-card,.connection-detail{margin:0 17px}.correlation-legend{font-size:9px;right:12px;bottom:16px}.scene-bottom{left:12px;bottom:16px}}@media(min-width:901px)and (max-width:1199px){.app-main,.app-main.has-inspector{position:relative;grid-template-columns:235px minmax(0,1fr)}.stellar-inspector{position:absolute;top:0;bottom:0;right:0;width:310px;box-shadow:-20px 0 60px #0008}.app-main.has-inspector .scene-topbar{right:326px}.app-main.has-inspector .scene-topbar .view-label{display:none}.app-main.has-inspector .correlation-legend{right:326px}.app-main.has-inspector .scene-bottom{bottom:118px}.news-popover{z-index:30;width:315px;max-width:calc(100% - 36px)}}@media(max-width:900px){.app-main,.app-main.has-inspector{height:auto;display:grid;grid-template-columns:245px minmax(0,1fr)}.galaxy-stage{height:720px;grid-column:2;grid-row:1}.news-rail{height:720px;grid-column:1;grid-row:1}.stellar-inspector{grid-column:1 / -1;grid-row:2;border-left:0;border-top:1px solid #294456}.inspector-scroll{overflow:visible;display:grid;grid-template-columns:minmax(220px,1fr) minmax(250px,1fr);align-items:start;gap:0 20px}.stellar-hero{height:270px;grid-column:1;grid-row:1 / 3;margin:0}.stellar-inspector .sentiment-card{grid-column:2;grid-row:1;margin:20px 20px 0 0}.connection-detail{grid-column:2;grid-row:2;margin:0 20px 0 0}.inspector-note{grid-column:1 / -1;text-align:center}.view-label{display:none}.scene-topbar{right:15px}.correlation-legend{left:18px;right:18px;max-width:none;bottom:14px}.scene-bottom{bottom:108px;left:18px}.news-popover{position:fixed;top:140px;bottom:auto;left:auto;right:18px;width:min(360px,calc(100vw - 36px));max-height:calc(100dvh - 170px);z-index:45}.app-main .scene-topbar .view-label{display:block;font-size:11px;padding:7px}.tool-button{font-size:12px}.view-tools{gap:3px}.scene-topbar{gap:5px;left:12px;right:12px}.tool-button{padding:0 6px}.scene-topbar .icon-button{width:28px}}@media(max-width:600px){.app-main,.app-main.has-inspector{display:flex;flex-direction:column}.galaxy-stage{order:0;height:600px}.stellar-inspector{order:1}.news-rail{order:2;height:520px}.inspector-scroll{display:block;padding-bottom:18px}.stellar-hero{height:280px}.stellar-inspector .sentiment-card,.connection-detail{margin:0 22px}.inspector-note{text-align:left;margin:10px 22px}.news-popover{top:auto;bottom:12px;left:12px;right:12px;width:auto;max-height:calc(100dvh - 36px)}.app-footer{font-size:9px}.stellar-inspector .sentiment-ratio strong{font-size:38px}.view-settings{right:12px}.inspector-heading{padding:18px 22px}.view-label{max-width:125px;overflow:hidden;text-overflow:ellipsis}}.stellar-color-key{padding:9px 0 0;margin:0 2px}.stellar-color-scale{position:relative;height:4px;border-radius:3px;background:linear-gradient(90deg,#b10d35,#fa556c,#b5bcc8,#28d995,#008c51)}.stellar-color-scale i{position:absolute;top:-3px;width:10px;height:10px;transform:translate(-50%);border:2px solid #e7f5fc;border-radius:50%;box-shadow:0 0 7px #000}.stellar-color-key>div+div{display:flex;justify-content:space-between;margin-top:8px;color:#819caf;font:500 10px Rajdhani,sans-serif;letter-spacing:.5px}.gold-key{color:#efc879}.connection-value strong small{font-size:21px;margin-left:3px}@media(max-width:900px){.scene-bottom{bottom:116px}}.overview-label{display:flex;gap:7px;align-items:center;color:#80a5b9}.overview-label strong{color:#c4dce9}.camera-controls .reset-overview{display:flex;align-items:center;gap:5px;width:auto;padding:0 10px;border-left:1px solid #29495b;color:#b9d4e3;font-size:11px}.correlation-list-heading{display:flex;flex-direction:column;gap:4px;margin:18px 0 9px}.correlation-list-heading strong{font-size:12px;color:#bad0dd;font-weight:500}.correlation-list-heading strong span{font:600 13px Rajdhani,sans-serif;color:#63e0d4;margin-left:6px}.correlation-list-heading small{font-size:10px;color:#7599ac}.correlation-list{max-height:274px;overflow-y:auto;overscroll-behavior:contain;border:1px solid #193543;border-radius:5px;scrollbar-width:thin;scrollbar-color:#38586a #07131d}.correlation-row{display:grid;grid-template-columns:70px minmax(25px,1fr) 43px;align-items:center;gap:9px;width:100%;padding:10px;border:0;border-bottom:1px solid #16303c;text-align:left;color:#a9c4d6}.correlation-row:last-child{border-bottom:0}.correlation-row:hover{background:#102c38}.correlation-row[aria-pressed=true]{background:#12303c;box-shadow:inset 3px 0 #f0c873}.correlation-symbol{font:600 15px Rajdhani,sans-serif;letter-spacing:.3px}.correlation-row strong{font:600 16px Rajdhani,sans-serif;text-align:right;font-variant-numeric:tabular-nums}.correlation-row.positive strong{color:#4dd7ac}.correlation-row.negative strong{color:#f47c8e}.correlation-meter{height:3px;border-radius:3px;background:#192c36;overflow:hidden}.correlation-meter i{display:block;height:100%;background:#31c69a;opacity:.8;border-radius:3px}.correlation-row.negative .correlation-meter i{background:#e96581}.connection-detail .list-scroll-hint{font-size:9px;color:#6e8fa3;margin:7px 0}.news-learn-more{display:flex;align-items:center;gap:7px;padding:8px 10px;margin:12px 0 16px;border:1px solid #285565;border-radius:4px;background:#0a2431;color:#75d4df;font-size:11px;text-align:left}.news-learn-more:hover,.news-learn-more[aria-expanded=true]{background:#113d4b;border-color:#66cad7}.overview-news-hint{padding:14px;border-left:2px solid #40c6c3;background:#0a2431;font-size:12px;color:#99c6d4;line-height:1.8}.news-explainer{position:fixed;right:24px;top:115px;width:350px;max-height:calc(100dvh - 145px);overflow:auto;z-index:60;border:1px solid #3d758a;border-top:2px solid #72dfd5;border-radius:8px;background:linear-gradient(155deg,#112c3c,#07151f 55%);box-shadow:0 16px 80px #000a}.news-explainer>header{display:flex;align-items:start;gap:14px;padding:20px 18px 14px;border-bottom:1px solid #264452}.news-explainer>header>div{flex:1}.news-explainer .eyebrow{font-size:9px;letter-spacing:2px;margin:0 0 9px;color:#65cad4}.news-explainer h2{font-size:18px;line-height:1.5;color:#e2edf4;margin:0}.explainer-points{padding:5px 18px 10px}.explainer-points p{display:flex;gap:12px;font-size:12px;line-height:1.9;margin:16px 0;color:#bacfdf}.explainer-points span{flex:0 0 19px;font:500 15px Rajdhani,sans-serif;color:#61c7cc;padding-top:2px}.news-explainer footer{padding:14px 18px;border-top:1px solid #264452;font-size:11px;display:flex;flex-direction:column;gap:10px}.news-explainer footer a{display:flex;align-items:center;gap:7px;color:#71d6d7}.news-explainer footer small{font-size:9px;color:#7c9db0;line-height:1.6}@media(max-width:600px){.news-explainer{top:auto;bottom:16px;right:16px;left:16px;width:auto;max-height:calc(100dvh - 48px)}.overview-label{white-space:nowrap}.camera-controls .reset-overview{padding:0 8px}}.app-main{--news-width:270px;--inspector-width:350px;--panel-ease:cubic-bezier(.22,.8,.25,1)}.app-main,.app-main.has-inspector{grid-template-columns:var(--news-width) minmax(0,1fr) 0px;transition:grid-template-columns .46s var(--panel-ease)}.app-main.has-inspector{grid-template-columns:var(--news-width) minmax(0,1fr) var(--inspector-width)}.inspector-dock{min-width:0;min-height:0;height:100%;overflow:hidden;z-index:12}.inspector-dock>.stellar-inspector{width:var(--inspector-width);height:100%;transform:translate(38px);opacity:0;transition:transform .46s var(--panel-ease),opacity .3s ease}.inspector-dock.is-open>.stellar-inspector{transform:translate(0);opacity:1}.camera-controls .reset-overview{border-left:0;min-height:35px;padding:0 13px;font-size:12px}.neutral-key,.connection-value.neutral{color:#e9bd63}.correlation-row strong{color:var(--correlation-color)!important}.correlation-row .correlation-meter i{background:var(--correlation-color)!important}.correlation-legend>div{flex-wrap:wrap;gap:4px 10px}.correlation-legend{max-width:282px}.correlation-legend .correlation-color-bands{display:grid;grid-template-columns:1fr 1fr;gap:6px 10px;margin:8px 0}.correlation-color-bands b{display:flex;align-items:center;gap:5px;font-size:9px;white-space:nowrap}.correlation-color-bands i{display:inline-block;width:16px;height:3px;border-radius:2px;flex-shrink:0}.correlation-color-bands small{font-size:8px;align-self:center}.correlation-legend:has(.correlation-color-bands){max-width:310px}@media(min-width:1800px){.app-main{--news-width:290px;--inspector-width:380px}}@media(max-width:1450px){.app-main{--news-width:245px;--inspector-width:320px}}@media(min-width:901px)and (max-width:1199px){.app-main{--news-width:235px;--inspector-width:310px}.app-main,.app-main.has-inspector{grid-template-columns:var(--news-width) minmax(0,1fr);overflow:hidden}.inspector-dock{position:absolute;top:0;bottom:0;right:0;width:310px;pointer-events:none}.inspector-dock.is-open{pointer-events:auto}.inspector-dock>.stellar-inspector{position:relative;inset:auto;transform:translate(100%);box-shadow:-20px 0 60px #0008}.inspector-dock.is-open>.stellar-inspector{transform:translate(0)}}@media(max-width:900px){.scene-bottom{bottom:174px}.app-main,.app-main.has-inspector{grid-template-columns:245px minmax(0,1fr)}.inspector-dock{grid-column:1 / -1;grid-row:2;display:grid;grid-template-rows:0fr;height:auto;transition:grid-template-rows .46s var(--panel-ease)}.inspector-dock.is-open{grid-template-rows:1fr}.inspector-dock>.stellar-inspector{grid-row:1;grid-column:1;width:auto;height:auto;overflow:hidden;transform:translateY(26px)}.inspector-dock.is-open>.stellar-inspector{transform:translateY(0)}.correlation-legend{max-width:none}}@media(max-width:600px){.inspector-dock{order:1;width:100%;flex-shrink:0}}.reduce-motion .inspector-dock,.reduce-motion .inspector-dock>.stellar-inspector{transition:none!important}.app-main{position:relative}.news-reading-layer{--reader-card:330px;position:absolute;top:0;right:0;bottom:0;left:0;z-index:80;pointer-events:none}.news-reading-backdrop{position:fixed;top:0;right:0;bottom:0;left:0;width:100%;height:100%;padding:0;border:0;border-radius:0;background:#000308b8;pointer-events:auto;cursor:default;animation:news-dim-in .18s ease-out}.news-reading-panels{position:absolute;top:86px;left:calc(var(--news-width) + 18px);display:flex;align-items:flex-start;gap:16px;max-width:calc(100% - var(--news-width) - 36px);pointer-events:auto;-webkit-user-select:text;user-select:text}.news-reading-panels .news-popover,.news-reading-panels .news-explainer{position:relative;inset:auto;width:var(--reader-card);max-width:none;max-height:calc(100dvh - 184px);flex:0 0 var(--reader-card);margin:0;box-shadow:0 16px 50px #0008;-webkit-user-select:text;user-select:text}.news-reading-panels .news-explainer{width:350px;flex-basis:350px;animation:news-card-in .2s ease-out}.news-reading-panels .news-popover>header,.news-reading-panels .news-popover>footer{flex-shrink:0}.news-reading-layer.is-expanded .news-reading-panels{left:min(calc(var(--news-width) + 18px),max(18px,calc(100% - var(--reader-card) - 384px)));max-width:calc(100% - 36px)}@keyframes news-dim-in{0%{opacity:0}to{opacity:1}}@keyframes news-card-in{0%{opacity:0;transform:translate(-10px)}to{opacity:1;transform:translate(0)}}@media(min-width:1451px){.news-reading-layer{--reader-card:350px}}@media(max-width:900px){.news-reading-layer{position:fixed;top:0;right:0;bottom:0;left:0;--reader-card:350px}.news-reading-panels,.news-reading-layer.is-expanded .news-reading-panels{top:90px;left:18px;max-width:calc(100% - 36px)}.news-reading-panels .news-popover,.news-reading-panels .news-explainer{max-height:calc(100dvh - 112px)}.news-reading-layer.is-expanded{--reader-card: calc((100vw - 52px)/2) }.news-reading-layer.is-expanded .news-explainer{width:var(--reader-card);flex-basis:var(--reader-card)}}@media(max-width:740px){.news-reading-panels,.news-reading-layer.is-expanded .news-reading-panels{inset:16px 12px auto;display:flex;flex-direction:column;gap:12px;width:auto;max-width:none;max-height:calc(100dvh - 32px);overflow-y:auto;overscroll-behavior:contain;scrollbar-width:thin;padding:0 0 8px}.news-reading-panels .news-popover,.news-reading-panels .news-explainer,.news-reading-layer.is-expanded .news-explainer{width:100%;flex:0 0 auto;max-height:none;overflow:visible}.news-reading-panels .popup-scroll{overflow:visible}.news-reading-panels .news-explainer{animation-name:news-card-in}}.reduce-motion .news-reading-backdrop,.reduce-motion .news-reading-panels .news-explainer{animation:none!important}.live-connect{display:inline-flex;align-items:center;gap:6px;text-decoration:none;border-color:#36677a;color:#a4e3ea;background:#08212c}.live-connect:hover{background:#103340;border-color:#25aec5}.news-date-controls{display:flex;gap:7px;align-items:center;margin:0 0 12px}.news-date-controls input{min-width:0;flex:1;width:100%;height:33px;padding:5px 8px;border:1px solid #315269;border-radius:4px;background:#061522;color:#d6e9f4;font-size:12px}.news-date-controls button{height:33px;padding:0 10px;font-size:11px;border:1px solid #315269;border-radius:4px;background:#0a2432;color:#91d9e5}.news-date-controls button:hover{background:#123d4d}.news-source-status{display:flex;flex-direction:column;gap:4px;margin-top:11px;font-size:10px;line-height:1.65;color:#90b6ca}.news-source-status a{display:inline-flex;gap:5px;align-items:center;text-decoration:none;color:#90d1de;font-size:10px}.news-source-status small{font-size:9px;line-height:1.7;color:#7a9bb1}.news-retry-notice{margin:8px 0 0;font-size:10px;line-height:1.6;color:#d5b776}.news-heading .time-zone{margin-bottom:10px}.news-filter .sample-mini{border-color:#2b5967;color:#96d3d9;background:#0a2732}.news-time-group .time-heading time{font-size:15px;line-height:1.5}.news-popover .popup-meta{font-size:10px;gap:7px;min-width:0}.news-popover .popup-meta time{line-height:1.5}.news-popover>footer a{overflow-wrap:anywhere;line-height:1.5}.news-popover>footer span{flex-shrink:0}.sentiment-source-meta{display:flex;flex-direction:column;gap:4px;margin:12px 0 6px;color:#7d9db2;font-size:10px;line-height:1.6}.stellar-inspector .sentiment-card>p.rounding-note{font-size:9px;line-height:1.65;color:#beaf83;text-align:left;margin:8px 0}.correlation-source-meta{padding-top:7px;border-top:1px solid #1d3547;font-size:10px;line-height:1.7;color:#86a8bd}.correlation-legend small.live-correlation-status{border-top:1px solid #264251;margin-top:6px;padding-top:6px;color:#9ab9cc}.app-footer .live-flow-status{line-height:1.6;justify-content:flex-end;text-align:right}@media(max-width:1150px){.news-source-status{font-size:9px}.news-source-status small{font-size:8px}.news-date-controls input{font-size:11px;padding-inline:5px}.news-filter{gap:6px}.app-footer{font-size:9px}}@media(max-width:900px){.news-rail{min-height:560px}.app-footer .live-flow-status{justify-content:flex-start;text-align:left}.news-source-status{font-size:10px}.news-source-status small{font-size:9px}}@media(max-width:600px){.news-rail{height:650px}.news-heading h1{margin-bottom:10px}.news-heading h2{margin-top:0}.news-heading .news-source-status{margin-top:8px}.news-source-status small br{display:none}.news-source-status small{line-height:1.8}.correlation-legend small.live-correlation-status{font-size:9px}}.connection-notice{position:absolute;top:69px;left:18px;right:18px;z-index:15;display:flex;align-items:center;justify-content:space-between;gap:16px;padding:12px 15px;border:1px solid #76663d;border-radius:7px;background:#1e221dee;color:#ead7a1;font-size:12px;line-height:1.7}.connection-notice strong{font-weight:500}.connection-notice small{display:block;color:#b8c7d1;font-size:10px}.connection-notice a{display:flex;align-items:center;gap:6px;white-space:nowrap;padding:6px;border:1px solid #526b73;border-radius:4px;color:#a4e9eb}.connection-notice+.scene-status{padding-top:120px}@media(max-width:600px){.connection-notice{flex-direction:column;align-items:flex-start;gap:5px;top:58px}}",O3='.orbital-canvas-wrap{position:absolute;top:0;right:0;bottom:0;left:0;overflow:hidden;isolation:isolate;background:#030a12;user-select:none;-webkit-user-select:none;-webkit-tap-highlight-color:transparent}.orbital-webgl{display:block;width:100%;height:100%;touch-action:none;cursor:grab;outline:none}.orbital-webgl:focus-visible{outline:1px solid #39bde5;outline-offset:-2px}.orbital-webgl.is-dragging{cursor:grabbing!important}.orbital-leaders,.orbital-label-layer{position:absolute;top:0;right:0;bottom:0;left:0;width:100%;height:100%;pointer-events:none}.orbital-label-layer{overflow:hidden}.orbital-node-label{position:absolute;top:0;left:0;pointer-events:auto;border:0!important;background:#030b1494!important;border-radius:2px!important;padding:2px 4px!important;color:#d8e9f5!important;font-family:Rajdhani,sans-serif!important;font-size:14px!important;font-weight:600!important;line-height:20px!important;letter-spacing:.25px;white-space:nowrap;cursor:pointer;text-shadow:0 1px 3px #020812;transition:color .15s,background .15s;min-height:0!important}.orbital-node-label:hover,.orbital-node-label:focus-visible{color:#64d8ff!important;background:#102d40!important;outline:1px solid #40a4ca!important}.orbital-node-label.is-selected{font-size:17px!important;line-height:22px!important;font-weight:700!important;color:#fff1d5!important;background:#040c14c2!important;padding:2px 5px!important;letter-spacing:.4px;text-shadow:0 0 13px #ecc77f55;box-shadow:inset 0 -1px #eac77d88}.orbital-node-label.is-connected{color:#e8d4aa!important}.orbital-correlation-label{position:absolute;top:0;left:0;pointer-events:auto;min-height:0!important;padding:1px 5px!important;border:1px solid color-mix(in srgb,var(--correlation-color) 30%,transparent)!important;border-radius:4px!important;background:#06121aeb!important;color:var(--correlation-color)!important;font:600 12px/17px Rajdhani,sans-serif!important;white-space:nowrap;-webkit-user-select:none;user-select:none;cursor:pointer;box-shadow:0 2px 8px #0006}.orbital-correlation-label:hover,.orbital-correlation-label:focus-visible,.orbital-correlation-label.is-selected{outline:1px solid #eac77d!important;background:#15252bee!important;z-index:2}.orbital-node-label,.galaxy-cluster-label{user-select:none!important;-webkit-user-select:none!important}.orbital-node-label::selection,.galaxy-cluster-label::selection{background:transparent;color:inherit}.galaxy-cluster-label{position:absolute;top:0;left:0;pointer-events:none;min-width:108px;padding:0 8px 5px 0;border-bottom:1px solid color-mix(in srgb,var(--cluster-color) 40%,transparent);color:#b0c1d5;font:500 18px/22px Rajdhani,sans-serif;letter-spacing:1.2px;text-shadow:0 2px 5px #020812}.galaxy-cluster-label:before{content:"";position:absolute;left:-12px;bottom:-2px;width:3px;height:3px;border-radius:50%;background:var(--cluster-color);box-shadow:0 0 6px var(--cluster-color)}.galaxy-cluster-label strong{color:#d4e3ee;font-weight:600;font-size:20px}.galaxy-cluster-label span{color:#9bb1c6;font-size:16px}[hidden]{display:none!important}@media(max-width:800px){.galaxy-cluster-label{font-size:14px;line-height:18px;min-width:72px;letter-spacing:.6px}.galaxy-cluster-label strong{font-size:14px}.galaxy-cluster-label span{font-size:13px}}@media(max-width:800px){.orbital-node-label{font-size:12px!important;line-height:17px!important}.orbital-node-label.is-selected{font-size:15px!important;line-height:20px!important}}',P3=".sentiment-preview{position:relative;width:100%;height:250px;min-height:190px;isolation:isolate;overflow:hidden;contain:layout paint;pointer-events:none}.sentiment-preview>canvas{display:block;width:100%;height:100%}.sentiment-preview-fallback{display:none;position:absolute;top:0;right:0;bottom:0;left:0;align-items:center;justify-content:center;color:#9aaec6;font-size:12px;text-align:center}.sentiment-preview[data-ready=false] .sentiment-preview-fallback{display:flex}@media(max-height:800px)and (min-width:1024px){.sentiment-preview{height:210px}}@media(max-width:700px){.sentiment-preview{height:230px}}",z3='@font-face{font-family:Rajdhani;font-style:normal;font-display:swap;font-weight:500;src:url(/frontend/public/sentiment-universe/assets/rajdhani-devanagari-500-normal-B_DH_jja.woff2) format("woff2"),url(/frontend/public/sentiment-universe/assets/rajdhani-devanagari-500-normal-BPH8g_s8.woff) format("woff");unicode-range:U+0900-097F,U+1CD0-1CF9,U+200C-200D,U+20A8,U+20B9,U+20F0,U+25CC,U+A830-A839,U+A8E0-A8FF,U+11B00-11B09}@font-face{font-family:Rajdhani;font-style:normal;font-display:swap;font-weight:500;src:url(/frontend/public/sentiment-universe/assets/rajdhani-latin-ext-500-normal-DiyUS11w.woff2) format("woff2"),url(/frontend/public/sentiment-universe/assets/rajdhani-latin-ext-500-normal-CyRWJZ5B.woff) format("woff");unicode-range:U+0100-02BA,U+02BD-02C5,U+02C7-02CC,U+02CE-02D7,U+02DD-02FF,U+0304,U+0308,U+0329,U+1D00-1DBF,U+1E00-1E9F,U+1EF2-1EFF,U+2020,U+20A0-20AB,U+20AD-20C0,U+2113,U+2C60-2C7F,U+A720-A7FF}@font-face{font-family:Rajdhani;font-style:normal;font-display:swap;font-weight:500;src:url(/frontend/public/sentiment-universe/assets/rajdhani-latin-500-normal-ByNUCHrt.woff2) format("woff2"),url(/frontend/public/sentiment-universe/assets/rajdhani-latin-500-normal-DfvNI-Td.woff) format("woff");unicode-range:U+0000-00FF,U+0131,U+0152-0153,U+02BB-02BC,U+02C6,U+02DA,U+02DC,U+0304,U+0308,U+0329,U+2000-206F,U+20AC,U+2122,U+2191,U+2193,U+2212,U+2215,U+FEFF,U+FFFD}@font-face{font-family:Rajdhani;font-style:normal;font-display:swap;font-weight:600;src:url(/frontend/public/sentiment-universe/assets/rajdhani-devanagari-600-normal-DhS7ScYx.woff2) format("woff2"),url(/frontend/public/sentiment-universe/assets/rajdhani-devanagari-600-normal-BtY48IV_.woff) format("woff");unicode-range:U+0900-097F,U+1CD0-1CF9,U+200C-200D,U+20A8,U+20B9,U+20F0,U+25CC,U+A830-A839,U+A8E0-A8FF,U+11B00-11B09}@font-face{font-family:Rajdhani;font-style:normal;font-display:swap;font-weight:600;src:url(/frontend/public/sentiment-universe/assets/rajdhani-latin-ext-600-normal-C9ZjJQAt.woff2) format("woff2"),url(/frontend/public/sentiment-universe/assets/rajdhani-latin-ext-600-normal-BleIgkPp.woff) format("woff");unicode-range:U+0100-02BA,U+02BD-02C5,U+02C7-02CC,U+02CE-02D7,U+02DD-02FF,U+0304,U+0308,U+0329,U+1D00-1DBF,U+1E00-1E9F,U+1EF2-1EFF,U+2020,U+20A0-20AB,U+20AD-20C0,U+2113,U+2C60-2C7F,U+A720-A7FF}@font-face{font-family:Rajdhani;font-style:normal;font-display:swap;font-weight:600;src:url(/frontend/public/sentiment-universe/assets/rajdhani-latin-600-normal-CXCVEoA9.woff2) format("woff2"),url(/frontend/public/sentiment-universe/assets/rajdhani-latin-600-normal-Dx02qI2_.woff) format("woff");unicode-range:U+0000-00FF,U+0131,U+0152-0153,U+02BB-02BC,U+02C6,U+02DA,U+02DC,U+0304,U+0308,U+0329,U+2000-206F,U+20AC,U+2122,U+2191,U+2193,U+2212,U+2215,U+FEFF,U+FFFD}@font-face{font-family:Rajdhani;font-style:normal;font-display:swap;font-weight:700;src:url(/frontend/public/sentiment-universe/assets/rajdhani-devanagari-700-normal-BQQOj9BB.woff2) format("woff2"),url(/frontend/public/sentiment-universe/assets/rajdhani-devanagari-700-normal-DBRwWuxA.woff) format("woff");unicode-range:U+0900-097F,U+1CD0-1CF9,U+200C-200D,U+20A8,U+20B9,U+20F0,U+25CC,U+A830-A839,U+A8E0-A8FF,U+11B00-11B09}@font-face{font-family:Rajdhani;font-style:normal;font-display:swap;font-weight:700;src:url(/frontend/public/sentiment-universe/assets/rajdhani-latin-ext-700-normal-S6aYESQK.woff2) format("woff2"),url(/frontend/public/sentiment-universe/assets/rajdhani-latin-ext-700-normal-BPaQ7tlD.woff) format("woff");unicode-range:U+0100-02BA,U+02BD-02C5,U+02C7-02CC,U+02CE-02D7,U+02DD-02FF,U+0304,U+0308,U+0329,U+1D00-1DBF,U+1E00-1E9F,U+1EF2-1EFF,U+2020,U+20A0-20AB,U+20AD-20C0,U+2113,U+2C60-2C7F,U+A720-A7FF}@font-face{font-family:Rajdhani;font-style:normal;font-display:swap;font-weight:700;src:url(/frontend/public/sentiment-universe/assets/rajdhani-latin-700-normal-BPDUZo87.woff2) format("woff2"),url(/frontend/public/sentiment-universe/assets/rajdhani-latin-700-normal-e0Uj8ZlN.woff) format("woff");unicode-range:U+0000-00FF,U+0131,U+0152-0153,U+02BB-02BC,U+02C6,U+02DA,U+02DC,U+0304,U+0308,U+0329,U+2000-206F,U+20AC,U+2122,U+2191,U+2193,U+2212,U+2215,U+FEFF,U+FFFD}@font-face{font-family:Sarabun;font-style:normal;font-display:swap;font-weight:400;src:url(/frontend/public/sentiment-universe/assets/sarabun-thai-400-normal-C2DaJlKK.woff2) format("woff2"),url(/frontend/public/sentiment-universe/assets/sarabun-thai-400-normal-CH-UbWgg.woff) format("woff");unicode-range:U+02D7,U+0303,U+0331,U+0E01-0E5B,U+200C-200D,U+25CC}@font-face{font-family:Sarabun;font-style:normal;font-display:swap;font-weight:400;src:url(/frontend/public/sentiment-universe/assets/sarabun-vietnamese-400-normal-igdrzAGY.woff2) format("woff2"),url(/frontend/public/sentiment-universe/assets/sarabun-vietnamese-400-normal-DPfkSCMy.woff) format("woff");unicode-range:U+0102-0103,U+0110-0111,U+0128-0129,U+0168-0169,U+01A0-01A1,U+01AF-01B0,U+0300-0301,U+0303-0304,U+0308-0309,U+0323,U+0329,U+1EA0-1EF9,U+20AB}@font-face{font-family:Sarabun;font-style:normal;font-display:swap;font-weight:400;src:url(/frontend/public/sentiment-universe/assets/sarabun-latin-ext-400-normal-BbP7GpLL.woff2) format("woff2"),url(/frontend/public/sentiment-universe/assets/sarabun-latin-ext-400-normal-BsmTn0SS.woff) format("woff");unicode-range:U+0100-02BA,U+02BD-02C5,U+02C7-02CC,U+02CE-02D7,U+02DD-02FF,U+0304,U+0308,U+0329,U+1D00-1DBF,U+1E00-1E9F,U+1EF2-1EFF,U+2020,U+20A0-20AB,U+20AD-20C0,U+2113,U+2C60-2C7F,U+A720-A7FF}@font-face{font-family:Sarabun;font-style:normal;font-display:swap;font-weight:400;src:url(/frontend/public/sentiment-universe/assets/sarabun-latin-400-normal-URPBxl-K.woff2) format("woff2"),url(/frontend/public/sentiment-universe/assets/sarabun-latin-400-normal-DmguIS-7.woff) format("woff");unicode-range:U+0000-00FF,U+0131,U+0152-0153,U+02BB-02BC,U+02C6,U+02DA,U+02DC,U+0304,U+0308,U+0329,U+2000-206F,U+20AC,U+2122,U+2191,U+2193,U+2212,U+2215,U+FEFF,U+FFFD}@font-face{font-family:Sarabun;font-style:normal;font-display:swap;font-weight:500;src:url(/frontend/public/sentiment-universe/assets/sarabun-thai-500-normal-BVssjame.woff2) format("woff2"),url(/frontend/public/sentiment-universe/assets/sarabun-thai-500-normal-C3iDLEzi.woff) format("woff");unicode-range:U+02D7,U+0303,U+0331,U+0E01-0E5B,U+200C-200D,U+25CC}@font-face{font-family:Sarabun;font-style:normal;font-display:swap;font-weight:500;src:url(/frontend/public/sentiment-universe/assets/sarabun-vietnamese-500-normal-Dpe7Br9m.woff2) format("woff2"),url(/frontend/public/sentiment-universe/assets/sarabun-vietnamese-500-normal-CpRVvGRU.woff) format("woff");unicode-range:U+0102-0103,U+0110-0111,U+0128-0129,U+0168-0169,U+01A0-01A1,U+01AF-01B0,U+0300-0301,U+0303-0304,U+0308-0309,U+0323,U+0329,U+1EA0-1EF9,U+20AB}@font-face{font-family:Sarabun;font-style:normal;font-display:swap;font-weight:500;src:url(/frontend/public/sentiment-universe/assets/sarabun-latin-ext-500-normal-DE1LysqI.woff2) format("woff2"),url(/frontend/public/sentiment-universe/assets/sarabun-latin-ext-500-normal-Cot16Bd2.woff) format("woff");unicode-range:U+0100-02BA,U+02BD-02C5,U+02C7-02CC,U+02CE-02D7,U+02DD-02FF,U+0304,U+0308,U+0329,U+1D00-1DBF,U+1E00-1E9F,U+1EF2-1EFF,U+2020,U+20A0-20AB,U+20AD-20C0,U+2113,U+2C60-2C7F,U+A720-A7FF}@font-face{font-family:Sarabun;font-style:normal;font-display:swap;font-weight:500;src:url(/frontend/public/sentiment-universe/assets/sarabun-latin-500-normal-BjUTcdxu.woff2) format("woff2"),url(/frontend/public/sentiment-universe/assets/sarabun-latin-500-normal-CJexTAnl.woff) format("woff");unicode-range:U+0000-00FF,U+0131,U+0152-0153,U+02BB-02BC,U+02C6,U+02DA,U+02DC,U+0304,U+0308,U+0329,U+2000-206F,U+20AC,U+2122,U+2191,U+2193,U+2212,U+2215,U+FEFF,U+FFFD}@font-face{font-family:Sarabun;font-style:normal;font-display:swap;font-weight:600;src:url(/frontend/public/sentiment-universe/assets/sarabun-thai-600-normal-3dIAQ-_s.woff2) format("woff2"),url(/frontend/public/sentiment-universe/assets/sarabun-thai-600-normal-DWKeTe6a.woff) format("woff");unicode-range:U+02D7,U+0303,U+0331,U+0E01-0E5B,U+200C-200D,U+25CC}@font-face{font-family:Sarabun;font-style:normal;font-display:swap;font-weight:600;src:url(/frontend/public/sentiment-universe/assets/sarabun-vietnamese-600-normal-DkxrOlLB.woff2) format("woff2"),url(/frontend/public/sentiment-universe/assets/sarabun-vietnamese-600-normal-BMbOgAW-.woff) format("woff");unicode-range:U+0102-0103,U+0110-0111,U+0128-0129,U+0168-0169,U+01A0-01A1,U+01AF-01B0,U+0300-0301,U+0303-0304,U+0308-0309,U+0323,U+0329,U+1EA0-1EF9,U+20AB}@font-face{font-family:Sarabun;font-style:normal;font-display:swap;font-weight:600;src:url(/frontend/public/sentiment-universe/assets/sarabun-latin-ext-600-normal-BRxjKUQ6.woff2) format("woff2"),url(/frontend/public/sentiment-universe/assets/sarabun-latin-ext-600-normal-0tXu9x_i.woff) format("woff");unicode-range:U+0100-02BA,U+02BD-02C5,U+02C7-02CC,U+02CE-02D7,U+02DD-02FF,U+0304,U+0308,U+0329,U+1D00-1DBF,U+1E00-1E9F,U+1EF2-1EFF,U+2020,U+20A0-20AB,U+20AD-20C0,U+2113,U+2C60-2C7F,U+A720-A7FF}@font-face{font-family:Sarabun;font-style:normal;font-display:swap;font-weight:600;src:url(/frontend/public/sentiment-universe/assets/sarabun-latin-600-normal-DMD3TROr.woff2) format("woff2"),url(/frontend/public/sentiment-universe/assets/sarabun-latin-600-normal-9FonlkKx.woff) format("woff");unicode-range:U+0000-00FF,U+0131,U+0152-0153,U+02BB-02BC,U+02C6,U+02DA,U+02DC,U+0304,U+0308,U+0329,U+2000-206F,U+20AC,U+2122,U+2191,U+2193,U+2212,U+2215,U+FEFF,U+FFFD}',F3=":host{display:block;height:100%;min-height:0;min-width:0;contain:layout style;isolation:isolate;overflow:auto;background:#020a12}.sentiment-embed-root{height:100%;min-height:0;min-width:0}.app-shell{height:100%;min-height:0}.embed-error{padding:40px;color:#d8edf8;font:400 15px/1.7 Sarabun,sans-serif}.embed-error h2{font-size:22px}.embed-error div{display:flex;gap:20px;align-items:center}.embed-error button{border:1px solid #31556d;border-radius:6px;padding:10px 18px;background:#133849}@media(min-width:901px){.app-main{height:auto;min-height:0}}@media(max-width:900px){.app-shell{height:auto;min-height:100%}}",Du=new WeakMap;let u_=0,xr;class B3 extends nt.Component{constructor(){super(...arguments);Ox(this,"state",{failed:!1,attempt:0})}static getDerivedStateFromError(){return{failed:!0}}render(){return this.state.failed?U.jsxs("section",{className:"embed-error",role:"alert",children:[U.jsx("h2",{children:"เปิดกาแล็กซี่ไม่สำเร็จ"}),U.jsx("p",{children:"ตรวจการเชื่อมบริการข้อมูลในเครื่อง แล้วลองเปิดหน้านี้อีกครั้ง"}),U.jsxs("div",{children:[U.jsx("button",{onClick:()=>this.setState(i=>({failed:!1,attempt:i.attempt+1})),children:"ลองอีกครั้ง"}),U.jsx("a",{href:this.props.options.setupUrl,target:"_blank",rel:"noopener noreferrer",children:"ตั้งค่าแหล่งข้อมูล"})]})]}):U.jsx(D3,{...this.props.options},this.state.attempt)}}function H3(r,e={}){if(!r||r.nodeType!==1)throw new Error("mount_host_required");if(Du.has(r))return Du.get(r);const i=N3(e,r.ownerDocument.location.origin),s=r.shadowRoot||r.attachShadow({mode:"open"}),l=r.ownerDocument.createElement("style");l.textContent=L3.replaceAll(":root",":host")+`
`+O3+`
`+P3+`
`+F3;const c=r.ownerDocument.createElement("div");c.className="sentiment-embed-root",c.setAttribute("role","region"),c.setAttribute("aria-label","Sentiment Universe · 32 สินทรัพย์"),s.replaceChildren(l,c),xr||(xr=r.ownerDocument.createElement("style"),xr.dataset.sentimentFonts="true",xr.textContent=z3.replaceAll("/frontend/public/sentiment-universe/",i.assetBase),r.ownerDocument.head.appendChild(xr)),u_++;const f=f1.createRoot(c);let h=!1;const m={unmount(){h||(h=!0,f.unmount(),s.replaceChildren(),Du.delete(r),--u_===0&&(xr==null||xr.remove(),xr=null))}};return Du.set(r,m),f.render(U.jsx(B3,{options:i})),m}export{H3 as mountSentimentUniverse};
