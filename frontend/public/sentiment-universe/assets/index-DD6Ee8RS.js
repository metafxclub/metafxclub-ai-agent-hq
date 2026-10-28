(function(){const e=document.createElement("link").relList;if(e&&e.supports&&e.supports("modulepreload"))return;for(const l of document.querySelectorAll('link[rel="modulepreload"]'))r(l);new MutationObserver(l=>{for(const c of l)if(c.type==="childList")for(const f of c.addedNodes)f.tagName==="LINK"&&f.rel==="modulepreload"&&r(f)}).observe(document,{childList:!0,subtree:!0});function i(l){const c={};return l.integrity&&(c.integrity=l.integrity),l.referrerPolicy&&(c.referrerPolicy=l.referrerPolicy),l.crossOrigin==="use-credentials"?c.credentials="include":l.crossOrigin==="anonymous"?c.credentials="omit":c.credentials="same-origin",c}function r(l){if(l.ep)return;l.ep=!0;const c=i(l);fetch(l.href,c)}})();function nM(s){return s&&s.__esModule&&Object.prototype.hasOwnProperty.call(s,"default")?s.default:s}var $d={exports:{}},wl={};/**
 * @license React
 * react-jsx-runtime.production.js
 *
 * Copyright (c) Meta Platforms, Inc. and affiliates.
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 */var Pv;function iM(){if(Pv)return wl;Pv=1;var s=Symbol.for("react.transitional.element"),e=Symbol.for("react.fragment");function i(r,l,c){var f=null;if(c!==void 0&&(f=""+c),l.key!==void 0&&(f=""+l.key),"key"in l){c={};for(var h in l)h!=="key"&&(c[h]=l[h])}else c=l;return l=c.ref,{$$typeof:s,type:r,key:f,ref:l!==void 0?l:null,props:c}}return wl.Fragment=e,wl.jsx=i,wl.jsxs=i,wl}var Iv;function aM(){return Iv||(Iv=1,$d.exports=iM()),$d.exports}var w=aM(),eh={exports:{}},St={};/**
 * @license React
 * react.production.js
 *
 * Copyright (c) Meta Platforms, Inc. and affiliates.
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 */var Fv;function rM(){if(Fv)return St;Fv=1;var s=Symbol.for("react.transitional.element"),e=Symbol.for("react.portal"),i=Symbol.for("react.fragment"),r=Symbol.for("react.strict_mode"),l=Symbol.for("react.profiler"),c=Symbol.for("react.consumer"),f=Symbol.for("react.context"),h=Symbol.for("react.forward_ref"),m=Symbol.for("react.suspense"),p=Symbol.for("react.memo"),g=Symbol.for("react.lazy"),_=Symbol.for("react.activity"),v=Symbol.iterator;function x(U){return U===null||typeof U!="object"?null:(U=v&&U[v]||U["@@iterator"],typeof U=="function"?U:null)}var E={isMounted:function(){return!1},enqueueForceUpdate:function(){},enqueueReplaceState:function(){},enqueueSetState:function(){}},D=Object.assign,M={};function y(U,re,xe){this.props=U,this.context=re,this.refs=M,this.updater=xe||E}y.prototype.isReactComponent={},y.prototype.setState=function(U,re){if(typeof U!="object"&&typeof U!="function"&&U!=null)throw Error("takes an object of state variables to update or a function which returns an object of state variables.");this.updater.enqueueSetState(this,U,re,"setState")},y.prototype.forceUpdate=function(U){this.updater.enqueueForceUpdate(this,U,"forceUpdate")};function F(){}F.prototype=y.prototype;function V(U,re,xe){this.props=U,this.context=re,this.refs=M,this.updater=xe||E}var R=V.prototype=new F;R.constructor=V,D(R,y.prototype),R.isPureReactComponent=!0;var N=Array.isArray;function L(){}var P={H:null,A:null,T:null,S:null},T=Object.prototype.hasOwnProperty;function O(U,re,xe){var Ue=xe.ref;return{$$typeof:s,type:U,key:re,ref:Ue!==void 0?Ue:null,props:xe}}function B(U,re){return O(U.type,re,U.props)}function k(U){return typeof U=="object"&&U!==null&&U.$$typeof===s}function J(U){var re={"=":"=0",":":"=2"};return"$"+U.replace(/[=:]/g,function(xe){return re[xe]})}var se=/\/+/g;function Y(U,re){return typeof U=="object"&&U!==null&&U.key!=null?J(""+U.key):re.toString(36)}function j(U){switch(U.status){case"fulfilled":return U.value;case"rejected":throw U.reason;default:switch(typeof U.status=="string"?U.then(L,L):(U.status="pending",U.then(function(re){U.status==="pending"&&(U.status="fulfilled",U.value=re)},function(re){U.status==="pending"&&(U.status="rejected",U.reason=re)})),U.status){case"fulfilled":return U.value;case"rejected":throw U.reason}}throw U}function z(U,re,xe,Ue,Ie){var Xe=typeof U;(Xe==="undefined"||Xe==="boolean")&&(U=null);var ue=!1;if(U===null)ue=!0;else switch(Xe){case"bigint":case"string":case"number":ue=!0;break;case"object":switch(U.$$typeof){case s:case e:ue=!0;break;case g:return ue=U._init,z(ue(U._payload),re,xe,Ue,Ie)}}if(ue)return Ie=Ie(U),ue=Ue===""?"."+Y(U,0):Ue,N(Ie)?(xe="",ue!=null&&(xe=ue.replace(se,"$&/")+"/"),z(Ie,re,xe,"",function(at){return at})):Ie!=null&&(k(Ie)&&(Ie=B(Ie,xe+(Ie.key==null||U&&U.key===Ie.key?"":(""+Ie.key).replace(se,"$&/")+"/")+ue)),re.push(Ie)),1;ue=0;var ye=Ue===""?".":Ue+":";if(N(U))for(var we=0;we<U.length;we++)Ue=U[we],Xe=ye+Y(Ue,we),ue+=z(Ue,re,xe,Xe,Ie);else if(we=x(U),typeof we=="function")for(U=we.call(U),we=0;!(Ue=U.next()).done;)Ue=Ue.value,Xe=ye+Y(Ue,we++),ue+=z(Ue,re,xe,Xe,Ie);else if(Xe==="object"){if(typeof U.then=="function")return z(j(U),re,xe,Ue,Ie);throw re=String(U),Error("Objects are not valid as a React child (found: "+(re==="[object Object]"?"object with keys {"+Object.keys(U).join(", ")+"}":re)+"). If you meant to render a collection of children, use an array instead.")}return ue}function H(U,re,xe){if(U==null)return U;var Ue=[],Ie=0;return z(U,Ue,"","",function(Xe){return re.call(xe,Xe,Ie++)}),Ue}function ee(U){if(U._status===-1){var re=U._result;re=re(),re.then(function(xe){(U._status===0||U._status===-1)&&(U._status=1,U._result=xe)},function(xe){(U._status===0||U._status===-1)&&(U._status=2,U._result=xe)}),U._status===-1&&(U._status=0,U._result=re)}if(U._status===1)return U._result.default;throw U._result}var oe=typeof reportError=="function"?reportError:function(U){if(typeof window=="object"&&typeof window.ErrorEvent=="function"){var re=new window.ErrorEvent("error",{bubbles:!0,cancelable:!0,message:typeof U=="object"&&U!==null&&typeof U.message=="string"?String(U.message):String(U),error:U});if(!window.dispatchEvent(re))return}else if(typeof process=="object"&&typeof process.emit=="function"){process.emit("uncaughtException",U);return}console.error(U)},fe={map:H,forEach:function(U,re,xe){H(U,function(){re.apply(this,arguments)},xe)},count:function(U){var re=0;return H(U,function(){re++}),re},toArray:function(U){return H(U,function(re){return re})||[]},only:function(U){if(!k(U))throw Error("React.Children.only expected to receive a single React element child.");return U}};return St.Activity=_,St.Children=fe,St.Component=y,St.Fragment=i,St.Profiler=l,St.PureComponent=V,St.StrictMode=r,St.Suspense=m,St.__CLIENT_INTERNALS_DO_NOT_USE_OR_WARN_USERS_THEY_CANNOT_UPGRADE=P,St.__COMPILER_RUNTIME={__proto__:null,c:function(U){return P.H.useMemoCache(U)}},St.cache=function(U){return function(){return U.apply(null,arguments)}},St.cacheSignal=function(){return null},St.cloneElement=function(U,re,xe){if(U==null)throw Error("The argument must be a React element, but you passed "+U+".");var Ue=D({},U.props),Ie=U.key;if(re!=null)for(Xe in re.key!==void 0&&(Ie=""+re.key),re)!T.call(re,Xe)||Xe==="key"||Xe==="__self"||Xe==="__source"||Xe==="ref"&&re.ref===void 0||(Ue[Xe]=re[Xe]);var Xe=arguments.length-2;if(Xe===1)Ue.children=xe;else if(1<Xe){for(var ue=Array(Xe),ye=0;ye<Xe;ye++)ue[ye]=arguments[ye+2];Ue.children=ue}return O(U.type,Ie,Ue)},St.createContext=function(U){return U={$$typeof:f,_currentValue:U,_currentValue2:U,_threadCount:0,Provider:null,Consumer:null},U.Provider=U,U.Consumer={$$typeof:c,_context:U},U},St.createElement=function(U,re,xe){var Ue,Ie={},Xe=null;if(re!=null)for(Ue in re.key!==void 0&&(Xe=""+re.key),re)T.call(re,Ue)&&Ue!=="key"&&Ue!=="__self"&&Ue!=="__source"&&(Ie[Ue]=re[Ue]);var ue=arguments.length-2;if(ue===1)Ie.children=xe;else if(1<ue){for(var ye=Array(ue),we=0;we<ue;we++)ye[we]=arguments[we+2];Ie.children=ye}if(U&&U.defaultProps)for(Ue in ue=U.defaultProps,ue)Ie[Ue]===void 0&&(Ie[Ue]=ue[Ue]);return O(U,Xe,Ie)},St.createRef=function(){return{current:null}},St.forwardRef=function(U){return{$$typeof:h,render:U}},St.isValidElement=k,St.lazy=function(U){return{$$typeof:g,_payload:{_status:-1,_result:U},_init:ee}},St.memo=function(U,re){return{$$typeof:p,type:U,compare:re===void 0?null:re}},St.startTransition=function(U){var re=P.T,xe={};P.T=xe;try{var Ue=U(),Ie=P.S;Ie!==null&&Ie(xe,Ue),typeof Ue=="object"&&Ue!==null&&typeof Ue.then=="function"&&Ue.then(L,oe)}catch(Xe){oe(Xe)}finally{re!==null&&xe.types!==null&&(re.types=xe.types),P.T=re}},St.unstable_useCacheRefresh=function(){return P.H.useCacheRefresh()},St.use=function(U){return P.H.use(U)},St.useActionState=function(U,re,xe){return P.H.useActionState(U,re,xe)},St.useCallback=function(U,re){return P.H.useCallback(U,re)},St.useContext=function(U){return P.H.useContext(U)},St.useDebugValue=function(){},St.useDeferredValue=function(U,re){return P.H.useDeferredValue(U,re)},St.useEffect=function(U,re){return P.H.useEffect(U,re)},St.useEffectEvent=function(U){return P.H.useEffectEvent(U)},St.useId=function(){return P.H.useId()},St.useImperativeHandle=function(U,re,xe){return P.H.useImperativeHandle(U,re,xe)},St.useInsertionEffect=function(U,re){return P.H.useInsertionEffect(U,re)},St.useLayoutEffect=function(U,re){return P.H.useLayoutEffect(U,re)},St.useMemo=function(U,re){return P.H.useMemo(U,re)},St.useOptimistic=function(U,re){return P.H.useOptimistic(U,re)},St.useReducer=function(U,re,xe){return P.H.useReducer(U,re,xe)},St.useRef=function(U){return P.H.useRef(U)},St.useState=function(U){return P.H.useState(U)},St.useSyncExternalStore=function(U,re,xe){return P.H.useSyncExternalStore(U,re,xe)},St.useTransition=function(){return P.H.useTransition()},St.version="19.2.0",St}var zv;function Ip(){return zv||(zv=1,eh.exports=rM()),eh.exports}var nt=Ip();const sM=nM(nt);var th={exports:{}},Dl={},nh={exports:{}},ih={};/**
 * @license React
 * scheduler.production.js
 *
 * Copyright (c) Meta Platforms, Inc. and affiliates.
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 */var Bv;function oM(){return Bv||(Bv=1,(function(s){function e(z,H){var ee=z.length;z.push(H);e:for(;0<ee;){var oe=ee-1>>>1,fe=z[oe];if(0<l(fe,H))z[oe]=H,z[ee]=fe,ee=oe;else break e}}function i(z){return z.length===0?null:z[0]}function r(z){if(z.length===0)return null;var H=z[0],ee=z.pop();if(ee!==H){z[0]=ee;e:for(var oe=0,fe=z.length,U=fe>>>1;oe<U;){var re=2*(oe+1)-1,xe=z[re],Ue=re+1,Ie=z[Ue];if(0>l(xe,ee))Ue<fe&&0>l(Ie,xe)?(z[oe]=Ie,z[Ue]=ee,oe=Ue):(z[oe]=xe,z[re]=ee,oe=re);else if(Ue<fe&&0>l(Ie,ee))z[oe]=Ie,z[Ue]=ee,oe=Ue;else break e}}return H}function l(z,H){var ee=z.sortIndex-H.sortIndex;return ee!==0?ee:z.id-H.id}if(s.unstable_now=void 0,typeof performance=="object"&&typeof performance.now=="function"){var c=performance;s.unstable_now=function(){return c.now()}}else{var f=Date,h=f.now();s.unstable_now=function(){return f.now()-h}}var m=[],p=[],g=1,_=null,v=3,x=!1,E=!1,D=!1,M=!1,y=typeof setTimeout=="function"?setTimeout:null,F=typeof clearTimeout=="function"?clearTimeout:null,V=typeof setImmediate<"u"?setImmediate:null;function R(z){for(var H=i(p);H!==null;){if(H.callback===null)r(p);else if(H.startTime<=z)r(p),H.sortIndex=H.expirationTime,e(m,H);else break;H=i(p)}}function N(z){if(D=!1,R(z),!E)if(i(m)!==null)E=!0,L||(L=!0,J());else{var H=i(p);H!==null&&j(N,H.startTime-z)}}var L=!1,P=-1,T=5,O=-1;function B(){return M?!0:!(s.unstable_now()-O<T)}function k(){if(M=!1,L){var z=s.unstable_now();O=z;var H=!0;try{e:{E=!1,D&&(D=!1,F(P),P=-1),x=!0;var ee=v;try{t:{for(R(z),_=i(m);_!==null&&!(_.expirationTime>z&&B());){var oe=_.callback;if(typeof oe=="function"){_.callback=null,v=_.priorityLevel;var fe=oe(_.expirationTime<=z);if(z=s.unstable_now(),typeof fe=="function"){_.callback=fe,R(z),H=!0;break t}_===i(m)&&r(m),R(z)}else r(m);_=i(m)}if(_!==null)H=!0;else{var U=i(p);U!==null&&j(N,U.startTime-z),H=!1}}break e}finally{_=null,v=ee,x=!1}H=void 0}}finally{H?J():L=!1}}}var J;if(typeof V=="function")J=function(){V(k)};else if(typeof MessageChannel<"u"){var se=new MessageChannel,Y=se.port2;se.port1.onmessage=k,J=function(){Y.postMessage(null)}}else J=function(){y(k,0)};function j(z,H){P=y(function(){z(s.unstable_now())},H)}s.unstable_IdlePriority=5,s.unstable_ImmediatePriority=1,s.unstable_LowPriority=4,s.unstable_NormalPriority=3,s.unstable_Profiling=null,s.unstable_UserBlockingPriority=2,s.unstable_cancelCallback=function(z){z.callback=null},s.unstable_forceFrameRate=function(z){0>z||125<z?console.error("forceFrameRate takes a positive int between 0 and 125, forcing frame rates higher than 125 fps is not supported"):T=0<z?Math.floor(1e3/z):5},s.unstable_getCurrentPriorityLevel=function(){return v},s.unstable_next=function(z){switch(v){case 1:case 2:case 3:var H=3;break;default:H=v}var ee=v;v=H;try{return z()}finally{v=ee}},s.unstable_requestPaint=function(){M=!0},s.unstable_runWithPriority=function(z,H){switch(z){case 1:case 2:case 3:case 4:case 5:break;default:z=3}var ee=v;v=z;try{return H()}finally{v=ee}},s.unstable_scheduleCallback=function(z,H,ee){var oe=s.unstable_now();switch(typeof ee=="object"&&ee!==null?(ee=ee.delay,ee=typeof ee=="number"&&0<ee?oe+ee:oe):ee=oe,z){case 1:var fe=-1;break;case 2:fe=250;break;case 5:fe=1073741823;break;case 4:fe=1e4;break;default:fe=5e3}return fe=ee+fe,z={id:g++,callback:H,priorityLevel:z,startTime:ee,expirationTime:fe,sortIndex:-1},ee>oe?(z.sortIndex=ee,e(p,z),i(m)===null&&z===i(p)&&(D?(F(P),P=-1):D=!0,j(N,ee-oe))):(z.sortIndex=fe,e(m,z),E||x||(E=!0,L||(L=!0,J()))),z},s.unstable_shouldYield=B,s.unstable_wrapCallback=function(z){var H=v;return function(){var ee=v;v=H;try{return z.apply(this,arguments)}finally{v=ee}}}})(ih)),ih}var Hv;function lM(){return Hv||(Hv=1,nh.exports=oM()),nh.exports}var ah={exports:{}},fi={};/**
 * @license React
 * react-dom.production.js
 *
 * Copyright (c) Meta Platforms, Inc. and affiliates.
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 */var Gv;function cM(){if(Gv)return fi;Gv=1;var s=Ip();function e(m){var p="https://react.dev/errors/"+m;if(1<arguments.length){p+="?args[]="+encodeURIComponent(arguments[1]);for(var g=2;g<arguments.length;g++)p+="&args[]="+encodeURIComponent(arguments[g])}return"Minified React error #"+m+"; visit "+p+" for the full message or use the non-minified dev environment for full errors and additional helpful warnings."}function i(){}var r={d:{f:i,r:function(){throw Error(e(522))},D:i,C:i,L:i,m:i,X:i,S:i,M:i},p:0,findDOMNode:null},l=Symbol.for("react.portal");function c(m,p,g){var _=3<arguments.length&&arguments[3]!==void 0?arguments[3]:null;return{$$typeof:l,key:_==null?null:""+_,children:m,containerInfo:p,implementation:g}}var f=s.__CLIENT_INTERNALS_DO_NOT_USE_OR_WARN_USERS_THEY_CANNOT_UPGRADE;function h(m,p){if(m==="font")return"";if(typeof p=="string")return p==="use-credentials"?p:""}return fi.__DOM_INTERNALS_DO_NOT_USE_OR_WARN_USERS_THEY_CANNOT_UPGRADE=r,fi.createPortal=function(m,p){var g=2<arguments.length&&arguments[2]!==void 0?arguments[2]:null;if(!p||p.nodeType!==1&&p.nodeType!==9&&p.nodeType!==11)throw Error(e(299));return c(m,p,null,g)},fi.flushSync=function(m){var p=f.T,g=r.p;try{if(f.T=null,r.p=2,m)return m()}finally{f.T=p,r.p=g,r.d.f()}},fi.preconnect=function(m,p){typeof m=="string"&&(p?(p=p.crossOrigin,p=typeof p=="string"?p==="use-credentials"?p:"":void 0):p=null,r.d.C(m,p))},fi.prefetchDNS=function(m){typeof m=="string"&&r.d.D(m)},fi.preinit=function(m,p){if(typeof m=="string"&&p&&typeof p.as=="string"){var g=p.as,_=h(g,p.crossOrigin),v=typeof p.integrity=="string"?p.integrity:void 0,x=typeof p.fetchPriority=="string"?p.fetchPriority:void 0;g==="style"?r.d.S(m,typeof p.precedence=="string"?p.precedence:void 0,{crossOrigin:_,integrity:v,fetchPriority:x}):g==="script"&&r.d.X(m,{crossOrigin:_,integrity:v,fetchPriority:x,nonce:typeof p.nonce=="string"?p.nonce:void 0})}},fi.preinitModule=function(m,p){if(typeof m=="string")if(typeof p=="object"&&p!==null){if(p.as==null||p.as==="script"){var g=h(p.as,p.crossOrigin);r.d.M(m,{crossOrigin:g,integrity:typeof p.integrity=="string"?p.integrity:void 0,nonce:typeof p.nonce=="string"?p.nonce:void 0})}}else p==null&&r.d.M(m)},fi.preload=function(m,p){if(typeof m=="string"&&typeof p=="object"&&p!==null&&typeof p.as=="string"){var g=p.as,_=h(g,p.crossOrigin);r.d.L(m,g,{crossOrigin:_,integrity:typeof p.integrity=="string"?p.integrity:void 0,nonce:typeof p.nonce=="string"?p.nonce:void 0,type:typeof p.type=="string"?p.type:void 0,fetchPriority:typeof p.fetchPriority=="string"?p.fetchPriority:void 0,referrerPolicy:typeof p.referrerPolicy=="string"?p.referrerPolicy:void 0,imageSrcSet:typeof p.imageSrcSet=="string"?p.imageSrcSet:void 0,imageSizes:typeof p.imageSizes=="string"?p.imageSizes:void 0,media:typeof p.media=="string"?p.media:void 0})}},fi.preloadModule=function(m,p){if(typeof m=="string")if(p){var g=h(p.as,p.crossOrigin);r.d.m(m,{as:typeof p.as=="string"&&p.as!=="script"?p.as:void 0,crossOrigin:g,integrity:typeof p.integrity=="string"?p.integrity:void 0})}else r.d.m(m)},fi.requestFormReset=function(m){r.d.r(m)},fi.unstable_batchedUpdates=function(m,p){return m(p)},fi.useFormState=function(m,p,g){return f.H.useFormState(m,p,g)},fi.useFormStatus=function(){return f.H.useHostTransitionStatus()},fi.version="19.2.0",fi}var Vv;function uM(){if(Vv)return ah.exports;Vv=1;function s(){if(!(typeof __REACT_DEVTOOLS_GLOBAL_HOOK__>"u"||typeof __REACT_DEVTOOLS_GLOBAL_HOOK__.checkDCE!="function"))try{__REACT_DEVTOOLS_GLOBAL_HOOK__.checkDCE(s)}catch(e){console.error(e)}}return s(),ah.exports=cM(),ah.exports}/**
 * @license React
 * react-dom-client.production.js
 *
 * Copyright (c) Meta Platforms, Inc. and affiliates.
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 */var kv;function fM(){if(kv)return Dl;kv=1;var s=lM(),e=Ip(),i=uM();function r(t){var n="https://react.dev/errors/"+t;if(1<arguments.length){n+="?args[]="+encodeURIComponent(arguments[1]);for(var a=2;a<arguments.length;a++)n+="&args[]="+encodeURIComponent(arguments[a])}return"Minified React error #"+t+"; visit "+n+" for the full message or use the non-minified dev environment for full errors and additional helpful warnings."}function l(t){return!(!t||t.nodeType!==1&&t.nodeType!==9&&t.nodeType!==11)}function c(t){var n=t,a=t;if(t.alternate)for(;n.return;)n=n.return;else{t=n;do n=t,(n.flags&4098)!==0&&(a=n.return),t=n.return;while(t)}return n.tag===3?a:null}function f(t){if(t.tag===13){var n=t.memoizedState;if(n===null&&(t=t.alternate,t!==null&&(n=t.memoizedState)),n!==null)return n.dehydrated}return null}function h(t){if(t.tag===31){var n=t.memoizedState;if(n===null&&(t=t.alternate,t!==null&&(n=t.memoizedState)),n!==null)return n.dehydrated}return null}function m(t){if(c(t)!==t)throw Error(r(188))}function p(t){var n=t.alternate;if(!n){if(n=c(t),n===null)throw Error(r(188));return n!==t?null:t}for(var a=t,o=n;;){var u=a.return;if(u===null)break;var d=u.alternate;if(d===null){if(o=u.return,o!==null){a=o;continue}break}if(u.child===d.child){for(d=u.child;d;){if(d===a)return m(u),t;if(d===o)return m(u),n;d=d.sibling}throw Error(r(188))}if(a.return!==o.return)a=u,o=d;else{for(var S=!1,C=u.child;C;){if(C===a){S=!0,a=u,o=d;break}if(C===o){S=!0,o=u,a=d;break}C=C.sibling}if(!S){for(C=d.child;C;){if(C===a){S=!0,a=d,o=u;break}if(C===o){S=!0,o=d,a=u;break}C=C.sibling}if(!S)throw Error(r(189))}}if(a.alternate!==o)throw Error(r(190))}if(a.tag!==3)throw Error(r(188));return a.stateNode.current===a?t:n}function g(t){var n=t.tag;if(n===5||n===26||n===27||n===6)return t;for(t=t.child;t!==null;){if(n=g(t),n!==null)return n;t=t.sibling}return null}var _=Object.assign,v=Symbol.for("react.element"),x=Symbol.for("react.transitional.element"),E=Symbol.for("react.portal"),D=Symbol.for("react.fragment"),M=Symbol.for("react.strict_mode"),y=Symbol.for("react.profiler"),F=Symbol.for("react.consumer"),V=Symbol.for("react.context"),R=Symbol.for("react.forward_ref"),N=Symbol.for("react.suspense"),L=Symbol.for("react.suspense_list"),P=Symbol.for("react.memo"),T=Symbol.for("react.lazy"),O=Symbol.for("react.activity"),B=Symbol.for("react.memo_cache_sentinel"),k=Symbol.iterator;function J(t){return t===null||typeof t!="object"?null:(t=k&&t[k]||t["@@iterator"],typeof t=="function"?t:null)}var se=Symbol.for("react.client.reference");function Y(t){if(t==null)return null;if(typeof t=="function")return t.$$typeof===se?null:t.displayName||t.name||null;if(typeof t=="string")return t;switch(t){case D:return"Fragment";case y:return"Profiler";case M:return"StrictMode";case N:return"Suspense";case L:return"SuspenseList";case O:return"Activity"}if(typeof t=="object")switch(t.$$typeof){case E:return"Portal";case V:return t.displayName||"Context";case F:return(t._context.displayName||"Context")+".Consumer";case R:var n=t.render;return t=t.displayName,t||(t=n.displayName||n.name||"",t=t!==""?"ForwardRef("+t+")":"ForwardRef"),t;case P:return n=t.displayName||null,n!==null?n:Y(t.type)||"Memo";case T:n=t._payload,t=t._init;try{return Y(t(n))}catch{}}return null}var j=Array.isArray,z=e.__CLIENT_INTERNALS_DO_NOT_USE_OR_WARN_USERS_THEY_CANNOT_UPGRADE,H=i.__DOM_INTERNALS_DO_NOT_USE_OR_WARN_USERS_THEY_CANNOT_UPGRADE,ee={pending:!1,data:null,method:null,action:null},oe=[],fe=-1;function U(t){return{current:t}}function re(t){0>fe||(t.current=oe[fe],oe[fe]=null,fe--)}function xe(t,n){fe++,oe[fe]=t.current,t.current=n}var Ue=U(null),Ie=U(null),Xe=U(null),ue=U(null);function ye(t,n){switch(xe(Xe,n),xe(Ie,t),xe(Ue,null),n.nodeType){case 9:case 11:t=(t=n.documentElement)&&(t=t.namespaceURI)?av(t):0;break;default:if(t=n.tagName,n=n.namespaceURI)n=av(n),t=rv(n,t);else switch(t){case"svg":t=1;break;case"math":t=2;break;default:t=0}}re(Ue),xe(Ue,t)}function we(){re(Ue),re(Ie),re(Xe)}function at(t){t.memoizedState!==null&&xe(ue,t);var n=Ue.current,a=rv(n,t.type);n!==a&&(xe(Ie,t),xe(Ue,a))}function Ge(t){Ie.current===t&&(re(Ue),re(Ie)),ue.current===t&&(re(ue),Tl._currentValue=ee)}var mt,un;function ut(t){if(mt===void 0)try{throw Error()}catch(a){var n=a.stack.trim().match(/\n( *(at )?)/);mt=n&&n[1]||"",un=-1<a.stack.indexOf(`
    at`)?" (<anonymous>)":-1<a.stack.indexOf("@")?"@unknown:0:0":""}return`
`+mt+t+un}var vt=!1;function Mt(t,n){if(!t||vt)return"";vt=!0;var a=Error.prepareStackTrace;Error.prepareStackTrace=void 0;try{var o={DetermineComponentFrameRoot:function(){try{if(n){var Te=function(){throw Error()};if(Object.defineProperty(Te.prototype,"props",{set:function(){throw Error()}}),typeof Reflect=="object"&&Reflect.construct){try{Reflect.construct(Te,[])}catch(_e){var me=_e}Reflect.construct(t,[],Te)}else{try{Te.call()}catch(_e){me=_e}t.call(Te.prototype)}}else{try{throw Error()}catch(_e){me=_e}(Te=t())&&typeof Te.catch=="function"&&Te.catch(function(){})}}catch(_e){if(_e&&me&&typeof _e.stack=="string")return[_e.stack,me.stack]}return[null,null]}};o.DetermineComponentFrameRoot.displayName="DetermineComponentFrameRoot";var u=Object.getOwnPropertyDescriptor(o.DetermineComponentFrameRoot,"name");u&&u.configurable&&Object.defineProperty(o.DetermineComponentFrameRoot,"name",{value:"DetermineComponentFrameRoot"});var d=o.DetermineComponentFrameRoot(),S=d[0],C=d[1];if(S&&C){var G=S.split(`
`),he=C.split(`
`);for(u=o=0;o<G.length&&!G[o].includes("DetermineComponentFrameRoot");)o++;for(;u<he.length&&!he[u].includes("DetermineComponentFrameRoot");)u++;if(o===G.length||u===he.length)for(o=G.length-1,u=he.length-1;1<=o&&0<=u&&G[o]!==he[u];)u--;for(;1<=o&&0<=u;o--,u--)if(G[o]!==he[u]){if(o!==1||u!==1)do if(o--,u--,0>u||G[o]!==he[u]){var be=`
`+G[o].replace(" at new "," at ");return t.displayName&&be.includes("<anonymous>")&&(be=be.replace("<anonymous>",t.displayName)),be}while(1<=o&&0<=u);break}}}finally{vt=!1,Error.prepareStackTrace=a}return(a=t?t.displayName||t.name:"")?ut(a):""}function pt(t,n){switch(t.tag){case 26:case 27:case 5:return ut(t.type);case 16:return ut("Lazy");case 13:return t.child!==n&&n!==null?ut("Suspense Fallback"):ut("Suspense");case 19:return ut("SuspenseList");case 0:case 15:return Mt(t.type,!1);case 11:return Mt(t.type.render,!1);case 1:return Mt(t.type,!0);case 31:return ut("Activity");default:return""}}function _t(t){try{var n="",a=null;do n+=pt(t,a),a=t,t=t.return;while(t);return n}catch(o){return`
Error generating stack: `+o.message+`
`+o.stack}}var Gt=Object.prototype.hasOwnProperty,_n=s.unstable_scheduleCallback,Xt=s.unstable_cancelCallback,fn=s.unstable_shouldYield,Z=s.unstable_requestPaint,Ft=s.unstable_now,Dt=s.unstable_getCurrentPriorityLevel,I=s.unstable_ImmediatePriority,b=s.unstable_UserBlockingPriority,K=s.unstable_NormalPriority,ce=s.unstable_LowPriority,ve=s.unstable_IdlePriority,ne=s.log,Ae=s.unstable_setDisableYieldValue,pe=null,Se=null;function Ne(t){if(typeof ne=="function"&&Ae(t),Se&&typeof Se.setStrictMode=="function")try{Se.setStrictMode(pe,t)}catch{}}var Ze=Math.clz32?Math.clz32:rt,He=Math.log,Fe=Math.LN2;function rt(t){return t>>>=0,t===0?32:31-(He(t)/Fe|0)|0}var lt=256,dt=262144,W=4194304;function Oe(t){var n=t&42;if(n!==0)return n;switch(t&-t){case 1:return 1;case 2:return 2;case 4:return 4;case 8:return 8;case 16:return 16;case 32:return 32;case 64:return 64;case 128:return 128;case 256:case 512:case 1024:case 2048:case 4096:case 8192:case 16384:case 32768:case 65536:case 131072:return t&261888;case 262144:case 524288:case 1048576:case 2097152:return t&3932160;case 4194304:case 8388608:case 16777216:case 33554432:return t&62914560;case 67108864:return 67108864;case 134217728:return 134217728;case 268435456:return 268435456;case 536870912:return 536870912;case 1073741824:return 0;default:return t}}function Me(t,n,a){var o=t.pendingLanes;if(o===0)return 0;var u=0,d=t.suspendedLanes,S=t.pingedLanes;t=t.warmLanes;var C=o&134217727;return C!==0?(o=C&~d,o!==0?u=Oe(o):(S&=C,S!==0?u=Oe(S):a||(a=C&~t,a!==0&&(u=Oe(a))))):(C=o&~d,C!==0?u=Oe(C):S!==0?u=Oe(S):a||(a=o&~t,a!==0&&(u=Oe(a)))),u===0?0:n!==0&&n!==u&&(n&d)===0&&(d=u&-u,a=n&-n,d>=a||d===32&&(a&4194048)!==0)?n:u}function Pe(t,n){return(t.pendingLanes&~(t.suspendedLanes&~t.pingedLanes)&n)===0}function Ve(t,n){switch(t){case 1:case 2:case 4:case 8:case 64:return n+250;case 16:case 32:case 128:case 256:case 512:case 1024:case 2048:case 4096:case 8192:case 16384:case 32768:case 65536:case 131072:case 262144:case 524288:case 1048576:case 2097152:return n+5e3;case 4194304:case 8388608:case 16777216:case 33554432:return-1;case 67108864:case 134217728:case 268435456:case 536870912:case 1073741824:return-1;default:return-1}}function Re(){var t=W;return W<<=1,(W&62914560)===0&&(W=4194304),t}function et(t){for(var n=[],a=0;31>a;a++)n.push(t);return n}function Je(t,n){t.pendingLanes|=n,n!==268435456&&(t.suspendedLanes=0,t.pingedLanes=0,t.warmLanes=0)}function Qt(t,n,a,o,u,d){var S=t.pendingLanes;t.pendingLanes=a,t.suspendedLanes=0,t.pingedLanes=0,t.warmLanes=0,t.expiredLanes&=a,t.entangledLanes&=a,t.errorRecoveryDisabledLanes&=a,t.shellSuspendCounter=0;var C=t.entanglements,G=t.expirationTimes,he=t.hiddenUpdates;for(a=S&~a;0<a;){var be=31-Ze(a),Te=1<<be;C[be]=0,G[be]=-1;var me=he[be];if(me!==null)for(he[be]=null,be=0;be<me.length;be++){var _e=me[be];_e!==null&&(_e.lane&=-536870913)}a&=~Te}o!==0&&Nt(t,o,0),d!==0&&u===0&&t.tag!==0&&(t.suspendedLanes|=d&~(S&~n))}function Nt(t,n,a){t.pendingLanes|=n,t.suspendedLanes&=~n;var o=31-Ze(n);t.entangledLanes|=n,t.entanglements[o]=t.entanglements[o]|1073741824|a&261930}function ei(t,n){var a=t.entangledLanes|=n;for(t=t.entanglements;a;){var o=31-Ze(a),u=1<<o;u&n|t[o]&n&&(t[o]|=n),a&=~u}}function ti(t,n){var a=n&-n;return a=(a&42)!==0?1:Qi(a),(a&(t.suspendedLanes|n))!==0?0:a}function Qi(t){switch(t){case 2:t=1;break;case 8:t=4;break;case 32:t=16;break;case 256:case 512:case 1024:case 2048:case 4096:case 8192:case 16384:case 32768:case 65536:case 131072:case 262144:case 524288:case 1048576:case 2097152:case 4194304:case 8388608:case 16777216:case 33554432:t=128;break;case 268435456:t=134217728;break;default:t=0}return t}function os(t){return t&=-t,2<t?8<t?(t&134217727)!==0?32:268435456:8:2}function Da(){var t=H.p;return t!==0?t:(t=window.event,t===void 0?32:Cv(t.type))}function pa(t,n){var a=H.p;try{return H.p=t,n()}finally{H.p=a}}var _i=Math.random().toString(36).slice(2),yn="__reactFiber$"+_i,Bn="__reactProps$"+_i,Kn="__reactContainer$"+_i,Wt="__reactEvents$"+_i,Mn="__reactListeners$"+_i,Tr="__reactHandles$"+_i,Ua="__reactResources$"+_i,qt="__reactMarker$"+_i;function Ji(t){delete t[yn],delete t[Bn],delete t[Wt],delete t[Mn],delete t[Tr]}function Pi(t){var n=t[yn];if(n)return n;for(var a=t.parentNode;a;){if(n=a[Kn]||a[yn]){if(a=n.alternate,n.child!==null||a!==null&&a.child!==null)for(t=dv(t);t!==null;){if(a=t[yn])return a;t=dv(t)}return n}t=a,a=t.parentNode}return null}function Ii(t){if(t=t[yn]||t[Kn]){var n=t.tag;if(n===5||n===6||n===13||n===31||n===26||n===27||n===3)return t}return null}function ma(t){var n=t.tag;if(n===5||n===26||n===27||n===6)return t.stateNode;throw Error(r(33))}function ga(t){var n=t[Ua];return n||(n=t[Ua]={hoistableStyles:new Map,hoistableScripts:new Map}),n}function sn(t){t[qt]=!0}var Na=new Set,xi={};function A(t,n){X(t,n),X(t+"Capture",n)}function X(t,n){for(xi[t]=n,t=0;t<n.length;t++)Na.add(n[t])}var ge=RegExp("^[:A-Z_a-z\\u00C0-\\u00D6\\u00D8-\\u00F6\\u00F8-\\u02FF\\u0370-\\u037D\\u037F-\\u1FFF\\u200C-\\u200D\\u2070-\\u218F\\u2C00-\\u2FEF\\u3001-\\uD7FF\\uF900-\\uFDCF\\uFDF0-\\uFFFD][:A-Z_a-z\\u00C0-\\u00D6\\u00D8-\\u00F6\\u00F8-\\u02FF\\u0370-\\u037D\\u037F-\\u1FFF\\u200C-\\u200D\\u2070-\\u218F\\u2C00-\\u2FEF\\u3001-\\uD7FF\\uF900-\\uFDCF\\uFDF0-\\uFFFD\\-.0-9\\u00B7\\u0300-\\u036F\\u203F-\\u2040]*$"),ie={},ae={};function ze(t){return Gt.call(ae,t)?!0:Gt.call(ie,t)?!1:ge.test(t)?ae[t]=!0:(ie[t]=!0,!1)}function We(t,n,a){if(ze(n))if(a===null)t.removeAttribute(n);else{switch(typeof a){case"undefined":case"function":case"symbol":t.removeAttribute(n);return;case"boolean":var o=n.toLowerCase().slice(0,5);if(o!=="data-"&&o!=="aria-"){t.removeAttribute(n);return}}t.setAttribute(n,""+a)}}function Be(t,n,a){if(a===null)t.removeAttribute(n);else{switch(typeof a){case"undefined":case"function":case"symbol":case"boolean":t.removeAttribute(n);return}t.setAttribute(n,""+a)}}function qe(t,n,a,o){if(o===null)t.removeAttribute(a);else{switch(typeof o){case"undefined":case"function":case"symbol":case"boolean":t.removeAttribute(a);return}t.setAttributeNS(n,a,""+o)}}function Ye(t){switch(typeof t){case"bigint":case"boolean":case"number":case"string":case"undefined":return t;case"object":return t;default:return""}}function gt(t){var n=t.type;return(t=t.nodeName)&&t.toLowerCase()==="input"&&(n==="checkbox"||n==="radio")}function Tt(t,n,a){var o=Object.getOwnPropertyDescriptor(t.constructor.prototype,n);if(!t.hasOwnProperty(n)&&typeof o<"u"&&typeof o.get=="function"&&typeof o.set=="function"){var u=o.get,d=o.set;return Object.defineProperty(t,n,{configurable:!0,get:function(){return u.call(this)},set:function(S){a=""+S,d.call(this,S)}}),Object.defineProperty(t,n,{enumerable:o.enumerable}),{getValue:function(){return a},setValue:function(S){a=""+S},stopTracking:function(){t._valueTracker=null,delete t[n]}}}}function $e(t){if(!t._valueTracker){var n=gt(t)?"checked":"value";t._valueTracker=Tt(t,n,""+t[n])}}function zt(t){if(!t)return!1;var n=t._valueTracker;if(!n)return!0;var a=n.getValue(),o="";return t&&(o=gt(t)?t.checked?"true":"false":t.value),t=o,t!==a?(n.setValue(t),!0):!1}function dn(t){if(t=t||(typeof document<"u"?document:void 0),typeof t>"u")return null;try{return t.activeElement||t.body}catch{return t.body}}var rn=/[\n"\\]/g;function bt(t){return t.replace(rn,function(n){return"\\"+n.charCodeAt(0).toString(16)+" "})}function Tn(t,n,a,o,u,d,S,C){t.name="",S!=null&&typeof S!="function"&&typeof S!="symbol"&&typeof S!="boolean"?t.type=S:t.removeAttribute("type"),n!=null?S==="number"?(n===0&&t.value===""||t.value!=n)&&(t.value=""+Ye(n)):t.value!==""+Ye(n)&&(t.value=""+Ye(n)):S!=="submit"&&S!=="reset"||t.removeAttribute("value"),n!=null?wn(t,S,Ye(n)):a!=null?wn(t,S,Ye(a)):o!=null&&t.removeAttribute("value"),u==null&&d!=null&&(t.defaultChecked=!!d),u!=null&&(t.checked=u&&typeof u!="function"&&typeof u!="symbol"),C!=null&&typeof C!="function"&&typeof C!="symbol"&&typeof C!="boolean"?t.name=""+Ye(C):t.removeAttribute("name")}function Ke(t,n,a,o,u,d,S,C){if(d!=null&&typeof d!="function"&&typeof d!="symbol"&&typeof d!="boolean"&&(t.type=d),n!=null||a!=null){if(!(d!=="submit"&&d!=="reset"||n!=null)){$e(t);return}a=a!=null?""+Ye(a):"",n=n!=null?""+Ye(n):a,C||n===t.value||(t.value=n),t.defaultValue=n}o=o??u,o=typeof o!="function"&&typeof o!="symbol"&&!!o,t.checked=C?t.checked:!!o,t.defaultChecked=!!o,S!=null&&typeof S!="function"&&typeof S!="symbol"&&typeof S!="boolean"&&(t.name=S),$e(t)}function wn(t,n,a){n==="number"&&dn(t.ownerDocument)===t||t.defaultValue===""+a||(t.defaultValue=""+a)}function Et(t,n,a,o){if(t=t.options,n){n={};for(var u=0;u<a.length;u++)n["$"+a[u]]=!0;for(a=0;a<t.length;a++)u=n.hasOwnProperty("$"+t[a].value),t[a].selected!==u&&(t[a].selected=u),u&&o&&(t[a].defaultSelected=!0)}else{for(a=""+Ye(a),n=null,u=0;u<t.length;u++){if(t[u].value===a){t[u].selected=!0,o&&(t[u].defaultSelected=!0);return}n!==null||t[u].disabled||(n=t[u])}n!==null&&(n.selected=!0)}}function Qn(t,n,a){if(n!=null&&(n=""+Ye(n),n!==t.value&&(t.value=n),a==null)){t.defaultValue!==n&&(t.defaultValue=n);return}t.defaultValue=a!=null?""+Ye(a):""}function ci(t,n,a,o){if(n==null){if(o!=null){if(a!=null)throw Error(r(92));if(j(o)){if(1<o.length)throw Error(r(93));o=o[0]}a=o}a==null&&(a=""),n=a}a=Ye(n),t.defaultValue=a,o=t.textContent,o===a&&o!==""&&o!==null&&(t.value=o),$e(t)}function ni(t,n){if(n){var a=t.firstChild;if(a&&a===t.lastChild&&a.nodeType===3){a.nodeValue=n;return}}t.textContent=n}var $i=new Set("animationIterationCount aspectRatio borderImageOutset borderImageSlice borderImageWidth boxFlex boxFlexGroup boxOrdinalGroup columnCount columns flex flexGrow flexPositive flexShrink flexNegative flexOrder gridArea gridRow gridRowEnd gridRowSpan gridRowStart gridColumn gridColumnEnd gridColumnSpan gridColumnStart fontWeight lineClamp lineHeight opacity order orphans scale tabSize widows zIndex zoom fillOpacity floodOpacity stopOpacity strokeDasharray strokeDashoffset strokeMiterlimit strokeOpacity strokeWidth MozAnimationIterationCount MozBoxFlex MozBoxFlexGroup MozLineClamp msAnimationIterationCount msFlex msZoom msFlexGrow msFlexNegative msFlexOrder msFlexPositive msFlexShrink msGridColumn msGridColumnSpan msGridRow msGridRowSpan WebkitAnimationIterationCount WebkitBoxFlex WebKitBoxFlexGroup WebkitBoxOrdinalGroup WebkitColumnCount WebkitColumns WebkitFlex WebkitFlexGrow WebkitFlexPositive WebkitFlexShrink WebkitLineClamp".split(" "));function jt(t,n,a){var o=n.indexOf("--")===0;a==null||typeof a=="boolean"||a===""?o?t.setProperty(n,""):n==="float"?t.cssFloat="":t[n]="":o?t.setProperty(n,a):typeof a!="number"||a===0||$i.has(n)?n==="float"?t.cssFloat=a:t[n]=(""+a).trim():t[n]=a+"px"}function gn(t,n,a){if(n!=null&&typeof n!="object")throw Error(r(62));if(t=t.style,a!=null){for(var o in a)!a.hasOwnProperty(o)||n!=null&&n.hasOwnProperty(o)||(o.indexOf("--")===0?t.setProperty(o,""):o==="float"?t.cssFloat="":t[o]="");for(var u in n)o=n[u],n.hasOwnProperty(u)&&a[u]!==o&&jt(t,u,o)}else for(var d in n)n.hasOwnProperty(d)&&jt(t,d,n[d])}function Ai(t){if(t.indexOf("-")===-1)return!1;switch(t){case"annotation-xml":case"color-profile":case"font-face":case"font-face-src":case"font-face-uri":case"font-face-format":case"font-face-name":case"missing-glyph":return!1;default:return!0}}var en=new Map([["acceptCharset","accept-charset"],["htmlFor","for"],["httpEquiv","http-equiv"],["crossOrigin","crossorigin"],["accentHeight","accent-height"],["alignmentBaseline","alignment-baseline"],["arabicForm","arabic-form"],["baselineShift","baseline-shift"],["capHeight","cap-height"],["clipPath","clip-path"],["clipRule","clip-rule"],["colorInterpolation","color-interpolation"],["colorInterpolationFilters","color-interpolation-filters"],["colorProfile","color-profile"],["colorRendering","color-rendering"],["dominantBaseline","dominant-baseline"],["enableBackground","enable-background"],["fillOpacity","fill-opacity"],["fillRule","fill-rule"],["floodColor","flood-color"],["floodOpacity","flood-opacity"],["fontFamily","font-family"],["fontSize","font-size"],["fontSizeAdjust","font-size-adjust"],["fontStretch","font-stretch"],["fontStyle","font-style"],["fontVariant","font-variant"],["fontWeight","font-weight"],["glyphName","glyph-name"],["glyphOrientationHorizontal","glyph-orientation-horizontal"],["glyphOrientationVertical","glyph-orientation-vertical"],["horizAdvX","horiz-adv-x"],["horizOriginX","horiz-origin-x"],["imageRendering","image-rendering"],["letterSpacing","letter-spacing"],["lightingColor","lighting-color"],["markerEnd","marker-end"],["markerMid","marker-mid"],["markerStart","marker-start"],["overlinePosition","overline-position"],["overlineThickness","overline-thickness"],["paintOrder","paint-order"],["panose-1","panose-1"],["pointerEvents","pointer-events"],["renderingIntent","rendering-intent"],["shapeRendering","shape-rendering"],["stopColor","stop-color"],["stopOpacity","stop-opacity"],["strikethroughPosition","strikethrough-position"],["strikethroughThickness","strikethrough-thickness"],["strokeDasharray","stroke-dasharray"],["strokeDashoffset","stroke-dashoffset"],["strokeLinecap","stroke-linecap"],["strokeLinejoin","stroke-linejoin"],["strokeMiterlimit","stroke-miterlimit"],["strokeOpacity","stroke-opacity"],["strokeWidth","stroke-width"],["textAnchor","text-anchor"],["textDecoration","text-decoration"],["textRendering","text-rendering"],["transformOrigin","transform-origin"],["underlinePosition","underline-position"],["underlineThickness","underline-thickness"],["unicodeBidi","unicode-bidi"],["unicodeRange","unicode-range"],["unitsPerEm","units-per-em"],["vAlphabetic","v-alphabetic"],["vHanging","v-hanging"],["vIdeographic","v-ideographic"],["vMathematical","v-mathematical"],["vectorEffect","vector-effect"],["vertAdvY","vert-adv-y"],["vertOriginX","vert-origin-x"],["vertOriginY","vert-origin-y"],["wordSpacing","word-spacing"],["writingMode","writing-mode"],["xmlnsXlink","xmlns:xlink"],["xHeight","x-height"]]),ea=/^[\u0000-\u001F ]*j[\r\n\t]*a[\r\n\t]*v[\r\n\t]*a[\r\n\t]*s[\r\n\t]*c[\r\n\t]*r[\r\n\t]*i[\r\n\t]*p[\r\n\t]*t[\r\n\t]*:/i;function Fi(t){return ea.test(""+t)?"javascript:throw new Error('React has blocked a javascript: URL as a security precaution.')":t}function Si(){}var zs=null;function Bs(t){return t=t.target||t.srcElement||window,t.correspondingUseElement&&(t=t.correspondingUseElement),t.nodeType===3?t.parentNode:t}var ja=null,Za=null;function Wo(t){var n=Ii(t);if(n&&(t=n.stateNode)){var a=t[Bn]||null;e:switch(t=n.stateNode,n.type){case"input":if(Tn(t,a.value,a.defaultValue,a.defaultValue,a.checked,a.defaultChecked,a.type,a.name),n=a.name,a.type==="radio"&&n!=null){for(a=t;a.parentNode;)a=a.parentNode;for(a=a.querySelectorAll('input[name="'+bt(""+n)+'"][type="radio"]'),n=0;n<a.length;n++){var o=a[n];if(o!==t&&o.form===t.form){var u=o[Bn]||null;if(!u)throw Error(r(90));Tn(o,u.value,u.defaultValue,u.defaultValue,u.checked,u.defaultChecked,u.type,u.name)}}for(n=0;n<a.length;n++)o=a[n],o.form===t.form&&zt(o)}break e;case"textarea":Qn(t,a.value,a.defaultValue);break e;case"select":n=a.value,n!=null&&Et(t,!!a.multiple,n,!1)}}}var le=!1;function te(t,n,a){if(le)return t(n,a);le=!0;try{var o=t(n);return o}finally{if(le=!1,(ja!==null||Za!==null)&&(Ic(),ja&&(n=ja,t=Za,Za=ja=null,Wo(n),t)))for(n=0;n<t.length;n++)Wo(t[n])}}function De(t,n){var a=t.stateNode;if(a===null)return null;var o=a[Bn]||null;if(o===null)return null;a=o[n];e:switch(n){case"onClick":case"onClickCapture":case"onDoubleClick":case"onDoubleClickCapture":case"onMouseDown":case"onMouseDownCapture":case"onMouseMove":case"onMouseMoveCapture":case"onMouseUp":case"onMouseUpCapture":case"onMouseEnter":(o=!o.disabled)||(t=t.type,o=!(t==="button"||t==="input"||t==="select"||t==="textarea")),t=!o;break e;default:t=!1}if(t)return null;if(a&&typeof a!="function")throw Error(r(231,n,typeof a));return a}var Ce=!(typeof window>"u"||typeof window.document>"u"||typeof window.document.createElement>"u"),Qe=!1;if(Ce)try{var Lt={};Object.defineProperty(Lt,"passive",{get:function(){Qe=!0}}),window.addEventListener("test",Lt,Lt),window.removeEventListener("test",Lt,Lt)}catch{Qe=!1}var Le=null,st=null,xt=null;function Ot(){if(xt)return xt;var t,n=st,a=n.length,o,u="value"in Le?Le.value:Le.textContent,d=u.length;for(t=0;t<a&&n[t]===u[t];t++);var S=a-t;for(o=1;o<=S&&n[a-o]===u[d-o];o++);return xt=u.slice(t,1<o?1-o:void 0)}function Yt(t){var n=t.keyCode;return"charCode"in t?(t=t.charCode,t===0&&n===13&&(t=13)):t=n,t===10&&(t=13),32<=t||t===13?t:0}function Wn(){return!0}function it(){return!1}function ke(t){function n(a,o,u,d,S){this._reactName=a,this._targetInst=u,this.type=o,this.nativeEvent=d,this.target=S,this.currentTarget=null;for(var C in t)t.hasOwnProperty(C)&&(a=t[C],this[C]=a?a(d):d[C]);return this.isDefaultPrevented=(d.defaultPrevented!=null?d.defaultPrevented:d.returnValue===!1)?Wn:it,this.isPropagationStopped=it,this}return _(n.prototype,{preventDefault:function(){this.defaultPrevented=!0;var a=this.nativeEvent;a&&(a.preventDefault?a.preventDefault():typeof a.returnValue!="unknown"&&(a.returnValue=!1),this.isDefaultPrevented=Wn)},stopPropagation:function(){var a=this.nativeEvent;a&&(a.stopPropagation?a.stopPropagation():typeof a.cancelBubble!="unknown"&&(a.cancelBubble=!0),this.isPropagationStopped=Wn)},persist:function(){},isPersistent:Wn}),n}var tn={eventPhase:0,bubbles:0,cancelable:0,timeStamp:function(t){return t.timeStamp||Date.now()},defaultPrevented:0,isTrusted:0},An=ke(tn),Rn=_({},tn,{view:0,detail:0}),va=ke(Rn),Dn,On,Ri,La=_({},Rn,{screenX:0,screenY:0,clientX:0,clientY:0,pageX:0,pageY:0,ctrlKey:0,shiftKey:0,altKey:0,metaKey:0,getModifierState:af,button:0,buttons:0,relatedTarget:function(t){return t.relatedTarget===void 0?t.fromElement===t.srcElement?t.toElement:t.fromElement:t.relatedTarget},movementX:function(t){return"movementX"in t?t.movementX:(t!==Ri&&(Ri&&t.type==="mousemove"?(Dn=t.screenX-Ri.screenX,On=t.screenY-Ri.screenY):On=Dn=0,Ri=t),Dn)},movementY:function(t){return"movementY"in t?t.movementY:On}}),Oa=ke(La),Ka=_({},La,{dataTransfer:0}),nn=ke(Ka),ui=_({},Rn,{relatedTarget:0}),ta=ke(ui),_a=_({},tn,{animationName:0,elapsedTime:0,pseudoElement:0}),xa=ke(_a),na=_({},tn,{clipboardData:function(t){return"clipboardData"in t?t.clipboardData:window.clipboardData}}),Qa=ke(na),Ar=_({},tn,{data:0}),Ci=ke(Ar),Rr={Esc:"Escape",Spacebar:" ",Left:"ArrowLeft",Up:"ArrowUp",Right:"ArrowRight",Down:"ArrowDown",Del:"Delete",Win:"OS",Menu:"ContextMenu",Apps:"ContextMenu",Scroll:"ScrollLock",MozPrintableKey:"Unidentified"},Cr={8:"Backspace",9:"Tab",12:"Clear",13:"Enter",16:"Shift",17:"Control",18:"Alt",19:"Pause",20:"CapsLock",27:"Escape",32:" ",33:"PageUp",34:"PageDown",35:"End",36:"Home",37:"ArrowLeft",38:"ArrowUp",39:"ArrowRight",40:"ArrowDown",45:"Insert",46:"Delete",112:"F1",113:"F2",114:"F3",115:"F4",116:"F5",117:"F6",118:"F7",119:"F8",120:"F9",121:"F10",122:"F11",123:"F12",144:"NumLock",145:"ScrollLock",224:"Meta"},ii={Alt:"altKey",Control:"ctrlKey",Meta:"metaKey",Shift:"shiftKey"};function dS(t){var n=this.nativeEvent;return n.getModifierState?n.getModifierState(t):(t=ii[t])?!!n[t]:!1}function af(){return dS}var hS=_({},Rn,{key:function(t){if(t.key){var n=Rr[t.key]||t.key;if(n!=="Unidentified")return n}return t.type==="keypress"?(t=Yt(t),t===13?"Enter":String.fromCharCode(t)):t.type==="keydown"||t.type==="keyup"?Cr[t.keyCode]||"Unidentified":""},code:0,location:0,ctrlKey:0,shiftKey:0,altKey:0,metaKey:0,repeat:0,locale:0,getModifierState:af,charCode:function(t){return t.type==="keypress"?Yt(t):0},keyCode:function(t){return t.type==="keydown"||t.type==="keyup"?t.keyCode:0},which:function(t){return t.type==="keypress"?Yt(t):t.type==="keydown"||t.type==="keyup"?t.keyCode:0}}),pS=ke(hS),mS=_({},La,{pointerId:0,width:0,height:0,pressure:0,tangentialPressure:0,tiltX:0,tiltY:0,twist:0,pointerType:0,isPrimary:0}),cm=ke(mS),gS=_({},Rn,{touches:0,targetTouches:0,changedTouches:0,altKey:0,metaKey:0,ctrlKey:0,shiftKey:0,getModifierState:af}),vS=ke(gS),_S=_({},tn,{propertyName:0,elapsedTime:0,pseudoElement:0}),xS=ke(_S),SS=_({},La,{deltaX:function(t){return"deltaX"in t?t.deltaX:"wheelDeltaX"in t?-t.wheelDeltaX:0},deltaY:function(t){return"deltaY"in t?t.deltaY:"wheelDeltaY"in t?-t.wheelDeltaY:"wheelDelta"in t?-t.wheelDelta:0},deltaZ:0,deltaMode:0}),yS=ke(SS),MS=_({},tn,{newState:0,oldState:0}),bS=ke(MS),ES=[9,13,27,32],rf=Ce&&"CompositionEvent"in window,qo=null;Ce&&"documentMode"in document&&(qo=document.documentMode);var TS=Ce&&"TextEvent"in window&&!qo,um=Ce&&(!rf||qo&&8<qo&&11>=qo),fm=" ",dm=!1;function hm(t,n){switch(t){case"keyup":return ES.indexOf(n.keyCode)!==-1;case"keydown":return n.keyCode!==229;case"keypress":case"mousedown":case"focusout":return!0;default:return!1}}function pm(t){return t=t.detail,typeof t=="object"&&"data"in t?t.data:null}var Hs=!1;function AS(t,n){switch(t){case"compositionend":return pm(n);case"keypress":return n.which!==32?null:(dm=!0,fm);case"textInput":return t=n.data,t===fm&&dm?null:t;default:return null}}function RS(t,n){if(Hs)return t==="compositionend"||!rf&&hm(t,n)?(t=Ot(),xt=st=Le=null,Hs=!1,t):null;switch(t){case"paste":return null;case"keypress":if(!(n.ctrlKey||n.altKey||n.metaKey)||n.ctrlKey&&n.altKey){if(n.char&&1<n.char.length)return n.char;if(n.which)return String.fromCharCode(n.which)}return null;case"compositionend":return um&&n.locale!=="ko"?null:n.data;default:return null}}var CS={color:!0,date:!0,datetime:!0,"datetime-local":!0,email:!0,month:!0,number:!0,password:!0,range:!0,search:!0,tel:!0,text:!0,time:!0,url:!0,week:!0};function mm(t){var n=t&&t.nodeName&&t.nodeName.toLowerCase();return n==="input"?!!CS[t.type]:n==="textarea"}function gm(t,n,a,o){ja?Za?Za.push(o):Za=[o]:ja=o,n=kc(n,"onChange"),0<n.length&&(a=new An("onChange","change",null,a,o),t.push({event:a,listeners:n}))}var Yo=null,jo=null;function wS(t){J0(t,0)}function tc(t){var n=ma(t);if(zt(n))return t}function vm(t,n){if(t==="change")return n}var _m=!1;if(Ce){var sf;if(Ce){var of="oninput"in document;if(!of){var xm=document.createElement("div");xm.setAttribute("oninput","return;"),of=typeof xm.oninput=="function"}sf=of}else sf=!1;_m=sf&&(!document.documentMode||9<document.documentMode)}function Sm(){Yo&&(Yo.detachEvent("onpropertychange",ym),jo=Yo=null)}function ym(t){if(t.propertyName==="value"&&tc(jo)){var n=[];gm(n,jo,t,Bs(t)),te(wS,n)}}function DS(t,n,a){t==="focusin"?(Sm(),Yo=n,jo=a,Yo.attachEvent("onpropertychange",ym)):t==="focusout"&&Sm()}function US(t){if(t==="selectionchange"||t==="keyup"||t==="keydown")return tc(jo)}function NS(t,n){if(t==="click")return tc(n)}function LS(t,n){if(t==="input"||t==="change")return tc(n)}function OS(t,n){return t===n&&(t!==0||1/t===1/n)||t!==t&&n!==n}var zi=typeof Object.is=="function"?Object.is:OS;function Zo(t,n){if(zi(t,n))return!0;if(typeof t!="object"||t===null||typeof n!="object"||n===null)return!1;var a=Object.keys(t),o=Object.keys(n);if(a.length!==o.length)return!1;for(o=0;o<a.length;o++){var u=a[o];if(!Gt.call(n,u)||!zi(t[u],n[u]))return!1}return!0}function Mm(t){for(;t&&t.firstChild;)t=t.firstChild;return t}function bm(t,n){var a=Mm(t);t=0;for(var o;a;){if(a.nodeType===3){if(o=t+a.textContent.length,t<=n&&o>=n)return{node:a,offset:n-t};t=o}e:{for(;a;){if(a.nextSibling){a=a.nextSibling;break e}a=a.parentNode}a=void 0}a=Mm(a)}}function Em(t,n){return t&&n?t===n?!0:t&&t.nodeType===3?!1:n&&n.nodeType===3?Em(t,n.parentNode):"contains"in t?t.contains(n):t.compareDocumentPosition?!!(t.compareDocumentPosition(n)&16):!1:!1}function Tm(t){t=t!=null&&t.ownerDocument!=null&&t.ownerDocument.defaultView!=null?t.ownerDocument.defaultView:window;for(var n=dn(t.document);n instanceof t.HTMLIFrameElement;){try{var a=typeof n.contentWindow.location.href=="string"}catch{a=!1}if(a)t=n.contentWindow;else break;n=dn(t.document)}return n}function lf(t){var n=t&&t.nodeName&&t.nodeName.toLowerCase();return n&&(n==="input"&&(t.type==="text"||t.type==="search"||t.type==="tel"||t.type==="url"||t.type==="password")||n==="textarea"||t.contentEditable==="true")}var PS=Ce&&"documentMode"in document&&11>=document.documentMode,Gs=null,cf=null,Ko=null,uf=!1;function Am(t,n,a){var o=a.window===a?a.document:a.nodeType===9?a:a.ownerDocument;uf||Gs==null||Gs!==dn(o)||(o=Gs,"selectionStart"in o&&lf(o)?o={start:o.selectionStart,end:o.selectionEnd}:(o=(o.ownerDocument&&o.ownerDocument.defaultView||window).getSelection(),o={anchorNode:o.anchorNode,anchorOffset:o.anchorOffset,focusNode:o.focusNode,focusOffset:o.focusOffset}),Ko&&Zo(Ko,o)||(Ko=o,o=kc(cf,"onSelect"),0<o.length&&(n=new An("onSelect","select",null,n,a),t.push({event:n,listeners:o}),n.target=Gs)))}function ls(t,n){var a={};return a[t.toLowerCase()]=n.toLowerCase(),a["Webkit"+t]="webkit"+n,a["Moz"+t]="moz"+n,a}var Vs={animationend:ls("Animation","AnimationEnd"),animationiteration:ls("Animation","AnimationIteration"),animationstart:ls("Animation","AnimationStart"),transitionrun:ls("Transition","TransitionRun"),transitionstart:ls("Transition","TransitionStart"),transitioncancel:ls("Transition","TransitionCancel"),transitionend:ls("Transition","TransitionEnd")},ff={},Rm={};Ce&&(Rm=document.createElement("div").style,"AnimationEvent"in window||(delete Vs.animationend.animation,delete Vs.animationiteration.animation,delete Vs.animationstart.animation),"TransitionEvent"in window||delete Vs.transitionend.transition);function cs(t){if(ff[t])return ff[t];if(!Vs[t])return t;var n=Vs[t],a;for(a in n)if(n.hasOwnProperty(a)&&a in Rm)return ff[t]=n[a];return t}var Cm=cs("animationend"),wm=cs("animationiteration"),Dm=cs("animationstart"),IS=cs("transitionrun"),FS=cs("transitionstart"),zS=cs("transitioncancel"),Um=cs("transitionend"),Nm=new Map,df="abort auxClick beforeToggle cancel canPlay canPlayThrough click close contextMenu copy cut drag dragEnd dragEnter dragExit dragLeave dragOver dragStart drop durationChange emptied encrypted ended error gotPointerCapture input invalid keyDown keyPress keyUp load loadedData loadedMetadata loadStart lostPointerCapture mouseDown mouseMove mouseOut mouseOver mouseUp paste pause play playing pointerCancel pointerDown pointerMove pointerOut pointerOver pointerUp progress rateChange reset resize seeked seeking stalled submit suspend timeUpdate touchCancel touchEnd touchStart volumeChange scroll toggle touchMove waiting wheel".split(" ");df.push("scrollEnd");function Sa(t,n){Nm.set(t,n),A(n,[t])}var nc=typeof reportError=="function"?reportError:function(t){if(typeof window=="object"&&typeof window.ErrorEvent=="function"){var n=new window.ErrorEvent("error",{bubbles:!0,cancelable:!0,message:typeof t=="object"&&t!==null&&typeof t.message=="string"?String(t.message):String(t),error:t});if(!window.dispatchEvent(n))return}else if(typeof process=="object"&&typeof process.emit=="function"){process.emit("uncaughtException",t);return}console.error(t)},ia=[],ks=0,hf=0;function ic(){for(var t=ks,n=hf=ks=0;n<t;){var a=ia[n];ia[n++]=null;var o=ia[n];ia[n++]=null;var u=ia[n];ia[n++]=null;var d=ia[n];if(ia[n++]=null,o!==null&&u!==null){var S=o.pending;S===null?u.next=u:(u.next=S.next,S.next=u),o.pending=u}d!==0&&Lm(a,u,d)}}function ac(t,n,a,o){ia[ks++]=t,ia[ks++]=n,ia[ks++]=a,ia[ks++]=o,hf|=o,t.lanes|=o,t=t.alternate,t!==null&&(t.lanes|=o)}function pf(t,n,a,o){return ac(t,n,a,o),rc(t)}function us(t,n){return ac(t,null,null,n),rc(t)}function Lm(t,n,a){t.lanes|=a;var o=t.alternate;o!==null&&(o.lanes|=a);for(var u=!1,d=t.return;d!==null;)d.childLanes|=a,o=d.alternate,o!==null&&(o.childLanes|=a),d.tag===22&&(t=d.stateNode,t===null||t._visibility&1||(u=!0)),t=d,d=d.return;return t.tag===3?(d=t.stateNode,u&&n!==null&&(u=31-Ze(a),t=d.hiddenUpdates,o=t[u],o===null?t[u]=[n]:o.push(n),n.lane=a|536870912),d):null}function rc(t){if(50<_l)throw _l=0,bd=null,Error(r(185));for(var n=t.return;n!==null;)t=n,n=t.return;return t.tag===3?t.stateNode:null}var Xs={};function BS(t,n,a,o){this.tag=t,this.key=a,this.sibling=this.child=this.return=this.stateNode=this.type=this.elementType=null,this.index=0,this.refCleanup=this.ref=null,this.pendingProps=n,this.dependencies=this.memoizedState=this.updateQueue=this.memoizedProps=null,this.mode=o,this.subtreeFlags=this.flags=0,this.deletions=null,this.childLanes=this.lanes=0,this.alternate=null}function Bi(t,n,a,o){return new BS(t,n,a,o)}function mf(t){return t=t.prototype,!(!t||!t.isReactComponent)}function Ja(t,n){var a=t.alternate;return a===null?(a=Bi(t.tag,n,t.key,t.mode),a.elementType=t.elementType,a.type=t.type,a.stateNode=t.stateNode,a.alternate=t,t.alternate=a):(a.pendingProps=n,a.type=t.type,a.flags=0,a.subtreeFlags=0,a.deletions=null),a.flags=t.flags&65011712,a.childLanes=t.childLanes,a.lanes=t.lanes,a.child=t.child,a.memoizedProps=t.memoizedProps,a.memoizedState=t.memoizedState,a.updateQueue=t.updateQueue,n=t.dependencies,a.dependencies=n===null?null:{lanes:n.lanes,firstContext:n.firstContext},a.sibling=t.sibling,a.index=t.index,a.ref=t.ref,a.refCleanup=t.refCleanup,a}function Om(t,n){t.flags&=65011714;var a=t.alternate;return a===null?(t.childLanes=0,t.lanes=n,t.child=null,t.subtreeFlags=0,t.memoizedProps=null,t.memoizedState=null,t.updateQueue=null,t.dependencies=null,t.stateNode=null):(t.childLanes=a.childLanes,t.lanes=a.lanes,t.child=a.child,t.subtreeFlags=0,t.deletions=null,t.memoizedProps=a.memoizedProps,t.memoizedState=a.memoizedState,t.updateQueue=a.updateQueue,t.type=a.type,n=a.dependencies,t.dependencies=n===null?null:{lanes:n.lanes,firstContext:n.firstContext}),t}function sc(t,n,a,o,u,d){var S=0;if(o=t,typeof t=="function")mf(t)&&(S=1);else if(typeof t=="string")S=Xy(t,a,Ue.current)?26:t==="html"||t==="head"||t==="body"?27:5;else e:switch(t){case O:return t=Bi(31,a,n,u),t.elementType=O,t.lanes=d,t;case D:return fs(a.children,u,d,n);case M:S=8,u|=24;break;case y:return t=Bi(12,a,n,u|2),t.elementType=y,t.lanes=d,t;case N:return t=Bi(13,a,n,u),t.elementType=N,t.lanes=d,t;case L:return t=Bi(19,a,n,u),t.elementType=L,t.lanes=d,t;default:if(typeof t=="object"&&t!==null)switch(t.$$typeof){case V:S=10;break e;case F:S=9;break e;case R:S=11;break e;case P:S=14;break e;case T:S=16,o=null;break e}S=29,a=Error(r(130,t===null?"null":typeof t,"")),o=null}return n=Bi(S,a,n,u),n.elementType=t,n.type=o,n.lanes=d,n}function fs(t,n,a,o){return t=Bi(7,t,o,n),t.lanes=a,t}function gf(t,n,a){return t=Bi(6,t,null,n),t.lanes=a,t}function Pm(t){var n=Bi(18,null,null,0);return n.stateNode=t,n}function vf(t,n,a){return n=Bi(4,t.children!==null?t.children:[],t.key,n),n.lanes=a,n.stateNode={containerInfo:t.containerInfo,pendingChildren:null,implementation:t.implementation},n}var Im=new WeakMap;function aa(t,n){if(typeof t=="object"&&t!==null){var a=Im.get(t);return a!==void 0?a:(n={value:t,source:n,stack:_t(n)},Im.set(t,n),n)}return{value:t,source:n,stack:_t(n)}}var Ws=[],qs=0,oc=null,Qo=0,ra=[],sa=0,wr=null,Pa=1,Ia="";function $a(t,n){Ws[qs++]=Qo,Ws[qs++]=oc,oc=t,Qo=n}function Fm(t,n,a){ra[sa++]=Pa,ra[sa++]=Ia,ra[sa++]=wr,wr=t;var o=Pa;t=Ia;var u=32-Ze(o)-1;o&=~(1<<u),a+=1;var d=32-Ze(n)+u;if(30<d){var S=u-u%5;d=(o&(1<<S)-1).toString(32),o>>=S,u-=S,Pa=1<<32-Ze(n)+u|a<<u|o,Ia=d+t}else Pa=1<<d|a<<u|o,Ia=t}function _f(t){t.return!==null&&($a(t,1),Fm(t,1,0))}function xf(t){for(;t===oc;)oc=Ws[--qs],Ws[qs]=null,Qo=Ws[--qs],Ws[qs]=null;for(;t===wr;)wr=ra[--sa],ra[sa]=null,Ia=ra[--sa],ra[sa]=null,Pa=ra[--sa],ra[sa]=null}function zm(t,n){ra[sa++]=Pa,ra[sa++]=Ia,ra[sa++]=wr,Pa=n.id,Ia=n.overflow,wr=t}var ai=null,xn=null,Vt=!1,Dr=null,oa=!1,Sf=Error(r(519));function Ur(t){var n=Error(r(418,1<arguments.length&&arguments[1]!==void 0&&arguments[1]?"text":"HTML",""));throw Jo(aa(n,t)),Sf}function Bm(t){var n=t.stateNode,a=t.type,o=t.memoizedProps;switch(n[yn]=t,n[Bn]=o,a){case"dialog":It("cancel",n),It("close",n);break;case"iframe":case"object":case"embed":It("load",n);break;case"video":case"audio":for(a=0;a<Sl.length;a++)It(Sl[a],n);break;case"source":It("error",n);break;case"img":case"image":case"link":It("error",n),It("load",n);break;case"details":It("toggle",n);break;case"input":It("invalid",n),Ke(n,o.value,o.defaultValue,o.checked,o.defaultChecked,o.type,o.name,!0);break;case"select":It("invalid",n);break;case"textarea":It("invalid",n),ci(n,o.value,o.defaultValue,o.children)}a=o.children,typeof a!="string"&&typeof a!="number"&&typeof a!="bigint"||n.textContent===""+a||o.suppressHydrationWarning===!0||nv(n.textContent,a)?(o.popover!=null&&(It("beforetoggle",n),It("toggle",n)),o.onScroll!=null&&It("scroll",n),o.onScrollEnd!=null&&It("scrollend",n),o.onClick!=null&&(n.onclick=Si),n=!0):n=!1,n||Ur(t,!0)}function Hm(t){for(ai=t.return;ai;)switch(ai.tag){case 5:case 31:case 13:oa=!1;return;case 27:case 3:oa=!0;return;default:ai=ai.return}}function Ys(t){if(t!==ai)return!1;if(!Vt)return Hm(t),Vt=!0,!1;var n=t.tag,a;if((a=n!==3&&n!==27)&&((a=n===5)&&(a=t.type,a=!(a!=="form"&&a!=="button")||zd(t.type,t.memoizedProps)),a=!a),a&&xn&&Ur(t),Hm(t),n===13){if(t=t.memoizedState,t=t!==null?t.dehydrated:null,!t)throw Error(r(317));xn=fv(t)}else if(n===31){if(t=t.memoizedState,t=t!==null?t.dehydrated:null,!t)throw Error(r(317));xn=fv(t)}else n===27?(n=xn,Wr(t.type)?(t=kd,kd=null,xn=t):xn=n):xn=ai?ca(t.stateNode.nextSibling):null;return!0}function ds(){xn=ai=null,Vt=!1}function yf(){var t=Dr;return t!==null&&(Ni===null?Ni=t:Ni.push.apply(Ni,t),Dr=null),t}function Jo(t){Dr===null?Dr=[t]:Dr.push(t)}var Mf=U(null),hs=null,er=null;function Nr(t,n,a){xe(Mf,n._currentValue),n._currentValue=a}function tr(t){t._currentValue=Mf.current,re(Mf)}function bf(t,n,a){for(;t!==null;){var o=t.alternate;if((t.childLanes&n)!==n?(t.childLanes|=n,o!==null&&(o.childLanes|=n)):o!==null&&(o.childLanes&n)!==n&&(o.childLanes|=n),t===a)break;t=t.return}}function Ef(t,n,a,o){var u=t.child;for(u!==null&&(u.return=t);u!==null;){var d=u.dependencies;if(d!==null){var S=u.child;d=d.firstContext;e:for(;d!==null;){var C=d;d=u;for(var G=0;G<n.length;G++)if(C.context===n[G]){d.lanes|=a,C=d.alternate,C!==null&&(C.lanes|=a),bf(d.return,a,t),o||(S=null);break e}d=C.next}}else if(u.tag===18){if(S=u.return,S===null)throw Error(r(341));S.lanes|=a,d=S.alternate,d!==null&&(d.lanes|=a),bf(S,a,t),S=null}else S=u.child;if(S!==null)S.return=u;else for(S=u;S!==null;){if(S===t){S=null;break}if(u=S.sibling,u!==null){u.return=S.return,S=u;break}S=S.return}u=S}}function js(t,n,a,o){t=null;for(var u=n,d=!1;u!==null;){if(!d){if((u.flags&524288)!==0)d=!0;else if((u.flags&262144)!==0)break}if(u.tag===10){var S=u.alternate;if(S===null)throw Error(r(387));if(S=S.memoizedProps,S!==null){var C=u.type;zi(u.pendingProps.value,S.value)||(t!==null?t.push(C):t=[C])}}else if(u===ue.current){if(S=u.alternate,S===null)throw Error(r(387));S.memoizedState.memoizedState!==u.memoizedState.memoizedState&&(t!==null?t.push(Tl):t=[Tl])}u=u.return}t!==null&&Ef(n,t,a,o),n.flags|=262144}function lc(t){for(t=t.firstContext;t!==null;){if(!zi(t.context._currentValue,t.memoizedValue))return!0;t=t.next}return!1}function ps(t){hs=t,er=null,t=t.dependencies,t!==null&&(t.firstContext=null)}function ri(t){return Gm(hs,t)}function cc(t,n){return hs===null&&ps(t),Gm(t,n)}function Gm(t,n){var a=n._currentValue;if(n={context:n,memoizedValue:a,next:null},er===null){if(t===null)throw Error(r(308));er=n,t.dependencies={lanes:0,firstContext:n},t.flags|=524288}else er=er.next=n;return a}var HS=typeof AbortController<"u"?AbortController:function(){var t=[],n=this.signal={aborted:!1,addEventListener:function(a,o){t.push(o)}};this.abort=function(){n.aborted=!0,t.forEach(function(a){return a()})}},GS=s.unstable_scheduleCallback,VS=s.unstable_NormalPriority,Hn={$$typeof:V,Consumer:null,Provider:null,_currentValue:null,_currentValue2:null,_threadCount:0};function Tf(){return{controller:new HS,data:new Map,refCount:0}}function $o(t){t.refCount--,t.refCount===0&&GS(VS,function(){t.controller.abort()})}var el=null,Af=0,Zs=0,Ks=null;function kS(t,n){if(el===null){var a=el=[];Af=0,Zs=wd(),Ks={status:"pending",value:void 0,then:function(o){a.push(o)}}}return Af++,n.then(Vm,Vm),n}function Vm(){if(--Af===0&&el!==null){Ks!==null&&(Ks.status="fulfilled");var t=el;el=null,Zs=0,Ks=null;for(var n=0;n<t.length;n++)(0,t[n])()}}function XS(t,n){var a=[],o={status:"pending",value:null,reason:null,then:function(u){a.push(u)}};return t.then(function(){o.status="fulfilled",o.value=n;for(var u=0;u<a.length;u++)(0,a[u])(n)},function(u){for(o.status="rejected",o.reason=u,u=0;u<a.length;u++)(0,a[u])(void 0)}),o}var km=z.S;z.S=function(t,n){A0=Ft(),typeof n=="object"&&n!==null&&typeof n.then=="function"&&kS(t,n),km!==null&&km(t,n)};var ms=U(null);function Rf(){var t=ms.current;return t!==null?t:vn.pooledCache}function uc(t,n){n===null?xe(ms,ms.current):xe(ms,n.pool)}function Xm(){var t=Rf();return t===null?null:{parent:Hn._currentValue,pool:t}}var Qs=Error(r(460)),Cf=Error(r(474)),fc=Error(r(542)),dc={then:function(){}};function Wm(t){return t=t.status,t==="fulfilled"||t==="rejected"}function qm(t,n,a){switch(a=t[a],a===void 0?t.push(n):a!==n&&(n.then(Si,Si),n=a),n.status){case"fulfilled":return n.value;case"rejected":throw t=n.reason,jm(t),t;default:if(typeof n.status=="string")n.then(Si,Si);else{if(t=vn,t!==null&&100<t.shellSuspendCounter)throw Error(r(482));t=n,t.status="pending",t.then(function(o){if(n.status==="pending"){var u=n;u.status="fulfilled",u.value=o}},function(o){if(n.status==="pending"){var u=n;u.status="rejected",u.reason=o}})}switch(n.status){case"fulfilled":return n.value;case"rejected":throw t=n.reason,jm(t),t}throw vs=n,Qs}}function gs(t){try{var n=t._init;return n(t._payload)}catch(a){throw a!==null&&typeof a=="object"&&typeof a.then=="function"?(vs=a,Qs):a}}var vs=null;function Ym(){if(vs===null)throw Error(r(459));var t=vs;return vs=null,t}function jm(t){if(t===Qs||t===fc)throw Error(r(483))}var Js=null,tl=0;function hc(t){var n=tl;return tl+=1,Js===null&&(Js=[]),qm(Js,t,n)}function nl(t,n){n=n.props.ref,t.ref=n!==void 0?n:null}function pc(t,n){throw n.$$typeof===v?Error(r(525)):(t=Object.prototype.toString.call(n),Error(r(31,t==="[object Object]"?"object with keys {"+Object.keys(n).join(", ")+"}":t)))}function Zm(t){function n($,q){if(t){var de=$.deletions;de===null?($.deletions=[q],$.flags|=16):de.push(q)}}function a($,q){if(!t)return null;for(;q!==null;)n($,q),q=q.sibling;return null}function o($){for(var q=new Map;$!==null;)$.key!==null?q.set($.key,$):q.set($.index,$),$=$.sibling;return q}function u($,q){return $=Ja($,q),$.index=0,$.sibling=null,$}function d($,q,de){return $.index=de,t?(de=$.alternate,de!==null?(de=de.index,de<q?($.flags|=67108866,q):de):($.flags|=67108866,q)):($.flags|=1048576,q)}function S($){return t&&$.alternate===null&&($.flags|=67108866),$}function C($,q,de,Ee){return q===null||q.tag!==6?(q=gf(de,$.mode,Ee),q.return=$,q):(q=u(q,de),q.return=$,q)}function G($,q,de,Ee){var ct=de.type;return ct===D?be($,q,de.props.children,Ee,de.key):q!==null&&(q.elementType===ct||typeof ct=="object"&&ct!==null&&ct.$$typeof===T&&gs(ct)===q.type)?(q=u(q,de.props),nl(q,de),q.return=$,q):(q=sc(de.type,de.key,de.props,null,$.mode,Ee),nl(q,de),q.return=$,q)}function he($,q,de,Ee){return q===null||q.tag!==4||q.stateNode.containerInfo!==de.containerInfo||q.stateNode.implementation!==de.implementation?(q=vf(de,$.mode,Ee),q.return=$,q):(q=u(q,de.children||[]),q.return=$,q)}function be($,q,de,Ee,ct){return q===null||q.tag!==7?(q=fs(de,$.mode,Ee,ct),q.return=$,q):(q=u(q,de),q.return=$,q)}function Te($,q,de){if(typeof q=="string"&&q!==""||typeof q=="number"||typeof q=="bigint")return q=gf(""+q,$.mode,de),q.return=$,q;if(typeof q=="object"&&q!==null){switch(q.$$typeof){case x:return de=sc(q.type,q.key,q.props,null,$.mode,de),nl(de,q),de.return=$,de;case E:return q=vf(q,$.mode,de),q.return=$,q;case T:return q=gs(q),Te($,q,de)}if(j(q)||J(q))return q=fs(q,$.mode,de,null),q.return=$,q;if(typeof q.then=="function")return Te($,hc(q),de);if(q.$$typeof===V)return Te($,cc($,q),de);pc($,q)}return null}function me($,q,de,Ee){var ct=q!==null?q.key:null;if(typeof de=="string"&&de!==""||typeof de=="number"||typeof de=="bigint")return ct!==null?null:C($,q,""+de,Ee);if(typeof de=="object"&&de!==null){switch(de.$$typeof){case x:return de.key===ct?G($,q,de,Ee):null;case E:return de.key===ct?he($,q,de,Ee):null;case T:return de=gs(de),me($,q,de,Ee)}if(j(de)||J(de))return ct!==null?null:be($,q,de,Ee,null);if(typeof de.then=="function")return me($,q,hc(de),Ee);if(de.$$typeof===V)return me($,q,cc($,de),Ee);pc($,de)}return null}function _e($,q,de,Ee,ct){if(typeof Ee=="string"&&Ee!==""||typeof Ee=="number"||typeof Ee=="bigint")return $=$.get(de)||null,C(q,$,""+Ee,ct);if(typeof Ee=="object"&&Ee!==null){switch(Ee.$$typeof){case x:return $=$.get(Ee.key===null?de:Ee.key)||null,G(q,$,Ee,ct);case E:return $=$.get(Ee.key===null?de:Ee.key)||null,he(q,$,Ee,ct);case T:return Ee=gs(Ee),_e($,q,de,Ee,ct)}if(j(Ee)||J(Ee))return $=$.get(de)||null,be(q,$,Ee,ct,null);if(typeof Ee.then=="function")return _e($,q,de,hc(Ee),ct);if(Ee.$$typeof===V)return _e($,q,de,cc(q,Ee),ct);pc(q,Ee)}return null}function tt($,q,de,Ee){for(var ct=null,Jt=null,ot=q,Ct=q=0,Ht=null;ot!==null&&Ct<de.length;Ct++){ot.index>Ct?(Ht=ot,ot=null):Ht=ot.sibling;var $t=me($,ot,de[Ct],Ee);if($t===null){ot===null&&(ot=Ht);break}t&&ot&&$t.alternate===null&&n($,ot),q=d($t,q,Ct),Jt===null?ct=$t:Jt.sibling=$t,Jt=$t,ot=Ht}if(Ct===de.length)return a($,ot),Vt&&$a($,Ct),ct;if(ot===null){for(;Ct<de.length;Ct++)ot=Te($,de[Ct],Ee),ot!==null&&(q=d(ot,q,Ct),Jt===null?ct=ot:Jt.sibling=ot,Jt=ot);return Vt&&$a($,Ct),ct}for(ot=o(ot);Ct<de.length;Ct++)Ht=_e(ot,$,Ct,de[Ct],Ee),Ht!==null&&(t&&Ht.alternate!==null&&ot.delete(Ht.key===null?Ct:Ht.key),q=d(Ht,q,Ct),Jt===null?ct=Ht:Jt.sibling=Ht,Jt=Ht);return t&&ot.forEach(function(Kr){return n($,Kr)}),Vt&&$a($,Ct),ct}function ft($,q,de,Ee){if(de==null)throw Error(r(151));for(var ct=null,Jt=null,ot=q,Ct=q=0,Ht=null,$t=de.next();ot!==null&&!$t.done;Ct++,$t=de.next()){ot.index>Ct?(Ht=ot,ot=null):Ht=ot.sibling;var Kr=me($,ot,$t.value,Ee);if(Kr===null){ot===null&&(ot=Ht);break}t&&ot&&Kr.alternate===null&&n($,ot),q=d(Kr,q,Ct),Jt===null?ct=Kr:Jt.sibling=Kr,Jt=Kr,ot=Ht}if($t.done)return a($,ot),Vt&&$a($,Ct),ct;if(ot===null){for(;!$t.done;Ct++,$t=de.next())$t=Te($,$t.value,Ee),$t!==null&&(q=d($t,q,Ct),Jt===null?ct=$t:Jt.sibling=$t,Jt=$t);return Vt&&$a($,Ct),ct}for(ot=o(ot);!$t.done;Ct++,$t=de.next())$t=_e(ot,$,Ct,$t.value,Ee),$t!==null&&(t&&$t.alternate!==null&&ot.delete($t.key===null?Ct:$t.key),q=d($t,q,Ct),Jt===null?ct=$t:Jt.sibling=$t,Jt=$t);return t&&ot.forEach(function(tM){return n($,tM)}),Vt&&$a($,Ct),ct}function mn($,q,de,Ee){if(typeof de=="object"&&de!==null&&de.type===D&&de.key===null&&(de=de.props.children),typeof de=="object"&&de!==null){switch(de.$$typeof){case x:e:{for(var ct=de.key;q!==null;){if(q.key===ct){if(ct=de.type,ct===D){if(q.tag===7){a($,q.sibling),Ee=u(q,de.props.children),Ee.return=$,$=Ee;break e}}else if(q.elementType===ct||typeof ct=="object"&&ct!==null&&ct.$$typeof===T&&gs(ct)===q.type){a($,q.sibling),Ee=u(q,de.props),nl(Ee,de),Ee.return=$,$=Ee;break e}a($,q);break}else n($,q);q=q.sibling}de.type===D?(Ee=fs(de.props.children,$.mode,Ee,de.key),Ee.return=$,$=Ee):(Ee=sc(de.type,de.key,de.props,null,$.mode,Ee),nl(Ee,de),Ee.return=$,$=Ee)}return S($);case E:e:{for(ct=de.key;q!==null;){if(q.key===ct)if(q.tag===4&&q.stateNode.containerInfo===de.containerInfo&&q.stateNode.implementation===de.implementation){a($,q.sibling),Ee=u(q,de.children||[]),Ee.return=$,$=Ee;break e}else{a($,q);break}else n($,q);q=q.sibling}Ee=vf(de,$.mode,Ee),Ee.return=$,$=Ee}return S($);case T:return de=gs(de),mn($,q,de,Ee)}if(j(de))return tt($,q,de,Ee);if(J(de)){if(ct=J(de),typeof ct!="function")throw Error(r(150));return de=ct.call(de),ft($,q,de,Ee)}if(typeof de.then=="function")return mn($,q,hc(de),Ee);if(de.$$typeof===V)return mn($,q,cc($,de),Ee);pc($,de)}return typeof de=="string"&&de!==""||typeof de=="number"||typeof de=="bigint"?(de=""+de,q!==null&&q.tag===6?(a($,q.sibling),Ee=u(q,de),Ee.return=$,$=Ee):(a($,q),Ee=gf(de,$.mode,Ee),Ee.return=$,$=Ee),S($)):a($,q)}return function($,q,de,Ee){try{tl=0;var ct=mn($,q,de,Ee);return Js=null,ct}catch(ot){if(ot===Qs||ot===fc)throw ot;var Jt=Bi(29,ot,null,$.mode);return Jt.lanes=Ee,Jt.return=$,Jt}finally{}}}var _s=Zm(!0),Km=Zm(!1),Lr=!1;function wf(t){t.updateQueue={baseState:t.memoizedState,firstBaseUpdate:null,lastBaseUpdate:null,shared:{pending:null,lanes:0,hiddenCallbacks:null},callbacks:null}}function Df(t,n){t=t.updateQueue,n.updateQueue===t&&(n.updateQueue={baseState:t.baseState,firstBaseUpdate:t.firstBaseUpdate,lastBaseUpdate:t.lastBaseUpdate,shared:t.shared,callbacks:null})}function Or(t){return{lane:t,tag:0,payload:null,callback:null,next:null}}function Pr(t,n,a){var o=t.updateQueue;if(o===null)return null;if(o=o.shared,(an&2)!==0){var u=o.pending;return u===null?n.next=n:(n.next=u.next,u.next=n),o.pending=n,n=rc(t),Lm(t,null,a),n}return ac(t,o,n,a),rc(t)}function il(t,n,a){if(n=n.updateQueue,n!==null&&(n=n.shared,(a&4194048)!==0)){var o=n.lanes;o&=t.pendingLanes,a|=o,n.lanes=a,ei(t,a)}}function Uf(t,n){var a=t.updateQueue,o=t.alternate;if(o!==null&&(o=o.updateQueue,a===o)){var u=null,d=null;if(a=a.firstBaseUpdate,a!==null){do{var S={lane:a.lane,tag:a.tag,payload:a.payload,callback:null,next:null};d===null?u=d=S:d=d.next=S,a=a.next}while(a!==null);d===null?u=d=n:d=d.next=n}else u=d=n;a={baseState:o.baseState,firstBaseUpdate:u,lastBaseUpdate:d,shared:o.shared,callbacks:o.callbacks},t.updateQueue=a;return}t=a.lastBaseUpdate,t===null?a.firstBaseUpdate=n:t.next=n,a.lastBaseUpdate=n}var Nf=!1;function al(){if(Nf){var t=Ks;if(t!==null)throw t}}function rl(t,n,a,o){Nf=!1;var u=t.updateQueue;Lr=!1;var d=u.firstBaseUpdate,S=u.lastBaseUpdate,C=u.shared.pending;if(C!==null){u.shared.pending=null;var G=C,he=G.next;G.next=null,S===null?d=he:S.next=he,S=G;var be=t.alternate;be!==null&&(be=be.updateQueue,C=be.lastBaseUpdate,C!==S&&(C===null?be.firstBaseUpdate=he:C.next=he,be.lastBaseUpdate=G))}if(d!==null){var Te=u.baseState;S=0,be=he=G=null,C=d;do{var me=C.lane&-536870913,_e=me!==C.lane;if(_e?(Bt&me)===me:(o&me)===me){me!==0&&me===Zs&&(Nf=!0),be!==null&&(be=be.next={lane:0,tag:C.tag,payload:C.payload,callback:null,next:null});e:{var tt=t,ft=C;me=n;var mn=a;switch(ft.tag){case 1:if(tt=ft.payload,typeof tt=="function"){Te=tt.call(mn,Te,me);break e}Te=tt;break e;case 3:tt.flags=tt.flags&-65537|128;case 0:if(tt=ft.payload,me=typeof tt=="function"?tt.call(mn,Te,me):tt,me==null)break e;Te=_({},Te,me);break e;case 2:Lr=!0}}me=C.callback,me!==null&&(t.flags|=64,_e&&(t.flags|=8192),_e=u.callbacks,_e===null?u.callbacks=[me]:_e.push(me))}else _e={lane:me,tag:C.tag,payload:C.payload,callback:C.callback,next:null},be===null?(he=be=_e,G=Te):be=be.next=_e,S|=me;if(C=C.next,C===null){if(C=u.shared.pending,C===null)break;_e=C,C=_e.next,_e.next=null,u.lastBaseUpdate=_e,u.shared.pending=null}}while(!0);be===null&&(G=Te),u.baseState=G,u.firstBaseUpdate=he,u.lastBaseUpdate=be,d===null&&(u.shared.lanes=0),Hr|=S,t.lanes=S,t.memoizedState=Te}}function Qm(t,n){if(typeof t!="function")throw Error(r(191,t));t.call(n)}function Jm(t,n){var a=t.callbacks;if(a!==null)for(t.callbacks=null,t=0;t<a.length;t++)Qm(a[t],n)}var $s=U(null),mc=U(0);function $m(t,n){t=ur,xe(mc,t),xe($s,n),ur=t|n.baseLanes}function Lf(){xe(mc,ur),xe($s,$s.current)}function Of(){ur=mc.current,re($s),re(mc)}var Hi=U(null),la=null;function Ir(t){var n=t.alternate;xe(Pn,Pn.current&1),xe(Hi,t),la===null&&(n===null||$s.current!==null||n.memoizedState!==null)&&(la=t)}function Pf(t){xe(Pn,Pn.current),xe(Hi,t),la===null&&(la=t)}function eg(t){t.tag===22?(xe(Pn,Pn.current),xe(Hi,t),la===null&&(la=t)):Fr()}function Fr(){xe(Pn,Pn.current),xe(Hi,Hi.current)}function Gi(t){re(Hi),la===t&&(la=null),re(Pn)}var Pn=U(0);function gc(t){for(var n=t;n!==null;){if(n.tag===13){var a=n.memoizedState;if(a!==null&&(a=a.dehydrated,a===null||Gd(a)||Vd(a)))return n}else if(n.tag===19&&(n.memoizedProps.revealOrder==="forwards"||n.memoizedProps.revealOrder==="backwards"||n.memoizedProps.revealOrder==="unstable_legacy-backwards"||n.memoizedProps.revealOrder==="together")){if((n.flags&128)!==0)return n}else if(n.child!==null){n.child.return=n,n=n.child;continue}if(n===t)break;for(;n.sibling===null;){if(n.return===null||n.return===t)return null;n=n.return}n.sibling.return=n.return,n=n.sibling}return null}var nr=0,At=null,hn=null,Gn=null,vc=!1,eo=!1,xs=!1,_c=0,sl=0,to=null,WS=0;function Un(){throw Error(r(321))}function If(t,n){if(n===null)return!1;for(var a=0;a<n.length&&a<t.length;a++)if(!zi(t[a],n[a]))return!1;return!0}function Ff(t,n,a,o,u,d){return nr=d,At=n,n.memoizedState=null,n.updateQueue=null,n.lanes=0,z.H=t===null||t.memoizedState===null?Fg:Jf,xs=!1,d=a(o,u),xs=!1,eo&&(d=ng(n,a,o,u)),tg(t),d}function tg(t){z.H=cl;var n=hn!==null&&hn.next!==null;if(nr=0,Gn=hn=At=null,vc=!1,sl=0,to=null,n)throw Error(r(300));t===null||Vn||(t=t.dependencies,t!==null&&lc(t)&&(Vn=!0))}function ng(t,n,a,o){At=t;var u=0;do{if(eo&&(to=null),sl=0,eo=!1,25<=u)throw Error(r(301));if(u+=1,Gn=hn=null,t.updateQueue!=null){var d=t.updateQueue;d.lastEffect=null,d.events=null,d.stores=null,d.memoCache!=null&&(d.memoCache.index=0)}z.H=zg,d=n(a,o)}while(eo);return d}function qS(){var t=z.H,n=t.useState()[0];return n=typeof n.then=="function"?ol(n):n,t=t.useState()[0],(hn!==null?hn.memoizedState:null)!==t&&(At.flags|=1024),n}function zf(){var t=_c!==0;return _c=0,t}function Bf(t,n,a){n.updateQueue=t.updateQueue,n.flags&=-2053,t.lanes&=~a}function Hf(t){if(vc){for(t=t.memoizedState;t!==null;){var n=t.queue;n!==null&&(n.pending=null),t=t.next}vc=!1}nr=0,Gn=hn=At=null,eo=!1,sl=_c=0,to=null}function yi(){var t={memoizedState:null,baseState:null,baseQueue:null,queue:null,next:null};return Gn===null?At.memoizedState=Gn=t:Gn=Gn.next=t,Gn}function In(){if(hn===null){var t=At.alternate;t=t!==null?t.memoizedState:null}else t=hn.next;var n=Gn===null?At.memoizedState:Gn.next;if(n!==null)Gn=n,hn=t;else{if(t===null)throw At.alternate===null?Error(r(467)):Error(r(310));hn=t,t={memoizedState:hn.memoizedState,baseState:hn.baseState,baseQueue:hn.baseQueue,queue:hn.queue,next:null},Gn===null?At.memoizedState=Gn=t:Gn=Gn.next=t}return Gn}function xc(){return{lastEffect:null,events:null,stores:null,memoCache:null}}function ol(t){var n=sl;return sl+=1,to===null&&(to=[]),t=qm(to,t,n),n=At,(Gn===null?n.memoizedState:Gn.next)===null&&(n=n.alternate,z.H=n===null||n.memoizedState===null?Fg:Jf),t}function Sc(t){if(t!==null&&typeof t=="object"){if(typeof t.then=="function")return ol(t);if(t.$$typeof===V)return ri(t)}throw Error(r(438,String(t)))}function Gf(t){var n=null,a=At.updateQueue;if(a!==null&&(n=a.memoCache),n==null){var o=At.alternate;o!==null&&(o=o.updateQueue,o!==null&&(o=o.memoCache,o!=null&&(n={data:o.data.map(function(u){return u.slice()}),index:0})))}if(n==null&&(n={data:[],index:0}),a===null&&(a=xc(),At.updateQueue=a),a.memoCache=n,a=n.data[n.index],a===void 0)for(a=n.data[n.index]=Array(t),o=0;o<t;o++)a[o]=B;return n.index++,a}function ir(t,n){return typeof n=="function"?n(t):n}function yc(t){var n=In();return Vf(n,hn,t)}function Vf(t,n,a){var o=t.queue;if(o===null)throw Error(r(311));o.lastRenderedReducer=a;var u=t.baseQueue,d=o.pending;if(d!==null){if(u!==null){var S=u.next;u.next=d.next,d.next=S}n.baseQueue=u=d,o.pending=null}if(d=t.baseState,u===null)t.memoizedState=d;else{n=u.next;var C=S=null,G=null,he=n,be=!1;do{var Te=he.lane&-536870913;if(Te!==he.lane?(Bt&Te)===Te:(nr&Te)===Te){var me=he.revertLane;if(me===0)G!==null&&(G=G.next={lane:0,revertLane:0,gesture:null,action:he.action,hasEagerState:he.hasEagerState,eagerState:he.eagerState,next:null}),Te===Zs&&(be=!0);else if((nr&me)===me){he=he.next,me===Zs&&(be=!0);continue}else Te={lane:0,revertLane:he.revertLane,gesture:null,action:he.action,hasEagerState:he.hasEagerState,eagerState:he.eagerState,next:null},G===null?(C=G=Te,S=d):G=G.next=Te,At.lanes|=me,Hr|=me;Te=he.action,xs&&a(d,Te),d=he.hasEagerState?he.eagerState:a(d,Te)}else me={lane:Te,revertLane:he.revertLane,gesture:he.gesture,action:he.action,hasEagerState:he.hasEagerState,eagerState:he.eagerState,next:null},G===null?(C=G=me,S=d):G=G.next=me,At.lanes|=Te,Hr|=Te;he=he.next}while(he!==null&&he!==n);if(G===null?S=d:G.next=C,!zi(d,t.memoizedState)&&(Vn=!0,be&&(a=Ks,a!==null)))throw a;t.memoizedState=d,t.baseState=S,t.baseQueue=G,o.lastRenderedState=d}return u===null&&(o.lanes=0),[t.memoizedState,o.dispatch]}function kf(t){var n=In(),a=n.queue;if(a===null)throw Error(r(311));a.lastRenderedReducer=t;var o=a.dispatch,u=a.pending,d=n.memoizedState;if(u!==null){a.pending=null;var S=u=u.next;do d=t(d,S.action),S=S.next;while(S!==u);zi(d,n.memoizedState)||(Vn=!0),n.memoizedState=d,n.baseQueue===null&&(n.baseState=d),a.lastRenderedState=d}return[d,o]}function ig(t,n,a){var o=At,u=In(),d=Vt;if(d){if(a===void 0)throw Error(r(407));a=a()}else a=n();var S=!zi((hn||u).memoizedState,a);if(S&&(u.memoizedState=a,Vn=!0),u=u.queue,qf(sg.bind(null,o,u,t),[t]),u.getSnapshot!==n||S||Gn!==null&&Gn.memoizedState.tag&1){if(o.flags|=2048,no(9,{destroy:void 0},rg.bind(null,o,u,a,n),null),vn===null)throw Error(r(349));d||(nr&127)!==0||ag(o,n,a)}return a}function ag(t,n,a){t.flags|=16384,t={getSnapshot:n,value:a},n=At.updateQueue,n===null?(n=xc(),At.updateQueue=n,n.stores=[t]):(a=n.stores,a===null?n.stores=[t]:a.push(t))}function rg(t,n,a,o){n.value=a,n.getSnapshot=o,og(n)&&lg(t)}function sg(t,n,a){return a(function(){og(n)&&lg(t)})}function og(t){var n=t.getSnapshot;t=t.value;try{var a=n();return!zi(t,a)}catch{return!0}}function lg(t){var n=us(t,2);n!==null&&Li(n,t,2)}function Xf(t){var n=yi();if(typeof t=="function"){var a=t;if(t=a(),xs){Ne(!0);try{a()}finally{Ne(!1)}}}return n.memoizedState=n.baseState=t,n.queue={pending:null,lanes:0,dispatch:null,lastRenderedReducer:ir,lastRenderedState:t},n}function cg(t,n,a,o){return t.baseState=a,Vf(t,hn,typeof o=="function"?o:ir)}function YS(t,n,a,o,u){if(Ec(t))throw Error(r(485));if(t=n.action,t!==null){var d={payload:u,action:t,next:null,isTransition:!0,status:"pending",value:null,reason:null,listeners:[],then:function(S){d.listeners.push(S)}};z.T!==null?a(!0):d.isTransition=!1,o(d),a=n.pending,a===null?(d.next=n.pending=d,ug(n,d)):(d.next=a.next,n.pending=a.next=d)}}function ug(t,n){var a=n.action,o=n.payload,u=t.state;if(n.isTransition){var d=z.T,S={};z.T=S;try{var C=a(u,o),G=z.S;G!==null&&G(S,C),fg(t,n,C)}catch(he){Wf(t,n,he)}finally{d!==null&&S.types!==null&&(d.types=S.types),z.T=d}}else try{d=a(u,o),fg(t,n,d)}catch(he){Wf(t,n,he)}}function fg(t,n,a){a!==null&&typeof a=="object"&&typeof a.then=="function"?a.then(function(o){dg(t,n,o)},function(o){return Wf(t,n,o)}):dg(t,n,a)}function dg(t,n,a){n.status="fulfilled",n.value=a,hg(n),t.state=a,n=t.pending,n!==null&&(a=n.next,a===n?t.pending=null:(a=a.next,n.next=a,ug(t,a)))}function Wf(t,n,a){var o=t.pending;if(t.pending=null,o!==null){o=o.next;do n.status="rejected",n.reason=a,hg(n),n=n.next;while(n!==o)}t.action=null}function hg(t){t=t.listeners;for(var n=0;n<t.length;n++)(0,t[n])()}function pg(t,n){return n}function mg(t,n){if(Vt){var a=vn.formState;if(a!==null){e:{var o=At;if(Vt){if(xn){t:{for(var u=xn,d=oa;u.nodeType!==8;){if(!d){u=null;break t}if(u=ca(u.nextSibling),u===null){u=null;break t}}d=u.data,u=d==="F!"||d==="F"?u:null}if(u){xn=ca(u.nextSibling),o=u.data==="F!";break e}}Ur(o)}o=!1}o&&(n=a[0])}}return a=yi(),a.memoizedState=a.baseState=n,o={pending:null,lanes:0,dispatch:null,lastRenderedReducer:pg,lastRenderedState:n},a.queue=o,a=Og.bind(null,At,o),o.dispatch=a,o=Xf(!1),d=Qf.bind(null,At,!1,o.queue),o=yi(),u={state:n,dispatch:null,action:t,pending:null},o.queue=u,a=YS.bind(null,At,u,d,a),u.dispatch=a,o.memoizedState=t,[n,a,!1]}function gg(t){var n=In();return vg(n,hn,t)}function vg(t,n,a){if(n=Vf(t,n,pg)[0],t=yc(ir)[0],typeof n=="object"&&n!==null&&typeof n.then=="function")try{var o=ol(n)}catch(S){throw S===Qs?fc:S}else o=n;n=In();var u=n.queue,d=u.dispatch;return a!==n.memoizedState&&(At.flags|=2048,no(9,{destroy:void 0},jS.bind(null,u,a),null)),[o,d,t]}function jS(t,n){t.action=n}function _g(t){var n=In(),a=hn;if(a!==null)return vg(n,a,t);In(),n=n.memoizedState,a=In();var o=a.queue.dispatch;return a.memoizedState=t,[n,o,!1]}function no(t,n,a,o){return t={tag:t,create:a,deps:o,inst:n,next:null},n=At.updateQueue,n===null&&(n=xc(),At.updateQueue=n),a=n.lastEffect,a===null?n.lastEffect=t.next=t:(o=a.next,a.next=t,t.next=o,n.lastEffect=t),t}function xg(){return In().memoizedState}function Mc(t,n,a,o){var u=yi();At.flags|=t,u.memoizedState=no(1|n,{destroy:void 0},a,o===void 0?null:o)}function bc(t,n,a,o){var u=In();o=o===void 0?null:o;var d=u.memoizedState.inst;hn!==null&&o!==null&&If(o,hn.memoizedState.deps)?u.memoizedState=no(n,d,a,o):(At.flags|=t,u.memoizedState=no(1|n,d,a,o))}function Sg(t,n){Mc(8390656,8,t,n)}function qf(t,n){bc(2048,8,t,n)}function ZS(t){At.flags|=4;var n=At.updateQueue;if(n===null)n=xc(),At.updateQueue=n,n.events=[t];else{var a=n.events;a===null?n.events=[t]:a.push(t)}}function yg(t){var n=In().memoizedState;return ZS({ref:n,nextImpl:t}),function(){if((an&2)!==0)throw Error(r(440));return n.impl.apply(void 0,arguments)}}function Mg(t,n){return bc(4,2,t,n)}function bg(t,n){return bc(4,4,t,n)}function Eg(t,n){if(typeof n=="function"){t=t();var a=n(t);return function(){typeof a=="function"?a():n(null)}}if(n!=null)return t=t(),n.current=t,function(){n.current=null}}function Tg(t,n,a){a=a!=null?a.concat([t]):null,bc(4,4,Eg.bind(null,n,t),a)}function Yf(){}function Ag(t,n){var a=In();n=n===void 0?null:n;var o=a.memoizedState;return n!==null&&If(n,o[1])?o[0]:(a.memoizedState=[t,n],t)}function Rg(t,n){var a=In();n=n===void 0?null:n;var o=a.memoizedState;if(n!==null&&If(n,o[1]))return o[0];if(o=t(),xs){Ne(!0);try{t()}finally{Ne(!1)}}return a.memoizedState=[o,n],o}function jf(t,n,a){return a===void 0||(nr&1073741824)!==0&&(Bt&261930)===0?t.memoizedState=n:(t.memoizedState=a,t=C0(),At.lanes|=t,Hr|=t,a)}function Cg(t,n,a,o){return zi(a,n)?a:$s.current!==null?(t=jf(t,a,o),zi(t,n)||(Vn=!0),t):(nr&42)===0||(nr&1073741824)!==0&&(Bt&261930)===0?(Vn=!0,t.memoizedState=a):(t=C0(),At.lanes|=t,Hr|=t,n)}function wg(t,n,a,o,u){var d=H.p;H.p=d!==0&&8>d?d:8;var S=z.T,C={};z.T=C,Qf(t,!1,n,a);try{var G=u(),he=z.S;if(he!==null&&he(C,G),G!==null&&typeof G=="object"&&typeof G.then=="function"){var be=XS(G,o);ll(t,n,be,Xi(t))}else ll(t,n,o,Xi(t))}catch(Te){ll(t,n,{then:function(){},status:"rejected",reason:Te},Xi())}finally{H.p=d,S!==null&&C.types!==null&&(S.types=C.types),z.T=S}}function KS(){}function Zf(t,n,a,o){if(t.tag!==5)throw Error(r(476));var u=Dg(t).queue;wg(t,u,n,ee,a===null?KS:function(){return Ug(t),a(o)})}function Dg(t){var n=t.memoizedState;if(n!==null)return n;n={memoizedState:ee,baseState:ee,baseQueue:null,queue:{pending:null,lanes:0,dispatch:null,lastRenderedReducer:ir,lastRenderedState:ee},next:null};var a={};return n.next={memoizedState:a,baseState:a,baseQueue:null,queue:{pending:null,lanes:0,dispatch:null,lastRenderedReducer:ir,lastRenderedState:a},next:null},t.memoizedState=n,t=t.alternate,t!==null&&(t.memoizedState=n),n}function Ug(t){var n=Dg(t);n.next===null&&(n=t.alternate.memoizedState),ll(t,n.next.queue,{},Xi())}function Kf(){return ri(Tl)}function Ng(){return In().memoizedState}function Lg(){return In().memoizedState}function QS(t){for(var n=t.return;n!==null;){switch(n.tag){case 24:case 3:var a=Xi();t=Or(a);var o=Pr(n,t,a);o!==null&&(Li(o,n,a),il(o,n,a)),n={cache:Tf()},t.payload=n;return}n=n.return}}function JS(t,n,a){var o=Xi();a={lane:o,revertLane:0,gesture:null,action:a,hasEagerState:!1,eagerState:null,next:null},Ec(t)?Pg(n,a):(a=pf(t,n,a,o),a!==null&&(Li(a,t,o),Ig(a,n,o)))}function Og(t,n,a){var o=Xi();ll(t,n,a,o)}function ll(t,n,a,o){var u={lane:o,revertLane:0,gesture:null,action:a,hasEagerState:!1,eagerState:null,next:null};if(Ec(t))Pg(n,u);else{var d=t.alternate;if(t.lanes===0&&(d===null||d.lanes===0)&&(d=n.lastRenderedReducer,d!==null))try{var S=n.lastRenderedState,C=d(S,a);if(u.hasEagerState=!0,u.eagerState=C,zi(C,S))return ac(t,n,u,0),vn===null&&ic(),!1}catch{}finally{}if(a=pf(t,n,u,o),a!==null)return Li(a,t,o),Ig(a,n,o),!0}return!1}function Qf(t,n,a,o){if(o={lane:2,revertLane:wd(),gesture:null,action:o,hasEagerState:!1,eagerState:null,next:null},Ec(t)){if(n)throw Error(r(479))}else n=pf(t,a,o,2),n!==null&&Li(n,t,2)}function Ec(t){var n=t.alternate;return t===At||n!==null&&n===At}function Pg(t,n){eo=vc=!0;var a=t.pending;a===null?n.next=n:(n.next=a.next,a.next=n),t.pending=n}function Ig(t,n,a){if((a&4194048)!==0){var o=n.lanes;o&=t.pendingLanes,a|=o,n.lanes=a,ei(t,a)}}var cl={readContext:ri,use:Sc,useCallback:Un,useContext:Un,useEffect:Un,useImperativeHandle:Un,useLayoutEffect:Un,useInsertionEffect:Un,useMemo:Un,useReducer:Un,useRef:Un,useState:Un,useDebugValue:Un,useDeferredValue:Un,useTransition:Un,useSyncExternalStore:Un,useId:Un,useHostTransitionStatus:Un,useFormState:Un,useActionState:Un,useOptimistic:Un,useMemoCache:Un,useCacheRefresh:Un};cl.useEffectEvent=Un;var Fg={readContext:ri,use:Sc,useCallback:function(t,n){return yi().memoizedState=[t,n===void 0?null:n],t},useContext:ri,useEffect:Sg,useImperativeHandle:function(t,n,a){a=a!=null?a.concat([t]):null,Mc(4194308,4,Eg.bind(null,n,t),a)},useLayoutEffect:function(t,n){return Mc(4194308,4,t,n)},useInsertionEffect:function(t,n){Mc(4,2,t,n)},useMemo:function(t,n){var a=yi();n=n===void 0?null:n;var o=t();if(xs){Ne(!0);try{t()}finally{Ne(!1)}}return a.memoizedState=[o,n],o},useReducer:function(t,n,a){var o=yi();if(a!==void 0){var u=a(n);if(xs){Ne(!0);try{a(n)}finally{Ne(!1)}}}else u=n;return o.memoizedState=o.baseState=u,t={pending:null,lanes:0,dispatch:null,lastRenderedReducer:t,lastRenderedState:u},o.queue=t,t=t.dispatch=JS.bind(null,At,t),[o.memoizedState,t]},useRef:function(t){var n=yi();return t={current:t},n.memoizedState=t},useState:function(t){t=Xf(t);var n=t.queue,a=Og.bind(null,At,n);return n.dispatch=a,[t.memoizedState,a]},useDebugValue:Yf,useDeferredValue:function(t,n){var a=yi();return jf(a,t,n)},useTransition:function(){var t=Xf(!1);return t=wg.bind(null,At,t.queue,!0,!1),yi().memoizedState=t,[!1,t]},useSyncExternalStore:function(t,n,a){var o=At,u=yi();if(Vt){if(a===void 0)throw Error(r(407));a=a()}else{if(a=n(),vn===null)throw Error(r(349));(Bt&127)!==0||ag(o,n,a)}u.memoizedState=a;var d={value:a,getSnapshot:n};return u.queue=d,Sg(sg.bind(null,o,d,t),[t]),o.flags|=2048,no(9,{destroy:void 0},rg.bind(null,o,d,a,n),null),a},useId:function(){var t=yi(),n=vn.identifierPrefix;if(Vt){var a=Ia,o=Pa;a=(o&~(1<<32-Ze(o)-1)).toString(32)+a,n="_"+n+"R_"+a,a=_c++,0<a&&(n+="H"+a.toString(32)),n+="_"}else a=WS++,n="_"+n+"r_"+a.toString(32)+"_";return t.memoizedState=n},useHostTransitionStatus:Kf,useFormState:mg,useActionState:mg,useOptimistic:function(t){var n=yi();n.memoizedState=n.baseState=t;var a={pending:null,lanes:0,dispatch:null,lastRenderedReducer:null,lastRenderedState:null};return n.queue=a,n=Qf.bind(null,At,!0,a),a.dispatch=n,[t,n]},useMemoCache:Gf,useCacheRefresh:function(){return yi().memoizedState=QS.bind(null,At)},useEffectEvent:function(t){var n=yi(),a={impl:t};return n.memoizedState=a,function(){if((an&2)!==0)throw Error(r(440));return a.impl.apply(void 0,arguments)}}},Jf={readContext:ri,use:Sc,useCallback:Ag,useContext:ri,useEffect:qf,useImperativeHandle:Tg,useInsertionEffect:Mg,useLayoutEffect:bg,useMemo:Rg,useReducer:yc,useRef:xg,useState:function(){return yc(ir)},useDebugValue:Yf,useDeferredValue:function(t,n){var a=In();return Cg(a,hn.memoizedState,t,n)},useTransition:function(){var t=yc(ir)[0],n=In().memoizedState;return[typeof t=="boolean"?t:ol(t),n]},useSyncExternalStore:ig,useId:Ng,useHostTransitionStatus:Kf,useFormState:gg,useActionState:gg,useOptimistic:function(t,n){var a=In();return cg(a,hn,t,n)},useMemoCache:Gf,useCacheRefresh:Lg};Jf.useEffectEvent=yg;var zg={readContext:ri,use:Sc,useCallback:Ag,useContext:ri,useEffect:qf,useImperativeHandle:Tg,useInsertionEffect:Mg,useLayoutEffect:bg,useMemo:Rg,useReducer:kf,useRef:xg,useState:function(){return kf(ir)},useDebugValue:Yf,useDeferredValue:function(t,n){var a=In();return hn===null?jf(a,t,n):Cg(a,hn.memoizedState,t,n)},useTransition:function(){var t=kf(ir)[0],n=In().memoizedState;return[typeof t=="boolean"?t:ol(t),n]},useSyncExternalStore:ig,useId:Ng,useHostTransitionStatus:Kf,useFormState:_g,useActionState:_g,useOptimistic:function(t,n){var a=In();return hn!==null?cg(a,hn,t,n):(a.baseState=t,[t,a.queue.dispatch])},useMemoCache:Gf,useCacheRefresh:Lg};zg.useEffectEvent=yg;function $f(t,n,a,o){n=t.memoizedState,a=a(o,n),a=a==null?n:_({},n,a),t.memoizedState=a,t.lanes===0&&(t.updateQueue.baseState=a)}var ed={enqueueSetState:function(t,n,a){t=t._reactInternals;var o=Xi(),u=Or(o);u.payload=n,a!=null&&(u.callback=a),n=Pr(t,u,o),n!==null&&(Li(n,t,o),il(n,t,o))},enqueueReplaceState:function(t,n,a){t=t._reactInternals;var o=Xi(),u=Or(o);u.tag=1,u.payload=n,a!=null&&(u.callback=a),n=Pr(t,u,o),n!==null&&(Li(n,t,o),il(n,t,o))},enqueueForceUpdate:function(t,n){t=t._reactInternals;var a=Xi(),o=Or(a);o.tag=2,n!=null&&(o.callback=n),n=Pr(t,o,a),n!==null&&(Li(n,t,a),il(n,t,a))}};function Bg(t,n,a,o,u,d,S){return t=t.stateNode,typeof t.shouldComponentUpdate=="function"?t.shouldComponentUpdate(o,d,S):n.prototype&&n.prototype.isPureReactComponent?!Zo(a,o)||!Zo(u,d):!0}function Hg(t,n,a,o){t=n.state,typeof n.componentWillReceiveProps=="function"&&n.componentWillReceiveProps(a,o),typeof n.UNSAFE_componentWillReceiveProps=="function"&&n.UNSAFE_componentWillReceiveProps(a,o),n.state!==t&&ed.enqueueReplaceState(n,n.state,null)}function Ss(t,n){var a=n;if("ref"in n){a={};for(var o in n)o!=="ref"&&(a[o]=n[o])}if(t=t.defaultProps){a===n&&(a=_({},a));for(var u in t)a[u]===void 0&&(a[u]=t[u])}return a}function Gg(t){nc(t)}function Vg(t){console.error(t)}function kg(t){nc(t)}function Tc(t,n){try{var a=t.onUncaughtError;a(n.value,{componentStack:n.stack})}catch(o){setTimeout(function(){throw o})}}function Xg(t,n,a){try{var o=t.onCaughtError;o(a.value,{componentStack:a.stack,errorBoundary:n.tag===1?n.stateNode:null})}catch(u){setTimeout(function(){throw u})}}function td(t,n,a){return a=Or(a),a.tag=3,a.payload={element:null},a.callback=function(){Tc(t,n)},a}function Wg(t){return t=Or(t),t.tag=3,t}function qg(t,n,a,o){var u=a.type.getDerivedStateFromError;if(typeof u=="function"){var d=o.value;t.payload=function(){return u(d)},t.callback=function(){Xg(n,a,o)}}var S=a.stateNode;S!==null&&typeof S.componentDidCatch=="function"&&(t.callback=function(){Xg(n,a,o),typeof u!="function"&&(Gr===null?Gr=new Set([this]):Gr.add(this));var C=o.stack;this.componentDidCatch(o.value,{componentStack:C!==null?C:""})})}function $S(t,n,a,o,u){if(a.flags|=32768,o!==null&&typeof o=="object"&&typeof o.then=="function"){if(n=a.alternate,n!==null&&js(n,a,u,!0),a=Hi.current,a!==null){switch(a.tag){case 31:case 13:return la===null?Fc():a.alternate===null&&Nn===0&&(Nn=3),a.flags&=-257,a.flags|=65536,a.lanes=u,o===dc?a.flags|=16384:(n=a.updateQueue,n===null?a.updateQueue=new Set([o]):n.add(o),Ad(t,o,u)),!1;case 22:return a.flags|=65536,o===dc?a.flags|=16384:(n=a.updateQueue,n===null?(n={transitions:null,markerInstances:null,retryQueue:new Set([o])},a.updateQueue=n):(a=n.retryQueue,a===null?n.retryQueue=new Set([o]):a.add(o)),Ad(t,o,u)),!1}throw Error(r(435,a.tag))}return Ad(t,o,u),Fc(),!1}if(Vt)return n=Hi.current,n!==null?((n.flags&65536)===0&&(n.flags|=256),n.flags|=65536,n.lanes=u,o!==Sf&&(t=Error(r(422),{cause:o}),Jo(aa(t,a)))):(o!==Sf&&(n=Error(r(423),{cause:o}),Jo(aa(n,a))),t=t.current.alternate,t.flags|=65536,u&=-u,t.lanes|=u,o=aa(o,a),u=td(t.stateNode,o,u),Uf(t,u),Nn!==4&&(Nn=2)),!1;var d=Error(r(520),{cause:o});if(d=aa(d,a),vl===null?vl=[d]:vl.push(d),Nn!==4&&(Nn=2),n===null)return!0;o=aa(o,a),a=n;do{switch(a.tag){case 3:return a.flags|=65536,t=u&-u,a.lanes|=t,t=td(a.stateNode,o,t),Uf(a,t),!1;case 1:if(n=a.type,d=a.stateNode,(a.flags&128)===0&&(typeof n.getDerivedStateFromError=="function"||d!==null&&typeof d.componentDidCatch=="function"&&(Gr===null||!Gr.has(d))))return a.flags|=65536,u&=-u,a.lanes|=u,u=Wg(u),qg(u,t,a,o),Uf(a,u),!1}a=a.return}while(a!==null);return!1}var nd=Error(r(461)),Vn=!1;function si(t,n,a,o){n.child=t===null?Km(n,null,a,o):_s(n,t.child,a,o)}function Yg(t,n,a,o,u){a=a.render;var d=n.ref;if("ref"in o){var S={};for(var C in o)C!=="ref"&&(S[C]=o[C])}else S=o;return ps(n),o=Ff(t,n,a,S,d,u),C=zf(),t!==null&&!Vn?(Bf(t,n,u),ar(t,n,u)):(Vt&&C&&_f(n),n.flags|=1,si(t,n,o,u),n.child)}function jg(t,n,a,o,u){if(t===null){var d=a.type;return typeof d=="function"&&!mf(d)&&d.defaultProps===void 0&&a.compare===null?(n.tag=15,n.type=d,Zg(t,n,d,o,u)):(t=sc(a.type,null,o,n,n.mode,u),t.ref=n.ref,t.return=n,n.child=t)}if(d=t.child,!ud(t,u)){var S=d.memoizedProps;if(a=a.compare,a=a!==null?a:Zo,a(S,o)&&t.ref===n.ref)return ar(t,n,u)}return n.flags|=1,t=Ja(d,o),t.ref=n.ref,t.return=n,n.child=t}function Zg(t,n,a,o,u){if(t!==null){var d=t.memoizedProps;if(Zo(d,o)&&t.ref===n.ref)if(Vn=!1,n.pendingProps=o=d,ud(t,u))(t.flags&131072)!==0&&(Vn=!0);else return n.lanes=t.lanes,ar(t,n,u)}return id(t,n,a,o,u)}function Kg(t,n,a,o){var u=o.children,d=t!==null?t.memoizedState:null;if(t===null&&n.stateNode===null&&(n.stateNode={_visibility:1,_pendingMarkers:null,_retryCache:null,_transitions:null}),o.mode==="hidden"){if((n.flags&128)!==0){if(d=d!==null?d.baseLanes|a:a,t!==null){for(o=n.child=t.child,u=0;o!==null;)u=u|o.lanes|o.childLanes,o=o.sibling;o=u&~d}else o=0,n.child=null;return Qg(t,n,d,a,o)}if((a&536870912)!==0)n.memoizedState={baseLanes:0,cachePool:null},t!==null&&uc(n,d!==null?d.cachePool:null),d!==null?$m(n,d):Lf(),eg(n);else return o=n.lanes=536870912,Qg(t,n,d!==null?d.baseLanes|a:a,a,o)}else d!==null?(uc(n,d.cachePool),$m(n,d),Fr(),n.memoizedState=null):(t!==null&&uc(n,null),Lf(),Fr());return si(t,n,u,a),n.child}function ul(t,n){return t!==null&&t.tag===22||n.stateNode!==null||(n.stateNode={_visibility:1,_pendingMarkers:null,_retryCache:null,_transitions:null}),n.sibling}function Qg(t,n,a,o,u){var d=Rf();return d=d===null?null:{parent:Hn._currentValue,pool:d},n.memoizedState={baseLanes:a,cachePool:d},t!==null&&uc(n,null),Lf(),eg(n),t!==null&&js(t,n,o,!0),n.childLanes=u,null}function Ac(t,n){return n=Cc({mode:n.mode,children:n.children},t.mode),n.ref=t.ref,t.child=n,n.return=t,n}function Jg(t,n,a){return _s(n,t.child,null,a),t=Ac(n,n.pendingProps),t.flags|=2,Gi(n),n.memoizedState=null,t}function ey(t,n,a){var o=n.pendingProps,u=(n.flags&128)!==0;if(n.flags&=-129,t===null){if(Vt){if(o.mode==="hidden")return t=Ac(n,o),n.lanes=536870912,ul(null,t);if(Pf(n),(t=xn)?(t=uv(t,oa),t=t!==null&&t.data==="&"?t:null,t!==null&&(n.memoizedState={dehydrated:t,treeContext:wr!==null?{id:Pa,overflow:Ia}:null,retryLane:536870912,hydrationErrors:null},a=Pm(t),a.return=n,n.child=a,ai=n,xn=null)):t=null,t===null)throw Ur(n);return n.lanes=536870912,null}return Ac(n,o)}var d=t.memoizedState;if(d!==null){var S=d.dehydrated;if(Pf(n),u)if(n.flags&256)n.flags&=-257,n=Jg(t,n,a);else if(n.memoizedState!==null)n.child=t.child,n.flags|=128,n=null;else throw Error(r(558));else if(Vn||js(t,n,a,!1),u=(a&t.childLanes)!==0,Vn||u){if(o=vn,o!==null&&(S=ti(o,a),S!==0&&S!==d.retryLane))throw d.retryLane=S,us(t,S),Li(o,t,S),nd;Fc(),n=Jg(t,n,a)}else t=d.treeContext,xn=ca(S.nextSibling),ai=n,Vt=!0,Dr=null,oa=!1,t!==null&&zm(n,t),n=Ac(n,o),n.flags|=4096;return n}return t=Ja(t.child,{mode:o.mode,children:o.children}),t.ref=n.ref,n.child=t,t.return=n,t}function Rc(t,n){var a=n.ref;if(a===null)t!==null&&t.ref!==null&&(n.flags|=4194816);else{if(typeof a!="function"&&typeof a!="object")throw Error(r(284));(t===null||t.ref!==a)&&(n.flags|=4194816)}}function id(t,n,a,o,u){return ps(n),a=Ff(t,n,a,o,void 0,u),o=zf(),t!==null&&!Vn?(Bf(t,n,u),ar(t,n,u)):(Vt&&o&&_f(n),n.flags|=1,si(t,n,a,u),n.child)}function $g(t,n,a,o,u,d){return ps(n),n.updateQueue=null,a=ng(n,o,a,u),tg(t),o=zf(),t!==null&&!Vn?(Bf(t,n,d),ar(t,n,d)):(Vt&&o&&_f(n),n.flags|=1,si(t,n,a,d),n.child)}function e0(t,n,a,o,u){if(ps(n),n.stateNode===null){var d=Xs,S=a.contextType;typeof S=="object"&&S!==null&&(d=ri(S)),d=new a(o,d),n.memoizedState=d.state!==null&&d.state!==void 0?d.state:null,d.updater=ed,n.stateNode=d,d._reactInternals=n,d=n.stateNode,d.props=o,d.state=n.memoizedState,d.refs={},wf(n),S=a.contextType,d.context=typeof S=="object"&&S!==null?ri(S):Xs,d.state=n.memoizedState,S=a.getDerivedStateFromProps,typeof S=="function"&&($f(n,a,S,o),d.state=n.memoizedState),typeof a.getDerivedStateFromProps=="function"||typeof d.getSnapshotBeforeUpdate=="function"||typeof d.UNSAFE_componentWillMount!="function"&&typeof d.componentWillMount!="function"||(S=d.state,typeof d.componentWillMount=="function"&&d.componentWillMount(),typeof d.UNSAFE_componentWillMount=="function"&&d.UNSAFE_componentWillMount(),S!==d.state&&ed.enqueueReplaceState(d,d.state,null),rl(n,o,d,u),al(),d.state=n.memoizedState),typeof d.componentDidMount=="function"&&(n.flags|=4194308),o=!0}else if(t===null){d=n.stateNode;var C=n.memoizedProps,G=Ss(a,C);d.props=G;var he=d.context,be=a.contextType;S=Xs,typeof be=="object"&&be!==null&&(S=ri(be));var Te=a.getDerivedStateFromProps;be=typeof Te=="function"||typeof d.getSnapshotBeforeUpdate=="function",C=n.pendingProps!==C,be||typeof d.UNSAFE_componentWillReceiveProps!="function"&&typeof d.componentWillReceiveProps!="function"||(C||he!==S)&&Hg(n,d,o,S),Lr=!1;var me=n.memoizedState;d.state=me,rl(n,o,d,u),al(),he=n.memoizedState,C||me!==he||Lr?(typeof Te=="function"&&($f(n,a,Te,o),he=n.memoizedState),(G=Lr||Bg(n,a,G,o,me,he,S))?(be||typeof d.UNSAFE_componentWillMount!="function"&&typeof d.componentWillMount!="function"||(typeof d.componentWillMount=="function"&&d.componentWillMount(),typeof d.UNSAFE_componentWillMount=="function"&&d.UNSAFE_componentWillMount()),typeof d.componentDidMount=="function"&&(n.flags|=4194308)):(typeof d.componentDidMount=="function"&&(n.flags|=4194308),n.memoizedProps=o,n.memoizedState=he),d.props=o,d.state=he,d.context=S,o=G):(typeof d.componentDidMount=="function"&&(n.flags|=4194308),o=!1)}else{d=n.stateNode,Df(t,n),S=n.memoizedProps,be=Ss(a,S),d.props=be,Te=n.pendingProps,me=d.context,he=a.contextType,G=Xs,typeof he=="object"&&he!==null&&(G=ri(he)),C=a.getDerivedStateFromProps,(he=typeof C=="function"||typeof d.getSnapshotBeforeUpdate=="function")||typeof d.UNSAFE_componentWillReceiveProps!="function"&&typeof d.componentWillReceiveProps!="function"||(S!==Te||me!==G)&&Hg(n,d,o,G),Lr=!1,me=n.memoizedState,d.state=me,rl(n,o,d,u),al();var _e=n.memoizedState;S!==Te||me!==_e||Lr||t!==null&&t.dependencies!==null&&lc(t.dependencies)?(typeof C=="function"&&($f(n,a,C,o),_e=n.memoizedState),(be=Lr||Bg(n,a,be,o,me,_e,G)||t!==null&&t.dependencies!==null&&lc(t.dependencies))?(he||typeof d.UNSAFE_componentWillUpdate!="function"&&typeof d.componentWillUpdate!="function"||(typeof d.componentWillUpdate=="function"&&d.componentWillUpdate(o,_e,G),typeof d.UNSAFE_componentWillUpdate=="function"&&d.UNSAFE_componentWillUpdate(o,_e,G)),typeof d.componentDidUpdate=="function"&&(n.flags|=4),typeof d.getSnapshotBeforeUpdate=="function"&&(n.flags|=1024)):(typeof d.componentDidUpdate!="function"||S===t.memoizedProps&&me===t.memoizedState||(n.flags|=4),typeof d.getSnapshotBeforeUpdate!="function"||S===t.memoizedProps&&me===t.memoizedState||(n.flags|=1024),n.memoizedProps=o,n.memoizedState=_e),d.props=o,d.state=_e,d.context=G,o=be):(typeof d.componentDidUpdate!="function"||S===t.memoizedProps&&me===t.memoizedState||(n.flags|=4),typeof d.getSnapshotBeforeUpdate!="function"||S===t.memoizedProps&&me===t.memoizedState||(n.flags|=1024),o=!1)}return d=o,Rc(t,n),o=(n.flags&128)!==0,d||o?(d=n.stateNode,a=o&&typeof a.getDerivedStateFromError!="function"?null:d.render(),n.flags|=1,t!==null&&o?(n.child=_s(n,t.child,null,u),n.child=_s(n,null,a,u)):si(t,n,a,u),n.memoizedState=d.state,t=n.child):t=ar(t,n,u),t}function t0(t,n,a,o){return ds(),n.flags|=256,si(t,n,a,o),n.child}var ad={dehydrated:null,treeContext:null,retryLane:0,hydrationErrors:null};function rd(t){return{baseLanes:t,cachePool:Xm()}}function sd(t,n,a){return t=t!==null?t.childLanes&~a:0,n&&(t|=ki),t}function n0(t,n,a){var o=n.pendingProps,u=!1,d=(n.flags&128)!==0,S;if((S=d)||(S=t!==null&&t.memoizedState===null?!1:(Pn.current&2)!==0),S&&(u=!0,n.flags&=-129),S=(n.flags&32)!==0,n.flags&=-33,t===null){if(Vt){if(u?Ir(n):Fr(),(t=xn)?(t=uv(t,oa),t=t!==null&&t.data!=="&"?t:null,t!==null&&(n.memoizedState={dehydrated:t,treeContext:wr!==null?{id:Pa,overflow:Ia}:null,retryLane:536870912,hydrationErrors:null},a=Pm(t),a.return=n,n.child=a,ai=n,xn=null)):t=null,t===null)throw Ur(n);return Vd(t)?n.lanes=32:n.lanes=536870912,null}var C=o.children;return o=o.fallback,u?(Fr(),u=n.mode,C=Cc({mode:"hidden",children:C},u),o=fs(o,u,a,null),C.return=n,o.return=n,C.sibling=o,n.child=C,o=n.child,o.memoizedState=rd(a),o.childLanes=sd(t,S,a),n.memoizedState=ad,ul(null,o)):(Ir(n),od(n,C))}var G=t.memoizedState;if(G!==null&&(C=G.dehydrated,C!==null)){if(d)n.flags&256?(Ir(n),n.flags&=-257,n=ld(t,n,a)):n.memoizedState!==null?(Fr(),n.child=t.child,n.flags|=128,n=null):(Fr(),C=o.fallback,u=n.mode,o=Cc({mode:"visible",children:o.children},u),C=fs(C,u,a,null),C.flags|=2,o.return=n,C.return=n,o.sibling=C,n.child=o,_s(n,t.child,null,a),o=n.child,o.memoizedState=rd(a),o.childLanes=sd(t,S,a),n.memoizedState=ad,n=ul(null,o));else if(Ir(n),Vd(C)){if(S=C.nextSibling&&C.nextSibling.dataset,S)var he=S.dgst;S=he,o=Error(r(419)),o.stack="",o.digest=S,Jo({value:o,source:null,stack:null}),n=ld(t,n,a)}else if(Vn||js(t,n,a,!1),S=(a&t.childLanes)!==0,Vn||S){if(S=vn,S!==null&&(o=ti(S,a),o!==0&&o!==G.retryLane))throw G.retryLane=o,us(t,o),Li(S,t,o),nd;Gd(C)||Fc(),n=ld(t,n,a)}else Gd(C)?(n.flags|=192,n.child=t.child,n=null):(t=G.treeContext,xn=ca(C.nextSibling),ai=n,Vt=!0,Dr=null,oa=!1,t!==null&&zm(n,t),n=od(n,o.children),n.flags|=4096);return n}return u?(Fr(),C=o.fallback,u=n.mode,G=t.child,he=G.sibling,o=Ja(G,{mode:"hidden",children:o.children}),o.subtreeFlags=G.subtreeFlags&65011712,he!==null?C=Ja(he,C):(C=fs(C,u,a,null),C.flags|=2),C.return=n,o.return=n,o.sibling=C,n.child=o,ul(null,o),o=n.child,C=t.child.memoizedState,C===null?C=rd(a):(u=C.cachePool,u!==null?(G=Hn._currentValue,u=u.parent!==G?{parent:G,pool:G}:u):u=Xm(),C={baseLanes:C.baseLanes|a,cachePool:u}),o.memoizedState=C,o.childLanes=sd(t,S,a),n.memoizedState=ad,ul(t.child,o)):(Ir(n),a=t.child,t=a.sibling,a=Ja(a,{mode:"visible",children:o.children}),a.return=n,a.sibling=null,t!==null&&(S=n.deletions,S===null?(n.deletions=[t],n.flags|=16):S.push(t)),n.child=a,n.memoizedState=null,a)}function od(t,n){return n=Cc({mode:"visible",children:n},t.mode),n.return=t,t.child=n}function Cc(t,n){return t=Bi(22,t,null,n),t.lanes=0,t}function ld(t,n,a){return _s(n,t.child,null,a),t=od(n,n.pendingProps.children),t.flags|=2,n.memoizedState=null,t}function i0(t,n,a){t.lanes|=n;var o=t.alternate;o!==null&&(o.lanes|=n),bf(t.return,n,a)}function cd(t,n,a,o,u,d){var S=t.memoizedState;S===null?t.memoizedState={isBackwards:n,rendering:null,renderingStartTime:0,last:o,tail:a,tailMode:u,treeForkCount:d}:(S.isBackwards=n,S.rendering=null,S.renderingStartTime=0,S.last=o,S.tail=a,S.tailMode=u,S.treeForkCount=d)}function a0(t,n,a){var o=n.pendingProps,u=o.revealOrder,d=o.tail;o=o.children;var S=Pn.current,C=(S&2)!==0;if(C?(S=S&1|2,n.flags|=128):S&=1,xe(Pn,S),si(t,n,o,a),o=Vt?Qo:0,!C&&t!==null&&(t.flags&128)!==0)e:for(t=n.child;t!==null;){if(t.tag===13)t.memoizedState!==null&&i0(t,a,n);else if(t.tag===19)i0(t,a,n);else if(t.child!==null){t.child.return=t,t=t.child;continue}if(t===n)break e;for(;t.sibling===null;){if(t.return===null||t.return===n)break e;t=t.return}t.sibling.return=t.return,t=t.sibling}switch(u){case"forwards":for(a=n.child,u=null;a!==null;)t=a.alternate,t!==null&&gc(t)===null&&(u=a),a=a.sibling;a=u,a===null?(u=n.child,n.child=null):(u=a.sibling,a.sibling=null),cd(n,!1,u,a,d,o);break;case"backwards":case"unstable_legacy-backwards":for(a=null,u=n.child,n.child=null;u!==null;){if(t=u.alternate,t!==null&&gc(t)===null){n.child=u;break}t=u.sibling,u.sibling=a,a=u,u=t}cd(n,!0,a,null,d,o);break;case"together":cd(n,!1,null,null,void 0,o);break;default:n.memoizedState=null}return n.child}function ar(t,n,a){if(t!==null&&(n.dependencies=t.dependencies),Hr|=n.lanes,(a&n.childLanes)===0)if(t!==null){if(js(t,n,a,!1),(a&n.childLanes)===0)return null}else return null;if(t!==null&&n.child!==t.child)throw Error(r(153));if(n.child!==null){for(t=n.child,a=Ja(t,t.pendingProps),n.child=a,a.return=n;t.sibling!==null;)t=t.sibling,a=a.sibling=Ja(t,t.pendingProps),a.return=n;a.sibling=null}return n.child}function ud(t,n){return(t.lanes&n)!==0?!0:(t=t.dependencies,!!(t!==null&&lc(t)))}function ty(t,n,a){switch(n.tag){case 3:ye(n,n.stateNode.containerInfo),Nr(n,Hn,t.memoizedState.cache),ds();break;case 27:case 5:at(n);break;case 4:ye(n,n.stateNode.containerInfo);break;case 10:Nr(n,n.type,n.memoizedProps.value);break;case 31:if(n.memoizedState!==null)return n.flags|=128,Pf(n),null;break;case 13:var o=n.memoizedState;if(o!==null)return o.dehydrated!==null?(Ir(n),n.flags|=128,null):(a&n.child.childLanes)!==0?n0(t,n,a):(Ir(n),t=ar(t,n,a),t!==null?t.sibling:null);Ir(n);break;case 19:var u=(t.flags&128)!==0;if(o=(a&n.childLanes)!==0,o||(js(t,n,a,!1),o=(a&n.childLanes)!==0),u){if(o)return a0(t,n,a);n.flags|=128}if(u=n.memoizedState,u!==null&&(u.rendering=null,u.tail=null,u.lastEffect=null),xe(Pn,Pn.current),o)break;return null;case 22:return n.lanes=0,Kg(t,n,a,n.pendingProps);case 24:Nr(n,Hn,t.memoizedState.cache)}return ar(t,n,a)}function r0(t,n,a){if(t!==null)if(t.memoizedProps!==n.pendingProps)Vn=!0;else{if(!ud(t,a)&&(n.flags&128)===0)return Vn=!1,ty(t,n,a);Vn=(t.flags&131072)!==0}else Vn=!1,Vt&&(n.flags&1048576)!==0&&Fm(n,Qo,n.index);switch(n.lanes=0,n.tag){case 16:e:{var o=n.pendingProps;if(t=gs(n.elementType),n.type=t,typeof t=="function")mf(t)?(o=Ss(t,o),n.tag=1,n=e0(null,n,t,o,a)):(n.tag=0,n=id(null,n,t,o,a));else{if(t!=null){var u=t.$$typeof;if(u===R){n.tag=11,n=Yg(null,n,t,o,a);break e}else if(u===P){n.tag=14,n=jg(null,n,t,o,a);break e}}throw n=Y(t)||t,Error(r(306,n,""))}}return n;case 0:return id(t,n,n.type,n.pendingProps,a);case 1:return o=n.type,u=Ss(o,n.pendingProps),e0(t,n,o,u,a);case 3:e:{if(ye(n,n.stateNode.containerInfo),t===null)throw Error(r(387));o=n.pendingProps;var d=n.memoizedState;u=d.element,Df(t,n),rl(n,o,null,a);var S=n.memoizedState;if(o=S.cache,Nr(n,Hn,o),o!==d.cache&&Ef(n,[Hn],a,!0),al(),o=S.element,d.isDehydrated)if(d={element:o,isDehydrated:!1,cache:S.cache},n.updateQueue.baseState=d,n.memoizedState=d,n.flags&256){n=t0(t,n,o,a);break e}else if(o!==u){u=aa(Error(r(424)),n),Jo(u),n=t0(t,n,o,a);break e}else{switch(t=n.stateNode.containerInfo,t.nodeType){case 9:t=t.body;break;default:t=t.nodeName==="HTML"?t.ownerDocument.body:t}for(xn=ca(t.firstChild),ai=n,Vt=!0,Dr=null,oa=!0,a=Km(n,null,o,a),n.child=a;a;)a.flags=a.flags&-3|4096,a=a.sibling}else{if(ds(),o===u){n=ar(t,n,a);break e}si(t,n,o,a)}n=n.child}return n;case 26:return Rc(t,n),t===null?(a=gv(n.type,null,n.pendingProps,null))?n.memoizedState=a:Vt||(a=n.type,t=n.pendingProps,o=Xc(Xe.current).createElement(a),o[yn]=n,o[Bn]=t,oi(o,a,t),sn(o),n.stateNode=o):n.memoizedState=gv(n.type,t.memoizedProps,n.pendingProps,t.memoizedState),null;case 27:return at(n),t===null&&Vt&&(o=n.stateNode=hv(n.type,n.pendingProps,Xe.current),ai=n,oa=!0,u=xn,Wr(n.type)?(kd=u,xn=ca(o.firstChild)):xn=u),si(t,n,n.pendingProps.children,a),Rc(t,n),t===null&&(n.flags|=4194304),n.child;case 5:return t===null&&Vt&&((u=o=xn)&&(o=Uy(o,n.type,n.pendingProps,oa),o!==null?(n.stateNode=o,ai=n,xn=ca(o.firstChild),oa=!1,u=!0):u=!1),u||Ur(n)),at(n),u=n.type,d=n.pendingProps,S=t!==null?t.memoizedProps:null,o=d.children,zd(u,d)?o=null:S!==null&&zd(u,S)&&(n.flags|=32),n.memoizedState!==null&&(u=Ff(t,n,qS,null,null,a),Tl._currentValue=u),Rc(t,n),si(t,n,o,a),n.child;case 6:return t===null&&Vt&&((t=a=xn)&&(a=Ny(a,n.pendingProps,oa),a!==null?(n.stateNode=a,ai=n,xn=null,t=!0):t=!1),t||Ur(n)),null;case 13:return n0(t,n,a);case 4:return ye(n,n.stateNode.containerInfo),o=n.pendingProps,t===null?n.child=_s(n,null,o,a):si(t,n,o,a),n.child;case 11:return Yg(t,n,n.type,n.pendingProps,a);case 7:return si(t,n,n.pendingProps,a),n.child;case 8:return si(t,n,n.pendingProps.children,a),n.child;case 12:return si(t,n,n.pendingProps.children,a),n.child;case 10:return o=n.pendingProps,Nr(n,n.type,o.value),si(t,n,o.children,a),n.child;case 9:return u=n.type._context,o=n.pendingProps.children,ps(n),u=ri(u),o=o(u),n.flags|=1,si(t,n,o,a),n.child;case 14:return jg(t,n,n.type,n.pendingProps,a);case 15:return Zg(t,n,n.type,n.pendingProps,a);case 19:return a0(t,n,a);case 31:return ey(t,n,a);case 22:return Kg(t,n,a,n.pendingProps);case 24:return ps(n),o=ri(Hn),t===null?(u=Rf(),u===null&&(u=vn,d=Tf(),u.pooledCache=d,d.refCount++,d!==null&&(u.pooledCacheLanes|=a),u=d),n.memoizedState={parent:o,cache:u},wf(n),Nr(n,Hn,u)):((t.lanes&a)!==0&&(Df(t,n),rl(n,null,null,a),al()),u=t.memoizedState,d=n.memoizedState,u.parent!==o?(u={parent:o,cache:o},n.memoizedState=u,n.lanes===0&&(n.memoizedState=n.updateQueue.baseState=u),Nr(n,Hn,o)):(o=d.cache,Nr(n,Hn,o),o!==u.cache&&Ef(n,[Hn],a,!0))),si(t,n,n.pendingProps.children,a),n.child;case 29:throw n.pendingProps}throw Error(r(156,n.tag))}function rr(t){t.flags|=4}function fd(t,n,a,o,u){if((n=(t.mode&32)!==0)&&(n=!1),n){if(t.flags|=16777216,(u&335544128)===u)if(t.stateNode.complete)t.flags|=8192;else if(N0())t.flags|=8192;else throw vs=dc,Cf}else t.flags&=-16777217}function s0(t,n){if(n.type!=="stylesheet"||(n.state.loading&4)!==0)t.flags&=-16777217;else if(t.flags|=16777216,!yv(n))if(N0())t.flags|=8192;else throw vs=dc,Cf}function wc(t,n){n!==null&&(t.flags|=4),t.flags&16384&&(n=t.tag!==22?Re():536870912,t.lanes|=n,so|=n)}function fl(t,n){if(!Vt)switch(t.tailMode){case"hidden":n=t.tail;for(var a=null;n!==null;)n.alternate!==null&&(a=n),n=n.sibling;a===null?t.tail=null:a.sibling=null;break;case"collapsed":a=t.tail;for(var o=null;a!==null;)a.alternate!==null&&(o=a),a=a.sibling;o===null?n||t.tail===null?t.tail=null:t.tail.sibling=null:o.sibling=null}}function Sn(t){var n=t.alternate!==null&&t.alternate.child===t.child,a=0,o=0;if(n)for(var u=t.child;u!==null;)a|=u.lanes|u.childLanes,o|=u.subtreeFlags&65011712,o|=u.flags&65011712,u.return=t,u=u.sibling;else for(u=t.child;u!==null;)a|=u.lanes|u.childLanes,o|=u.subtreeFlags,o|=u.flags,u.return=t,u=u.sibling;return t.subtreeFlags|=o,t.childLanes=a,n}function ny(t,n,a){var o=n.pendingProps;switch(xf(n),n.tag){case 16:case 15:case 0:case 11:case 7:case 8:case 12:case 9:case 14:return Sn(n),null;case 1:return Sn(n),null;case 3:return a=n.stateNode,o=null,t!==null&&(o=t.memoizedState.cache),n.memoizedState.cache!==o&&(n.flags|=2048),tr(Hn),we(),a.pendingContext&&(a.context=a.pendingContext,a.pendingContext=null),(t===null||t.child===null)&&(Ys(n)?rr(n):t===null||t.memoizedState.isDehydrated&&(n.flags&256)===0||(n.flags|=1024,yf())),Sn(n),null;case 26:var u=n.type,d=n.memoizedState;return t===null?(rr(n),d!==null?(Sn(n),s0(n,d)):(Sn(n),fd(n,u,null,o,a))):d?d!==t.memoizedState?(rr(n),Sn(n),s0(n,d)):(Sn(n),n.flags&=-16777217):(t=t.memoizedProps,t!==o&&rr(n),Sn(n),fd(n,u,t,o,a)),null;case 27:if(Ge(n),a=Xe.current,u=n.type,t!==null&&n.stateNode!=null)t.memoizedProps!==o&&rr(n);else{if(!o){if(n.stateNode===null)throw Error(r(166));return Sn(n),null}t=Ue.current,Ys(n)?Bm(n):(t=hv(u,o,a),n.stateNode=t,rr(n))}return Sn(n),null;case 5:if(Ge(n),u=n.type,t!==null&&n.stateNode!=null)t.memoizedProps!==o&&rr(n);else{if(!o){if(n.stateNode===null)throw Error(r(166));return Sn(n),null}if(d=Ue.current,Ys(n))Bm(n);else{var S=Xc(Xe.current);switch(d){case 1:d=S.createElementNS("http://www.w3.org/2000/svg",u);break;case 2:d=S.createElementNS("http://www.w3.org/1998/Math/MathML",u);break;default:switch(u){case"svg":d=S.createElementNS("http://www.w3.org/2000/svg",u);break;case"math":d=S.createElementNS("http://www.w3.org/1998/Math/MathML",u);break;case"script":d=S.createElement("div"),d.innerHTML="<script><\/script>",d=d.removeChild(d.firstChild);break;case"select":d=typeof o.is=="string"?S.createElement("select",{is:o.is}):S.createElement("select"),o.multiple?d.multiple=!0:o.size&&(d.size=o.size);break;default:d=typeof o.is=="string"?S.createElement(u,{is:o.is}):S.createElement(u)}}d[yn]=n,d[Bn]=o;e:for(S=n.child;S!==null;){if(S.tag===5||S.tag===6)d.appendChild(S.stateNode);else if(S.tag!==4&&S.tag!==27&&S.child!==null){S.child.return=S,S=S.child;continue}if(S===n)break e;for(;S.sibling===null;){if(S.return===null||S.return===n)break e;S=S.return}S.sibling.return=S.return,S=S.sibling}n.stateNode=d;e:switch(oi(d,u,o),u){case"button":case"input":case"select":case"textarea":o=!!o.autoFocus;break e;case"img":o=!0;break e;default:o=!1}o&&rr(n)}}return Sn(n),fd(n,n.type,t===null?null:t.memoizedProps,n.pendingProps,a),null;case 6:if(t&&n.stateNode!=null)t.memoizedProps!==o&&rr(n);else{if(typeof o!="string"&&n.stateNode===null)throw Error(r(166));if(t=Xe.current,Ys(n)){if(t=n.stateNode,a=n.memoizedProps,o=null,u=ai,u!==null)switch(u.tag){case 27:case 5:o=u.memoizedProps}t[yn]=n,t=!!(t.nodeValue===a||o!==null&&o.suppressHydrationWarning===!0||nv(t.nodeValue,a)),t||Ur(n,!0)}else t=Xc(t).createTextNode(o),t[yn]=n,n.stateNode=t}return Sn(n),null;case 31:if(a=n.memoizedState,t===null||t.memoizedState!==null){if(o=Ys(n),a!==null){if(t===null){if(!o)throw Error(r(318));if(t=n.memoizedState,t=t!==null?t.dehydrated:null,!t)throw Error(r(557));t[yn]=n}else ds(),(n.flags&128)===0&&(n.memoizedState=null),n.flags|=4;Sn(n),t=!1}else a=yf(),t!==null&&t.memoizedState!==null&&(t.memoizedState.hydrationErrors=a),t=!0;if(!t)return n.flags&256?(Gi(n),n):(Gi(n),null);if((n.flags&128)!==0)throw Error(r(558))}return Sn(n),null;case 13:if(o=n.memoizedState,t===null||t.memoizedState!==null&&t.memoizedState.dehydrated!==null){if(u=Ys(n),o!==null&&o.dehydrated!==null){if(t===null){if(!u)throw Error(r(318));if(u=n.memoizedState,u=u!==null?u.dehydrated:null,!u)throw Error(r(317));u[yn]=n}else ds(),(n.flags&128)===0&&(n.memoizedState=null),n.flags|=4;Sn(n),u=!1}else u=yf(),t!==null&&t.memoizedState!==null&&(t.memoizedState.hydrationErrors=u),u=!0;if(!u)return n.flags&256?(Gi(n),n):(Gi(n),null)}return Gi(n),(n.flags&128)!==0?(n.lanes=a,n):(a=o!==null,t=t!==null&&t.memoizedState!==null,a&&(o=n.child,u=null,o.alternate!==null&&o.alternate.memoizedState!==null&&o.alternate.memoizedState.cachePool!==null&&(u=o.alternate.memoizedState.cachePool.pool),d=null,o.memoizedState!==null&&o.memoizedState.cachePool!==null&&(d=o.memoizedState.cachePool.pool),d!==u&&(o.flags|=2048)),a!==t&&a&&(n.child.flags|=8192),wc(n,n.updateQueue),Sn(n),null);case 4:return we(),t===null&&Ld(n.stateNode.containerInfo),Sn(n),null;case 10:return tr(n.type),Sn(n),null;case 19:if(re(Pn),o=n.memoizedState,o===null)return Sn(n),null;if(u=(n.flags&128)!==0,d=o.rendering,d===null)if(u)fl(o,!1);else{if(Nn!==0||t!==null&&(t.flags&128)!==0)for(t=n.child;t!==null;){if(d=gc(t),d!==null){for(n.flags|=128,fl(o,!1),t=d.updateQueue,n.updateQueue=t,wc(n,t),n.subtreeFlags=0,t=a,a=n.child;a!==null;)Om(a,t),a=a.sibling;return xe(Pn,Pn.current&1|2),Vt&&$a(n,o.treeForkCount),n.child}t=t.sibling}o.tail!==null&&Ft()>Oc&&(n.flags|=128,u=!0,fl(o,!1),n.lanes=4194304)}else{if(!u)if(t=gc(d),t!==null){if(n.flags|=128,u=!0,t=t.updateQueue,n.updateQueue=t,wc(n,t),fl(o,!0),o.tail===null&&o.tailMode==="hidden"&&!d.alternate&&!Vt)return Sn(n),null}else 2*Ft()-o.renderingStartTime>Oc&&a!==536870912&&(n.flags|=128,u=!0,fl(o,!1),n.lanes=4194304);o.isBackwards?(d.sibling=n.child,n.child=d):(t=o.last,t!==null?t.sibling=d:n.child=d,o.last=d)}return o.tail!==null?(t=o.tail,o.rendering=t,o.tail=t.sibling,o.renderingStartTime=Ft(),t.sibling=null,a=Pn.current,xe(Pn,u?a&1|2:a&1),Vt&&$a(n,o.treeForkCount),t):(Sn(n),null);case 22:case 23:return Gi(n),Of(),o=n.memoizedState!==null,t!==null?t.memoizedState!==null!==o&&(n.flags|=8192):o&&(n.flags|=8192),o?(a&536870912)!==0&&(n.flags&128)===0&&(Sn(n),n.subtreeFlags&6&&(n.flags|=8192)):Sn(n),a=n.updateQueue,a!==null&&wc(n,a.retryQueue),a=null,t!==null&&t.memoizedState!==null&&t.memoizedState.cachePool!==null&&(a=t.memoizedState.cachePool.pool),o=null,n.memoizedState!==null&&n.memoizedState.cachePool!==null&&(o=n.memoizedState.cachePool.pool),o!==a&&(n.flags|=2048),t!==null&&re(ms),null;case 24:return a=null,t!==null&&(a=t.memoizedState.cache),n.memoizedState.cache!==a&&(n.flags|=2048),tr(Hn),Sn(n),null;case 25:return null;case 30:return null}throw Error(r(156,n.tag))}function iy(t,n){switch(xf(n),n.tag){case 1:return t=n.flags,t&65536?(n.flags=t&-65537|128,n):null;case 3:return tr(Hn),we(),t=n.flags,(t&65536)!==0&&(t&128)===0?(n.flags=t&-65537|128,n):null;case 26:case 27:case 5:return Ge(n),null;case 31:if(n.memoizedState!==null){if(Gi(n),n.alternate===null)throw Error(r(340));ds()}return t=n.flags,t&65536?(n.flags=t&-65537|128,n):null;case 13:if(Gi(n),t=n.memoizedState,t!==null&&t.dehydrated!==null){if(n.alternate===null)throw Error(r(340));ds()}return t=n.flags,t&65536?(n.flags=t&-65537|128,n):null;case 19:return re(Pn),null;case 4:return we(),null;case 10:return tr(n.type),null;case 22:case 23:return Gi(n),Of(),t!==null&&re(ms),t=n.flags,t&65536?(n.flags=t&-65537|128,n):null;case 24:return tr(Hn),null;case 25:return null;default:return null}}function o0(t,n){switch(xf(n),n.tag){case 3:tr(Hn),we();break;case 26:case 27:case 5:Ge(n);break;case 4:we();break;case 31:n.memoizedState!==null&&Gi(n);break;case 13:Gi(n);break;case 19:re(Pn);break;case 10:tr(n.type);break;case 22:case 23:Gi(n),Of(),t!==null&&re(ms);break;case 24:tr(Hn)}}function dl(t,n){try{var a=n.updateQueue,o=a!==null?a.lastEffect:null;if(o!==null){var u=o.next;a=u;do{if((a.tag&t)===t){o=void 0;var d=a.create,S=a.inst;o=d(),S.destroy=o}a=a.next}while(a!==u)}}catch(C){ln(n,n.return,C)}}function zr(t,n,a){try{var o=n.updateQueue,u=o!==null?o.lastEffect:null;if(u!==null){var d=u.next;o=d;do{if((o.tag&t)===t){var S=o.inst,C=S.destroy;if(C!==void 0){S.destroy=void 0,u=n;var G=a,he=C;try{he()}catch(be){ln(u,G,be)}}}o=o.next}while(o!==d)}}catch(be){ln(n,n.return,be)}}function l0(t){var n=t.updateQueue;if(n!==null){var a=t.stateNode;try{Jm(n,a)}catch(o){ln(t,t.return,o)}}}function c0(t,n,a){a.props=Ss(t.type,t.memoizedProps),a.state=t.memoizedState;try{a.componentWillUnmount()}catch(o){ln(t,n,o)}}function hl(t,n){try{var a=t.ref;if(a!==null){switch(t.tag){case 26:case 27:case 5:var o=t.stateNode;break;case 30:o=t.stateNode;break;default:o=t.stateNode}typeof a=="function"?t.refCleanup=a(o):a.current=o}}catch(u){ln(t,n,u)}}function Fa(t,n){var a=t.ref,o=t.refCleanup;if(a!==null)if(typeof o=="function")try{o()}catch(u){ln(t,n,u)}finally{t.refCleanup=null,t=t.alternate,t!=null&&(t.refCleanup=null)}else if(typeof a=="function")try{a(null)}catch(u){ln(t,n,u)}else a.current=null}function u0(t){var n=t.type,a=t.memoizedProps,o=t.stateNode;try{e:switch(n){case"button":case"input":case"select":case"textarea":a.autoFocus&&o.focus();break e;case"img":a.src?o.src=a.src:a.srcSet&&(o.srcset=a.srcSet)}}catch(u){ln(t,t.return,u)}}function dd(t,n,a){try{var o=t.stateNode;Ty(o,t.type,a,n),o[Bn]=n}catch(u){ln(t,t.return,u)}}function f0(t){return t.tag===5||t.tag===3||t.tag===26||t.tag===27&&Wr(t.type)||t.tag===4}function hd(t){e:for(;;){for(;t.sibling===null;){if(t.return===null||f0(t.return))return null;t=t.return}for(t.sibling.return=t.return,t=t.sibling;t.tag!==5&&t.tag!==6&&t.tag!==18;){if(t.tag===27&&Wr(t.type)||t.flags&2||t.child===null||t.tag===4)continue e;t.child.return=t,t=t.child}if(!(t.flags&2))return t.stateNode}}function pd(t,n,a){var o=t.tag;if(o===5||o===6)t=t.stateNode,n?(a.nodeType===9?a.body:a.nodeName==="HTML"?a.ownerDocument.body:a).insertBefore(t,n):(n=a.nodeType===9?a.body:a.nodeName==="HTML"?a.ownerDocument.body:a,n.appendChild(t),a=a._reactRootContainer,a!=null||n.onclick!==null||(n.onclick=Si));else if(o!==4&&(o===27&&Wr(t.type)&&(a=t.stateNode,n=null),t=t.child,t!==null))for(pd(t,n,a),t=t.sibling;t!==null;)pd(t,n,a),t=t.sibling}function Dc(t,n,a){var o=t.tag;if(o===5||o===6)t=t.stateNode,n?a.insertBefore(t,n):a.appendChild(t);else if(o!==4&&(o===27&&Wr(t.type)&&(a=t.stateNode),t=t.child,t!==null))for(Dc(t,n,a),t=t.sibling;t!==null;)Dc(t,n,a),t=t.sibling}function d0(t){var n=t.stateNode,a=t.memoizedProps;try{for(var o=t.type,u=n.attributes;u.length;)n.removeAttributeNode(u[0]);oi(n,o,a),n[yn]=t,n[Bn]=a}catch(d){ln(t,t.return,d)}}var sr=!1,kn=!1,md=!1,h0=typeof WeakSet=="function"?WeakSet:Set,Jn=null;function ay(t,n){if(t=t.containerInfo,Id=Qc,t=Tm(t),lf(t)){if("selectionStart"in t)var a={start:t.selectionStart,end:t.selectionEnd};else e:{a=(a=t.ownerDocument)&&a.defaultView||window;var o=a.getSelection&&a.getSelection();if(o&&o.rangeCount!==0){a=o.anchorNode;var u=o.anchorOffset,d=o.focusNode;o=o.focusOffset;try{a.nodeType,d.nodeType}catch{a=null;break e}var S=0,C=-1,G=-1,he=0,be=0,Te=t,me=null;t:for(;;){for(var _e;Te!==a||u!==0&&Te.nodeType!==3||(C=S+u),Te!==d||o!==0&&Te.nodeType!==3||(G=S+o),Te.nodeType===3&&(S+=Te.nodeValue.length),(_e=Te.firstChild)!==null;)me=Te,Te=_e;for(;;){if(Te===t)break t;if(me===a&&++he===u&&(C=S),me===d&&++be===o&&(G=S),(_e=Te.nextSibling)!==null)break;Te=me,me=Te.parentNode}Te=_e}a=C===-1||G===-1?null:{start:C,end:G}}else a=null}a=a||{start:0,end:0}}else a=null;for(Fd={focusedElem:t,selectionRange:a},Qc=!1,Jn=n;Jn!==null;)if(n=Jn,t=n.child,(n.subtreeFlags&1028)!==0&&t!==null)t.return=n,Jn=t;else for(;Jn!==null;){switch(n=Jn,d=n.alternate,t=n.flags,n.tag){case 0:if((t&4)!==0&&(t=n.updateQueue,t=t!==null?t.events:null,t!==null))for(a=0;a<t.length;a++)u=t[a],u.ref.impl=u.nextImpl;break;case 11:case 15:break;case 1:if((t&1024)!==0&&d!==null){t=void 0,a=n,u=d.memoizedProps,d=d.memoizedState,o=a.stateNode;try{var tt=Ss(a.type,u);t=o.getSnapshotBeforeUpdate(tt,d),o.__reactInternalSnapshotBeforeUpdate=t}catch(ft){ln(a,a.return,ft)}}break;case 3:if((t&1024)!==0){if(t=n.stateNode.containerInfo,a=t.nodeType,a===9)Hd(t);else if(a===1)switch(t.nodeName){case"HEAD":case"HTML":case"BODY":Hd(t);break;default:t.textContent=""}}break;case 5:case 26:case 27:case 6:case 4:case 17:break;default:if((t&1024)!==0)throw Error(r(163))}if(t=n.sibling,t!==null){t.return=n.return,Jn=t;break}Jn=n.return}}function p0(t,n,a){var o=a.flags;switch(a.tag){case 0:case 11:case 15:lr(t,a),o&4&&dl(5,a);break;case 1:if(lr(t,a),o&4)if(t=a.stateNode,n===null)try{t.componentDidMount()}catch(S){ln(a,a.return,S)}else{var u=Ss(a.type,n.memoizedProps);n=n.memoizedState;try{t.componentDidUpdate(u,n,t.__reactInternalSnapshotBeforeUpdate)}catch(S){ln(a,a.return,S)}}o&64&&l0(a),o&512&&hl(a,a.return);break;case 3:if(lr(t,a),o&64&&(t=a.updateQueue,t!==null)){if(n=null,a.child!==null)switch(a.child.tag){case 27:case 5:n=a.child.stateNode;break;case 1:n=a.child.stateNode}try{Jm(t,n)}catch(S){ln(a,a.return,S)}}break;case 27:n===null&&o&4&&d0(a);case 26:case 5:lr(t,a),n===null&&o&4&&u0(a),o&512&&hl(a,a.return);break;case 12:lr(t,a);break;case 31:lr(t,a),o&4&&v0(t,a);break;case 13:lr(t,a),o&4&&_0(t,a),o&64&&(t=a.memoizedState,t!==null&&(t=t.dehydrated,t!==null&&(a=hy.bind(null,a),Ly(t,a))));break;case 22:if(o=a.memoizedState!==null||sr,!o){n=n!==null&&n.memoizedState!==null||kn,u=sr;var d=kn;sr=o,(kn=n)&&!d?cr(t,a,(a.subtreeFlags&8772)!==0):lr(t,a),sr=u,kn=d}break;case 30:break;default:lr(t,a)}}function m0(t){var n=t.alternate;n!==null&&(t.alternate=null,m0(n)),t.child=null,t.deletions=null,t.sibling=null,t.tag===5&&(n=t.stateNode,n!==null&&Ji(n)),t.stateNode=null,t.return=null,t.dependencies=null,t.memoizedProps=null,t.memoizedState=null,t.pendingProps=null,t.stateNode=null,t.updateQueue=null}var bn=null,wi=!1;function or(t,n,a){for(a=a.child;a!==null;)g0(t,n,a),a=a.sibling}function g0(t,n,a){if(Se&&typeof Se.onCommitFiberUnmount=="function")try{Se.onCommitFiberUnmount(pe,a)}catch{}switch(a.tag){case 26:kn||Fa(a,n),or(t,n,a),a.memoizedState?a.memoizedState.count--:a.stateNode&&(a=a.stateNode,a.parentNode.removeChild(a));break;case 27:kn||Fa(a,n);var o=bn,u=wi;Wr(a.type)&&(bn=a.stateNode,wi=!1),or(t,n,a),Ml(a.stateNode),bn=o,wi=u;break;case 5:kn||Fa(a,n);case 6:if(o=bn,u=wi,bn=null,or(t,n,a),bn=o,wi=u,bn!==null)if(wi)try{(bn.nodeType===9?bn.body:bn.nodeName==="HTML"?bn.ownerDocument.body:bn).removeChild(a.stateNode)}catch(d){ln(a,n,d)}else try{bn.removeChild(a.stateNode)}catch(d){ln(a,n,d)}break;case 18:bn!==null&&(wi?(t=bn,lv(t.nodeType===9?t.body:t.nodeName==="HTML"?t.ownerDocument.body:t,a.stateNode),mo(t)):lv(bn,a.stateNode));break;case 4:o=bn,u=wi,bn=a.stateNode.containerInfo,wi=!0,or(t,n,a),bn=o,wi=u;break;case 0:case 11:case 14:case 15:zr(2,a,n),kn||zr(4,a,n),or(t,n,a);break;case 1:kn||(Fa(a,n),o=a.stateNode,typeof o.componentWillUnmount=="function"&&c0(a,n,o)),or(t,n,a);break;case 21:or(t,n,a);break;case 22:kn=(o=kn)||a.memoizedState!==null,or(t,n,a),kn=o;break;default:or(t,n,a)}}function v0(t,n){if(n.memoizedState===null&&(t=n.alternate,t!==null&&(t=t.memoizedState,t!==null))){t=t.dehydrated;try{mo(t)}catch(a){ln(n,n.return,a)}}}function _0(t,n){if(n.memoizedState===null&&(t=n.alternate,t!==null&&(t=t.memoizedState,t!==null&&(t=t.dehydrated,t!==null))))try{mo(t)}catch(a){ln(n,n.return,a)}}function ry(t){switch(t.tag){case 31:case 13:case 19:var n=t.stateNode;return n===null&&(n=t.stateNode=new h0),n;case 22:return t=t.stateNode,n=t._retryCache,n===null&&(n=t._retryCache=new h0),n;default:throw Error(r(435,t.tag))}}function Uc(t,n){var a=ry(t);n.forEach(function(o){if(!a.has(o)){a.add(o);var u=py.bind(null,t,o);o.then(u,u)}})}function Di(t,n){var a=n.deletions;if(a!==null)for(var o=0;o<a.length;o++){var u=a[o],d=t,S=n,C=S;e:for(;C!==null;){switch(C.tag){case 27:if(Wr(C.type)){bn=C.stateNode,wi=!1;break e}break;case 5:bn=C.stateNode,wi=!1;break e;case 3:case 4:bn=C.stateNode.containerInfo,wi=!0;break e}C=C.return}if(bn===null)throw Error(r(160));g0(d,S,u),bn=null,wi=!1,d=u.alternate,d!==null&&(d.return=null),u.return=null}if(n.subtreeFlags&13886)for(n=n.child;n!==null;)x0(n,t),n=n.sibling}var ya=null;function x0(t,n){var a=t.alternate,o=t.flags;switch(t.tag){case 0:case 11:case 14:case 15:Di(n,t),Ui(t),o&4&&(zr(3,t,t.return),dl(3,t),zr(5,t,t.return));break;case 1:Di(n,t),Ui(t),o&512&&(kn||a===null||Fa(a,a.return)),o&64&&sr&&(t=t.updateQueue,t!==null&&(o=t.callbacks,o!==null&&(a=t.shared.hiddenCallbacks,t.shared.hiddenCallbacks=a===null?o:a.concat(o))));break;case 26:var u=ya;if(Di(n,t),Ui(t),o&512&&(kn||a===null||Fa(a,a.return)),o&4){var d=a!==null?a.memoizedState:null;if(o=t.memoizedState,a===null)if(o===null)if(t.stateNode===null){e:{o=t.type,a=t.memoizedProps,u=u.ownerDocument||u;t:switch(o){case"title":d=u.getElementsByTagName("title")[0],(!d||d[qt]||d[yn]||d.namespaceURI==="http://www.w3.org/2000/svg"||d.hasAttribute("itemprop"))&&(d=u.createElement(o),u.head.insertBefore(d,u.querySelector("head > title"))),oi(d,o,a),d[yn]=t,sn(d),o=d;break e;case"link":var S=xv("link","href",u).get(o+(a.href||""));if(S){for(var C=0;C<S.length;C++)if(d=S[C],d.getAttribute("href")===(a.href==null||a.href===""?null:a.href)&&d.getAttribute("rel")===(a.rel==null?null:a.rel)&&d.getAttribute("title")===(a.title==null?null:a.title)&&d.getAttribute("crossorigin")===(a.crossOrigin==null?null:a.crossOrigin)){S.splice(C,1);break t}}d=u.createElement(o),oi(d,o,a),u.head.appendChild(d);break;case"meta":if(S=xv("meta","content",u).get(o+(a.content||""))){for(C=0;C<S.length;C++)if(d=S[C],d.getAttribute("content")===(a.content==null?null:""+a.content)&&d.getAttribute("name")===(a.name==null?null:a.name)&&d.getAttribute("property")===(a.property==null?null:a.property)&&d.getAttribute("http-equiv")===(a.httpEquiv==null?null:a.httpEquiv)&&d.getAttribute("charset")===(a.charSet==null?null:a.charSet)){S.splice(C,1);break t}}d=u.createElement(o),oi(d,o,a),u.head.appendChild(d);break;default:throw Error(r(468,o))}d[yn]=t,sn(d),o=d}t.stateNode=o}else Sv(u,t.type,t.stateNode);else t.stateNode=_v(u,o,t.memoizedProps);else d!==o?(d===null?a.stateNode!==null&&(a=a.stateNode,a.parentNode.removeChild(a)):d.count--,o===null?Sv(u,t.type,t.stateNode):_v(u,o,t.memoizedProps)):o===null&&t.stateNode!==null&&dd(t,t.memoizedProps,a.memoizedProps)}break;case 27:Di(n,t),Ui(t),o&512&&(kn||a===null||Fa(a,a.return)),a!==null&&o&4&&dd(t,t.memoizedProps,a.memoizedProps);break;case 5:if(Di(n,t),Ui(t),o&512&&(kn||a===null||Fa(a,a.return)),t.flags&32){u=t.stateNode;try{ni(u,"")}catch(tt){ln(t,t.return,tt)}}o&4&&t.stateNode!=null&&(u=t.memoizedProps,dd(t,u,a!==null?a.memoizedProps:u)),o&1024&&(md=!0);break;case 6:if(Di(n,t),Ui(t),o&4){if(t.stateNode===null)throw Error(r(162));o=t.memoizedProps,a=t.stateNode;try{a.nodeValue=o}catch(tt){ln(t,t.return,tt)}}break;case 3:if(Yc=null,u=ya,ya=Wc(n.containerInfo),Di(n,t),ya=u,Ui(t),o&4&&a!==null&&a.memoizedState.isDehydrated)try{mo(n.containerInfo)}catch(tt){ln(t,t.return,tt)}md&&(md=!1,S0(t));break;case 4:o=ya,ya=Wc(t.stateNode.containerInfo),Di(n,t),Ui(t),ya=o;break;case 12:Di(n,t),Ui(t);break;case 31:Di(n,t),Ui(t),o&4&&(o=t.updateQueue,o!==null&&(t.updateQueue=null,Uc(t,o)));break;case 13:Di(n,t),Ui(t),t.child.flags&8192&&t.memoizedState!==null!=(a!==null&&a.memoizedState!==null)&&(Lc=Ft()),o&4&&(o=t.updateQueue,o!==null&&(t.updateQueue=null,Uc(t,o)));break;case 22:u=t.memoizedState!==null;var G=a!==null&&a.memoizedState!==null,he=sr,be=kn;if(sr=he||u,kn=be||G,Di(n,t),kn=be,sr=he,Ui(t),o&8192)e:for(n=t.stateNode,n._visibility=u?n._visibility&-2:n._visibility|1,u&&(a===null||G||sr||kn||ys(t)),a=null,n=t;;){if(n.tag===5||n.tag===26){if(a===null){G=a=n;try{if(d=G.stateNode,u)S=d.style,typeof S.setProperty=="function"?S.setProperty("display","none","important"):S.display="none";else{C=G.stateNode;var Te=G.memoizedProps.style,me=Te!=null&&Te.hasOwnProperty("display")?Te.display:null;C.style.display=me==null||typeof me=="boolean"?"":(""+me).trim()}}catch(tt){ln(G,G.return,tt)}}}else if(n.tag===6){if(a===null){G=n;try{G.stateNode.nodeValue=u?"":G.memoizedProps}catch(tt){ln(G,G.return,tt)}}}else if(n.tag===18){if(a===null){G=n;try{var _e=G.stateNode;u?cv(_e,!0):cv(G.stateNode,!1)}catch(tt){ln(G,G.return,tt)}}}else if((n.tag!==22&&n.tag!==23||n.memoizedState===null||n===t)&&n.child!==null){n.child.return=n,n=n.child;continue}if(n===t)break e;for(;n.sibling===null;){if(n.return===null||n.return===t)break e;a===n&&(a=null),n=n.return}a===n&&(a=null),n.sibling.return=n.return,n=n.sibling}o&4&&(o=t.updateQueue,o!==null&&(a=o.retryQueue,a!==null&&(o.retryQueue=null,Uc(t,a))));break;case 19:Di(n,t),Ui(t),o&4&&(o=t.updateQueue,o!==null&&(t.updateQueue=null,Uc(t,o)));break;case 30:break;case 21:break;default:Di(n,t),Ui(t)}}function Ui(t){var n=t.flags;if(n&2){try{for(var a,o=t.return;o!==null;){if(f0(o)){a=o;break}o=o.return}if(a==null)throw Error(r(160));switch(a.tag){case 27:var u=a.stateNode,d=hd(t);Dc(t,d,u);break;case 5:var S=a.stateNode;a.flags&32&&(ni(S,""),a.flags&=-33);var C=hd(t);Dc(t,C,S);break;case 3:case 4:var G=a.stateNode.containerInfo,he=hd(t);pd(t,he,G);break;default:throw Error(r(161))}}catch(be){ln(t,t.return,be)}t.flags&=-3}n&4096&&(t.flags&=-4097)}function S0(t){if(t.subtreeFlags&1024)for(t=t.child;t!==null;){var n=t;S0(n),n.tag===5&&n.flags&1024&&n.stateNode.reset(),t=t.sibling}}function lr(t,n){if(n.subtreeFlags&8772)for(n=n.child;n!==null;)p0(t,n.alternate,n),n=n.sibling}function ys(t){for(t=t.child;t!==null;){var n=t;switch(n.tag){case 0:case 11:case 14:case 15:zr(4,n,n.return),ys(n);break;case 1:Fa(n,n.return);var a=n.stateNode;typeof a.componentWillUnmount=="function"&&c0(n,n.return,a),ys(n);break;case 27:Ml(n.stateNode);case 26:case 5:Fa(n,n.return),ys(n);break;case 22:n.memoizedState===null&&ys(n);break;case 30:ys(n);break;default:ys(n)}t=t.sibling}}function cr(t,n,a){for(a=a&&(n.subtreeFlags&8772)!==0,n=n.child;n!==null;){var o=n.alternate,u=t,d=n,S=d.flags;switch(d.tag){case 0:case 11:case 15:cr(u,d,a),dl(4,d);break;case 1:if(cr(u,d,a),o=d,u=o.stateNode,typeof u.componentDidMount=="function")try{u.componentDidMount()}catch(he){ln(o,o.return,he)}if(o=d,u=o.updateQueue,u!==null){var C=o.stateNode;try{var G=u.shared.hiddenCallbacks;if(G!==null)for(u.shared.hiddenCallbacks=null,u=0;u<G.length;u++)Qm(G[u],C)}catch(he){ln(o,o.return,he)}}a&&S&64&&l0(d),hl(d,d.return);break;case 27:d0(d);case 26:case 5:cr(u,d,a),a&&o===null&&S&4&&u0(d),hl(d,d.return);break;case 12:cr(u,d,a);break;case 31:cr(u,d,a),a&&S&4&&v0(u,d);break;case 13:cr(u,d,a),a&&S&4&&_0(u,d);break;case 22:d.memoizedState===null&&cr(u,d,a),hl(d,d.return);break;case 30:break;default:cr(u,d,a)}n=n.sibling}}function gd(t,n){var a=null;t!==null&&t.memoizedState!==null&&t.memoizedState.cachePool!==null&&(a=t.memoizedState.cachePool.pool),t=null,n.memoizedState!==null&&n.memoizedState.cachePool!==null&&(t=n.memoizedState.cachePool.pool),t!==a&&(t!=null&&t.refCount++,a!=null&&$o(a))}function vd(t,n){t=null,n.alternate!==null&&(t=n.alternate.memoizedState.cache),n=n.memoizedState.cache,n!==t&&(n.refCount++,t!=null&&$o(t))}function Ma(t,n,a,o){if(n.subtreeFlags&10256)for(n=n.child;n!==null;)y0(t,n,a,o),n=n.sibling}function y0(t,n,a,o){var u=n.flags;switch(n.tag){case 0:case 11:case 15:Ma(t,n,a,o),u&2048&&dl(9,n);break;case 1:Ma(t,n,a,o);break;case 3:Ma(t,n,a,o),u&2048&&(t=null,n.alternate!==null&&(t=n.alternate.memoizedState.cache),n=n.memoizedState.cache,n!==t&&(n.refCount++,t!=null&&$o(t)));break;case 12:if(u&2048){Ma(t,n,a,o),t=n.stateNode;try{var d=n.memoizedProps,S=d.id,C=d.onPostCommit;typeof C=="function"&&C(S,n.alternate===null?"mount":"update",t.passiveEffectDuration,-0)}catch(G){ln(n,n.return,G)}}else Ma(t,n,a,o);break;case 31:Ma(t,n,a,o);break;case 13:Ma(t,n,a,o);break;case 23:break;case 22:d=n.stateNode,S=n.alternate,n.memoizedState!==null?d._visibility&2?Ma(t,n,a,o):pl(t,n):d._visibility&2?Ma(t,n,a,o):(d._visibility|=2,io(t,n,a,o,(n.subtreeFlags&10256)!==0||!1)),u&2048&&gd(S,n);break;case 24:Ma(t,n,a,o),u&2048&&vd(n.alternate,n);break;default:Ma(t,n,a,o)}}function io(t,n,a,o,u){for(u=u&&((n.subtreeFlags&10256)!==0||!1),n=n.child;n!==null;){var d=t,S=n,C=a,G=o,he=S.flags;switch(S.tag){case 0:case 11:case 15:io(d,S,C,G,u),dl(8,S);break;case 23:break;case 22:var be=S.stateNode;S.memoizedState!==null?be._visibility&2?io(d,S,C,G,u):pl(d,S):(be._visibility|=2,io(d,S,C,G,u)),u&&he&2048&&gd(S.alternate,S);break;case 24:io(d,S,C,G,u),u&&he&2048&&vd(S.alternate,S);break;default:io(d,S,C,G,u)}n=n.sibling}}function pl(t,n){if(n.subtreeFlags&10256)for(n=n.child;n!==null;){var a=t,o=n,u=o.flags;switch(o.tag){case 22:pl(a,o),u&2048&&gd(o.alternate,o);break;case 24:pl(a,o),u&2048&&vd(o.alternate,o);break;default:pl(a,o)}n=n.sibling}}var ml=8192;function ao(t,n,a){if(t.subtreeFlags&ml)for(t=t.child;t!==null;)M0(t,n,a),t=t.sibling}function M0(t,n,a){switch(t.tag){case 26:ao(t,n,a),t.flags&ml&&t.memoizedState!==null&&Wy(a,ya,t.memoizedState,t.memoizedProps);break;case 5:ao(t,n,a);break;case 3:case 4:var o=ya;ya=Wc(t.stateNode.containerInfo),ao(t,n,a),ya=o;break;case 22:t.memoizedState===null&&(o=t.alternate,o!==null&&o.memoizedState!==null?(o=ml,ml=16777216,ao(t,n,a),ml=o):ao(t,n,a));break;default:ao(t,n,a)}}function b0(t){var n=t.alternate;if(n!==null&&(t=n.child,t!==null)){n.child=null;do n=t.sibling,t.sibling=null,t=n;while(t!==null)}}function gl(t){var n=t.deletions;if((t.flags&16)!==0){if(n!==null)for(var a=0;a<n.length;a++){var o=n[a];Jn=o,T0(o,t)}b0(t)}if(t.subtreeFlags&10256)for(t=t.child;t!==null;)E0(t),t=t.sibling}function E0(t){switch(t.tag){case 0:case 11:case 15:gl(t),t.flags&2048&&zr(9,t,t.return);break;case 3:gl(t);break;case 12:gl(t);break;case 22:var n=t.stateNode;t.memoizedState!==null&&n._visibility&2&&(t.return===null||t.return.tag!==13)?(n._visibility&=-3,Nc(t)):gl(t);break;default:gl(t)}}function Nc(t){var n=t.deletions;if((t.flags&16)!==0){if(n!==null)for(var a=0;a<n.length;a++){var o=n[a];Jn=o,T0(o,t)}b0(t)}for(t=t.child;t!==null;){switch(n=t,n.tag){case 0:case 11:case 15:zr(8,n,n.return),Nc(n);break;case 22:a=n.stateNode,a._visibility&2&&(a._visibility&=-3,Nc(n));break;default:Nc(n)}t=t.sibling}}function T0(t,n){for(;Jn!==null;){var a=Jn;switch(a.tag){case 0:case 11:case 15:zr(8,a,n);break;case 23:case 22:if(a.memoizedState!==null&&a.memoizedState.cachePool!==null){var o=a.memoizedState.cachePool.pool;o!=null&&o.refCount++}break;case 24:$o(a.memoizedState.cache)}if(o=a.child,o!==null)o.return=a,Jn=o;else e:for(a=t;Jn!==null;){o=Jn;var u=o.sibling,d=o.return;if(m0(o),o===a){Jn=null;break e}if(u!==null){u.return=d,Jn=u;break e}Jn=d}}}var sy={getCacheForType:function(t){var n=ri(Hn),a=n.data.get(t);return a===void 0&&(a=t(),n.data.set(t,a)),a},cacheSignal:function(){return ri(Hn).controller.signal}},oy=typeof WeakMap=="function"?WeakMap:Map,an=0,vn=null,Pt=null,Bt=0,on=0,Vi=null,Br=!1,ro=!1,_d=!1,ur=0,Nn=0,Hr=0,Ms=0,xd=0,ki=0,so=0,vl=null,Ni=null,Sd=!1,Lc=0,A0=0,Oc=1/0,Pc=null,Gr=null,qn=0,Vr=null,oo=null,fr=0,yd=0,Md=null,R0=null,_l=0,bd=null;function Xi(){return(an&2)!==0&&Bt!==0?Bt&-Bt:z.T!==null?wd():Da()}function C0(){if(ki===0)if((Bt&536870912)===0||Vt){var t=dt;dt<<=1,(dt&3932160)===0&&(dt=262144),ki=t}else ki=536870912;return t=Hi.current,t!==null&&(t.flags|=32),ki}function Li(t,n,a){(t===vn&&(on===2||on===9)||t.cancelPendingCommit!==null)&&(lo(t,0),kr(t,Bt,ki,!1)),Je(t,a),((an&2)===0||t!==vn)&&(t===vn&&((an&2)===0&&(Ms|=a),Nn===4&&kr(t,Bt,ki,!1)),za(t))}function w0(t,n,a){if((an&6)!==0)throw Error(r(327));var o=!a&&(n&127)===0&&(n&t.expiredLanes)===0||Pe(t,n),u=o?uy(t,n):Td(t,n,!0),d=o;do{if(u===0){ro&&!o&&kr(t,n,0,!1);break}else{if(a=t.current.alternate,d&&!ly(a)){u=Td(t,n,!1),d=!1;continue}if(u===2){if(d=n,t.errorRecoveryDisabledLanes&d)var S=0;else S=t.pendingLanes&-536870913,S=S!==0?S:S&536870912?536870912:0;if(S!==0){n=S;e:{var C=t;u=vl;var G=C.current.memoizedState.isDehydrated;if(G&&(lo(C,S).flags|=256),S=Td(C,S,!1),S!==2){if(_d&&!G){C.errorRecoveryDisabledLanes|=d,Ms|=d,u=4;break e}d=Ni,Ni=u,d!==null&&(Ni===null?Ni=d:Ni.push.apply(Ni,d))}u=S}if(d=!1,u!==2)continue}}if(u===1){lo(t,0),kr(t,n,0,!0);break}e:{switch(o=t,d=u,d){case 0:case 1:throw Error(r(345));case 4:if((n&4194048)!==n)break;case 6:kr(o,n,ki,!Br);break e;case 2:Ni=null;break;case 3:case 5:break;default:throw Error(r(329))}if((n&62914560)===n&&(u=Lc+300-Ft(),10<u)){if(kr(o,n,ki,!Br),Me(o,0,!0)!==0)break e;fr=n,o.timeoutHandle=sv(D0.bind(null,o,a,Ni,Pc,Sd,n,ki,Ms,so,Br,d,"Throttled",-0,0),u);break e}D0(o,a,Ni,Pc,Sd,n,ki,Ms,so,Br,d,null,-0,0)}}break}while(!0);za(t)}function D0(t,n,a,o,u,d,S,C,G,he,be,Te,me,_e){if(t.timeoutHandle=-1,Te=n.subtreeFlags,Te&8192||(Te&16785408)===16785408){Te={stylesheets:null,count:0,imgCount:0,imgBytes:0,suspenseyImages:[],waitingForImages:!0,waitingForViewTransition:!1,unsuspend:Si},M0(n,d,Te);var tt=(d&62914560)===d?Lc-Ft():(d&4194048)===d?A0-Ft():0;if(tt=qy(Te,tt),tt!==null){fr=d,t.cancelPendingCommit=tt(z0.bind(null,t,n,d,a,o,u,S,C,G,be,Te,null,me,_e)),kr(t,d,S,!he);return}}z0(t,n,d,a,o,u,S,C,G)}function ly(t){for(var n=t;;){var a=n.tag;if((a===0||a===11||a===15)&&n.flags&16384&&(a=n.updateQueue,a!==null&&(a=a.stores,a!==null)))for(var o=0;o<a.length;o++){var u=a[o],d=u.getSnapshot;u=u.value;try{if(!zi(d(),u))return!1}catch{return!1}}if(a=n.child,n.subtreeFlags&16384&&a!==null)a.return=n,n=a;else{if(n===t)break;for(;n.sibling===null;){if(n.return===null||n.return===t)return!0;n=n.return}n.sibling.return=n.return,n=n.sibling}}return!0}function kr(t,n,a,o){n&=~xd,n&=~Ms,t.suspendedLanes|=n,t.pingedLanes&=~n,o&&(t.warmLanes|=n),o=t.expirationTimes;for(var u=n;0<u;){var d=31-Ze(u),S=1<<d;o[d]=-1,u&=~S}a!==0&&Nt(t,a,n)}function Ic(){return(an&6)===0?(xl(0),!1):!0}function Ed(){if(Pt!==null){if(on===0)var t=Pt.return;else t=Pt,er=hs=null,Hf(t),Js=null,tl=0,t=Pt;for(;t!==null;)o0(t.alternate,t),t=t.return;Pt=null}}function lo(t,n){var a=t.timeoutHandle;a!==-1&&(t.timeoutHandle=-1,Cy(a)),a=t.cancelPendingCommit,a!==null&&(t.cancelPendingCommit=null,a()),fr=0,Ed(),vn=t,Pt=a=Ja(t.current,null),Bt=n,on=0,Vi=null,Br=!1,ro=Pe(t,n),_d=!1,so=ki=xd=Ms=Hr=Nn=0,Ni=vl=null,Sd=!1,(n&8)!==0&&(n|=n&32);var o=t.entangledLanes;if(o!==0)for(t=t.entanglements,o&=n;0<o;){var u=31-Ze(o),d=1<<u;n|=t[u],o&=~d}return ur=n,ic(),a}function U0(t,n){At=null,z.H=cl,n===Qs||n===fc?(n=Ym(),on=3):n===Cf?(n=Ym(),on=4):on=n===nd?8:n!==null&&typeof n=="object"&&typeof n.then=="function"?6:1,Vi=n,Pt===null&&(Nn=1,Tc(t,aa(n,t.current)))}function N0(){var t=Hi.current;return t===null?!0:(Bt&4194048)===Bt?la===null:(Bt&62914560)===Bt||(Bt&536870912)!==0?t===la:!1}function L0(){var t=z.H;return z.H=cl,t===null?cl:t}function O0(){var t=z.A;return z.A=sy,t}function Fc(){Nn=4,Br||(Bt&4194048)!==Bt&&Hi.current!==null||(ro=!0),(Hr&134217727)===0&&(Ms&134217727)===0||vn===null||kr(vn,Bt,ki,!1)}function Td(t,n,a){var o=an;an|=2;var u=L0(),d=O0();(vn!==t||Bt!==n)&&(Pc=null,lo(t,n)),n=!1;var S=Nn;e:do try{if(on!==0&&Pt!==null){var C=Pt,G=Vi;switch(on){case 8:Ed(),S=6;break e;case 3:case 2:case 9:case 6:Hi.current===null&&(n=!0);var he=on;if(on=0,Vi=null,co(t,C,G,he),a&&ro){S=0;break e}break;default:he=on,on=0,Vi=null,co(t,C,G,he)}}cy(),S=Nn;break}catch(be){U0(t,be)}while(!0);return n&&t.shellSuspendCounter++,er=hs=null,an=o,z.H=u,z.A=d,Pt===null&&(vn=null,Bt=0,ic()),S}function cy(){for(;Pt!==null;)P0(Pt)}function uy(t,n){var a=an;an|=2;var o=L0(),u=O0();vn!==t||Bt!==n?(Pc=null,Oc=Ft()+500,lo(t,n)):ro=Pe(t,n);e:do try{if(on!==0&&Pt!==null){n=Pt;var d=Vi;t:switch(on){case 1:on=0,Vi=null,co(t,n,d,1);break;case 2:case 9:if(Wm(d)){on=0,Vi=null,I0(n);break}n=function(){on!==2&&on!==9||vn!==t||(on=7),za(t)},d.then(n,n);break e;case 3:on=7;break e;case 4:on=5;break e;case 7:Wm(d)?(on=0,Vi=null,I0(n)):(on=0,Vi=null,co(t,n,d,7));break;case 5:var S=null;switch(Pt.tag){case 26:S=Pt.memoizedState;case 5:case 27:var C=Pt;if(S?yv(S):C.stateNode.complete){on=0,Vi=null;var G=C.sibling;if(G!==null)Pt=G;else{var he=C.return;he!==null?(Pt=he,zc(he)):Pt=null}break t}}on=0,Vi=null,co(t,n,d,5);break;case 6:on=0,Vi=null,co(t,n,d,6);break;case 8:Ed(),Nn=6;break e;default:throw Error(r(462))}}fy();break}catch(be){U0(t,be)}while(!0);return er=hs=null,z.H=o,z.A=u,an=a,Pt!==null?0:(vn=null,Bt=0,ic(),Nn)}function fy(){for(;Pt!==null&&!fn();)P0(Pt)}function P0(t){var n=r0(t.alternate,t,ur);t.memoizedProps=t.pendingProps,n===null?zc(t):Pt=n}function I0(t){var n=t,a=n.alternate;switch(n.tag){case 15:case 0:n=$g(a,n,n.pendingProps,n.type,void 0,Bt);break;case 11:n=$g(a,n,n.pendingProps,n.type.render,n.ref,Bt);break;case 5:Hf(n);default:o0(a,n),n=Pt=Om(n,ur),n=r0(a,n,ur)}t.memoizedProps=t.pendingProps,n===null?zc(t):Pt=n}function co(t,n,a,o){er=hs=null,Hf(n),Js=null,tl=0;var u=n.return;try{if($S(t,u,n,a,Bt)){Nn=1,Tc(t,aa(a,t.current)),Pt=null;return}}catch(d){if(u!==null)throw Pt=u,d;Nn=1,Tc(t,aa(a,t.current)),Pt=null;return}n.flags&32768?(Vt||o===1?t=!0:ro||(Bt&536870912)!==0?t=!1:(Br=t=!0,(o===2||o===9||o===3||o===6)&&(o=Hi.current,o!==null&&o.tag===13&&(o.flags|=16384))),F0(n,t)):zc(n)}function zc(t){var n=t;do{if((n.flags&32768)!==0){F0(n,Br);return}t=n.return;var a=ny(n.alternate,n,ur);if(a!==null){Pt=a;return}if(n=n.sibling,n!==null){Pt=n;return}Pt=n=t}while(n!==null);Nn===0&&(Nn=5)}function F0(t,n){do{var a=iy(t.alternate,t);if(a!==null){a.flags&=32767,Pt=a;return}if(a=t.return,a!==null&&(a.flags|=32768,a.subtreeFlags=0,a.deletions=null),!n&&(t=t.sibling,t!==null)){Pt=t;return}Pt=t=a}while(t!==null);Nn=6,Pt=null}function z0(t,n,a,o,u,d,S,C,G){t.cancelPendingCommit=null;do Bc();while(qn!==0);if((an&6)!==0)throw Error(r(327));if(n!==null){if(n===t.current)throw Error(r(177));if(d=n.lanes|n.childLanes,d|=hf,Qt(t,a,d,S,C,G),t===vn&&(Pt=vn=null,Bt=0),oo=n,Vr=t,fr=a,yd=d,Md=u,R0=o,(n.subtreeFlags&10256)!==0||(n.flags&10256)!==0?(t.callbackNode=null,t.callbackPriority=0,my(K,function(){return k0(),null})):(t.callbackNode=null,t.callbackPriority=0),o=(n.flags&13878)!==0,(n.subtreeFlags&13878)!==0||o){o=z.T,z.T=null,u=H.p,H.p=2,S=an,an|=4;try{ay(t,n,a)}finally{an=S,H.p=u,z.T=o}}qn=1,B0(),H0(),G0()}}function B0(){if(qn===1){qn=0;var t=Vr,n=oo,a=(n.flags&13878)!==0;if((n.subtreeFlags&13878)!==0||a){a=z.T,z.T=null;var o=H.p;H.p=2;var u=an;an|=4;try{x0(n,t);var d=Fd,S=Tm(t.containerInfo),C=d.focusedElem,G=d.selectionRange;if(S!==C&&C&&C.ownerDocument&&Em(C.ownerDocument.documentElement,C)){if(G!==null&&lf(C)){var he=G.start,be=G.end;if(be===void 0&&(be=he),"selectionStart"in C)C.selectionStart=he,C.selectionEnd=Math.min(be,C.value.length);else{var Te=C.ownerDocument||document,me=Te&&Te.defaultView||window;if(me.getSelection){var _e=me.getSelection(),tt=C.textContent.length,ft=Math.min(G.start,tt),mn=G.end===void 0?ft:Math.min(G.end,tt);!_e.extend&&ft>mn&&(S=mn,mn=ft,ft=S);var $=bm(C,ft),q=bm(C,mn);if($&&q&&(_e.rangeCount!==1||_e.anchorNode!==$.node||_e.anchorOffset!==$.offset||_e.focusNode!==q.node||_e.focusOffset!==q.offset)){var de=Te.createRange();de.setStart($.node,$.offset),_e.removeAllRanges(),ft>mn?(_e.addRange(de),_e.extend(q.node,q.offset)):(de.setEnd(q.node,q.offset),_e.addRange(de))}}}}for(Te=[],_e=C;_e=_e.parentNode;)_e.nodeType===1&&Te.push({element:_e,left:_e.scrollLeft,top:_e.scrollTop});for(typeof C.focus=="function"&&C.focus(),C=0;C<Te.length;C++){var Ee=Te[C];Ee.element.scrollLeft=Ee.left,Ee.element.scrollTop=Ee.top}}Qc=!!Id,Fd=Id=null}finally{an=u,H.p=o,z.T=a}}t.current=n,qn=2}}function H0(){if(qn===2){qn=0;var t=Vr,n=oo,a=(n.flags&8772)!==0;if((n.subtreeFlags&8772)!==0||a){a=z.T,z.T=null;var o=H.p;H.p=2;var u=an;an|=4;try{p0(t,n.alternate,n)}finally{an=u,H.p=o,z.T=a}}qn=3}}function G0(){if(qn===4||qn===3){qn=0,Z();var t=Vr,n=oo,a=fr,o=R0;(n.subtreeFlags&10256)!==0||(n.flags&10256)!==0?qn=5:(qn=0,oo=Vr=null,V0(t,t.pendingLanes));var u=t.pendingLanes;if(u===0&&(Gr=null),os(a),n=n.stateNode,Se&&typeof Se.onCommitFiberRoot=="function")try{Se.onCommitFiberRoot(pe,n,void 0,(n.current.flags&128)===128)}catch{}if(o!==null){n=z.T,u=H.p,H.p=2,z.T=null;try{for(var d=t.onRecoverableError,S=0;S<o.length;S++){var C=o[S];d(C.value,{componentStack:C.stack})}}finally{z.T=n,H.p=u}}(fr&3)!==0&&Bc(),za(t),u=t.pendingLanes,(a&261930)!==0&&(u&42)!==0?t===bd?_l++:(_l=0,bd=t):_l=0,xl(0)}}function V0(t,n){(t.pooledCacheLanes&=n)===0&&(n=t.pooledCache,n!=null&&(t.pooledCache=null,$o(n)))}function Bc(){return B0(),H0(),G0(),k0()}function k0(){if(qn!==5)return!1;var t=Vr,n=yd;yd=0;var a=os(fr),o=z.T,u=H.p;try{H.p=32>a?32:a,z.T=null,a=Md,Md=null;var d=Vr,S=fr;if(qn=0,oo=Vr=null,fr=0,(an&6)!==0)throw Error(r(331));var C=an;if(an|=4,E0(d.current),y0(d,d.current,S,a),an=C,xl(0,!1),Se&&typeof Se.onPostCommitFiberRoot=="function")try{Se.onPostCommitFiberRoot(pe,d)}catch{}return!0}finally{H.p=u,z.T=o,V0(t,n)}}function X0(t,n,a){n=aa(a,n),n=td(t.stateNode,n,2),t=Pr(t,n,2),t!==null&&(Je(t,2),za(t))}function ln(t,n,a){if(t.tag===3)X0(t,t,a);else for(;n!==null;){if(n.tag===3){X0(n,t,a);break}else if(n.tag===1){var o=n.stateNode;if(typeof n.type.getDerivedStateFromError=="function"||typeof o.componentDidCatch=="function"&&(Gr===null||!Gr.has(o))){t=aa(a,t),a=Wg(2),o=Pr(n,a,2),o!==null&&(qg(a,o,n,t),Je(o,2),za(o));break}}n=n.return}}function Ad(t,n,a){var o=t.pingCache;if(o===null){o=t.pingCache=new oy;var u=new Set;o.set(n,u)}else u=o.get(n),u===void 0&&(u=new Set,o.set(n,u));u.has(a)||(_d=!0,u.add(a),t=dy.bind(null,t,n,a),n.then(t,t))}function dy(t,n,a){var o=t.pingCache;o!==null&&o.delete(n),t.pingedLanes|=t.suspendedLanes&a,t.warmLanes&=~a,vn===t&&(Bt&a)===a&&(Nn===4||Nn===3&&(Bt&62914560)===Bt&&300>Ft()-Lc?(an&2)===0&&lo(t,0):xd|=a,so===Bt&&(so=0)),za(t)}function W0(t,n){n===0&&(n=Re()),t=us(t,n),t!==null&&(Je(t,n),za(t))}function hy(t){var n=t.memoizedState,a=0;n!==null&&(a=n.retryLane),W0(t,a)}function py(t,n){var a=0;switch(t.tag){case 31:case 13:var o=t.stateNode,u=t.memoizedState;u!==null&&(a=u.retryLane);break;case 19:o=t.stateNode;break;case 22:o=t.stateNode._retryCache;break;default:throw Error(r(314))}o!==null&&o.delete(n),W0(t,a)}function my(t,n){return _n(t,n)}var Hc=null,uo=null,Rd=!1,Gc=!1,Cd=!1,Xr=0;function za(t){t!==uo&&t.next===null&&(uo===null?Hc=uo=t:uo=uo.next=t),Gc=!0,Rd||(Rd=!0,vy())}function xl(t,n){if(!Cd&&Gc){Cd=!0;do for(var a=!1,o=Hc;o!==null;){if(t!==0){var u=o.pendingLanes;if(u===0)var d=0;else{var S=o.suspendedLanes,C=o.pingedLanes;d=(1<<31-Ze(42|t)+1)-1,d&=u&~(S&~C),d=d&201326741?d&201326741|1:d?d|2:0}d!==0&&(a=!0,Z0(o,d))}else d=Bt,d=Me(o,o===vn?d:0,o.cancelPendingCommit!==null||o.timeoutHandle!==-1),(d&3)===0||Pe(o,d)||(a=!0,Z0(o,d));o=o.next}while(a);Cd=!1}}function gy(){q0()}function q0(){Gc=Rd=!1;var t=0;Xr!==0&&Ry()&&(t=Xr);for(var n=Ft(),a=null,o=Hc;o!==null;){var u=o.next,d=Y0(o,n);d===0?(o.next=null,a===null?Hc=u:a.next=u,u===null&&(uo=a)):(a=o,(t!==0||(d&3)!==0)&&(Gc=!0)),o=u}qn!==0&&qn!==5||xl(t),Xr!==0&&(Xr=0)}function Y0(t,n){for(var a=t.suspendedLanes,o=t.pingedLanes,u=t.expirationTimes,d=t.pendingLanes&-62914561;0<d;){var S=31-Ze(d),C=1<<S,G=u[S];G===-1?((C&a)===0||(C&o)!==0)&&(u[S]=Ve(C,n)):G<=n&&(t.expiredLanes|=C),d&=~C}if(n=vn,a=Bt,a=Me(t,t===n?a:0,t.cancelPendingCommit!==null||t.timeoutHandle!==-1),o=t.callbackNode,a===0||t===n&&(on===2||on===9)||t.cancelPendingCommit!==null)return o!==null&&o!==null&&Xt(o),t.callbackNode=null,t.callbackPriority=0;if((a&3)===0||Pe(t,a)){if(n=a&-a,n===t.callbackPriority)return n;switch(o!==null&&Xt(o),os(a)){case 2:case 8:a=b;break;case 32:a=K;break;case 268435456:a=ve;break;default:a=K}return o=j0.bind(null,t),a=_n(a,o),t.callbackPriority=n,t.callbackNode=a,n}return o!==null&&o!==null&&Xt(o),t.callbackPriority=2,t.callbackNode=null,2}function j0(t,n){if(qn!==0&&qn!==5)return t.callbackNode=null,t.callbackPriority=0,null;var a=t.callbackNode;if(Bc()&&t.callbackNode!==a)return null;var o=Bt;return o=Me(t,t===vn?o:0,t.cancelPendingCommit!==null||t.timeoutHandle!==-1),o===0?null:(w0(t,o,n),Y0(t,Ft()),t.callbackNode!=null&&t.callbackNode===a?j0.bind(null,t):null)}function Z0(t,n){if(Bc())return null;w0(t,n,!0)}function vy(){wy(function(){(an&6)!==0?_n(I,gy):q0()})}function wd(){if(Xr===0){var t=Zs;t===0&&(t=lt,lt<<=1,(lt&261888)===0&&(lt=256)),Xr=t}return Xr}function K0(t){return t==null||typeof t=="symbol"||typeof t=="boolean"?null:typeof t=="function"?t:Fi(""+t)}function Q0(t,n){var a=n.ownerDocument.createElement("input");return a.name=n.name,a.value=n.value,t.id&&a.setAttribute("form",t.id),n.parentNode.insertBefore(a,n),t=new FormData(t),a.parentNode.removeChild(a),t}function _y(t,n,a,o,u){if(n==="submit"&&a&&a.stateNode===u){var d=K0((u[Bn]||null).action),S=o.submitter;S&&(n=(n=S[Bn]||null)?K0(n.formAction):S.getAttribute("formAction"),n!==null&&(d=n,S=null));var C=new An("action","action",null,o,u);t.push({event:C,listeners:[{instance:null,listener:function(){if(o.defaultPrevented){if(Xr!==0){var G=S?Q0(u,S):new FormData(u);Zf(a,{pending:!0,data:G,method:u.method,action:d},null,G)}}else typeof d=="function"&&(C.preventDefault(),G=S?Q0(u,S):new FormData(u),Zf(a,{pending:!0,data:G,method:u.method,action:d},d,G))},currentTarget:u}]})}}for(var Dd=0;Dd<df.length;Dd++){var Ud=df[Dd],xy=Ud.toLowerCase(),Sy=Ud[0].toUpperCase()+Ud.slice(1);Sa(xy,"on"+Sy)}Sa(Cm,"onAnimationEnd"),Sa(wm,"onAnimationIteration"),Sa(Dm,"onAnimationStart"),Sa("dblclick","onDoubleClick"),Sa("focusin","onFocus"),Sa("focusout","onBlur"),Sa(IS,"onTransitionRun"),Sa(FS,"onTransitionStart"),Sa(zS,"onTransitionCancel"),Sa(Um,"onTransitionEnd"),X("onMouseEnter",["mouseout","mouseover"]),X("onMouseLeave",["mouseout","mouseover"]),X("onPointerEnter",["pointerout","pointerover"]),X("onPointerLeave",["pointerout","pointerover"]),A("onChange","change click focusin focusout input keydown keyup selectionchange".split(" ")),A("onSelect","focusout contextmenu dragend focusin keydown keyup mousedown mouseup selectionchange".split(" ")),A("onBeforeInput",["compositionend","keypress","textInput","paste"]),A("onCompositionEnd","compositionend focusout keydown keypress keyup mousedown".split(" ")),A("onCompositionStart","compositionstart focusout keydown keypress keyup mousedown".split(" ")),A("onCompositionUpdate","compositionupdate focusout keydown keypress keyup mousedown".split(" "));var Sl="abort canplay canplaythrough durationchange emptied encrypted ended error loadeddata loadedmetadata loadstart pause play playing progress ratechange resize seeked seeking stalled suspend timeupdate volumechange waiting".split(" "),yy=new Set("beforetoggle cancel close invalid load scroll scrollend toggle".split(" ").concat(Sl));function J0(t,n){n=(n&4)!==0;for(var a=0;a<t.length;a++){var o=t[a],u=o.event;o=o.listeners;e:{var d=void 0;if(n)for(var S=o.length-1;0<=S;S--){var C=o[S],G=C.instance,he=C.currentTarget;if(C=C.listener,G!==d&&u.isPropagationStopped())break e;d=C,u.currentTarget=he;try{d(u)}catch(be){nc(be)}u.currentTarget=null,d=G}else for(S=0;S<o.length;S++){if(C=o[S],G=C.instance,he=C.currentTarget,C=C.listener,G!==d&&u.isPropagationStopped())break e;d=C,u.currentTarget=he;try{d(u)}catch(be){nc(be)}u.currentTarget=null,d=G}}}}function It(t,n){var a=n[Wt];a===void 0&&(a=n[Wt]=new Set);var o=t+"__bubble";a.has(o)||($0(n,t,2,!1),a.add(o))}function Nd(t,n,a){var o=0;n&&(o|=4),$0(a,t,o,n)}var Vc="_reactListening"+Math.random().toString(36).slice(2);function Ld(t){if(!t[Vc]){t[Vc]=!0,Na.forEach(function(a){a!=="selectionchange"&&(yy.has(a)||Nd(a,!1,t),Nd(a,!0,t))});var n=t.nodeType===9?t:t.ownerDocument;n===null||n[Vc]||(n[Vc]=!0,Nd("selectionchange",!1,n))}}function $0(t,n,a,o){switch(Cv(n)){case 2:var u=Zy;break;case 8:u=Ky;break;default:u=jd}a=u.bind(null,n,a,t),u=void 0,!Qe||n!=="touchstart"&&n!=="touchmove"&&n!=="wheel"||(u=!0),o?u!==void 0?t.addEventListener(n,a,{capture:!0,passive:u}):t.addEventListener(n,a,!0):u!==void 0?t.addEventListener(n,a,{passive:u}):t.addEventListener(n,a,!1)}function Od(t,n,a,o,u){var d=o;if((n&1)===0&&(n&2)===0&&o!==null)e:for(;;){if(o===null)return;var S=o.tag;if(S===3||S===4){var C=o.stateNode.containerInfo;if(C===u)break;if(S===4)for(S=o.return;S!==null;){var G=S.tag;if((G===3||G===4)&&S.stateNode.containerInfo===u)return;S=S.return}for(;C!==null;){if(S=Pi(C),S===null)return;if(G=S.tag,G===5||G===6||G===26||G===27){o=d=S;continue e}C=C.parentNode}}o=o.return}te(function(){var he=d,be=Bs(a),Te=[];e:{var me=Nm.get(t);if(me!==void 0){var _e=An,tt=t;switch(t){case"keypress":if(Yt(a)===0)break e;case"keydown":case"keyup":_e=pS;break;case"focusin":tt="focus",_e=ta;break;case"focusout":tt="blur",_e=ta;break;case"beforeblur":case"afterblur":_e=ta;break;case"click":if(a.button===2)break e;case"auxclick":case"dblclick":case"mousedown":case"mousemove":case"mouseup":case"mouseout":case"mouseover":case"contextmenu":_e=Oa;break;case"drag":case"dragend":case"dragenter":case"dragexit":case"dragleave":case"dragover":case"dragstart":case"drop":_e=nn;break;case"touchcancel":case"touchend":case"touchmove":case"touchstart":_e=vS;break;case Cm:case wm:case Dm:_e=xa;break;case Um:_e=xS;break;case"scroll":case"scrollend":_e=va;break;case"wheel":_e=yS;break;case"copy":case"cut":case"paste":_e=Qa;break;case"gotpointercapture":case"lostpointercapture":case"pointercancel":case"pointerdown":case"pointermove":case"pointerout":case"pointerover":case"pointerup":_e=cm;break;case"toggle":case"beforetoggle":_e=bS}var ft=(n&4)!==0,mn=!ft&&(t==="scroll"||t==="scrollend"),$=ft?me!==null?me+"Capture":null:me;ft=[];for(var q=he,de;q!==null;){var Ee=q;if(de=Ee.stateNode,Ee=Ee.tag,Ee!==5&&Ee!==26&&Ee!==27||de===null||$===null||(Ee=De(q,$),Ee!=null&&ft.push(yl(q,Ee,de))),mn)break;q=q.return}0<ft.length&&(me=new _e(me,tt,null,a,be),Te.push({event:me,listeners:ft}))}}if((n&7)===0){e:{if(me=t==="mouseover"||t==="pointerover",_e=t==="mouseout"||t==="pointerout",me&&a!==zs&&(tt=a.relatedTarget||a.fromElement)&&(Pi(tt)||tt[Kn]))break e;if((_e||me)&&(me=be.window===be?be:(me=be.ownerDocument)?me.defaultView||me.parentWindow:window,_e?(tt=a.relatedTarget||a.toElement,_e=he,tt=tt?Pi(tt):null,tt!==null&&(mn=c(tt),ft=tt.tag,tt!==mn||ft!==5&&ft!==27&&ft!==6)&&(tt=null)):(_e=null,tt=he),_e!==tt)){if(ft=Oa,Ee="onMouseLeave",$="onMouseEnter",q="mouse",(t==="pointerout"||t==="pointerover")&&(ft=cm,Ee="onPointerLeave",$="onPointerEnter",q="pointer"),mn=_e==null?me:ma(_e),de=tt==null?me:ma(tt),me=new ft(Ee,q+"leave",_e,a,be),me.target=mn,me.relatedTarget=de,Ee=null,Pi(be)===he&&(ft=new ft($,q+"enter",tt,a,be),ft.target=de,ft.relatedTarget=mn,Ee=ft),mn=Ee,_e&&tt)t:{for(ft=My,$=_e,q=tt,de=0,Ee=$;Ee;Ee=ft(Ee))de++;Ee=0;for(var ct=q;ct;ct=ft(ct))Ee++;for(;0<de-Ee;)$=ft($),de--;for(;0<Ee-de;)q=ft(q),Ee--;for(;de--;){if($===q||q!==null&&$===q.alternate){ft=$;break t}$=ft($),q=ft(q)}ft=null}else ft=null;_e!==null&&ev(Te,me,_e,ft,!1),tt!==null&&mn!==null&&ev(Te,mn,tt,ft,!0)}}e:{if(me=he?ma(he):window,_e=me.nodeName&&me.nodeName.toLowerCase(),_e==="select"||_e==="input"&&me.type==="file")var Jt=vm;else if(mm(me))if(_m)Jt=LS;else{Jt=US;var ot=DS}else _e=me.nodeName,!_e||_e.toLowerCase()!=="input"||me.type!=="checkbox"&&me.type!=="radio"?he&&Ai(he.elementType)&&(Jt=vm):Jt=NS;if(Jt&&(Jt=Jt(t,he))){gm(Te,Jt,a,be);break e}ot&&ot(t,me,he),t==="focusout"&&he&&me.type==="number"&&he.memoizedProps.value!=null&&wn(me,"number",me.value)}switch(ot=he?ma(he):window,t){case"focusin":(mm(ot)||ot.contentEditable==="true")&&(Gs=ot,cf=he,Ko=null);break;case"focusout":Ko=cf=Gs=null;break;case"mousedown":uf=!0;break;case"contextmenu":case"mouseup":case"dragend":uf=!1,Am(Te,a,be);break;case"selectionchange":if(PS)break;case"keydown":case"keyup":Am(Te,a,be)}var Ct;if(rf)e:{switch(t){case"compositionstart":var Ht="onCompositionStart";break e;case"compositionend":Ht="onCompositionEnd";break e;case"compositionupdate":Ht="onCompositionUpdate";break e}Ht=void 0}else Hs?hm(t,a)&&(Ht="onCompositionEnd"):t==="keydown"&&a.keyCode===229&&(Ht="onCompositionStart");Ht&&(um&&a.locale!=="ko"&&(Hs||Ht!=="onCompositionStart"?Ht==="onCompositionEnd"&&Hs&&(Ct=Ot()):(Le=be,st="value"in Le?Le.value:Le.textContent,Hs=!0)),ot=kc(he,Ht),0<ot.length&&(Ht=new Ci(Ht,t,null,a,be),Te.push({event:Ht,listeners:ot}),Ct?Ht.data=Ct:(Ct=pm(a),Ct!==null&&(Ht.data=Ct)))),(Ct=TS?AS(t,a):RS(t,a))&&(Ht=kc(he,"onBeforeInput"),0<Ht.length&&(ot=new Ci("onBeforeInput","beforeinput",null,a,be),Te.push({event:ot,listeners:Ht}),ot.data=Ct)),_y(Te,t,he,a,be)}J0(Te,n)})}function yl(t,n,a){return{instance:t,listener:n,currentTarget:a}}function kc(t,n){for(var a=n+"Capture",o=[];t!==null;){var u=t,d=u.stateNode;if(u=u.tag,u!==5&&u!==26&&u!==27||d===null||(u=De(t,a),u!=null&&o.unshift(yl(t,u,d)),u=De(t,n),u!=null&&o.push(yl(t,u,d))),t.tag===3)return o;t=t.return}return[]}function My(t){if(t===null)return null;do t=t.return;while(t&&t.tag!==5&&t.tag!==27);return t||null}function ev(t,n,a,o,u){for(var d=n._reactName,S=[];a!==null&&a!==o;){var C=a,G=C.alternate,he=C.stateNode;if(C=C.tag,G!==null&&G===o)break;C!==5&&C!==26&&C!==27||he===null||(G=he,u?(he=De(a,d),he!=null&&S.unshift(yl(a,he,G))):u||(he=De(a,d),he!=null&&S.push(yl(a,he,G)))),a=a.return}S.length!==0&&t.push({event:n,listeners:S})}var by=/\r\n?/g,Ey=/\u0000|\uFFFD/g;function tv(t){return(typeof t=="string"?t:""+t).replace(by,`
`).replace(Ey,"")}function nv(t,n){return n=tv(n),tv(t)===n}function pn(t,n,a,o,u,d){switch(a){case"children":typeof o=="string"?n==="body"||n==="textarea"&&o===""||ni(t,o):(typeof o=="number"||typeof o=="bigint")&&n!=="body"&&ni(t,""+o);break;case"className":Be(t,"class",o);break;case"tabIndex":Be(t,"tabindex",o);break;case"dir":case"role":case"viewBox":case"width":case"height":Be(t,a,o);break;case"style":gn(t,o,d);break;case"data":if(n!=="object"){Be(t,"data",o);break}case"src":case"href":if(o===""&&(n!=="a"||a!=="href")){t.removeAttribute(a);break}if(o==null||typeof o=="function"||typeof o=="symbol"||typeof o=="boolean"){t.removeAttribute(a);break}o=Fi(""+o),t.setAttribute(a,o);break;case"action":case"formAction":if(typeof o=="function"){t.setAttribute(a,"javascript:throw new Error('A React form was unexpectedly submitted. If you called form.submit() manually, consider using form.requestSubmit() instead. If you\\'re trying to use event.stopPropagation() in a submit event handler, consider also calling event.preventDefault().')");break}else typeof d=="function"&&(a==="formAction"?(n!=="input"&&pn(t,n,"name",u.name,u,null),pn(t,n,"formEncType",u.formEncType,u,null),pn(t,n,"formMethod",u.formMethod,u,null),pn(t,n,"formTarget",u.formTarget,u,null)):(pn(t,n,"encType",u.encType,u,null),pn(t,n,"method",u.method,u,null),pn(t,n,"target",u.target,u,null)));if(o==null||typeof o=="symbol"||typeof o=="boolean"){t.removeAttribute(a);break}o=Fi(""+o),t.setAttribute(a,o);break;case"onClick":o!=null&&(t.onclick=Si);break;case"onScroll":o!=null&&It("scroll",t);break;case"onScrollEnd":o!=null&&It("scrollend",t);break;case"dangerouslySetInnerHTML":if(o!=null){if(typeof o!="object"||!("__html"in o))throw Error(r(61));if(a=o.__html,a!=null){if(u.children!=null)throw Error(r(60));t.innerHTML=a}}break;case"multiple":t.multiple=o&&typeof o!="function"&&typeof o!="symbol";break;case"muted":t.muted=o&&typeof o!="function"&&typeof o!="symbol";break;case"suppressContentEditableWarning":case"suppressHydrationWarning":case"defaultValue":case"defaultChecked":case"innerHTML":case"ref":break;case"autoFocus":break;case"xlinkHref":if(o==null||typeof o=="function"||typeof o=="boolean"||typeof o=="symbol"){t.removeAttribute("xlink:href");break}a=Fi(""+o),t.setAttributeNS("http://www.w3.org/1999/xlink","xlink:href",a);break;case"contentEditable":case"spellCheck":case"draggable":case"value":case"autoReverse":case"externalResourcesRequired":case"focusable":case"preserveAlpha":o!=null&&typeof o!="function"&&typeof o!="symbol"?t.setAttribute(a,""+o):t.removeAttribute(a);break;case"inert":case"allowFullScreen":case"async":case"autoPlay":case"controls":case"default":case"defer":case"disabled":case"disablePictureInPicture":case"disableRemotePlayback":case"formNoValidate":case"hidden":case"loop":case"noModule":case"noValidate":case"open":case"playsInline":case"readOnly":case"required":case"reversed":case"scoped":case"seamless":case"itemScope":o&&typeof o!="function"&&typeof o!="symbol"?t.setAttribute(a,""):t.removeAttribute(a);break;case"capture":case"download":o===!0?t.setAttribute(a,""):o!==!1&&o!=null&&typeof o!="function"&&typeof o!="symbol"?t.setAttribute(a,o):t.removeAttribute(a);break;case"cols":case"rows":case"size":case"span":o!=null&&typeof o!="function"&&typeof o!="symbol"&&!isNaN(o)&&1<=o?t.setAttribute(a,o):t.removeAttribute(a);break;case"rowSpan":case"start":o==null||typeof o=="function"||typeof o=="symbol"||isNaN(o)?t.removeAttribute(a):t.setAttribute(a,o);break;case"popover":It("beforetoggle",t),It("toggle",t),We(t,"popover",o);break;case"xlinkActuate":qe(t,"http://www.w3.org/1999/xlink","xlink:actuate",o);break;case"xlinkArcrole":qe(t,"http://www.w3.org/1999/xlink","xlink:arcrole",o);break;case"xlinkRole":qe(t,"http://www.w3.org/1999/xlink","xlink:role",o);break;case"xlinkShow":qe(t,"http://www.w3.org/1999/xlink","xlink:show",o);break;case"xlinkTitle":qe(t,"http://www.w3.org/1999/xlink","xlink:title",o);break;case"xlinkType":qe(t,"http://www.w3.org/1999/xlink","xlink:type",o);break;case"xmlBase":qe(t,"http://www.w3.org/XML/1998/namespace","xml:base",o);break;case"xmlLang":qe(t,"http://www.w3.org/XML/1998/namespace","xml:lang",o);break;case"xmlSpace":qe(t,"http://www.w3.org/XML/1998/namespace","xml:space",o);break;case"is":We(t,"is",o);break;case"innerText":case"textContent":break;default:(!(2<a.length)||a[0]!=="o"&&a[0]!=="O"||a[1]!=="n"&&a[1]!=="N")&&(a=en.get(a)||a,We(t,a,o))}}function Pd(t,n,a,o,u,d){switch(a){case"style":gn(t,o,d);break;case"dangerouslySetInnerHTML":if(o!=null){if(typeof o!="object"||!("__html"in o))throw Error(r(61));if(a=o.__html,a!=null){if(u.children!=null)throw Error(r(60));t.innerHTML=a}}break;case"children":typeof o=="string"?ni(t,o):(typeof o=="number"||typeof o=="bigint")&&ni(t,""+o);break;case"onScroll":o!=null&&It("scroll",t);break;case"onScrollEnd":o!=null&&It("scrollend",t);break;case"onClick":o!=null&&(t.onclick=Si);break;case"suppressContentEditableWarning":case"suppressHydrationWarning":case"innerHTML":case"ref":break;case"innerText":case"textContent":break;default:if(!xi.hasOwnProperty(a))e:{if(a[0]==="o"&&a[1]==="n"&&(u=a.endsWith("Capture"),n=a.slice(2,u?a.length-7:void 0),d=t[Bn]||null,d=d!=null?d[a]:null,typeof d=="function"&&t.removeEventListener(n,d,u),typeof o=="function")){typeof d!="function"&&d!==null&&(a in t?t[a]=null:t.hasAttribute(a)&&t.removeAttribute(a)),t.addEventListener(n,o,u);break e}a in t?t[a]=o:o===!0?t.setAttribute(a,""):We(t,a,o)}}}function oi(t,n,a){switch(n){case"div":case"span":case"svg":case"path":case"a":case"g":case"p":case"li":break;case"img":It("error",t),It("load",t);var o=!1,u=!1,d;for(d in a)if(a.hasOwnProperty(d)){var S=a[d];if(S!=null)switch(d){case"src":o=!0;break;case"srcSet":u=!0;break;case"children":case"dangerouslySetInnerHTML":throw Error(r(137,n));default:pn(t,n,d,S,a,null)}}u&&pn(t,n,"srcSet",a.srcSet,a,null),o&&pn(t,n,"src",a.src,a,null);return;case"input":It("invalid",t);var C=d=S=u=null,G=null,he=null;for(o in a)if(a.hasOwnProperty(o)){var be=a[o];if(be!=null)switch(o){case"name":u=be;break;case"type":S=be;break;case"checked":G=be;break;case"defaultChecked":he=be;break;case"value":d=be;break;case"defaultValue":C=be;break;case"children":case"dangerouslySetInnerHTML":if(be!=null)throw Error(r(137,n));break;default:pn(t,n,o,be,a,null)}}Ke(t,d,C,G,he,S,u,!1);return;case"select":It("invalid",t),o=S=d=null;for(u in a)if(a.hasOwnProperty(u)&&(C=a[u],C!=null))switch(u){case"value":d=C;break;case"defaultValue":S=C;break;case"multiple":o=C;default:pn(t,n,u,C,a,null)}n=d,a=S,t.multiple=!!o,n!=null?Et(t,!!o,n,!1):a!=null&&Et(t,!!o,a,!0);return;case"textarea":It("invalid",t),d=u=o=null;for(S in a)if(a.hasOwnProperty(S)&&(C=a[S],C!=null))switch(S){case"value":o=C;break;case"defaultValue":u=C;break;case"children":d=C;break;case"dangerouslySetInnerHTML":if(C!=null)throw Error(r(91));break;default:pn(t,n,S,C,a,null)}ci(t,o,u,d);return;case"option":for(G in a)if(a.hasOwnProperty(G)&&(o=a[G],o!=null))switch(G){case"selected":t.selected=o&&typeof o!="function"&&typeof o!="symbol";break;default:pn(t,n,G,o,a,null)}return;case"dialog":It("beforetoggle",t),It("toggle",t),It("cancel",t),It("close",t);break;case"iframe":case"object":It("load",t);break;case"video":case"audio":for(o=0;o<Sl.length;o++)It(Sl[o],t);break;case"image":It("error",t),It("load",t);break;case"details":It("toggle",t);break;case"embed":case"source":case"link":It("error",t),It("load",t);case"area":case"base":case"br":case"col":case"hr":case"keygen":case"meta":case"param":case"track":case"wbr":case"menuitem":for(he in a)if(a.hasOwnProperty(he)&&(o=a[he],o!=null))switch(he){case"children":case"dangerouslySetInnerHTML":throw Error(r(137,n));default:pn(t,n,he,o,a,null)}return;default:if(Ai(n)){for(be in a)a.hasOwnProperty(be)&&(o=a[be],o!==void 0&&Pd(t,n,be,o,a,void 0));return}}for(C in a)a.hasOwnProperty(C)&&(o=a[C],o!=null&&pn(t,n,C,o,a,null))}function Ty(t,n,a,o){switch(n){case"div":case"span":case"svg":case"path":case"a":case"g":case"p":case"li":break;case"input":var u=null,d=null,S=null,C=null,G=null,he=null,be=null;for(_e in a){var Te=a[_e];if(a.hasOwnProperty(_e)&&Te!=null)switch(_e){case"checked":break;case"value":break;case"defaultValue":G=Te;default:o.hasOwnProperty(_e)||pn(t,n,_e,null,o,Te)}}for(var me in o){var _e=o[me];if(Te=a[me],o.hasOwnProperty(me)&&(_e!=null||Te!=null))switch(me){case"type":d=_e;break;case"name":u=_e;break;case"checked":he=_e;break;case"defaultChecked":be=_e;break;case"value":S=_e;break;case"defaultValue":C=_e;break;case"children":case"dangerouslySetInnerHTML":if(_e!=null)throw Error(r(137,n));break;default:_e!==Te&&pn(t,n,me,_e,o,Te)}}Tn(t,S,C,G,he,be,d,u);return;case"select":_e=S=C=me=null;for(d in a)if(G=a[d],a.hasOwnProperty(d)&&G!=null)switch(d){case"value":break;case"multiple":_e=G;default:o.hasOwnProperty(d)||pn(t,n,d,null,o,G)}for(u in o)if(d=o[u],G=a[u],o.hasOwnProperty(u)&&(d!=null||G!=null))switch(u){case"value":me=d;break;case"defaultValue":C=d;break;case"multiple":S=d;default:d!==G&&pn(t,n,u,d,o,G)}n=C,a=S,o=_e,me!=null?Et(t,!!a,me,!1):!!o!=!!a&&(n!=null?Et(t,!!a,n,!0):Et(t,!!a,a?[]:"",!1));return;case"textarea":_e=me=null;for(C in a)if(u=a[C],a.hasOwnProperty(C)&&u!=null&&!o.hasOwnProperty(C))switch(C){case"value":break;case"children":break;default:pn(t,n,C,null,o,u)}for(S in o)if(u=o[S],d=a[S],o.hasOwnProperty(S)&&(u!=null||d!=null))switch(S){case"value":me=u;break;case"defaultValue":_e=u;break;case"children":break;case"dangerouslySetInnerHTML":if(u!=null)throw Error(r(91));break;default:u!==d&&pn(t,n,S,u,o,d)}Qn(t,me,_e);return;case"option":for(var tt in a)if(me=a[tt],a.hasOwnProperty(tt)&&me!=null&&!o.hasOwnProperty(tt))switch(tt){case"selected":t.selected=!1;break;default:pn(t,n,tt,null,o,me)}for(G in o)if(me=o[G],_e=a[G],o.hasOwnProperty(G)&&me!==_e&&(me!=null||_e!=null))switch(G){case"selected":t.selected=me&&typeof me!="function"&&typeof me!="symbol";break;default:pn(t,n,G,me,o,_e)}return;case"img":case"link":case"area":case"base":case"br":case"col":case"embed":case"hr":case"keygen":case"meta":case"param":case"source":case"track":case"wbr":case"menuitem":for(var ft in a)me=a[ft],a.hasOwnProperty(ft)&&me!=null&&!o.hasOwnProperty(ft)&&pn(t,n,ft,null,o,me);for(he in o)if(me=o[he],_e=a[he],o.hasOwnProperty(he)&&me!==_e&&(me!=null||_e!=null))switch(he){case"children":case"dangerouslySetInnerHTML":if(me!=null)throw Error(r(137,n));break;default:pn(t,n,he,me,o,_e)}return;default:if(Ai(n)){for(var mn in a)me=a[mn],a.hasOwnProperty(mn)&&me!==void 0&&!o.hasOwnProperty(mn)&&Pd(t,n,mn,void 0,o,me);for(be in o)me=o[be],_e=a[be],!o.hasOwnProperty(be)||me===_e||me===void 0&&_e===void 0||Pd(t,n,be,me,o,_e);return}}for(var $ in a)me=a[$],a.hasOwnProperty($)&&me!=null&&!o.hasOwnProperty($)&&pn(t,n,$,null,o,me);for(Te in o)me=o[Te],_e=a[Te],!o.hasOwnProperty(Te)||me===_e||me==null&&_e==null||pn(t,n,Te,me,o,_e)}function iv(t){switch(t){case"css":case"script":case"font":case"img":case"image":case"input":case"link":return!0;default:return!1}}function Ay(){if(typeof performance.getEntriesByType=="function"){for(var t=0,n=0,a=performance.getEntriesByType("resource"),o=0;o<a.length;o++){var u=a[o],d=u.transferSize,S=u.initiatorType,C=u.duration;if(d&&C&&iv(S)){for(S=0,C=u.responseEnd,o+=1;o<a.length;o++){var G=a[o],he=G.startTime;if(he>C)break;var be=G.transferSize,Te=G.initiatorType;be&&iv(Te)&&(G=G.responseEnd,S+=be*(G<C?1:(C-he)/(G-he)))}if(--o,n+=8*(d+S)/(u.duration/1e3),t++,10<t)break}}if(0<t)return n/t/1e6}return navigator.connection&&(t=navigator.connection.downlink,typeof t=="number")?t:5}var Id=null,Fd=null;function Xc(t){return t.nodeType===9?t:t.ownerDocument}function av(t){switch(t){case"http://www.w3.org/2000/svg":return 1;case"http://www.w3.org/1998/Math/MathML":return 2;default:return 0}}function rv(t,n){if(t===0)switch(n){case"svg":return 1;case"math":return 2;default:return 0}return t===1&&n==="foreignObject"?0:t}function zd(t,n){return t==="textarea"||t==="noscript"||typeof n.children=="string"||typeof n.children=="number"||typeof n.children=="bigint"||typeof n.dangerouslySetInnerHTML=="object"&&n.dangerouslySetInnerHTML!==null&&n.dangerouslySetInnerHTML.__html!=null}var Bd=null;function Ry(){var t=window.event;return t&&t.type==="popstate"?t===Bd?!1:(Bd=t,!0):(Bd=null,!1)}var sv=typeof setTimeout=="function"?setTimeout:void 0,Cy=typeof clearTimeout=="function"?clearTimeout:void 0,ov=typeof Promise=="function"?Promise:void 0,wy=typeof queueMicrotask=="function"?queueMicrotask:typeof ov<"u"?function(t){return ov.resolve(null).then(t).catch(Dy)}:sv;function Dy(t){setTimeout(function(){throw t})}function Wr(t){return t==="head"}function lv(t,n){var a=n,o=0;do{var u=a.nextSibling;if(t.removeChild(a),u&&u.nodeType===8)if(a=u.data,a==="/$"||a==="/&"){if(o===0){t.removeChild(u),mo(n);return}o--}else if(a==="$"||a==="$?"||a==="$~"||a==="$!"||a==="&")o++;else if(a==="html")Ml(t.ownerDocument.documentElement);else if(a==="head"){a=t.ownerDocument.head,Ml(a);for(var d=a.firstChild;d;){var S=d.nextSibling,C=d.nodeName;d[qt]||C==="SCRIPT"||C==="STYLE"||C==="LINK"&&d.rel.toLowerCase()==="stylesheet"||a.removeChild(d),d=S}}else a==="body"&&Ml(t.ownerDocument.body);a=u}while(a);mo(n)}function cv(t,n){var a=t;t=0;do{var o=a.nextSibling;if(a.nodeType===1?n?(a._stashedDisplay=a.style.display,a.style.display="none"):(a.style.display=a._stashedDisplay||"",a.getAttribute("style")===""&&a.removeAttribute("style")):a.nodeType===3&&(n?(a._stashedText=a.nodeValue,a.nodeValue=""):a.nodeValue=a._stashedText||""),o&&o.nodeType===8)if(a=o.data,a==="/$"){if(t===0)break;t--}else a!=="$"&&a!=="$?"&&a!=="$~"&&a!=="$!"||t++;a=o}while(a)}function Hd(t){var n=t.firstChild;for(n&&n.nodeType===10&&(n=n.nextSibling);n;){var a=n;switch(n=n.nextSibling,a.nodeName){case"HTML":case"HEAD":case"BODY":Hd(a),Ji(a);continue;case"SCRIPT":case"STYLE":continue;case"LINK":if(a.rel.toLowerCase()==="stylesheet")continue}t.removeChild(a)}}function Uy(t,n,a,o){for(;t.nodeType===1;){var u=a;if(t.nodeName.toLowerCase()!==n.toLowerCase()){if(!o&&(t.nodeName!=="INPUT"||t.type!=="hidden"))break}else if(o){if(!t[qt])switch(n){case"meta":if(!t.hasAttribute("itemprop"))break;return t;case"link":if(d=t.getAttribute("rel"),d==="stylesheet"&&t.hasAttribute("data-precedence"))break;if(d!==u.rel||t.getAttribute("href")!==(u.href==null||u.href===""?null:u.href)||t.getAttribute("crossorigin")!==(u.crossOrigin==null?null:u.crossOrigin)||t.getAttribute("title")!==(u.title==null?null:u.title))break;return t;case"style":if(t.hasAttribute("data-precedence"))break;return t;case"script":if(d=t.getAttribute("src"),(d!==(u.src==null?null:u.src)||t.getAttribute("type")!==(u.type==null?null:u.type)||t.getAttribute("crossorigin")!==(u.crossOrigin==null?null:u.crossOrigin))&&d&&t.hasAttribute("async")&&!t.hasAttribute("itemprop"))break;return t;default:return t}}else if(n==="input"&&t.type==="hidden"){var d=u.name==null?null:""+u.name;if(u.type==="hidden"&&t.getAttribute("name")===d)return t}else return t;if(t=ca(t.nextSibling),t===null)break}return null}function Ny(t,n,a){if(n==="")return null;for(;t.nodeType!==3;)if((t.nodeType!==1||t.nodeName!=="INPUT"||t.type!=="hidden")&&!a||(t=ca(t.nextSibling),t===null))return null;return t}function uv(t,n){for(;t.nodeType!==8;)if((t.nodeType!==1||t.nodeName!=="INPUT"||t.type!=="hidden")&&!n||(t=ca(t.nextSibling),t===null))return null;return t}function Gd(t){return t.data==="$?"||t.data==="$~"}function Vd(t){return t.data==="$!"||t.data==="$?"&&t.ownerDocument.readyState!=="loading"}function Ly(t,n){var a=t.ownerDocument;if(t.data==="$~")t._reactRetry=n;else if(t.data!=="$?"||a.readyState!=="loading")n();else{var o=function(){n(),a.removeEventListener("DOMContentLoaded",o)};a.addEventListener("DOMContentLoaded",o),t._reactRetry=o}}function ca(t){for(;t!=null;t=t.nextSibling){var n=t.nodeType;if(n===1||n===3)break;if(n===8){if(n=t.data,n==="$"||n==="$!"||n==="$?"||n==="$~"||n==="&"||n==="F!"||n==="F")break;if(n==="/$"||n==="/&")return null}}return t}var kd=null;function fv(t){t=t.nextSibling;for(var n=0;t;){if(t.nodeType===8){var a=t.data;if(a==="/$"||a==="/&"){if(n===0)return ca(t.nextSibling);n--}else a!=="$"&&a!=="$!"&&a!=="$?"&&a!=="$~"&&a!=="&"||n++}t=t.nextSibling}return null}function dv(t){t=t.previousSibling;for(var n=0;t;){if(t.nodeType===8){var a=t.data;if(a==="$"||a==="$!"||a==="$?"||a==="$~"||a==="&"){if(n===0)return t;n--}else a!=="/$"&&a!=="/&"||n++}t=t.previousSibling}return null}function hv(t,n,a){switch(n=Xc(a),t){case"html":if(t=n.documentElement,!t)throw Error(r(452));return t;case"head":if(t=n.head,!t)throw Error(r(453));return t;case"body":if(t=n.body,!t)throw Error(r(454));return t;default:throw Error(r(451))}}function Ml(t){for(var n=t.attributes;n.length;)t.removeAttributeNode(n[0]);Ji(t)}var ua=new Map,pv=new Set;function Wc(t){return typeof t.getRootNode=="function"?t.getRootNode():t.nodeType===9?t:t.ownerDocument}var dr=H.d;H.d={f:Oy,r:Py,D:Iy,C:Fy,L:zy,m:By,X:Gy,S:Hy,M:Vy};function Oy(){var t=dr.f(),n=Ic();return t||n}function Py(t){var n=Ii(t);n!==null&&n.tag===5&&n.type==="form"?Ug(n):dr.r(t)}var fo=typeof document>"u"?null:document;function mv(t,n,a){var o=fo;if(o&&typeof n=="string"&&n){var u=bt(n);u='link[rel="'+t+'"][href="'+u+'"]',typeof a=="string"&&(u+='[crossorigin="'+a+'"]'),pv.has(u)||(pv.add(u),t={rel:t,crossOrigin:a,href:n},o.querySelector(u)===null&&(n=o.createElement("link"),oi(n,"link",t),sn(n),o.head.appendChild(n)))}}function Iy(t){dr.D(t),mv("dns-prefetch",t,null)}function Fy(t,n){dr.C(t,n),mv("preconnect",t,n)}function zy(t,n,a){dr.L(t,n,a);var o=fo;if(o&&t&&n){var u='link[rel="preload"][as="'+bt(n)+'"]';n==="image"&&a&&a.imageSrcSet?(u+='[imagesrcset="'+bt(a.imageSrcSet)+'"]',typeof a.imageSizes=="string"&&(u+='[imagesizes="'+bt(a.imageSizes)+'"]')):u+='[href="'+bt(t)+'"]';var d=u;switch(n){case"style":d=ho(t);break;case"script":d=po(t)}ua.has(d)||(t=_({rel:"preload",href:n==="image"&&a&&a.imageSrcSet?void 0:t,as:n},a),ua.set(d,t),o.querySelector(u)!==null||n==="style"&&o.querySelector(bl(d))||n==="script"&&o.querySelector(El(d))||(n=o.createElement("link"),oi(n,"link",t),sn(n),o.head.appendChild(n)))}}function By(t,n){dr.m(t,n);var a=fo;if(a&&t){var o=n&&typeof n.as=="string"?n.as:"script",u='link[rel="modulepreload"][as="'+bt(o)+'"][href="'+bt(t)+'"]',d=u;switch(o){case"audioworklet":case"paintworklet":case"serviceworker":case"sharedworker":case"worker":case"script":d=po(t)}if(!ua.has(d)&&(t=_({rel:"modulepreload",href:t},n),ua.set(d,t),a.querySelector(u)===null)){switch(o){case"audioworklet":case"paintworklet":case"serviceworker":case"sharedworker":case"worker":case"script":if(a.querySelector(El(d)))return}o=a.createElement("link"),oi(o,"link",t),sn(o),a.head.appendChild(o)}}}function Hy(t,n,a){dr.S(t,n,a);var o=fo;if(o&&t){var u=ga(o).hoistableStyles,d=ho(t);n=n||"default";var S=u.get(d);if(!S){var C={loading:0,preload:null};if(S=o.querySelector(bl(d)))C.loading=5;else{t=_({rel:"stylesheet",href:t,"data-precedence":n},a),(a=ua.get(d))&&Xd(t,a);var G=S=o.createElement("link");sn(G),oi(G,"link",t),G._p=new Promise(function(he,be){G.onload=he,G.onerror=be}),G.addEventListener("load",function(){C.loading|=1}),G.addEventListener("error",function(){C.loading|=2}),C.loading|=4,qc(S,n,o)}S={type:"stylesheet",instance:S,count:1,state:C},u.set(d,S)}}}function Gy(t,n){dr.X(t,n);var a=fo;if(a&&t){var o=ga(a).hoistableScripts,u=po(t),d=o.get(u);d||(d=a.querySelector(El(u)),d||(t=_({src:t,async:!0},n),(n=ua.get(u))&&Wd(t,n),d=a.createElement("script"),sn(d),oi(d,"link",t),a.head.appendChild(d)),d={type:"script",instance:d,count:1,state:null},o.set(u,d))}}function Vy(t,n){dr.M(t,n);var a=fo;if(a&&t){var o=ga(a).hoistableScripts,u=po(t),d=o.get(u);d||(d=a.querySelector(El(u)),d||(t=_({src:t,async:!0,type:"module"},n),(n=ua.get(u))&&Wd(t,n),d=a.createElement("script"),sn(d),oi(d,"link",t),a.head.appendChild(d)),d={type:"script",instance:d,count:1,state:null},o.set(u,d))}}function gv(t,n,a,o){var u=(u=Xe.current)?Wc(u):null;if(!u)throw Error(r(446));switch(t){case"meta":case"title":return null;case"style":return typeof a.precedence=="string"&&typeof a.href=="string"?(n=ho(a.href),a=ga(u).hoistableStyles,o=a.get(n),o||(o={type:"style",instance:null,count:0,state:null},a.set(n,o)),o):{type:"void",instance:null,count:0,state:null};case"link":if(a.rel==="stylesheet"&&typeof a.href=="string"&&typeof a.precedence=="string"){t=ho(a.href);var d=ga(u).hoistableStyles,S=d.get(t);if(S||(u=u.ownerDocument||u,S={type:"stylesheet",instance:null,count:0,state:{loading:0,preload:null}},d.set(t,S),(d=u.querySelector(bl(t)))&&!d._p&&(S.instance=d,S.state.loading=5),ua.has(t)||(a={rel:"preload",as:"style",href:a.href,crossOrigin:a.crossOrigin,integrity:a.integrity,media:a.media,hrefLang:a.hrefLang,referrerPolicy:a.referrerPolicy},ua.set(t,a),d||ky(u,t,a,S.state))),n&&o===null)throw Error(r(528,""));return S}if(n&&o!==null)throw Error(r(529,""));return null;case"script":return n=a.async,a=a.src,typeof a=="string"&&n&&typeof n!="function"&&typeof n!="symbol"?(n=po(a),a=ga(u).hoistableScripts,o=a.get(n),o||(o={type:"script",instance:null,count:0,state:null},a.set(n,o)),o):{type:"void",instance:null,count:0,state:null};default:throw Error(r(444,t))}}function ho(t){return'href="'+bt(t)+'"'}function bl(t){return'link[rel="stylesheet"]['+t+"]"}function vv(t){return _({},t,{"data-precedence":t.precedence,precedence:null})}function ky(t,n,a,o){t.querySelector('link[rel="preload"][as="style"]['+n+"]")?o.loading=1:(n=t.createElement("link"),o.preload=n,n.addEventListener("load",function(){return o.loading|=1}),n.addEventListener("error",function(){return o.loading|=2}),oi(n,"link",a),sn(n),t.head.appendChild(n))}function po(t){return'[src="'+bt(t)+'"]'}function El(t){return"script[async]"+t}function _v(t,n,a){if(n.count++,n.instance===null)switch(n.type){case"style":var o=t.querySelector('style[data-href~="'+bt(a.href)+'"]');if(o)return n.instance=o,sn(o),o;var u=_({},a,{"data-href":a.href,"data-precedence":a.precedence,href:null,precedence:null});return o=(t.ownerDocument||t).createElement("style"),sn(o),oi(o,"style",u),qc(o,a.precedence,t),n.instance=o;case"stylesheet":u=ho(a.href);var d=t.querySelector(bl(u));if(d)return n.state.loading|=4,n.instance=d,sn(d),d;o=vv(a),(u=ua.get(u))&&Xd(o,u),d=(t.ownerDocument||t).createElement("link"),sn(d);var S=d;return S._p=new Promise(function(C,G){S.onload=C,S.onerror=G}),oi(d,"link",o),n.state.loading|=4,qc(d,a.precedence,t),n.instance=d;case"script":return d=po(a.src),(u=t.querySelector(El(d)))?(n.instance=u,sn(u),u):(o=a,(u=ua.get(d))&&(o=_({},a),Wd(o,u)),t=t.ownerDocument||t,u=t.createElement("script"),sn(u),oi(u,"link",o),t.head.appendChild(u),n.instance=u);case"void":return null;default:throw Error(r(443,n.type))}else n.type==="stylesheet"&&(n.state.loading&4)===0&&(o=n.instance,n.state.loading|=4,qc(o,a.precedence,t));return n.instance}function qc(t,n,a){for(var o=a.querySelectorAll('link[rel="stylesheet"][data-precedence],style[data-precedence]'),u=o.length?o[o.length-1]:null,d=u,S=0;S<o.length;S++){var C=o[S];if(C.dataset.precedence===n)d=C;else if(d!==u)break}d?d.parentNode.insertBefore(t,d.nextSibling):(n=a.nodeType===9?a.head:a,n.insertBefore(t,n.firstChild))}function Xd(t,n){t.crossOrigin==null&&(t.crossOrigin=n.crossOrigin),t.referrerPolicy==null&&(t.referrerPolicy=n.referrerPolicy),t.title==null&&(t.title=n.title)}function Wd(t,n){t.crossOrigin==null&&(t.crossOrigin=n.crossOrigin),t.referrerPolicy==null&&(t.referrerPolicy=n.referrerPolicy),t.integrity==null&&(t.integrity=n.integrity)}var Yc=null;function xv(t,n,a){if(Yc===null){var o=new Map,u=Yc=new Map;u.set(a,o)}else u=Yc,o=u.get(a),o||(o=new Map,u.set(a,o));if(o.has(t))return o;for(o.set(t,null),a=a.getElementsByTagName(t),u=0;u<a.length;u++){var d=a[u];if(!(d[qt]||d[yn]||t==="link"&&d.getAttribute("rel")==="stylesheet")&&d.namespaceURI!=="http://www.w3.org/2000/svg"){var S=d.getAttribute(n)||"";S=t+S;var C=o.get(S);C?C.push(d):o.set(S,[d])}}return o}function Sv(t,n,a){t=t.ownerDocument||t,t.head.insertBefore(a,n==="title"?t.querySelector("head > title"):null)}function Xy(t,n,a){if(a===1||n.itemProp!=null)return!1;switch(t){case"meta":case"title":return!0;case"style":if(typeof n.precedence!="string"||typeof n.href!="string"||n.href==="")break;return!0;case"link":if(typeof n.rel!="string"||typeof n.href!="string"||n.href===""||n.onLoad||n.onError)break;switch(n.rel){case"stylesheet":return t=n.disabled,typeof n.precedence=="string"&&t==null;default:return!0}case"script":if(n.async&&typeof n.async!="function"&&typeof n.async!="symbol"&&!n.onLoad&&!n.onError&&n.src&&typeof n.src=="string")return!0}return!1}function yv(t){return!(t.type==="stylesheet"&&(t.state.loading&3)===0)}function Wy(t,n,a,o){if(a.type==="stylesheet"&&(typeof o.media!="string"||matchMedia(o.media).matches!==!1)&&(a.state.loading&4)===0){if(a.instance===null){var u=ho(o.href),d=n.querySelector(bl(u));if(d){n=d._p,n!==null&&typeof n=="object"&&typeof n.then=="function"&&(t.count++,t=jc.bind(t),n.then(t,t)),a.state.loading|=4,a.instance=d,sn(d);return}d=n.ownerDocument||n,o=vv(o),(u=ua.get(u))&&Xd(o,u),d=d.createElement("link"),sn(d);var S=d;S._p=new Promise(function(C,G){S.onload=C,S.onerror=G}),oi(d,"link",o),a.instance=d}t.stylesheets===null&&(t.stylesheets=new Map),t.stylesheets.set(a,n),(n=a.state.preload)&&(a.state.loading&3)===0&&(t.count++,a=jc.bind(t),n.addEventListener("load",a),n.addEventListener("error",a))}}var qd=0;function qy(t,n){return t.stylesheets&&t.count===0&&Kc(t,t.stylesheets),0<t.count||0<t.imgCount?function(a){var o=setTimeout(function(){if(t.stylesheets&&Kc(t,t.stylesheets),t.unsuspend){var d=t.unsuspend;t.unsuspend=null,d()}},6e4+n);0<t.imgBytes&&qd===0&&(qd=62500*Ay());var u=setTimeout(function(){if(t.waitingForImages=!1,t.count===0&&(t.stylesheets&&Kc(t,t.stylesheets),t.unsuspend)){var d=t.unsuspend;t.unsuspend=null,d()}},(t.imgBytes>qd?50:800)+n);return t.unsuspend=a,function(){t.unsuspend=null,clearTimeout(o),clearTimeout(u)}}:null}function jc(){if(this.count--,this.count===0&&(this.imgCount===0||!this.waitingForImages)){if(this.stylesheets)Kc(this,this.stylesheets);else if(this.unsuspend){var t=this.unsuspend;this.unsuspend=null,t()}}}var Zc=null;function Kc(t,n){t.stylesheets=null,t.unsuspend!==null&&(t.count++,Zc=new Map,n.forEach(Yy,t),Zc=null,jc.call(t))}function Yy(t,n){if(!(n.state.loading&4)){var a=Zc.get(t);if(a)var o=a.get(null);else{a=new Map,Zc.set(t,a);for(var u=t.querySelectorAll("link[data-precedence],style[data-precedence]"),d=0;d<u.length;d++){var S=u[d];(S.nodeName==="LINK"||S.getAttribute("media")!=="not all")&&(a.set(S.dataset.precedence,S),o=S)}o&&a.set(null,o)}u=n.instance,S=u.getAttribute("data-precedence"),d=a.get(S)||o,d===o&&a.set(null,u),a.set(S,u),this.count++,o=jc.bind(this),u.addEventListener("load",o),u.addEventListener("error",o),d?d.parentNode.insertBefore(u,d.nextSibling):(t=t.nodeType===9?t.head:t,t.insertBefore(u,t.firstChild)),n.state.loading|=4}}var Tl={$$typeof:V,Provider:null,Consumer:null,_currentValue:ee,_currentValue2:ee,_threadCount:0};function jy(t,n,a,o,u,d,S,C,G){this.tag=1,this.containerInfo=t,this.pingCache=this.current=this.pendingChildren=null,this.timeoutHandle=-1,this.callbackNode=this.next=this.pendingContext=this.context=this.cancelPendingCommit=null,this.callbackPriority=0,this.expirationTimes=et(-1),this.entangledLanes=this.shellSuspendCounter=this.errorRecoveryDisabledLanes=this.expiredLanes=this.warmLanes=this.pingedLanes=this.suspendedLanes=this.pendingLanes=0,this.entanglements=et(0),this.hiddenUpdates=et(null),this.identifierPrefix=o,this.onUncaughtError=u,this.onCaughtError=d,this.onRecoverableError=S,this.pooledCache=null,this.pooledCacheLanes=0,this.formState=G,this.incompleteTransitions=new Map}function Mv(t,n,a,o,u,d,S,C,G,he,be,Te){return t=new jy(t,n,a,S,G,he,be,Te,C),n=1,d===!0&&(n|=24),d=Bi(3,null,null,n),t.current=d,d.stateNode=t,n=Tf(),n.refCount++,t.pooledCache=n,n.refCount++,d.memoizedState={element:o,isDehydrated:a,cache:n},wf(d),t}function bv(t){return t?(t=Xs,t):Xs}function Ev(t,n,a,o,u,d){u=bv(u),o.context===null?o.context=u:o.pendingContext=u,o=Or(n),o.payload={element:a},d=d===void 0?null:d,d!==null&&(o.callback=d),a=Pr(t,o,n),a!==null&&(Li(a,t,n),il(a,t,n))}function Tv(t,n){if(t=t.memoizedState,t!==null&&t.dehydrated!==null){var a=t.retryLane;t.retryLane=a!==0&&a<n?a:n}}function Yd(t,n){Tv(t,n),(t=t.alternate)&&Tv(t,n)}function Av(t){if(t.tag===13||t.tag===31){var n=us(t,67108864);n!==null&&Li(n,t,67108864),Yd(t,67108864)}}function Rv(t){if(t.tag===13||t.tag===31){var n=Xi();n=Qi(n);var a=us(t,n);a!==null&&Li(a,t,n),Yd(t,n)}}var Qc=!0;function Zy(t,n,a,o){var u=z.T;z.T=null;var d=H.p;try{H.p=2,jd(t,n,a,o)}finally{H.p=d,z.T=u}}function Ky(t,n,a,o){var u=z.T;z.T=null;var d=H.p;try{H.p=8,jd(t,n,a,o)}finally{H.p=d,z.T=u}}function jd(t,n,a,o){if(Qc){var u=Zd(o);if(u===null)Od(t,n,o,Jc,a),wv(t,o);else if(Jy(u,t,n,a,o))o.stopPropagation();else if(wv(t,o),n&4&&-1<Qy.indexOf(t)){for(;u!==null;){var d=Ii(u);if(d!==null)switch(d.tag){case 3:if(d=d.stateNode,d.current.memoizedState.isDehydrated){var S=Oe(d.pendingLanes);if(S!==0){var C=d;for(C.pendingLanes|=2,C.entangledLanes|=2;S;){var G=1<<31-Ze(S);C.entanglements[1]|=G,S&=~G}za(d),(an&6)===0&&(Oc=Ft()+500,xl(0))}}break;case 31:case 13:C=us(d,2),C!==null&&Li(C,d,2),Ic(),Yd(d,2)}if(d=Zd(o),d===null&&Od(t,n,o,Jc,a),d===u)break;u=d}u!==null&&o.stopPropagation()}else Od(t,n,o,null,a)}}function Zd(t){return t=Bs(t),Kd(t)}var Jc=null;function Kd(t){if(Jc=null,t=Pi(t),t!==null){var n=c(t);if(n===null)t=null;else{var a=n.tag;if(a===13){if(t=f(n),t!==null)return t;t=null}else if(a===31){if(t=h(n),t!==null)return t;t=null}else if(a===3){if(n.stateNode.current.memoizedState.isDehydrated)return n.tag===3?n.stateNode.containerInfo:null;t=null}else n!==t&&(t=null)}}return Jc=t,null}function Cv(t){switch(t){case"beforetoggle":case"cancel":case"click":case"close":case"contextmenu":case"copy":case"cut":case"auxclick":case"dblclick":case"dragend":case"dragstart":case"drop":case"focusin":case"focusout":case"input":case"invalid":case"keydown":case"keypress":case"keyup":case"mousedown":case"mouseup":case"paste":case"pause":case"play":case"pointercancel":case"pointerdown":case"pointerup":case"ratechange":case"reset":case"resize":case"seeked":case"submit":case"toggle":case"touchcancel":case"touchend":case"touchstart":case"volumechange":case"change":case"selectionchange":case"textInput":case"compositionstart":case"compositionend":case"compositionupdate":case"beforeblur":case"afterblur":case"beforeinput":case"blur":case"fullscreenchange":case"focus":case"hashchange":case"popstate":case"select":case"selectstart":return 2;case"drag":case"dragenter":case"dragexit":case"dragleave":case"dragover":case"mousemove":case"mouseout":case"mouseover":case"pointermove":case"pointerout":case"pointerover":case"scroll":case"touchmove":case"wheel":case"mouseenter":case"mouseleave":case"pointerenter":case"pointerleave":return 8;case"message":switch(Dt()){case I:return 2;case b:return 8;case K:case ce:return 32;case ve:return 268435456;default:return 32}default:return 32}}var Qd=!1,qr=null,Yr=null,jr=null,Al=new Map,Rl=new Map,Zr=[],Qy="mousedown mouseup touchcancel touchend touchstart auxclick dblclick pointercancel pointerdown pointerup dragend dragstart drop compositionend compositionstart keydown keypress keyup input textInput copy cut paste click change contextmenu reset".split(" ");function wv(t,n){switch(t){case"focusin":case"focusout":qr=null;break;case"dragenter":case"dragleave":Yr=null;break;case"mouseover":case"mouseout":jr=null;break;case"pointerover":case"pointerout":Al.delete(n.pointerId);break;case"gotpointercapture":case"lostpointercapture":Rl.delete(n.pointerId)}}function Cl(t,n,a,o,u,d){return t===null||t.nativeEvent!==d?(t={blockedOn:n,domEventName:a,eventSystemFlags:o,nativeEvent:d,targetContainers:[u]},n!==null&&(n=Ii(n),n!==null&&Av(n)),t):(t.eventSystemFlags|=o,n=t.targetContainers,u!==null&&n.indexOf(u)===-1&&n.push(u),t)}function Jy(t,n,a,o,u){switch(n){case"focusin":return qr=Cl(qr,t,n,a,o,u),!0;case"dragenter":return Yr=Cl(Yr,t,n,a,o,u),!0;case"mouseover":return jr=Cl(jr,t,n,a,o,u),!0;case"pointerover":var d=u.pointerId;return Al.set(d,Cl(Al.get(d)||null,t,n,a,o,u)),!0;case"gotpointercapture":return d=u.pointerId,Rl.set(d,Cl(Rl.get(d)||null,t,n,a,o,u)),!0}return!1}function Dv(t){var n=Pi(t.target);if(n!==null){var a=c(n);if(a!==null){if(n=a.tag,n===13){if(n=f(a),n!==null){t.blockedOn=n,pa(t.priority,function(){Rv(a)});return}}else if(n===31){if(n=h(a),n!==null){t.blockedOn=n,pa(t.priority,function(){Rv(a)});return}}else if(n===3&&a.stateNode.current.memoizedState.isDehydrated){t.blockedOn=a.tag===3?a.stateNode.containerInfo:null;return}}}t.blockedOn=null}function $c(t){if(t.blockedOn!==null)return!1;for(var n=t.targetContainers;0<n.length;){var a=Zd(t.nativeEvent);if(a===null){a=t.nativeEvent;var o=new a.constructor(a.type,a);zs=o,a.target.dispatchEvent(o),zs=null}else return n=Ii(a),n!==null&&Av(n),t.blockedOn=a,!1;n.shift()}return!0}function Uv(t,n,a){$c(t)&&a.delete(n)}function $y(){Qd=!1,qr!==null&&$c(qr)&&(qr=null),Yr!==null&&$c(Yr)&&(Yr=null),jr!==null&&$c(jr)&&(jr=null),Al.forEach(Uv),Rl.forEach(Uv)}function eu(t,n){t.blockedOn===n&&(t.blockedOn=null,Qd||(Qd=!0,s.unstable_scheduleCallback(s.unstable_NormalPriority,$y)))}var tu=null;function Nv(t){tu!==t&&(tu=t,s.unstable_scheduleCallback(s.unstable_NormalPriority,function(){tu===t&&(tu=null);for(var n=0;n<t.length;n+=3){var a=t[n],o=t[n+1],u=t[n+2];if(typeof o!="function"){if(Kd(o||a)===null)continue;break}var d=Ii(a);d!==null&&(t.splice(n,3),n-=3,Zf(d,{pending:!0,data:u,method:a.method,action:o},o,u))}}))}function mo(t){function n(G){return eu(G,t)}qr!==null&&eu(qr,t),Yr!==null&&eu(Yr,t),jr!==null&&eu(jr,t),Al.forEach(n),Rl.forEach(n);for(var a=0;a<Zr.length;a++){var o=Zr[a];o.blockedOn===t&&(o.blockedOn=null)}for(;0<Zr.length&&(a=Zr[0],a.blockedOn===null);)Dv(a),a.blockedOn===null&&Zr.shift();if(a=(t.ownerDocument||t).$$reactFormReplay,a!=null)for(o=0;o<a.length;o+=3){var u=a[o],d=a[o+1],S=u[Bn]||null;if(typeof d=="function")S||Nv(a);else if(S){var C=null;if(d&&d.hasAttribute("formAction")){if(u=d,S=d[Bn]||null)C=S.formAction;else if(Kd(u)!==null)continue}else C=S.action;typeof C=="function"?a[o+1]=C:(a.splice(o,3),o-=3),Nv(a)}}}function Lv(){function t(d){d.canIntercept&&d.info==="react-transition"&&d.intercept({handler:function(){return new Promise(function(S){return u=S})},focusReset:"manual",scroll:"manual"})}function n(){u!==null&&(u(),u=null),o||setTimeout(a,20)}function a(){if(!o&&!navigation.transition){var d=navigation.currentEntry;d&&d.url!=null&&navigation.navigate(d.url,{state:d.getState(),info:"react-transition",history:"replace"})}}if(typeof navigation=="object"){var o=!1,u=null;return navigation.addEventListener("navigate",t),navigation.addEventListener("navigatesuccess",n),navigation.addEventListener("navigateerror",n),setTimeout(a,100),function(){o=!0,navigation.removeEventListener("navigate",t),navigation.removeEventListener("navigatesuccess",n),navigation.removeEventListener("navigateerror",n),u!==null&&(u(),u=null)}}}function Jd(t){this._internalRoot=t}nu.prototype.render=Jd.prototype.render=function(t){var n=this._internalRoot;if(n===null)throw Error(r(409));var a=n.current,o=Xi();Ev(a,o,t,n,null,null)},nu.prototype.unmount=Jd.prototype.unmount=function(){var t=this._internalRoot;if(t!==null){this._internalRoot=null;var n=t.containerInfo;Ev(t.current,2,null,t,null,null),Ic(),n[Kn]=null}};function nu(t){this._internalRoot=t}nu.prototype.unstable_scheduleHydration=function(t){if(t){var n=Da();t={blockedOn:null,target:t,priority:n};for(var a=0;a<Zr.length&&n!==0&&n<Zr[a].priority;a++);Zr.splice(a,0,t),a===0&&Dv(t)}};var Ov=e.version;if(Ov!=="19.2.0")throw Error(r(527,Ov,"19.2.0"));H.findDOMNode=function(t){var n=t._reactInternals;if(n===void 0)throw typeof t.render=="function"?Error(r(188)):(t=Object.keys(t).join(","),Error(r(268,t)));return t=p(n),t=t!==null?g(t):null,t=t===null?null:t.stateNode,t};var eM={bundleType:0,version:"19.2.0",rendererPackageName:"react-dom",currentDispatcherRef:z,reconcilerVersion:"19.2.0"};if(typeof __REACT_DEVTOOLS_GLOBAL_HOOK__<"u"){var iu=__REACT_DEVTOOLS_GLOBAL_HOOK__;if(!iu.isDisabled&&iu.supportsFiber)try{pe=iu.inject(eM),Se=iu}catch{}}return Dl.createRoot=function(t,n){if(!l(t))throw Error(r(299));var a=!1,o="",u=Gg,d=Vg,S=kg;return n!=null&&(n.unstable_strictMode===!0&&(a=!0),n.identifierPrefix!==void 0&&(o=n.identifierPrefix),n.onUncaughtError!==void 0&&(u=n.onUncaughtError),n.onCaughtError!==void 0&&(d=n.onCaughtError),n.onRecoverableError!==void 0&&(S=n.onRecoverableError)),n=Mv(t,1,!1,null,null,a,o,null,u,d,S,Lv),t[Kn]=n.current,Ld(t),new Jd(n)},Dl.hydrateRoot=function(t,n,a){if(!l(t))throw Error(r(299));var o=!1,u="",d=Gg,S=Vg,C=kg,G=null;return a!=null&&(a.unstable_strictMode===!0&&(o=!0),a.identifierPrefix!==void 0&&(u=a.identifierPrefix),a.onUncaughtError!==void 0&&(d=a.onUncaughtError),a.onCaughtError!==void 0&&(S=a.onCaughtError),a.onRecoverableError!==void 0&&(C=a.onRecoverableError),a.formState!==void 0&&(G=a.formState)),n=Mv(t,1,!0,n,a??null,o,u,G,d,S,C,Lv),n.context=bv(null),a=n.current,o=Xi(),o=Qi(o),u=Or(o),u.callback=null,Pr(a,u,o),a=o,n.current.lanes=a,Je(n,a),za(n),t[Kn]=n.current,Ld(t),new nu(n)},Dl.version="19.2.0",Dl}var Xv;function dM(){if(Xv)return th.exports;Xv=1;function s(){if(!(typeof __REACT_DEVTOOLS_GLOBAL_HOOK__>"u"||typeof __REACT_DEVTOOLS_GLOBAL_HOOK__.checkDCE!="function"))try{__REACT_DEVTOOLS_GLOBAL_HOOK__.checkDCE(s)}catch(e){console.error(e)}}return s(),th.exports=fM(),th.exports}var hM=dM();/**
 * @license @tabler/icons-react v3.49.0 - MIT
 *
 * This source code is licensed under the MIT license.
 * See the LICENSE file in the root directory of this source tree.
 */var pM={outline:{xmlns:"http://www.w3.org/2000/svg",width:24,height:24,viewBox:"0 0 24 24",fill:"none",stroke:"currentColor",strokeWidth:2,strokeLinecap:"round",strokeLinejoin:"round"},filled:{xmlns:"http://www.w3.org/2000/svg",width:24,height:24,viewBox:"0 0 24 24",fill:"currentColor",stroke:"none"}};/**
 * @license @tabler/icons-react v3.49.0 - MIT
 *
 * This source code is licensed under the MIT license.
 * See the LICENSE file in the root directory of this source tree.
 */const vi=(s,e,i,r)=>{const l=nt.forwardRef(({color:c="currentColor",size:f=24,stroke:h=2,title:m,className:p,children:g,..._},v)=>nt.createElement("svg",{ref:v,...pM[s],width:f,height:f,className:["tabler-icon",`tabler-icon-${e}`,p].filter(Boolean).join(" "),...s==="filled"?{fill:c}:{strokeWidth:h,stroke:c},..._},[m&&nt.createElement("title",{key:"svg-title"},m),...r.map(([x,E])=>nt.createElement(x,E)),...Array.isArray(g)?g:[g]]));return l.displayName=`${i}`,l};/**
 * @license @tabler/icons-react v3.49.0 - MIT
 *
 * This source code is licensed under the MIT license.
 * See the LICENSE file in the root directory of this source tree.
 */const mM=[["path",{d:"M12 6a2 2 0 1 0 4 0a2 2 0 1 0 -4 0",key:"svg-0"}],["path",{d:"M4 6l8 0",key:"svg-1"}],["path",{d:"M16 6l4 0",key:"svg-2"}],["path",{d:"M6 12a2 2 0 1 0 4 0a2 2 0 1 0 -4 0",key:"svg-3"}],["path",{d:"M4 12l2 0",key:"svg-4"}],["path",{d:"M10 12l10 0",key:"svg-5"}],["path",{d:"M15 18a2 2 0 1 0 4 0a2 2 0 1 0 -4 0",key:"svg-6"}],["path",{d:"M4 18l11 0",key:"svg-7"}],["path",{d:"M19 18l1 0",key:"svg-8"}]],gM=vi("outline","adjustments-horizontal","AdjustmentsHorizontal",mM);/**
 * @license @tabler/icons-react v3.49.0 - MIT
 *
 * This source code is licensed under the MIT license.
 * See the LICENSE file in the root directory of this source tree.
 */const vM=[["path",{d:"M7 7l10 10",key:"svg-0"}],["path",{d:"M17 8l0 9l-9 0",key:"svg-1"}]],_M=vi("outline","arrow-down-right","ArrowDownRight",vM);/**
 * @license @tabler/icons-react v3.49.0 - MIT
 *
 * This source code is licensed under the MIT license.
 * See the LICENSE file in the root directory of this source tree.
 */const xM=[["path",{d:"M17 7l-10 10",key:"svg-0"}],["path",{d:"M8 7l9 0l0 9",key:"svg-1"}]],SM=vi("outline","arrow-up-right","ArrowUpRight",xM);/**
 * @license @tabler/icons-react v3.49.0 - MIT
 *
 * This source code is licensed under the MIT license.
 * See the LICENSE file in the root directory of this source tree.
 */const yM=[["path",{d:"M3 12a9 9 0 1 0 18 0a9 9 0 0 0 -18 0",key:"svg-0"}],["path",{d:"M12 7v5l3 3",key:"svg-1"}]],Wv=vi("outline","clock","Clock",yM);/**
 * @license @tabler/icons-react v3.49.0 - MIT
 *
 * This source code is licensed under the MIT license.
 * See the LICENSE file in the root directory of this source tree.
 */const MM=[["path",{d:"M12 6h-6a2 2 0 0 0 -2 2v10a2 2 0 0 0 2 2h10a2 2 0 0 0 2 -2v-6",key:"svg-0"}],["path",{d:"M11 13l9 -9",key:"svg-1"}],["path",{d:"M15 4h5v5",key:"svg-2"}]],Xl=vi("outline","external-link","ExternalLink",MM);/**
 * @license @tabler/icons-react v3.49.0 - MIT
 *
 * This source code is licensed under the MIT license.
 * See the LICENSE file in the root directory of this source tree.
 */const bM=[["path",{d:"M3 12a9 9 0 1 0 18 0a9 9 0 0 0 -18 0",key:"svg-0"}],["path",{d:"M12 9h.01",key:"svg-1"}],["path",{d:"M11 12h1v4h1",key:"svg-2"}]],Fp=vi("outline","info-circle","InfoCircle",bM);/**
 * @license @tabler/icons-react v3.49.0 - MIT
 *
 * This source code is licensed under the MIT license.
 * See the LICENSE file in the root directory of this source tree.
 */const EM=[["path",{d:"M9 15l6 -6",key:"svg-0"}],["path",{d:"M11 6l.463 -.536a5 5 0 0 1 7.071 7.072l-.534 .464",key:"svg-1"}],["path",{d:"M13 18l-.397 .534a5.068 5.068 0 0 1 -7.127 0a4.972 4.972 0 0 1 0 -7.071l.524 -.463",key:"svg-2"}]],Bu=vi("outline","link","Link",EM);/**
 * @license @tabler/icons-react v3.49.0 - MIT
 *
 * This source code is licensed under the MIT license.
 * See the LICENSE file in the root directory of this source tree.
 */const TM=[["path",{d:"M5 12l14 0",key:"svg-0"}]],AM=vi("outline","minus","Minus",TM);/**
 * @license @tabler/icons-react v3.49.0 - MIT
 *
 * This source code is licensed under the MIT license.
 * See the LICENSE file in the root directory of this source tree.
 */const RM=[["path",{d:"M16 6h3a1 1 0 0 1 1 1v11a2 2 0 0 1 -4 0v-13a1 1 0 0 0 -1 -1h-10a1 1 0 0 0 -1 1v12a3 3 0 0 0 3 3h11",key:"svg-0"}],["path",{d:"M8 8l4 0",key:"svg-1"}],["path",{d:"M8 12l4 0",key:"svg-2"}],["path",{d:"M8 16l4 0",key:"svg-3"}]],CM=vi("outline","news","News",RM);/**
 * @license @tabler/icons-react v3.49.0 - MIT
 *
 * This source code is licensed under the MIT license.
 * See the LICENSE file in the root directory of this source tree.
 */const wM=[["path",{d:"M6 6a1 1 0 0 1 1 -1h2a1 1 0 0 1 1 1v12a1 1 0 0 1 -1 1h-2a1 1 0 0 1 -1 -1l0 -12",key:"svg-0"}],["path",{d:"M14 6a1 1 0 0 1 1 -1h2a1 1 0 0 1 1 1v12a1 1 0 0 1 -1 1h-2a1 1 0 0 1 -1 -1l0 -12",key:"svg-1"}]],DM=vi("outline","player-pause","PlayerPause",wM);/**
 * @license @tabler/icons-react v3.49.0 - MIT
 *
 * This source code is licensed under the MIT license.
 * See the LICENSE file in the root directory of this source tree.
 */const UM=[["path",{d:"M7 4v16l13 -8l-13 -8",key:"svg-0"}]],NM=vi("outline","player-play","PlayerPlay",UM);/**
 * @license @tabler/icons-react v3.49.0 - MIT
 *
 * This source code is licensed under the MIT license.
 * See the LICENSE file in the root directory of this source tree.
 */const LM=[["path",{d:"M4.05 11a8 8 0 1 1 .5 4m-.5 5v-5h5",key:"svg-0"}]],OM=vi("outline","rotate-clockwise","RotateClockwise",LM);/**
 * @license @tabler/icons-react v3.49.0 - MIT
 *
 * This source code is licensed under the MIT license.
 * See the LICENSE file in the root directory of this source tree.
 */const PM=[["path",{d:"M3 10a7 7 0 1 0 14 0a7 7 0 1 0 -14 0",key:"svg-0"}],["path",{d:"M21 21l-6 -6",key:"svg-1"}]],IM=vi("outline","search","Search",PM);/**
 * @license @tabler/icons-react v3.49.0 - MIT
 *
 * This source code is licensed under the MIT license.
 * See the LICENSE file in the root directory of this source tree.
 */const FM=[["path",{d:"M5 7a4 4 0 1 0 8 0a4 4 0 1 0 -8 0",key:"svg-0"}],["path",{d:"M3 21v-2a4 4 0 0 1 4 -4h4a4 4 0 0 1 4 4v2",key:"svg-1"}],["path",{d:"M16 3.13a4 4 0 0 1 0 7.75",key:"svg-2"}],["path",{d:"M21 21v-2a4 4 0 0 0 -3 -3.85",key:"svg-3"}]],zM=vi("outline","users","Users",FM);/**
 * @license @tabler/icons-react v3.49.0 - MIT
 *
 * This source code is licensed under the MIT license.
 * See the LICENSE file in the root directory of this source tree.
 */const BM=[["path",{d:"M18 6l-12 12",key:"svg-0"}],["path",{d:"M6 6l12 12",key:"svg-1"}]],Wl=vi("outline","x","X",BM);/**
 * @license @tabler/icons-react v3.49.0 - MIT
 *
 * This source code is licensed under the MIT license.
 * See the LICENSE file in the root directory of this source tree.
 */const HM=[["path",{d:"M7 3.34a10 10 0 1 1 -4.995 8.984l-.005 -.324l.005 -.324a10 10 0 0 1 4.995 -8.336z",key:"svg-0"}]],qv=vi("filled","circle-filled","CircleFilled",HM);/**
 * @license
 * Copyright 2010-2026 Three.js Authors
 * SPDX-License-Identifier: MIT
 */const zp="186",GM=0,Yv=1,VM=2,Uu=1,kM=2,Bl=3,Ns=0,Oi=1,xr=2,Mr=0,Io=1,Ca=2,jv=3,Zv=4,XM=5,No=100,WM=101,qM=102,YM=103,jM=104,ZM=200,KM=201,QM=202,JM=203,ux=204,fx=205,$M=206,eb=207,tb=208,nb=209,ib=210,ab=211,rb=212,sb=213,ob=214,Xh=0,Wh=1,qh=2,ql=3,Yh=4,jh=5,Zh=6,Kh=7,dx=0,lb=1,cb=2,Xa=0,hx=1,px=2,mx=3,gx=4,vx=5,_x=6,xx=7,Sx=300,Ls=301,Bo=302,rh=303,sh=304,Zu=306,Qh=1e3,Sr=1001,Jh=1002,li=1003,ub=1004,au=1005,mi=1006,oh=1007,Cs=1008,ha=1009,yx=1010,Mx=1011,Yl=1012,Bp=1013,Wa=1014,Va=1015,qa=1016,Hp=1017,Gp=1018,jl=1020,bx=35902,Ex=35899,Tx=1021,Ax=1022,Ra=1023,Er=1026,ws=1027,Rx=1028,Vp=1029,Os=1030,kp=1031,Xp=1033,Nu=33776,Lu=33777,Ou=33778,Pu=33779,$h=35840,ep=35841,tp=35842,np=35843,ip=36196,ap=37492,rp=37496,sp=37488,op=37489,Hu=37490,lp=37491,cp=37808,up=37809,fp=37810,dp=37811,hp=37812,pp=37813,mp=37814,gp=37815,vp=37816,_p=37817,xp=37818,Sp=37819,yp=37820,Mp=37821,bp=36492,Ep=36494,Tp=36495,Ap=36283,Rp=36284,Gu=36285,Cp=36286,fb=3200,Kv=0,db=1,is="",Ei="srgb",Vu="srgb-linear",ku="linear",cn="srgb",lh=7680,hb=519,pb=512,mb=513,gb=514,Wp=515,vb=516,_b=517,qp=518,xb=519,Sb=35044,ch=35048,Qv="300 es",ka=2e3,Xu=2001;function yb(s){for(let e=s.length-1;e>=0;--e)if(s[e]>=65535)return!0;return!1}function Zl(s){return document.createElementNS("http://www.w3.org/1999/xhtml",s)}function Mb(){const s=Zl("canvas");return s.style.display="block",s}const Jv={};function $v(...s){const e="THREE."+s.shift();console.log(e,...s)}function Cx(s){const e=s[0];if(typeof e=="string"&&e.startsWith("TSL:")){const i=s[1];i&&i.isStackTrace?s[0]+=" "+i.getLocation():s[1]='Stack trace not available. Enable "THREE.Node.captureStackTrace" to capture stack traces.'}return s}function ht(...s){s=Cx(s);const e="THREE."+s.shift();{const i=s[0];i&&i.isStackTrace?console.warn(i.getError(e)):console.warn(e,...s)}}function Zt(...s){s=Cx(s);const e="THREE."+s.shift();{const i=s[0];i&&i.isStackTrace?console.error(i.getError(e)):console.error(e,...s)}}function Fo(...s){const e=s.join(" ");e in Jv||(Jv[e]=!0,ht(...s))}function bb(s,e,i){return new Promise(function(r,l){function c(){switch(s.clientWaitSync(e,s.SYNC_FLUSH_COMMANDS_BIT,0)){case s.WAIT_FAILED:l();break;case s.TIMEOUT_EXPIRED:setTimeout(c,i);break;default:r()}}setTimeout(c,i)})}const Eb={[Xh]:Wh,[qh]:Zh,[Yh]:Kh,[ql]:jh,[Wh]:Xh,[Zh]:qh,[Kh]:Yh,[jh]:ql};class Is{addEventListener(e,i){this._listeners===void 0&&(this._listeners={});const r=this._listeners;r[e]===void 0&&(r[e]=[]),r[e].indexOf(i)===-1&&r[e].push(i)}hasEventListener(e,i){const r=this._listeners;return r===void 0?!1:r[e]!==void 0&&r[e].indexOf(i)!==-1}removeEventListener(e,i){const r=this._listeners;if(r===void 0)return;const l=r[e];if(l!==void 0){const c=l.indexOf(i);c!==-1&&l.splice(c,1)}}dispatchEvent(e){const i=this._listeners;if(i===void 0)return;const r=i[e.type];if(r!==void 0){e.target=this;const l=r.slice(0);for(let c=0,f=l.length;c<f;c++)l[c].call(this,e);e.target=null}}}const di=["00","01","02","03","04","05","06","07","08","09","0a","0b","0c","0d","0e","0f","10","11","12","13","14","15","16","17","18","19","1a","1b","1c","1d","1e","1f","20","21","22","23","24","25","26","27","28","29","2a","2b","2c","2d","2e","2f","30","31","32","33","34","35","36","37","38","39","3a","3b","3c","3d","3e","3f","40","41","42","43","44","45","46","47","48","49","4a","4b","4c","4d","4e","4f","50","51","52","53","54","55","56","57","58","59","5a","5b","5c","5d","5e","5f","60","61","62","63","64","65","66","67","68","69","6a","6b","6c","6d","6e","6f","70","71","72","73","74","75","76","77","78","79","7a","7b","7c","7d","7e","7f","80","81","82","83","84","85","86","87","88","89","8a","8b","8c","8d","8e","8f","90","91","92","93","94","95","96","97","98","99","9a","9b","9c","9d","9e","9f","a0","a1","a2","a3","a4","a5","a6","a7","a8","a9","aa","ab","ac","ad","ae","af","b0","b1","b2","b3","b4","b5","b6","b7","b8","b9","ba","bb","bc","bd","be","bf","c0","c1","c2","c3","c4","c5","c6","c7","c8","c9","ca","cb","cc","cd","ce","cf","d0","d1","d2","d3","d4","d5","d6","d7","d8","d9","da","db","dc","dd","de","df","e0","e1","e2","e3","e4","e5","e6","e7","e8","e9","ea","eb","ec","ed","ee","ef","f0","f1","f2","f3","f4","f5","f6","f7","f8","f9","fa","fb","fc","fd","fe","ff"];let e_=1234567;const Gl=Math.PI/180,Kl=180/Math.PI;function Go(){const s=Math.random()*4294967295|0,e=Math.random()*4294967295|0,i=Math.random()*4294967295|0,r=Math.random()*4294967295|0;return(di[s&255]+di[s>>8&255]+di[s>>16&255]+di[s>>24&255]+"-"+di[e&255]+di[e>>8&255]+"-"+di[e>>16&15|64]+di[e>>24&255]+"-"+di[i&63|128]+di[i>>8&255]+"-"+di[i>>16&255]+di[i>>24&255]+di[r&255]+di[r>>8&255]+di[r>>16&255]+di[r>>24&255]).toLowerCase()}function Ut(s,e,i){return Math.max(e,Math.min(i,s))}function Yp(s,e){return(s%e+e)%e}function Tb(s,e,i,r,l){return r+(s-e)*(l-r)/(i-e)}function Ab(s,e,i){return s!==e?(i-s)/(e-s):0}function Vl(s,e,i){return(1-i)*s+i*e}function Rb(s,e,i,r){return Vl(s,e,1-Math.exp(-i*r))}function Cb(s,e=1){return e-Math.abs(Yp(s,e*2)-e)}function wb(s,e,i){return s<=e?0:s>=i?1:(s=(s-e)/(i-e),s*s*(3-2*s))}function Db(s,e,i){return s<=e?0:s>=i?1:(s=(s-e)/(i-e),s*s*s*(s*(s*6-15)+10))}function Ub(s,e){return s+Math.floor(Math.random()*(e-s+1))}function Nb(s,e){return s+Math.random()*(e-s)}function Lb(s){return s*(.5-Math.random())}function Ob(s){s!==void 0&&(e_=s);let e=e_+=1831565813;return e=Math.imul(e^e>>>15,e|1),e^=e+Math.imul(e^e>>>7,e|61),((e^e>>>14)>>>0)/4294967296}function Pb(s){return s*Gl}function Ib(s){return s*Kl}function Fb(s){return s>0&&Number.isInteger(s)&&2**Math.round(Math.log2(s))===s}function zb(s){return Math.pow(2,Math.ceil(Math.log(s)/Math.LN2))}function Bb(s){return Math.pow(2,Math.floor(Math.log(s)/Math.LN2))}function Hb(s,e,i,r,l){const c=Math.cos,f=Math.sin,h=c(i/2),m=f(i/2),p=c((e+r)/2),g=f((e+r)/2),_=c((e-r)/2),v=f((e-r)/2),x=c((r-e)/2),E=f((r-e)/2);switch(l){case"XYX":s.set(h*g,m*_,m*v,h*p);break;case"YZY":s.set(m*v,h*g,m*_,h*p);break;case"ZXZ":s.set(m*_,m*v,h*g,h*p);break;case"XZX":s.set(h*g,m*E,m*x,h*p);break;case"YXY":s.set(m*x,h*g,m*E,h*p);break;case"ZYZ":s.set(m*E,m*x,h*g,h*p);break;default:ht("MathUtils: .setQuaternionFromProperEuler() encountered an unknown order: "+l)}}function Lo(s,e){switch(e.constructor){case Float32Array:return s;case Uint32Array:return s/4294967295;case Uint16Array:return s/65535;case Uint8Array:case Uint8ClampedArray:return s/255;case Int32Array:return Math.max(s/2147483647,-1);case Int16Array:return Math.max(s/32767,-1);case Int8Array:return Math.max(s/127,-1);default:throw new Error("THREE.MathUtils: Invalid component type.")}}function Mi(s,e){switch(e.constructor){case Float32Array:return s;case Uint32Array:return Math.round(s*4294967295);case Uint16Array:return Math.round(s*65535);case Uint8Array:case Uint8ClampedArray:return Math.round(s*255);case Int32Array:return Math.round(s*2147483647);case Int16Array:return Math.round(s*32767);case Int8Array:return Math.round(s*127);default:throw new Error("THREE.MathUtils: Invalid component type.")}}const go={DEG2RAD:Gl,RAD2DEG:Kl,generateUUID:Go,clamp:Ut,euclideanModulo:Yp,mapLinear:Tb,inverseLerp:Ab,lerp:Vl,damp:Rb,pingpong:Cb,smoothstep:wb,smootherstep:Db,randInt:Ub,randFloat:Nb,randFloatSpread:Lb,seededRandom:Ob,degToRad:Pb,radToDeg:Ib,isPowerOfTwo:Fb,ceilPowerOfTwo:zb,floorPowerOfTwo:Bb,setQuaternionFromProperEuler:Hb,normalize:Mi,denormalize:Lo},am=class am{constructor(e=0,i=0){this.x=e,this.y=i}get width(){return this.x}set width(e){this.x=e}get height(){return this.y}set height(e){this.y=e}set(e,i){return this.x=e,this.y=i,this}setScalar(e){return this.x=e,this.y=e,this}setX(e){return this.x=e,this}setY(e){return this.y=e,this}setComponent(e,i){switch(e){case 0:this.x=i;break;case 1:this.y=i;break;default:throw new Error("THREE.Vector2: index is out of range: "+e)}return this}getComponent(e){switch(e){case 0:return this.x;case 1:return this.y;default:throw new Error("THREE.Vector2: index is out of range: "+e)}}clone(){return new this.constructor(this.x,this.y)}copy(e){return this.x=e.x,this.y=e.y,this}add(e){return this.x+=e.x,this.y+=e.y,this}addScalar(e){return this.x+=e,this.y+=e,this}addVectors(e,i){return this.x=e.x+i.x,this.y=e.y+i.y,this}addScaledVector(e,i){return this.x+=e.x*i,this.y+=e.y*i,this}sub(e){return this.x-=e.x,this.y-=e.y,this}subScalar(e){return this.x-=e,this.y-=e,this}subVectors(e,i){return this.x=e.x-i.x,this.y=e.y-i.y,this}multiply(e){return this.x*=e.x,this.y*=e.y,this}multiplyScalar(e){return this.x*=e,this.y*=e,this}divide(e){return this.x/=e.x,this.y/=e.y,this}divideScalar(e){return this.multiplyScalar(1/e)}applyMatrix3(e){const i=this.x,r=this.y,l=e.elements;return this.x=l[0]*i+l[3]*r+l[6],this.y=l[1]*i+l[4]*r+l[7],this}min(e){return this.x=Math.min(this.x,e.x),this.y=Math.min(this.y,e.y),this}max(e){return this.x=Math.max(this.x,e.x),this.y=Math.max(this.y,e.y),this}clamp(e,i){return this.x=Ut(this.x,e.x,i.x),this.y=Ut(this.y,e.y,i.y),this}clampScalar(e,i){return this.x=Ut(this.x,e,i),this.y=Ut(this.y,e,i),this}clampLength(e,i){const r=this.length();return this.divideScalar(r||1).multiplyScalar(Ut(r,e,i))}floor(){return this.x=Math.floor(this.x),this.y=Math.floor(this.y),this}ceil(){return this.x=Math.ceil(this.x),this.y=Math.ceil(this.y),this}round(){return this.x=Math.round(this.x),this.y=Math.round(this.y),this}roundToZero(){return this.x=Math.trunc(this.x),this.y=Math.trunc(this.y),this}negate(){return this.x=-this.x,this.y=-this.y,this}dot(e){return this.x*e.x+this.y*e.y}cross(e){return this.x*e.y-this.y*e.x}lengthSq(){return this.x*this.x+this.y*this.y}length(){return Math.sqrt(this.x*this.x+this.y*this.y)}manhattanLength(){return Math.abs(this.x)+Math.abs(this.y)}normalize(){return this.divideScalar(this.length()||1)}angle(){return Math.atan2(-this.y,-this.x)+Math.PI}angleTo(e){const i=Math.sqrt(this.lengthSq()*e.lengthSq());if(i===0)return Math.PI/2;const r=this.dot(e)/i;return Math.acos(Ut(r,-1,1))}distanceTo(e){return Math.sqrt(this.distanceToSquared(e))}distanceToSquared(e){const i=this.x-e.x,r=this.y-e.y;return i*i+r*r}manhattanDistanceTo(e){return Math.abs(this.x-e.x)+Math.abs(this.y-e.y)}setLength(e){return this.normalize().multiplyScalar(e)}lerp(e,i){return this.x+=(e.x-this.x)*i,this.y+=(e.y-this.y)*i,this}lerpVectors(e,i,r){return this.x=e.x+(i.x-e.x)*r,this.y=e.y+(i.y-e.y)*r,this}equals(e){return e.x===this.x&&e.y===this.y}fromArray(e,i=0){return this.x=e[i],this.y=e[i+1],this}toArray(e=[],i=0){return e[i]=this.x,e[i+1]=this.y,e}fromBufferAttribute(e,i){return this.x=e.getX(i),this.y=e.getY(i),this}rotateAround(e,i){const r=Math.cos(i),l=Math.sin(i),c=this.x-e.x,f=this.y-e.y;return this.x=c*r-f*l+e.x,this.y=c*l+f*r+e.y,this}random(){return this.x=Math.random(),this.y=Math.random(),this}*[Symbol.iterator](){yield this.x,yield this.y}};am.prototype.isVector2=!0;let Kt=am;class ss{constructor(e=0,i=0,r=0,l=1){this.isQuaternion=!0,this._x=e,this._y=i,this._z=r,this._w=l}static slerpFlat(e,i,r,l,c,f,h){let m=r[l+0],p=r[l+1],g=r[l+2],_=r[l+3],v=c[f+0],x=c[f+1],E=c[f+2],D=c[f+3];if(_!==D||m!==v||p!==x||g!==E){let M=m*v+p*x+g*E+_*D;M<0&&(v=-v,x=-x,E=-E,D=-D,M=-M);let y=1-h;if(M<.9995){const F=Math.acos(M),V=Math.sin(F);y=Math.sin(y*F)/V,h=Math.sin(h*F)/V,m=m*y+v*h,p=p*y+x*h,g=g*y+E*h,_=_*y+D*h}else{m=m*y+v*h,p=p*y+x*h,g=g*y+E*h,_=_*y+D*h;const F=1/Math.sqrt(m*m+p*p+g*g+_*_);m*=F,p*=F,g*=F,_*=F}}e[i]=m,e[i+1]=p,e[i+2]=g,e[i+3]=_}static multiplyQuaternionsFlat(e,i,r,l,c,f){const h=r[l],m=r[l+1],p=r[l+2],g=r[l+3],_=c[f],v=c[f+1],x=c[f+2],E=c[f+3];return e[i]=h*E+g*_+m*x-p*v,e[i+1]=m*E+g*v+p*_-h*x,e[i+2]=p*E+g*x+h*v-m*_,e[i+3]=g*E-h*_-m*v-p*x,e}get x(){return this._x}set x(e){this._x=e,this._onChangeCallback()}get y(){return this._y}set y(e){this._y=e,this._onChangeCallback()}get z(){return this._z}set z(e){this._z=e,this._onChangeCallback()}get w(){return this._w}set w(e){this._w=e,this._onChangeCallback()}set(e,i,r,l){return this._x=e,this._y=i,this._z=r,this._w=l,this._onChangeCallback(),this}clone(){return new this.constructor(this._x,this._y,this._z,this._w)}copy(e){return this._x=e.x,this._y=e.y,this._z=e.z,this._w=e.w,this._onChangeCallback(),this}setFromEuler(e,i=!0){const r=e._x,l=e._y,c=e._z,f=e._order,h=Math.cos,m=Math.sin,p=h(r/2),g=h(l/2),_=h(c/2),v=m(r/2),x=m(l/2),E=m(c/2);switch(f){case"XYZ":this._x=v*g*_+p*x*E,this._y=p*x*_-v*g*E,this._z=p*g*E+v*x*_,this._w=p*g*_-v*x*E;break;case"YXZ":this._x=v*g*_+p*x*E,this._y=p*x*_-v*g*E,this._z=p*g*E-v*x*_,this._w=p*g*_+v*x*E;break;case"ZXY":this._x=v*g*_-p*x*E,this._y=p*x*_+v*g*E,this._z=p*g*E+v*x*_,this._w=p*g*_-v*x*E;break;case"ZYX":this._x=v*g*_-p*x*E,this._y=p*x*_+v*g*E,this._z=p*g*E-v*x*_,this._w=p*g*_+v*x*E;break;case"YZX":this._x=v*g*_+p*x*E,this._y=p*x*_+v*g*E,this._z=p*g*E-v*x*_,this._w=p*g*_-v*x*E;break;case"XZY":this._x=v*g*_-p*x*E,this._y=p*x*_-v*g*E,this._z=p*g*E+v*x*_,this._w=p*g*_+v*x*E;break;default:ht("Quaternion: .setFromEuler() encountered an unknown order: "+f)}return i===!0&&this._onChangeCallback(),this}setFromAxisAngle(e,i){const r=i/2,l=Math.sin(r);return this._x=e.x*l,this._y=e.y*l,this._z=e.z*l,this._w=Math.cos(r),this._onChangeCallback(),this}setFromRotationMatrix(e){const i=e.elements,r=i[0],l=i[4],c=i[8],f=i[1],h=i[5],m=i[9],p=i[2],g=i[6],_=i[10],v=r+h+_;if(v>0){const x=.5/Math.sqrt(v+1);this._w=.25/x,this._x=(g-m)*x,this._y=(c-p)*x,this._z=(f-l)*x}else if(r>h&&r>_){const x=2*Math.sqrt(1+r-h-_);this._w=(g-m)/x,this._x=.25*x,this._y=(l+f)/x,this._z=(c+p)/x}else if(h>_){const x=2*Math.sqrt(1+h-r-_);this._w=(c-p)/x,this._x=(l+f)/x,this._y=.25*x,this._z=(m+g)/x}else{const x=2*Math.sqrt(1+_-r-h);this._w=(f-l)/x,this._x=(c+p)/x,this._y=(m+g)/x,this._z=.25*x}return this._onChangeCallback(),this}setFromUnitVectors(e,i){let r=e.dot(i)+1;return r<1e-8?(r=0,Math.abs(e.x)>Math.abs(e.z)?(this._x=-e.y,this._y=e.x,this._z=0,this._w=r):(this._x=0,this._y=-e.z,this._z=e.y,this._w=r)):(this._x=e.y*i.z-e.z*i.y,this._y=e.z*i.x-e.x*i.z,this._z=e.x*i.y-e.y*i.x,this._w=r),this.normalize()}angleTo(e){return 2*Math.acos(Math.abs(Ut(this.dot(e),-1,1)))}rotateTowards(e,i){const r=this.angleTo(e);if(r===0)return this;const l=Math.min(1,i/r);return this.slerp(e,l),this}identity(){return this.set(0,0,0,1)}invert(){return this.conjugate()}conjugate(){return this._x*=-1,this._y*=-1,this._z*=-1,this._onChangeCallback(),this}dot(e){return this._x*e._x+this._y*e._y+this._z*e._z+this._w*e._w}lengthSq(){return this._x*this._x+this._y*this._y+this._z*this._z+this._w*this._w}length(){return Math.sqrt(this._x*this._x+this._y*this._y+this._z*this._z+this._w*this._w)}normalize(){let e=this.length();return e===0?(this._x=0,this._y=0,this._z=0,this._w=1):(e=1/e,this._x=this._x*e,this._y=this._y*e,this._z=this._z*e,this._w=this._w*e),this._onChangeCallback(),this}multiply(e){return this.multiplyQuaternions(this,e)}premultiply(e){return this.multiplyQuaternions(e,this)}multiplyQuaternions(e,i){const r=e._x,l=e._y,c=e._z,f=e._w,h=i._x,m=i._y,p=i._z,g=i._w;return this._x=r*g+f*h+l*p-c*m,this._y=l*g+f*m+c*h-r*p,this._z=c*g+f*p+r*m-l*h,this._w=f*g-r*h-l*m-c*p,this._onChangeCallback(),this}slerp(e,i){let r=e._x,l=e._y,c=e._z,f=e._w,h=this.dot(e);h<0&&(r=-r,l=-l,c=-c,f=-f,h=-h);let m=1-i;if(h<.9995){const p=Math.acos(h),g=Math.sin(p);m=Math.sin(m*p)/g,i=Math.sin(i*p)/g,this._x=this._x*m+r*i,this._y=this._y*m+l*i,this._z=this._z*m+c*i,this._w=this._w*m+f*i,this._onChangeCallback()}else this._x=this._x*m+r*i,this._y=this._y*m+l*i,this._z=this._z*m+c*i,this._w=this._w*m+f*i,this.normalize();return this}slerpQuaternions(e,i,r){return this.copy(e).slerp(i,r)}random(){const e=2*Math.PI*Math.random(),i=2*Math.PI*Math.random(),r=Math.random(),l=Math.sqrt(1-r),c=Math.sqrt(r);return this.set(l*Math.sin(e),l*Math.cos(e),c*Math.sin(i),c*Math.cos(i))}equals(e){return e._x===this._x&&e._y===this._y&&e._z===this._z&&e._w===this._w}fromArray(e,i=0){return this._x=e[i],this._y=e[i+1],this._z=e[i+2],this._w=e[i+3],this._onChangeCallback(),this}toArray(e=[],i=0){return e[i]=this._x,e[i+1]=this._y,e[i+2]=this._z,e[i+3]=this._w,e}fromBufferAttribute(e,i){return this._x=e.getX(i),this._y=e.getY(i),this._z=e.getZ(i),this._w=e.getW(i),this._onChangeCallback(),this}toJSON(){return this.toArray()}_onChange(e){return this._onChangeCallback=e,this}_onChangeCallback(){}*[Symbol.iterator](){yield this._x,yield this._y,yield this._z,yield this._w}}const rm=class rm{constructor(e=0,i=0,r=0){this.x=e,this.y=i,this.z=r}set(e,i,r){return r===void 0&&(r=this.z),this.x=e,this.y=i,this.z=r,this}setScalar(e){return this.x=e,this.y=e,this.z=e,this}setX(e){return this.x=e,this}setY(e){return this.y=e,this}setZ(e){return this.z=e,this}setComponent(e,i){switch(e){case 0:this.x=i;break;case 1:this.y=i;break;case 2:this.z=i;break;default:throw new Error("THREE.Vector3: index is out of range: "+e)}return this}getComponent(e){switch(e){case 0:return this.x;case 1:return this.y;case 2:return this.z;default:throw new Error("THREE.Vector3: index is out of range: "+e)}}clone(){return new this.constructor(this.x,this.y,this.z)}copy(e){return this.x=e.x,this.y=e.y,this.z=e.z,this}add(e){return this.x+=e.x,this.y+=e.y,this.z+=e.z,this}addScalar(e){return this.x+=e,this.y+=e,this.z+=e,this}addVectors(e,i){return this.x=e.x+i.x,this.y=e.y+i.y,this.z=e.z+i.z,this}addScaledVector(e,i){return this.x+=e.x*i,this.y+=e.y*i,this.z+=e.z*i,this}sub(e){return this.x-=e.x,this.y-=e.y,this.z-=e.z,this}subScalar(e){return this.x-=e,this.y-=e,this.z-=e,this}subVectors(e,i){return this.x=e.x-i.x,this.y=e.y-i.y,this.z=e.z-i.z,this}multiply(e){return this.x*=e.x,this.y*=e.y,this.z*=e.z,this}multiplyScalar(e){return this.x*=e,this.y*=e,this.z*=e,this}multiplyVectors(e,i){return this.x=e.x*i.x,this.y=e.y*i.y,this.z=e.z*i.z,this}applyEuler(e){return this.applyQuaternion(t_.setFromEuler(e))}applyAxisAngle(e,i){return this.applyQuaternion(t_.setFromAxisAngle(e,i))}applyMatrix3(e){const i=this.x,r=this.y,l=this.z,c=e.elements;return this.x=c[0]*i+c[3]*r+c[6]*l,this.y=c[1]*i+c[4]*r+c[7]*l,this.z=c[2]*i+c[5]*r+c[8]*l,this}applyNormalMatrix(e){return this.applyMatrix3(e).normalize()}applyMatrix4(e){const i=this.x,r=this.y,l=this.z,c=e.elements,f=1/(c[3]*i+c[7]*r+c[11]*l+c[15]);return this.x=(c[0]*i+c[4]*r+c[8]*l+c[12])*f,this.y=(c[1]*i+c[5]*r+c[9]*l+c[13])*f,this.z=(c[2]*i+c[6]*r+c[10]*l+c[14])*f,this}applyQuaternion(e){const i=this.x,r=this.y,l=this.z,c=e.x,f=e.y,h=e.z,m=e.w,p=2*(f*l-h*r),g=2*(h*i-c*l),_=2*(c*r-f*i);return this.x=i+m*p+f*_-h*g,this.y=r+m*g+h*p-c*_,this.z=l+m*_+c*g-f*p,this}project(e){return this.applyMatrix4(e.matrixWorldInverse).applyMatrix4(e.projectionMatrix)}unproject(e){return this.applyMatrix4(e.projectionMatrixInverse).applyMatrix4(e.matrixWorld)}transformDirection(e){const i=this.x,r=this.y,l=this.z,c=e.elements;return this.x=c[0]*i+c[4]*r+c[8]*l,this.y=c[1]*i+c[5]*r+c[9]*l,this.z=c[2]*i+c[6]*r+c[10]*l,this.normalize()}divide(e){return this.x/=e.x,this.y/=e.y,this.z/=e.z,this}divideScalar(e){return this.multiplyScalar(1/e)}min(e){return this.x=Math.min(this.x,e.x),this.y=Math.min(this.y,e.y),this.z=Math.min(this.z,e.z),this}max(e){return this.x=Math.max(this.x,e.x),this.y=Math.max(this.y,e.y),this.z=Math.max(this.z,e.z),this}clamp(e,i){return this.x=Ut(this.x,e.x,i.x),this.y=Ut(this.y,e.y,i.y),this.z=Ut(this.z,e.z,i.z),this}clampScalar(e,i){return this.x=Ut(this.x,e,i),this.y=Ut(this.y,e,i),this.z=Ut(this.z,e,i),this}clampLength(e,i){const r=this.length();return this.divideScalar(r||1).multiplyScalar(Ut(r,e,i))}floor(){return this.x=Math.floor(this.x),this.y=Math.floor(this.y),this.z=Math.floor(this.z),this}ceil(){return this.x=Math.ceil(this.x),this.y=Math.ceil(this.y),this.z=Math.ceil(this.z),this}round(){return this.x=Math.round(this.x),this.y=Math.round(this.y),this.z=Math.round(this.z),this}roundToZero(){return this.x=Math.trunc(this.x),this.y=Math.trunc(this.y),this.z=Math.trunc(this.z),this}negate(){return this.x=-this.x,this.y=-this.y,this.z=-this.z,this}dot(e){return this.x*e.x+this.y*e.y+this.z*e.z}lengthSq(){return this.x*this.x+this.y*this.y+this.z*this.z}length(){return Math.sqrt(this.x*this.x+this.y*this.y+this.z*this.z)}manhattanLength(){return Math.abs(this.x)+Math.abs(this.y)+Math.abs(this.z)}normalize(){return this.divideScalar(this.length()||1)}setLength(e){return this.normalize().multiplyScalar(e)}lerp(e,i){return this.x+=(e.x-this.x)*i,this.y+=(e.y-this.y)*i,this.z+=(e.z-this.z)*i,this}lerpVectors(e,i,r){return this.x=e.x+(i.x-e.x)*r,this.y=e.y+(i.y-e.y)*r,this.z=e.z+(i.z-e.z)*r,this}cross(e){return this.crossVectors(this,e)}crossVectors(e,i){const r=e.x,l=e.y,c=e.z,f=i.x,h=i.y,m=i.z;return this.x=l*m-c*h,this.y=c*f-r*m,this.z=r*h-l*f,this}projectOnVector(e){const i=e.lengthSq();if(i===0)return this.set(0,0,0);const r=e.dot(this)/i;return this.copy(e).multiplyScalar(r)}projectOnPlane(e){return uh.copy(this).projectOnVector(e),this.sub(uh)}reflect(e){return this.sub(uh.copy(e).multiplyScalar(2*this.dot(e)))}angleTo(e){const i=Math.sqrt(this.lengthSq()*e.lengthSq());if(i===0)return Math.PI/2;const r=this.dot(e)/i;return Math.acos(Ut(r,-1,1))}distanceTo(e){return Math.sqrt(this.distanceToSquared(e))}distanceToSquared(e){const i=this.x-e.x,r=this.y-e.y,l=this.z-e.z;return i*i+r*r+l*l}manhattanDistanceTo(e){return Math.abs(this.x-e.x)+Math.abs(this.y-e.y)+Math.abs(this.z-e.z)}setFromSpherical(e){return this.setFromSphericalCoords(e.radius,e.phi,e.theta)}setFromSphericalCoords(e,i,r){const l=Math.sin(i)*e;return this.x=l*Math.sin(r),this.y=Math.cos(i)*e,this.z=l*Math.cos(r),this}setFromCylindrical(e){return this.setFromCylindricalCoords(e.radius,e.theta,e.y)}setFromCylindricalCoords(e,i,r){return this.x=e*Math.sin(i),this.y=r,this.z=e*Math.cos(i),this}setFromMatrixPosition(e){const i=e.elements;return this.x=i[12],this.y=i[13],this.z=i[14],this}setFromMatrixScale(e){const i=this.setFromMatrixColumn(e,0).length(),r=this.setFromMatrixColumn(e,1).length(),l=this.setFromMatrixColumn(e,2).length();return this.x=i,this.y=r,this.z=l,this}setFromMatrixColumn(e,i){return this.fromArray(e.elements,i*4)}setFromMatrix3Column(e,i){return this.fromArray(e.elements,i*3)}setFromEuler(e){return this.x=e._x,this.y=e._y,this.z=e._z,this}setFromColor(e){return this.x=e.r,this.y=e.g,this.z=e.b,this}equals(e){return e.x===this.x&&e.y===this.y&&e.z===this.z}fromArray(e,i=0){return this.x=e[i],this.y=e[i+1],this.z=e[i+2],this}toArray(e=[],i=0){return e[i]=this.x,e[i+1]=this.y,e[i+2]=this.z,e}fromBufferAttribute(e,i){return this.x=e.getX(i),this.y=e.getY(i),this.z=e.getZ(i),this}random(){return this.x=Math.random(),this.y=Math.random(),this.z=Math.random(),this}randomDirection(){const e=Math.random()*Math.PI*2,i=Math.random()*2-1,r=Math.sqrt(1-i*i);return this.x=r*Math.cos(e),this.y=i,this.z=r*Math.sin(e),this}*[Symbol.iterator](){yield this.x,yield this.y,yield this.z}};rm.prototype.isVector3=!0;let Q=rm;const uh=new Q,t_=new ss,sm=class sm{constructor(e,i,r,l,c,f,h,m,p){this.elements=[1,0,0,0,1,0,0,0,1],e!==void 0&&this.set(e,i,r,l,c,f,h,m,p)}set(e,i,r,l,c,f,h,m,p){const g=this.elements;return g[0]=e,g[1]=l,g[2]=h,g[3]=i,g[4]=c,g[5]=m,g[6]=r,g[7]=f,g[8]=p,this}identity(){return this.set(1,0,0,0,1,0,0,0,1),this}copy(e){const i=this.elements,r=e.elements;return i[0]=r[0],i[1]=r[1],i[2]=r[2],i[3]=r[3],i[4]=r[4],i[5]=r[5],i[6]=r[6],i[7]=r[7],i[8]=r[8],this}extractBasis(e,i,r){return e.setFromMatrix3Column(this,0),i.setFromMatrix3Column(this,1),r.setFromMatrix3Column(this,2),this}setFromMatrix4(e){const i=e.elements;return this.set(i[0],i[4],i[8],i[1],i[5],i[9],i[2],i[6],i[10]),this}multiply(e){return this.multiplyMatrices(this,e)}premultiply(e){return this.multiplyMatrices(e,this)}multiplyMatrices(e,i){const r=e.elements,l=i.elements,c=this.elements,f=r[0],h=r[3],m=r[6],p=r[1],g=r[4],_=r[7],v=r[2],x=r[5],E=r[8],D=l[0],M=l[3],y=l[6],F=l[1],V=l[4],R=l[7],N=l[2],L=l[5],P=l[8];return c[0]=f*D+h*F+m*N,c[3]=f*M+h*V+m*L,c[6]=f*y+h*R+m*P,c[1]=p*D+g*F+_*N,c[4]=p*M+g*V+_*L,c[7]=p*y+g*R+_*P,c[2]=v*D+x*F+E*N,c[5]=v*M+x*V+E*L,c[8]=v*y+x*R+E*P,this}multiplyScalar(e){const i=this.elements;return i[0]*=e,i[3]*=e,i[6]*=e,i[1]*=e,i[4]*=e,i[7]*=e,i[2]*=e,i[5]*=e,i[8]*=e,this}determinant(){const e=this.elements,i=e[0],r=e[1],l=e[2],c=e[3],f=e[4],h=e[5],m=e[6],p=e[7],g=e[8];return i*f*g-i*h*p-r*c*g+r*h*m+l*c*p-l*f*m}invert(){const e=this.elements,i=e[0],r=e[1],l=e[2],c=e[3],f=e[4],h=e[5],m=e[6],p=e[7],g=e[8],_=g*f-h*p,v=h*m-g*c,x=p*c-f*m,E=i*_+r*v+l*x;if(E===0)return this.set(0,0,0,0,0,0,0,0,0);const D=1/E;return e[0]=_*D,e[1]=(l*p-g*r)*D,e[2]=(h*r-l*f)*D,e[3]=v*D,e[4]=(g*i-l*m)*D,e[5]=(l*c-h*i)*D,e[6]=x*D,e[7]=(r*m-p*i)*D,e[8]=(f*i-r*c)*D,this}transpose(){let e;const i=this.elements;return e=i[1],i[1]=i[3],i[3]=e,e=i[2],i[2]=i[6],i[6]=e,e=i[5],i[5]=i[7],i[7]=e,this}getNormalMatrix(e){return this.setFromMatrix4(e).invert().transpose()}transposeIntoArray(e){const i=this.elements;return e[0]=i[0],e[1]=i[3],e[2]=i[6],e[3]=i[1],e[4]=i[4],e[5]=i[7],e[6]=i[2],e[7]=i[5],e[8]=i[8],this}setUvTransform(e,i,r,l,c,f,h){const m=Math.cos(c),p=Math.sin(c);return this.set(r*m,r*p,-r*(m*f+p*h)+f+e,-l*p,l*m,-l*(-p*f+m*h)+h+i,0,0,1),this}scale(e,i){return Fo("Matrix3: .scale() is deprecated. Use .makeScale() instead."),this.premultiply(fh.makeScale(e,i)),this}rotate(e){return Fo("Matrix3: .rotate() is deprecated. Use .makeRotation() instead."),this.premultiply(fh.makeRotation(-e)),this}translate(e,i){return Fo("Matrix3: .translate() is deprecated. Use .makeTranslation() instead."),this.premultiply(fh.makeTranslation(e,i)),this}makeTranslation(e,i){return e.isVector2?this.set(1,0,e.x,0,1,e.y,0,0,1):this.set(1,0,e,0,1,i,0,0,1),this}makeRotation(e){const i=Math.cos(e),r=Math.sin(e);return this.set(i,-r,0,r,i,0,0,0,1),this}makeScale(e,i){return this.set(e,0,0,0,i,0,0,0,1),this}equals(e){const i=this.elements,r=e.elements;for(let l=0;l<9;l++)if(i[l]!==r[l])return!1;return!0}fromArray(e,i=0){for(let r=0;r<9;r++)this.elements[r]=e[r+i];return this}toArray(e=[],i=0){const r=this.elements;return e[i]=r[0],e[i+1]=r[1],e[i+2]=r[2],e[i+3]=r[3],e[i+4]=r[4],e[i+5]=r[5],e[i+6]=r[6],e[i+7]=r[7],e[i+8]=r[8],e}clone(){return new this.constructor().fromArray(this.elements)}};sm.prototype.isMatrix3=!0;let yt=sm;const fh=new yt,n_=new yt().set(.4123908,.3575843,.1804808,.212639,.7151687,.0721923,.0193308,.1191948,.9505322),i_=new yt().set(3.2409699,-1.5373832,-.4986108,-.9692436,1.8759675,.0415551,.0556301,-.203977,1.0569715);function Gb(){const s={enabled:!0,workingColorSpace:Vu,spaces:{},convert:function(l,c,f){return this.enabled===!1||c===f||!c||!f||(this.spaces[c].transfer===cn&&(l.r=br(l.r),l.g=br(l.g),l.b=br(l.b)),this.spaces[c].primaries!==this.spaces[f].primaries&&(l.applyMatrix3(this.spaces[c].toXYZ),l.applyMatrix3(this.spaces[f].fromXYZ)),this.spaces[f].transfer===cn&&(l.r=zo(l.r),l.g=zo(l.g),l.b=zo(l.b))),l},workingToColorSpace:function(l,c){return this.convert(l,this.workingColorSpace,c)},colorSpaceToWorking:function(l,c){return this.convert(l,c,this.workingColorSpace)},getPrimaries:function(l){return this.spaces[l].primaries},getTransfer:function(l){return l===is?ku:this.spaces[l].transfer},getToneMappingMode:function(l){return this.spaces[l].outputColorSpaceConfig.toneMappingMode||"standard"},getLuminanceCoefficients:function(l,c=this.workingColorSpace){return l.fromArray(this.spaces[c].luminanceCoefficients)},define:function(l){Object.assign(this.spaces,l)},_getMatrix:function(l,c,f){return l.copy(this.spaces[c].toXYZ).multiply(this.spaces[f].fromXYZ)},_getDrawingBufferColorSpace:function(l){return this.spaces[l].outputColorSpaceConfig.drawingBufferColorSpace},_getUnpackColorSpace:function(l=this.workingColorSpace){return this.spaces[l].workingColorSpaceConfig.unpackColorSpace},fromWorkingColorSpace:function(l,c){return Fo("ColorManagement: .fromWorkingColorSpace() has been renamed to .workingToColorSpace()."),s.workingToColorSpace(l,c)},toWorkingColorSpace:function(l,c){return Fo("ColorManagement: .toWorkingColorSpace() has been renamed to .colorSpaceToWorking()."),s.colorSpaceToWorking(l,c)}},e=[.64,.33,.3,.6,.15,.06],i=[.2126,.7152,.0722],r=[.3127,.329];return s.define({[Vu]:{primaries:e,whitePoint:r,transfer:ku,toXYZ:n_,fromXYZ:i_,luminanceCoefficients:i,workingColorSpaceConfig:{unpackColorSpace:Ei},outputColorSpaceConfig:{drawingBufferColorSpace:Ei}},[Ei]:{primaries:e,whitePoint:r,transfer:cn,toXYZ:n_,fromXYZ:i_,luminanceCoefficients:i,outputColorSpaceConfig:{drawingBufferColorSpace:Ei}}}),s}const kt=Gb();function br(s){return s<.04045?s*.0773993808:Math.pow(s*.9478672986+.0521327014,2.4)}function zo(s){return s<.0031308?s*12.92:1.055*Math.pow(s,.41666)-.055}let vo;class Vb{static getDataURL(e,i="image/png"){if(/^data:/i.test(e.src)||typeof HTMLCanvasElement>"u")return e.src;let r;if(e instanceof HTMLCanvasElement)r=e;else{vo===void 0&&(vo=Zl("canvas")),vo.width=e.width,vo.height=e.height;const l=vo.getContext("2d");e instanceof ImageData?l.putImageData(e,0,0):l.drawImage(e,0,0,e.width,e.height),r=vo}return r.toDataURL(i)}static sRGBToLinear(e){if(typeof HTMLImageElement<"u"&&e instanceof HTMLImageElement||typeof HTMLCanvasElement<"u"&&e instanceof HTMLCanvasElement||typeof ImageBitmap<"u"&&e instanceof ImageBitmap){const i=Zl("canvas");i.width=e.width,i.height=e.height;const r=i.getContext("2d");r.drawImage(e,0,0,e.width,e.height);const l=r.getImageData(0,0,e.width,e.height),c=l.data;for(let f=0;f<c.length;f++)c[f]=br(c[f]/255)*255;return r.putImageData(l,0,0),i}else if(e.data){const i=e.data.slice(0);for(let r=0;r<i.length;r++)i instanceof Uint8Array||i instanceof Uint8ClampedArray?i[r]=Math.floor(br(i[r]/255)*255):i[r]=br(i[r]);return{data:i,width:e.width,height:e.height}}else return ht("ImageUtils.sRGBToLinear(): Unsupported image type. No color space conversion applied."),e}}let kb=0;class jp{constructor(e=null){this.isTextureSource=!0,Object.defineProperty(this,"id",{value:kb++}),this.uuid=Go(),this.data=e,this.dataReady=!0,this.version=0}getSize(e){const i=this.data;return typeof HTMLVideoElement<"u"&&i instanceof HTMLVideoElement?e.set(i.videoWidth,i.videoHeight,0):typeof VideoFrame<"u"&&i instanceof VideoFrame?e.set(i.displayWidth,i.displayHeight,0):i!==null?e.set(i.width,i.height,i.depth||0):e.set(0,0,0),e}set needsUpdate(e){e===!0&&this.version++}toJSON(e){const i=e===void 0||typeof e=="string";if(!i&&e.images[this.uuid]!==void 0)return e.images[this.uuid];const r={uuid:this.uuid,url:""},l=this.data;if(l!==null){let c;if(Array.isArray(l)){c=[];for(let f=0,h=l.length;f<h;f++)l[f].isDataTexture?c.push(dh(l[f].image)):c.push(dh(l[f]))}else c=dh(l);r.url=c}return i||(e.images[this.uuid]=r),r}}function dh(s){return typeof HTMLImageElement<"u"&&s instanceof HTMLImageElement||typeof HTMLCanvasElement<"u"&&s instanceof HTMLCanvasElement||typeof ImageBitmap<"u"&&s instanceof ImageBitmap?Vb.getDataURL(s):s.data?{data:Array.from(s.data),width:s.width,height:s.height,type:s.data.constructor.name}:(ht("Texture: Unable to serialize Texture."),{})}let Xb=0;const hh=new Q;class gi extends Is{constructor(e=gi.DEFAULT_IMAGE,i=gi.DEFAULT_MAPPING,r=Sr,l=Sr,c=mi,f=Cs,h=Ra,m=ha,p=gi.DEFAULT_ANISOTROPY,g=is){super(),this.isTexture=!0,Object.defineProperty(this,"id",{value:Xb++}),this.uuid=Go(),this.name="",this.source=new jp(e),this.mipmaps=[],this.mapping=i,this.channel=0,this.wrapS=r,this.wrapT=l,this.magFilter=c,this.minFilter=f,this.anisotropy=p,this.format=h,this.internalFormat=null,this.type=m,this.offset=new Kt(0,0),this.repeat=new Kt(1,1),this.center=new Kt(0,0),this.rotation=0,this.matrixAutoUpdate=!0,this.matrix=new yt,this.generateMipmaps=!0,this.premultiplyAlpha=!1,this.flipY=!0,this.unpackAlignment=4,this.colorSpace=g,this.userData={},this.updateRanges=[],this.version=0,this.onUpdate=null,this.renderTarget=null,this.isRenderTargetTexture=!1,this.isArrayTexture=!!(e&&e.depth&&e.depth>1),this.pmremVersion=0,this.normalized=!1}get width(){return this.source.getSize(hh).x}get height(){return this.source.getSize(hh).y}get depth(){return this.source.getSize(hh).z}get image(){return this.source.data}set image(e){this.source.data=e}updateMatrix(){this.matrix.setUvTransform(this.offset.x,this.offset.y,this.repeat.x,this.repeat.y,this.rotation,this.center.x,this.center.y)}addUpdateRange(e,i){this.updateRanges.push({start:e,count:i})}clearUpdateRanges(){this.updateRanges.length=0}clone(){return new this.constructor().copy(this)}copy(e){return this.name=e.name,this.source=e.source,this.mipmaps=e.mipmaps.slice(0),this.mapping=e.mapping,this.channel=e.channel,this.wrapS=e.wrapS,this.wrapT=e.wrapT,this.magFilter=e.magFilter,this.minFilter=e.minFilter,this.anisotropy=e.anisotropy,this.format=e.format,this.internalFormat=e.internalFormat,this.type=e.type,this.normalized=e.normalized,this.offset.copy(e.offset),this.repeat.copy(e.repeat),this.center.copy(e.center),this.rotation=e.rotation,this.matrixAutoUpdate=e.matrixAutoUpdate,this.matrix.copy(e.matrix),this.generateMipmaps=e.generateMipmaps,this.premultiplyAlpha=e.premultiplyAlpha,this.flipY=e.flipY,this.unpackAlignment=e.unpackAlignment,this.colorSpace=e.colorSpace,this.renderTarget=e.renderTarget,this.isRenderTargetTexture=e.isRenderTargetTexture,this.isArrayTexture=e.isArrayTexture,this.userData=JSON.parse(JSON.stringify(e.userData)),this.needsUpdate=!0,this}setValues(e){for(const i in e){const r=e[i];if(r===void 0){ht(`Texture.setValues(): parameter '${i}' has value of undefined.`);continue}const l=this[i];if(l===void 0){ht(`Texture.setValues(): property '${i}' does not exist.`);continue}l&&r&&l.isVector2&&r.isVector2||l&&r&&l.isVector3&&r.isVector3||l&&r&&l.isMatrix3&&r.isMatrix3?l.copy(r):this[i]=r}}toJSON(e){const i=e===void 0||typeof e=="string";if(!i&&e.textures[this.uuid]!==void 0)return e.textures[this.uuid];const r={metadata:{version:4.7,type:"Texture",generator:"Texture.toJSON"},uuid:this.uuid,name:this.name,image:this.source.toJSON(e).uuid,mapping:this.mapping,channel:this.channel,repeat:[this.repeat.x,this.repeat.y],offset:[this.offset.x,this.offset.y],center:[this.center.x,this.center.y],rotation:this.rotation,wrap:[this.wrapS,this.wrapT],format:this.format,internalFormat:this.internalFormat,type:this.type,normalized:this.normalized,colorSpace:this.colorSpace,minFilter:this.minFilter,magFilter:this.magFilter,anisotropy:this.anisotropy,flipY:this.flipY,generateMipmaps:this.generateMipmaps,premultiplyAlpha:this.premultiplyAlpha,unpackAlignment:this.unpackAlignment};return Object.keys(this.userData).length>0&&(r.userData=this.userData),i||(e.textures[this.uuid]=r),r}dispose(){this.dispatchEvent({type:"dispose"})}transformUv(e){if(this.mapping!==Sx)return e;if(e.applyMatrix3(this.matrix),e.x<0||e.x>1)switch(this.wrapS){case Qh:e.x=e.x-Math.floor(e.x);break;case Sr:e.x=e.x<0?0:1;break;case Jh:Math.abs(Math.floor(e.x)%2)===1?e.x=Math.ceil(e.x)-e.x:e.x=e.x-Math.floor(e.x);break}if(e.y<0||e.y>1)switch(this.wrapT){case Qh:e.y=e.y-Math.floor(e.y);break;case Sr:e.y=e.y<0?0:1;break;case Jh:Math.abs(Math.floor(e.y)%2)===1?e.y=Math.ceil(e.y)-e.y:e.y=e.y-Math.floor(e.y);break}return this.flipY&&(e.y=1-e.y),e}set needsUpdate(e){e===!0&&(this.version++,this.source.needsUpdate=!0)}set needsPMREMUpdate(e){e===!0&&this.pmremVersion++}}gi.DEFAULT_IMAGE=null;gi.DEFAULT_MAPPING=Sx;gi.DEFAULT_ANISOTROPY=1;const om=class om{constructor(e=0,i=0,r=0,l=1){this.x=e,this.y=i,this.z=r,this.w=l}get width(){return this.z}set width(e){this.z=e}get height(){return this.w}set height(e){this.w=e}set(e,i,r,l){return this.x=e,this.y=i,this.z=r,this.w=l,this}setScalar(e){return this.x=e,this.y=e,this.z=e,this.w=e,this}setX(e){return this.x=e,this}setY(e){return this.y=e,this}setZ(e){return this.z=e,this}setW(e){return this.w=e,this}setComponent(e,i){switch(e){case 0:this.x=i;break;case 1:this.y=i;break;case 2:this.z=i;break;case 3:this.w=i;break;default:throw new Error("THREE.Vector4: index is out of range: "+e)}return this}getComponent(e){switch(e){case 0:return this.x;case 1:return this.y;case 2:return this.z;case 3:return this.w;default:throw new Error("THREE.Vector4: index is out of range: "+e)}}clone(){return new this.constructor(this.x,this.y,this.z,this.w)}copy(e){return this.x=e.x,this.y=e.y,this.z=e.z,this.w=e.w!==void 0?e.w:1,this}add(e){return this.x+=e.x,this.y+=e.y,this.z+=e.z,this.w+=e.w,this}addScalar(e){return this.x+=e,this.y+=e,this.z+=e,this.w+=e,this}addVectors(e,i){return this.x=e.x+i.x,this.y=e.y+i.y,this.z=e.z+i.z,this.w=e.w+i.w,this}addScaledVector(e,i){return this.x+=e.x*i,this.y+=e.y*i,this.z+=e.z*i,this.w+=e.w*i,this}sub(e){return this.x-=e.x,this.y-=e.y,this.z-=e.z,this.w-=e.w,this}subScalar(e){return this.x-=e,this.y-=e,this.z-=e,this.w-=e,this}subVectors(e,i){return this.x=e.x-i.x,this.y=e.y-i.y,this.z=e.z-i.z,this.w=e.w-i.w,this}multiply(e){return this.x*=e.x,this.y*=e.y,this.z*=e.z,this.w*=e.w,this}multiplyScalar(e){return this.x*=e,this.y*=e,this.z*=e,this.w*=e,this}applyMatrix4(e){const i=this.x,r=this.y,l=this.z,c=this.w,f=e.elements;return this.x=f[0]*i+f[4]*r+f[8]*l+f[12]*c,this.y=f[1]*i+f[5]*r+f[9]*l+f[13]*c,this.z=f[2]*i+f[6]*r+f[10]*l+f[14]*c,this.w=f[3]*i+f[7]*r+f[11]*l+f[15]*c,this}divide(e){return this.x/=e.x,this.y/=e.y,this.z/=e.z,this.w/=e.w,this}divideScalar(e){return this.multiplyScalar(1/e)}setAxisAngleFromQuaternion(e){this.w=2*Math.acos(e.w);const i=Math.sqrt(1-e.w*e.w);return i<1e-4?(this.x=1,this.y=0,this.z=0):(this.x=e.x/i,this.y=e.y/i,this.z=e.z/i),this}setAxisAngleFromRotationMatrix(e){let i,r,l,c;const m=e.elements,p=m[0],g=m[4],_=m[8],v=m[1],x=m[5],E=m[9],D=m[2],M=m[6],y=m[10];if(Math.abs(g-v)<.01&&Math.abs(_-D)<.01&&Math.abs(E-M)<.01){if(Math.abs(g+v)<.1&&Math.abs(_+D)<.1&&Math.abs(E+M)<.1&&Math.abs(p+x+y-3)<.1)return this.set(1,0,0,0),this;i=Math.PI;const V=(p+1)/2,R=(x+1)/2,N=(y+1)/2,L=(g+v)/4,P=(_+D)/4,T=(E+M)/4;return V>R&&V>N?V<.01?(r=0,l=.707106781,c=.707106781):(r=Math.sqrt(V),l=L/r,c=P/r):R>N?R<.01?(r=.707106781,l=0,c=.707106781):(l=Math.sqrt(R),r=L/l,c=T/l):N<.01?(r=.707106781,l=.707106781,c=0):(c=Math.sqrt(N),r=P/c,l=T/c),this.set(r,l,c,i),this}let F=Math.sqrt((M-E)*(M-E)+(_-D)*(_-D)+(v-g)*(v-g));return Math.abs(F)<.001&&(F=1),this.x=(M-E)/F,this.y=(_-D)/F,this.z=(v-g)/F,this.w=Math.acos((p+x+y-1)/2),this}setFromMatrixPosition(e){const i=e.elements;return this.x=i[12],this.y=i[13],this.z=i[14],this.w=i[15],this}min(e){return this.x=Math.min(this.x,e.x),this.y=Math.min(this.y,e.y),this.z=Math.min(this.z,e.z),this.w=Math.min(this.w,e.w),this}max(e){return this.x=Math.max(this.x,e.x),this.y=Math.max(this.y,e.y),this.z=Math.max(this.z,e.z),this.w=Math.max(this.w,e.w),this}clamp(e,i){return this.x=Ut(this.x,e.x,i.x),this.y=Ut(this.y,e.y,i.y),this.z=Ut(this.z,e.z,i.z),this.w=Ut(this.w,e.w,i.w),this}clampScalar(e,i){return this.x=Ut(this.x,e,i),this.y=Ut(this.y,e,i),this.z=Ut(this.z,e,i),this.w=Ut(this.w,e,i),this}clampLength(e,i){const r=this.length();return this.divideScalar(r||1).multiplyScalar(Ut(r,e,i))}floor(){return this.x=Math.floor(this.x),this.y=Math.floor(this.y),this.z=Math.floor(this.z),this.w=Math.floor(this.w),this}ceil(){return this.x=Math.ceil(this.x),this.y=Math.ceil(this.y),this.z=Math.ceil(this.z),this.w=Math.ceil(this.w),this}round(){return this.x=Math.round(this.x),this.y=Math.round(this.y),this.z=Math.round(this.z),this.w=Math.round(this.w),this}roundToZero(){return this.x=Math.trunc(this.x),this.y=Math.trunc(this.y),this.z=Math.trunc(this.z),this.w=Math.trunc(this.w),this}negate(){return this.x=-this.x,this.y=-this.y,this.z=-this.z,this.w=-this.w,this}dot(e){return this.x*e.x+this.y*e.y+this.z*e.z+this.w*e.w}lengthSq(){return this.x*this.x+this.y*this.y+this.z*this.z+this.w*this.w}length(){return Math.sqrt(this.x*this.x+this.y*this.y+this.z*this.z+this.w*this.w)}manhattanLength(){return Math.abs(this.x)+Math.abs(this.y)+Math.abs(this.z)+Math.abs(this.w)}normalize(){return this.divideScalar(this.length()||1)}setLength(e){return this.normalize().multiplyScalar(e)}lerp(e,i){return this.x+=(e.x-this.x)*i,this.y+=(e.y-this.y)*i,this.z+=(e.z-this.z)*i,this.w+=(e.w-this.w)*i,this}lerpVectors(e,i,r){return this.x=e.x+(i.x-e.x)*r,this.y=e.y+(i.y-e.y)*r,this.z=e.z+(i.z-e.z)*r,this.w=e.w+(i.w-e.w)*r,this}equals(e){return e.x===this.x&&e.y===this.y&&e.z===this.z&&e.w===this.w}fromArray(e,i=0){return this.x=e[i],this.y=e[i+1],this.z=e[i+2],this.w=e[i+3],this}toArray(e=[],i=0){return e[i]=this.x,e[i+1]=this.y,e[i+2]=this.z,e[i+3]=this.w,e}fromBufferAttribute(e,i){return this.x=e.getX(i),this.y=e.getY(i),this.z=e.getZ(i),this.w=e.getW(i),this}random(){return this.x=Math.random(),this.y=Math.random(),this.z=Math.random(),this.w=Math.random(),this}*[Symbol.iterator](){yield this.x,yield this.y,yield this.z,yield this.w}};om.prototype.isVector4=!0;let Ln=om;class Wb extends Is{constructor(e=1,i=1,r={}){super(),r=Object.assign({generateMipmaps:!1,internalFormat:null,minFilter:mi,depthBuffer:!0,stencilBuffer:!1,resolveColorBuffer:!0,resolveDepthBuffer:!0,resolveStencilBuffer:!0,storeMultisampledColorBuffer:!0,storeMultisampledDepthBuffer:!0,storeMultisampledStencilBuffer:!0,depthTexture:null,samples:0,count:1,depth:1,multiview:!1,useArrayDepthTexture:!1},r),this.isRenderTarget=!0,this.width=e,this.height=i,this.depth=r.depth,this.scissor=new Ln(0,0,e,i),this.scissorTest=!1,this.viewport=new Ln(0,0,e,i),this.textures=[];const l={width:e,height:i,depth:r.depth},c=new gi(l),f=r.count;for(let h=0;h<f;h++)this.textures[h]=c.clone(),this.textures[h].isRenderTargetTexture=!0,this.textures[h].renderTarget=this;this._setTextureOptions(r),this.depthBuffer=r.depthBuffer,this.stencilBuffer=r.stencilBuffer,this.resolveColorBuffer=r.resolveColorBuffer,this.resolveDepthBuffer=r.resolveDepthBuffer,this.resolveStencilBuffer=r.resolveStencilBuffer,this.storeMultisampledColorBuffer=r.storeMultisampledColorBuffer,this.storeMultisampledDepthBuffer=r.storeMultisampledDepthBuffer,this.storeMultisampledStencilBuffer=r.storeMultisampledStencilBuffer,this._depthTexture=null,this.depthTexture=r.depthTexture,this.samples=r.samples,this.multiview=r.multiview,this.useArrayDepthTexture=r.useArrayDepthTexture}_setTextureOptions(e={}){const i={minFilter:mi,generateMipmaps:!1,flipY:!1,internalFormat:null};e.mapping!==void 0&&(i.mapping=e.mapping),e.wrapS!==void 0&&(i.wrapS=e.wrapS),e.wrapT!==void 0&&(i.wrapT=e.wrapT),e.wrapR!==void 0&&(i.wrapR=e.wrapR),e.magFilter!==void 0&&(i.magFilter=e.magFilter),e.minFilter!==void 0&&(i.minFilter=e.minFilter),e.format!==void 0&&(i.format=e.format),e.type!==void 0&&(i.type=e.type),e.anisotropy!==void 0&&(i.anisotropy=e.anisotropy),e.colorSpace!==void 0&&(i.colorSpace=e.colorSpace),e.flipY!==void 0&&(i.flipY=e.flipY),e.generateMipmaps!==void 0&&(i.generateMipmaps=e.generateMipmaps),e.internalFormat!==void 0&&(i.internalFormat=e.internalFormat);for(let r=0;r<this.textures.length;r++)this.textures[r].setValues(i)}get texture(){return this.textures[0]}set texture(e){this.textures[0]=e}set depthTexture(e){this._depthTexture!==null&&this._depthTexture.renderTarget===this&&(this._depthTexture.renderTarget=null),e!==null&&e.renderTarget===null&&(e.renderTarget=this),this._depthTexture=e}get depthTexture(){return this._depthTexture}setSize(e,i,r=1){if(this.width!==e||this.height!==i||this.depth!==r){this.width=e,this.height=i,this.depth=r;for(let l=0,c=this.textures.length;l<c;l++)this.textures[l].image.width=e,this.textures[l].image.height=i,this.textures[l].image.depth=r,this.textures[l].isData3DTexture!==!0&&(this.textures[l].isArrayTexture=this.textures[l].image.depth>1);this.dispose()}this.viewport.set(0,0,e,i),this.scissor.set(0,0,e,i)}clone(){return new this.constructor().copy(this)}copy(e){this.width=e.width,this.height=e.height,this.depth=e.depth,this.scissor.copy(e.scissor),this.scissorTest=e.scissorTest,this.viewport.copy(e.viewport),this.textures.length=0;for(let i=0,r=e.textures.length;i<r;i++){this.textures[i]=e.textures[i].clone(),this.textures[i].isRenderTargetTexture=!0,this.textures[i].renderTarget=this;const l=Object.assign({},e.textures[i].image);this.textures[i].source=new jp(l)}if(this.depthBuffer=e.depthBuffer,this.stencilBuffer=e.stencilBuffer,this.resolveColorBuffer=e.resolveColorBuffer,this.resolveDepthBuffer=e.resolveDepthBuffer,this.resolveStencilBuffer=e.resolveStencilBuffer,this.storeMultisampledColorBuffer=e.storeMultisampledColorBuffer,this.storeMultisampledDepthBuffer=e.storeMultisampledDepthBuffer,this.storeMultisampledStencilBuffer=e.storeMultisampledStencilBuffer,e.depthTexture!==null)if(e.depthTexture.renderTarget===e){const i=e.depthTexture.clone();i.renderTarget=null,this.depthTexture=i}else this.depthTexture=e.depthTexture;return this.samples=e.samples,this.multiview=e.multiview,this.useArrayDepthTexture=e.useArrayDepthTexture,this}dispose(){this.dispatchEvent({type:"dispose"})}}class wa extends Wb{constructor(e=1,i=1,r={}){super(e,i,r),this.isWebGLRenderTarget=!0}}class wx extends gi{constructor(e=null,i=1,r=1,l=1){super(null),this.isDataArrayTexture=!0,this.image={data:e,width:i,height:r,depth:l},this.magFilter=li,this.minFilter=li,this.wrapR=Sr,this.generateMipmaps=!1,this.flipY=!1,this.unpackAlignment=1,this.layerUpdates=new Set}copy(e){return super.copy(e),this.wrapR=e.wrapR,this}addLayerUpdate(e){this.layerUpdates.add(e)}clearLayerUpdates(){this.layerUpdates.clear()}}class qb extends gi{constructor(e=null,i=1,r=1,l=1){super(null),this.isData3DTexture=!0,this.image={data:e,width:i,height:r,depth:l},this.magFilter=li,this.minFilter=li,this.wrapR=Sr,this.generateMipmaps=!1,this.flipY=!1,this.unpackAlignment=1}copy(e){return super.copy(e),this.wrapR=e.wrapR,this}}const ju=class ju{constructor(e,i,r,l,c,f,h,m,p,g,_,v,x,E,D,M){this.elements=[1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1],e!==void 0&&this.set(e,i,r,l,c,f,h,m,p,g,_,v,x,E,D,M)}set(e,i,r,l,c,f,h,m,p,g,_,v,x,E,D,M){const y=this.elements;return y[0]=e,y[4]=i,y[8]=r,y[12]=l,y[1]=c,y[5]=f,y[9]=h,y[13]=m,y[2]=p,y[6]=g,y[10]=_,y[14]=v,y[3]=x,y[7]=E,y[11]=D,y[15]=M,this}identity(){return this.set(1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1),this}clone(){return new ju().fromArray(this.elements)}copy(e){const i=this.elements,r=e.elements;return i[0]=r[0],i[1]=r[1],i[2]=r[2],i[3]=r[3],i[4]=r[4],i[5]=r[5],i[6]=r[6],i[7]=r[7],i[8]=r[8],i[9]=r[9],i[10]=r[10],i[11]=r[11],i[12]=r[12],i[13]=r[13],i[14]=r[14],i[15]=r[15],this}copyPosition(e){const i=this.elements,r=e.elements;return i[12]=r[12],i[13]=r[13],i[14]=r[14],this}setFromMatrix3(e){const i=e.elements;return this.set(i[0],i[3],i[6],0,i[1],i[4],i[7],0,i[2],i[5],i[8],0,0,0,0,1),this}extractBasis(e,i,r){return this.determinantAffine()===0?(e.set(1,0,0),i.set(0,1,0),r.set(0,0,1),this):(e.setFromMatrixColumn(this,0),i.setFromMatrixColumn(this,1),r.setFromMatrixColumn(this,2),this)}makeBasis(e,i,r){return this.set(e.x,i.x,r.x,0,e.y,i.y,r.y,0,e.z,i.z,r.z,0,0,0,0,1),this}extractRotation(e){if(e.determinantAffine()===0)return this.identity();const i=this.elements,r=e.elements,l=1/_o.setFromMatrixColumn(e,0).length(),c=1/_o.setFromMatrixColumn(e,1).length(),f=1/_o.setFromMatrixColumn(e,2).length();return i[0]=r[0]*l,i[1]=r[1]*l,i[2]=r[2]*l,i[3]=0,i[4]=r[4]*c,i[5]=r[5]*c,i[6]=r[6]*c,i[7]=0,i[8]=r[8]*f,i[9]=r[9]*f,i[10]=r[10]*f,i[11]=0,i[12]=0,i[13]=0,i[14]=0,i[15]=1,this}makeRotationFromEuler(e){const i=this.elements,r=e.x,l=e.y,c=e.z,f=Math.cos(r),h=Math.sin(r),m=Math.cos(l),p=Math.sin(l),g=Math.cos(c),_=Math.sin(c);if(e.order==="XYZ"){const v=f*g,x=f*_,E=h*g,D=h*_;i[0]=m*g,i[4]=-m*_,i[8]=p,i[1]=x+E*p,i[5]=v-D*p,i[9]=-h*m,i[2]=D-v*p,i[6]=E+x*p,i[10]=f*m}else if(e.order==="YXZ"){const v=m*g,x=m*_,E=p*g,D=p*_;i[0]=v+D*h,i[4]=E*h-x,i[8]=f*p,i[1]=f*_,i[5]=f*g,i[9]=-h,i[2]=x*h-E,i[6]=D+v*h,i[10]=f*m}else if(e.order==="ZXY"){const v=m*g,x=m*_,E=p*g,D=p*_;i[0]=v-D*h,i[4]=-f*_,i[8]=E+x*h,i[1]=x+E*h,i[5]=f*g,i[9]=D-v*h,i[2]=-f*p,i[6]=h,i[10]=f*m}else if(e.order==="ZYX"){const v=f*g,x=f*_,E=h*g,D=h*_;i[0]=m*g,i[4]=E*p-x,i[8]=v*p+D,i[1]=m*_,i[5]=D*p+v,i[9]=x*p-E,i[2]=-p,i[6]=h*m,i[10]=f*m}else if(e.order==="YZX"){const v=f*m,x=f*p,E=h*m,D=h*p;i[0]=m*g,i[4]=D-v*_,i[8]=E*_+x,i[1]=_,i[5]=f*g,i[9]=-h*g,i[2]=-p*g,i[6]=x*_+E,i[10]=v-D*_}else if(e.order==="XZY"){const v=f*m,x=f*p,E=h*m,D=h*p;i[0]=m*g,i[4]=-_,i[8]=p*g,i[1]=v*_+D,i[5]=f*g,i[9]=x*_-E,i[2]=E*_-x,i[6]=h*g,i[10]=D*_+v}return i[3]=0,i[7]=0,i[11]=0,i[12]=0,i[13]=0,i[14]=0,i[15]=1,this}makeRotationFromQuaternion(e){return this.compose(Yb,e,jb)}lookAt(e,i,r){const l=this.elements;return Wi.subVectors(e,i),Wi.lengthSq()===0&&(Wi.z=1),Wi.normalize(),Qr.crossVectors(r,Wi),Qr.lengthSq()===0&&(Math.abs(r.z)===1?Wi.x+=1e-4:Wi.z+=1e-4,Wi.normalize(),Qr.crossVectors(r,Wi)),Qr.normalize(),ru.crossVectors(Wi,Qr),l[0]=Qr.x,l[4]=ru.x,l[8]=Wi.x,l[1]=Qr.y,l[5]=ru.y,l[9]=Wi.y,l[2]=Qr.z,l[6]=ru.z,l[10]=Wi.z,this}multiply(e){return this.multiplyMatrices(this,e)}premultiply(e){return this.multiplyMatrices(e,this)}multiplyMatrices(e,i){const r=e.elements,l=i.elements,c=this.elements,f=r[0],h=r[4],m=r[8],p=r[12],g=r[1],_=r[5],v=r[9],x=r[13],E=r[2],D=r[6],M=r[10],y=r[14],F=r[3],V=r[7],R=r[11],N=r[15],L=l[0],P=l[4],T=l[8],O=l[12],B=l[1],k=l[5],J=l[9],se=l[13],Y=l[2],j=l[6],z=l[10],H=l[14],ee=l[3],oe=l[7],fe=l[11],U=l[15];return c[0]=f*L+h*B+m*Y+p*ee,c[4]=f*P+h*k+m*j+p*oe,c[8]=f*T+h*J+m*z+p*fe,c[12]=f*O+h*se+m*H+p*U,c[1]=g*L+_*B+v*Y+x*ee,c[5]=g*P+_*k+v*j+x*oe,c[9]=g*T+_*J+v*z+x*fe,c[13]=g*O+_*se+v*H+x*U,c[2]=E*L+D*B+M*Y+y*ee,c[6]=E*P+D*k+M*j+y*oe,c[10]=E*T+D*J+M*z+y*fe,c[14]=E*O+D*se+M*H+y*U,c[3]=F*L+V*B+R*Y+N*ee,c[7]=F*P+V*k+R*j+N*oe,c[11]=F*T+V*J+R*z+N*fe,c[15]=F*O+V*se+R*H+N*U,this}multiplyScalar(e){const i=this.elements;return i[0]*=e,i[4]*=e,i[8]*=e,i[12]*=e,i[1]*=e,i[5]*=e,i[9]*=e,i[13]*=e,i[2]*=e,i[6]*=e,i[10]*=e,i[14]*=e,i[3]*=e,i[7]*=e,i[11]*=e,i[15]*=e,this}determinant(){const e=this.elements,i=e[0],r=e[4],l=e[8],c=e[12],f=e[1],h=e[5],m=e[9],p=e[13],g=e[2],_=e[6],v=e[10],x=e[14],E=e[3],D=e[7],M=e[11],y=e[15],F=m*x-p*v,V=h*x-p*_,R=h*v-m*_,N=f*x-p*g,L=f*v-m*g,P=f*_-h*g;return i*(D*F-M*V+y*R)-r*(E*F-M*N+y*L)+l*(E*V-D*N+y*P)-c*(E*R-D*L+M*P)}determinantAffine(){const e=this.elements,i=e[0],r=e[4],l=e[8],c=e[1],f=e[5],h=e[9],m=e[2],p=e[6],g=e[10];return i*(f*g-h*p)-r*(c*g-h*m)+l*(c*p-f*m)}transpose(){const e=this.elements;let i;return i=e[1],e[1]=e[4],e[4]=i,i=e[2],e[2]=e[8],e[8]=i,i=e[6],e[6]=e[9],e[9]=i,i=e[3],e[3]=e[12],e[12]=i,i=e[7],e[7]=e[13],e[13]=i,i=e[11],e[11]=e[14],e[14]=i,this}setPosition(e,i,r){const l=this.elements;return e.isVector3?(l[12]=e.x,l[13]=e.y,l[14]=e.z):(l[12]=e,l[13]=i,l[14]=r),this}invert(){const e=this.elements,i=e[0],r=e[1],l=e[2],c=e[3],f=e[4],h=e[5],m=e[6],p=e[7],g=e[8],_=e[9],v=e[10],x=e[11],E=e[12],D=e[13],M=e[14],y=e[15],F=i*h-r*f,V=i*m-l*f,R=i*p-c*f,N=r*m-l*h,L=r*p-c*h,P=l*p-c*m,T=g*D-_*E,O=g*M-v*E,B=g*y-x*E,k=_*M-v*D,J=_*y-x*D,se=v*y-x*M,Y=F*se-V*J+R*k+N*B-L*O+P*T;if(Y===0)return this.set(0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0);const j=1/Y;return e[0]=(h*se-m*J+p*k)*j,e[1]=(l*J-r*se-c*k)*j,e[2]=(D*P-M*L+y*N)*j,e[3]=(v*L-_*P-x*N)*j,e[4]=(m*B-f*se-p*O)*j,e[5]=(i*se-l*B+c*O)*j,e[6]=(M*R-E*P-y*V)*j,e[7]=(g*P-v*R+x*V)*j,e[8]=(f*J-h*B+p*T)*j,e[9]=(r*B-i*J-c*T)*j,e[10]=(E*L-D*R+y*F)*j,e[11]=(_*R-g*L-x*F)*j,e[12]=(h*O-f*k-m*T)*j,e[13]=(i*k-r*O+l*T)*j,e[14]=(D*V-E*N-M*F)*j,e[15]=(g*N-_*V+v*F)*j,this}scale(e){const i=this.elements,r=e.x,l=e.y,c=e.z;return i[0]*=r,i[4]*=l,i[8]*=c,i[1]*=r,i[5]*=l,i[9]*=c,i[2]*=r,i[6]*=l,i[10]*=c,i[3]*=r,i[7]*=l,i[11]*=c,this}getMaxScaleOnAxis(){const e=this.elements,i=e[0]*e[0]+e[1]*e[1]+e[2]*e[2],r=e[4]*e[4]+e[5]*e[5]+e[6]*e[6],l=e[8]*e[8]+e[9]*e[9]+e[10]*e[10];return Math.sqrt(Math.max(i,r,l))}makeTranslation(e,i,r){return e.isVector3?this.set(1,0,0,e.x,0,1,0,e.y,0,0,1,e.z,0,0,0,1):this.set(1,0,0,e,0,1,0,i,0,0,1,r,0,0,0,1),this}makeRotationX(e){const i=Math.cos(e),r=Math.sin(e);return this.set(1,0,0,0,0,i,-r,0,0,r,i,0,0,0,0,1),this}makeRotationY(e){const i=Math.cos(e),r=Math.sin(e);return this.set(i,0,r,0,0,1,0,0,-r,0,i,0,0,0,0,1),this}makeRotationZ(e){const i=Math.cos(e),r=Math.sin(e);return this.set(i,-r,0,0,r,i,0,0,0,0,1,0,0,0,0,1),this}makeRotationAxis(e,i){const r=Math.cos(i),l=Math.sin(i),c=1-r,f=e.x,h=e.y,m=e.z,p=c*f,g=c*h;return this.set(p*f+r,p*h-l*m,p*m+l*h,0,p*h+l*m,g*h+r,g*m-l*f,0,p*m-l*h,g*m+l*f,c*m*m+r,0,0,0,0,1),this}makeScale(e,i,r){return this.set(e,0,0,0,0,i,0,0,0,0,r,0,0,0,0,1),this}makeShear(e,i,r,l,c,f){return this.set(1,r,c,0,e,1,f,0,i,l,1,0,0,0,0,1),this}compose(e,i,r){const l=this.elements,c=i._x,f=i._y,h=i._z,m=i._w,p=c+c,g=f+f,_=h+h,v=c*p,x=c*g,E=c*_,D=f*g,M=f*_,y=h*_,F=m*p,V=m*g,R=m*_,N=r.x,L=r.y,P=r.z;return l[0]=(1-(D+y))*N,l[1]=(x+R)*N,l[2]=(E-V)*N,l[3]=0,l[4]=(x-R)*L,l[5]=(1-(v+y))*L,l[6]=(M+F)*L,l[7]=0,l[8]=(E+V)*P,l[9]=(M-F)*P,l[10]=(1-(v+D))*P,l[11]=0,l[12]=e.x,l[13]=e.y,l[14]=e.z,l[15]=1,this}decompose(e,i,r){const l=this.elements;e.x=l[12],e.y=l[13],e.z=l[14];const c=this.determinantAffine();if(c===0)return r.set(1,1,1),i.identity(),this;let f=_o.set(l[0],l[1],l[2]).length();const h=_o.set(l[4],l[5],l[6]).length(),m=_o.set(l[8],l[9],l[10]).length();c<0&&(f=-f),ba.copy(this);const p=1/f,g=1/h,_=1/m;return ba.elements[0]*=p,ba.elements[1]*=p,ba.elements[2]*=p,ba.elements[4]*=g,ba.elements[5]*=g,ba.elements[6]*=g,ba.elements[8]*=_,ba.elements[9]*=_,ba.elements[10]*=_,i.setFromRotationMatrix(ba),r.x=f,r.y=h,r.z=m,this}makePerspective(e,i,r,l,c,f,h=ka,m=!1){const p=this.elements,g=2*c/(i-e),_=2*c/(r-l),v=(i+e)/(i-e),x=(r+l)/(r-l);let E,D;if(m)E=c/(f-c),D=f*c/(f-c);else if(h===ka)E=-(f+c)/(f-c),D=-2*f*c/(f-c);else if(h===Xu)E=-f/(f-c),D=-f*c/(f-c);else throw new Error("THREE.Matrix4.makePerspective(): Invalid coordinate system: "+h);return p[0]=g,p[4]=0,p[8]=v,p[12]=0,p[1]=0,p[5]=_,p[9]=x,p[13]=0,p[2]=0,p[6]=0,p[10]=E,p[14]=D,p[3]=0,p[7]=0,p[11]=-1,p[15]=0,this}makeOrthographic(e,i,r,l,c,f,h=ka,m=!1){const p=this.elements,g=2/(i-e),_=2/(r-l),v=-(i+e)/(i-e),x=-(r+l)/(r-l);let E,D;if(m)E=1/(f-c),D=f/(f-c);else if(h===ka)E=-2/(f-c),D=-(f+c)/(f-c);else if(h===Xu)E=-1/(f-c),D=-c/(f-c);else throw new Error("THREE.Matrix4.makeOrthographic(): Invalid coordinate system: "+h);return p[0]=g,p[4]=0,p[8]=0,p[12]=v,p[1]=0,p[5]=_,p[9]=0,p[13]=x,p[2]=0,p[6]=0,p[10]=E,p[14]=D,p[3]=0,p[7]=0,p[11]=0,p[15]=1,this}equals(e){const i=this.elements,r=e.elements;for(let l=0;l<16;l++)if(i[l]!==r[l])return!1;return!0}fromArray(e,i=0){for(let r=0;r<16;r++)this.elements[r]=e[r+i];return this}toArray(e=[],i=0){const r=this.elements;return e[i]=r[0],e[i+1]=r[1],e[i+2]=r[2],e[i+3]=r[3],e[i+4]=r[4],e[i+5]=r[5],e[i+6]=r[6],e[i+7]=r[7],e[i+8]=r[8],e[i+9]=r[9],e[i+10]=r[10],e[i+11]=r[11],e[i+12]=r[12],e[i+13]=r[13],e[i+14]=r[14],e[i+15]=r[15],e}};ju.prototype.isMatrix4=!0;let En=ju;const _o=new Q,ba=new En,Yb=new Q(0,0,0),jb=new Q(1,1,1),Qr=new Q,ru=new Q,Wi=new Q,a_=new En,r_=new ss;class Ps{constructor(e=0,i=0,r=0,l=Ps.DEFAULT_ORDER){this.isEuler=!0,this._x=e,this._y=i,this._z=r,this._order=l}get x(){return this._x}set x(e){this._x=e,this._onChangeCallback()}get y(){return this._y}set y(e){this._y=e,this._onChangeCallback()}get z(){return this._z}set z(e){this._z=e,this._onChangeCallback()}get order(){return this._order}set order(e){this._order=e,this._onChangeCallback()}set(e,i,r,l=this._order){return this._x=e,this._y=i,this._z=r,this._order=l,this._onChangeCallback(),this}clone(){return new this.constructor(this._x,this._y,this._z,this._order)}copy(e){return this._x=e._x,this._y=e._y,this._z=e._z,this._order=e._order,this._onChangeCallback(),this}setFromRotationMatrix(e,i=this._order,r=!0){const l=e.elements,c=l[0],f=l[4],h=l[8],m=l[1],p=l[5],g=l[9],_=l[2],v=l[6],x=l[10];switch(i){case"XYZ":this._y=Math.asin(Ut(h,-1,1)),Math.abs(h)<.9999999?(this._x=Math.atan2(-g,x),this._z=Math.atan2(-f,c)):(this._x=Math.atan2(v,p),this._z=0);break;case"YXZ":this._x=Math.asin(-Ut(g,-1,1)),Math.abs(g)<.9999999?(this._y=Math.atan2(h,x),this._z=Math.atan2(m,p)):(this._y=Math.atan2(-_,c),this._z=0);break;case"ZXY":this._x=Math.asin(Ut(v,-1,1)),Math.abs(v)<.9999999?(this._y=Math.atan2(-_,x),this._z=Math.atan2(-f,p)):(this._y=0,this._z=Math.atan2(m,c));break;case"ZYX":this._y=Math.asin(-Ut(_,-1,1)),Math.abs(_)<.9999999?(this._x=Math.atan2(v,x),this._z=Math.atan2(m,c)):(this._x=0,this._z=Math.atan2(-f,p));break;case"YZX":this._z=Math.asin(Ut(m,-1,1)),Math.abs(m)<.9999999?(this._x=Math.atan2(-g,p),this._y=Math.atan2(-_,c)):(this._x=0,this._y=Math.atan2(h,x));break;case"XZY":this._z=Math.asin(-Ut(f,-1,1)),Math.abs(f)<.9999999?(this._x=Math.atan2(v,p),this._y=Math.atan2(h,c)):(this._x=Math.atan2(-g,x),this._y=0);break;default:ht("Euler: .setFromRotationMatrix() encountered an unknown order: "+i)}return this._order=i,r===!0&&this._onChangeCallback(),this}setFromQuaternion(e,i,r){return a_.makeRotationFromQuaternion(e),this.setFromRotationMatrix(a_,i,r)}setFromVector3(e,i=this._order){return this.set(e.x,e.y,e.z,i)}reorder(e){return r_.setFromEuler(this),this.setFromQuaternion(r_,e)}equals(e){return e._x===this._x&&e._y===this._y&&e._z===this._z&&e._order===this._order}fromArray(e){return this._x=e[0],this._y=e[1],this._z=e[2],e[3]!==void 0&&(this._order=e[3]),this._onChangeCallback(),this}toArray(e=[],i=0){return e[i]=this._x,e[i+1]=this._y,e[i+2]=this._z,e[i+3]=this._order,e}_onChange(e){return this._onChangeCallback=e,this}_onChangeCallback(){}*[Symbol.iterator](){yield this._x,yield this._y,yield this._z,yield this._order}}Ps.DEFAULT_ORDER="XYZ";class Zp{constructor(){this.mask=1}set(e){this.mask=(1<<e|0)>>>0}enable(e){this.mask|=1<<e|0}enableAll(){this.mask=-1}toggle(e){this.mask^=1<<e|0}disable(e){this.mask&=~(1<<e|0)}disableAll(){this.mask=0}test(e){return(this.mask&e.mask)!==0}isEnabled(e){return(this.mask&(1<<e|0))!==0}}let Zb=0;const s_=new Q,xo=new ss,hr=new En,su=new Q,Ul=new Q,Kb=new Q,Qb=new ss,o_=new Q(1,0,0),l_=new Q(0,1,0),c_=new Q(0,0,1),u_={type:"added"},Jb={type:"removed"},So={type:"childadded",child:null},ph={type:"childremoved",child:null};class Ti extends Is{constructor(){super(),this.isObject3D=!0,Object.defineProperty(this,"id",{value:Zb++}),this.uuid=Go(),this.name="",this.type="Object3D",this.parent=null,this.children=[],this.up=Ti.DEFAULT_UP.clone();const e=new Q,i=new Ps,r=new ss,l=new Q(1,1,1);function c(){r.setFromEuler(i,!1)}function f(){i.setFromQuaternion(r,void 0,!1)}i._onChange(c),r._onChange(f),Object.defineProperties(this,{position:{configurable:!0,enumerable:!0,value:e},rotation:{configurable:!0,enumerable:!0,value:i},quaternion:{configurable:!0,enumerable:!0,value:r},scale:{configurable:!0,enumerable:!0,value:l},modelViewMatrix:{value:new En},normalMatrix:{value:new yt}}),this.matrix=new En,this.matrixWorld=new En,this.matrixAutoUpdate=Ti.DEFAULT_MATRIX_AUTO_UPDATE,this.matrixWorldAutoUpdate=Ti.DEFAULT_MATRIX_WORLD_AUTO_UPDATE,this.matrixWorldNeedsUpdate=!1,this.layers=new Zp,this.visible=!0,this.castShadow=!1,this.receiveShadow=!1,this.frustumCulled=!0,this.renderOrder=0,this.animations=[],this.customDepthMaterial=void 0,this.customDistanceMaterial=void 0,this.static=!1,this.userData={},this.pivot=null}onBeforeShadow(){}onAfterShadow(){}onBeforeRender(){}onAfterRender(){}applyMatrix4(e){this.matrixAutoUpdate&&this.updateMatrix(),this.matrix.premultiply(e),this.matrix.decompose(this.position,this.quaternion,this.scale)}applyQuaternion(e){return this.quaternion.premultiply(e),this}setRotationFromAxisAngle(e,i){this.quaternion.setFromAxisAngle(e,i)}setRotationFromEuler(e){this.quaternion.setFromEuler(e,!0)}setRotationFromMatrix(e){this.quaternion.setFromRotationMatrix(e)}setRotationFromQuaternion(e){this.quaternion.copy(e)}rotateOnAxis(e,i){return xo.setFromAxisAngle(e,i),this.quaternion.multiply(xo),this}rotateOnWorldAxis(e,i){return xo.setFromAxisAngle(e,i),this.quaternion.premultiply(xo),this}rotateX(e){return this.rotateOnAxis(o_,e)}rotateY(e){return this.rotateOnAxis(l_,e)}rotateZ(e){return this.rotateOnAxis(c_,e)}translateOnAxis(e,i){return s_.copy(e).applyQuaternion(this.quaternion),this.position.add(s_.multiplyScalar(i)),this}translateX(e){return this.translateOnAxis(o_,e)}translateY(e){return this.translateOnAxis(l_,e)}translateZ(e){return this.translateOnAxis(c_,e)}localToWorld(e){return this.updateWorldMatrix(!0,!1),e.applyMatrix4(this.matrixWorld)}worldToLocal(e){return this.updateWorldMatrix(!0,!1),e.applyMatrix4(hr.copy(this.matrixWorld).invert())}lookAt(e,i,r){e.isVector3?su.copy(e):su.set(e,i,r);const l=this.parent;this.updateWorldMatrix(!0,!1),Ul.setFromMatrixPosition(this.matrixWorld),this.isCamera||this.isLight?hr.lookAt(Ul,su,this.up):hr.lookAt(su,Ul,this.up),this.quaternion.setFromRotationMatrix(hr),l&&(hr.extractRotation(l.matrixWorld),xo.setFromRotationMatrix(hr),this.quaternion.premultiply(xo.invert()))}add(e){if(arguments.length>1){for(let i=0;i<arguments.length;i++)this.add(arguments[i]);return this}return e===this?(Zt("Object3D.add: object can't be added as a child of itself.",e),this):(e&&e.isObject3D?(e.removeFromParent(),e.parent=this,this.children.push(e),e.dispatchEvent(u_),So.child=e,this.dispatchEvent(So),So.child=null):Zt("Object3D.add: object not an instance of THREE.Object3D.",e),this)}remove(e){if(arguments.length>1){for(let r=0;r<arguments.length;r++)this.remove(arguments[r]);return this}const i=this.children.indexOf(e);return i!==-1&&(e.parent=null,this.children.splice(i,1),e.dispatchEvent(Jb),ph.child=e,this.dispatchEvent(ph),ph.child=null),this}removeFromParent(){const e=this.parent;return e!==null&&e.remove(this),this}clear(){return this.remove(...this.children)}attach(e){return this.updateWorldMatrix(!0,!1),hr.copy(this.matrixWorld).invert(),e.parent!==null&&(e.parent.updateWorldMatrix(!0,!1),hr.multiply(e.parent.matrixWorld)),e.applyMatrix4(hr),e.removeFromParent(),e.parent=this,this.children.push(e),e.updateWorldMatrix(!1,!0),e.dispatchEvent(u_),So.child=e,this.dispatchEvent(So),So.child=null,this}getObjectById(e){return this.getObjectByProperty("id",e)}getObjectByName(e){return this.getObjectByProperty("name",e)}getObjectByProperty(e,i){if(this[e]===i)return this;for(let r=0,l=this.children.length;r<l;r++){const f=this.children[r].getObjectByProperty(e,i);if(f!==void 0)return f}}getObjectsByProperty(e,i,r=[]){this[e]===i&&r.push(this);const l=this.children;for(let c=0,f=l.length;c<f;c++)l[c].getObjectsByProperty(e,i,r);return r}getWorldPosition(e){return this.updateWorldMatrix(!0,!1),e.setFromMatrixPosition(this.matrixWorld)}getWorldQuaternion(e){return this.updateWorldMatrix(!0,!1),this.matrixWorld.decompose(Ul,e,Kb),e}getWorldScale(e){return this.updateWorldMatrix(!0,!1),this.matrixWorld.decompose(Ul,Qb,e),e}getWorldDirection(e){this.updateWorldMatrix(!0,!1);const i=this.matrixWorld.elements;return e.set(i[8],i[9],i[10]).normalize()}raycast(){}intersectsFrustum(){}traverse(e){e(this);const i=this.children;for(let r=0,l=i.length;r<l;r++)i[r].traverse(e)}traverseVisible(e){if(this.visible===!1)return;e(this);const i=this.children;for(let r=0,l=i.length;r<l;r++)i[r].traverseVisible(e)}traverseAncestors(e){const i=this.parent;i!==null&&(e(i),i.traverseAncestors(e))}updateMatrix(){this.matrix.compose(this.position,this.quaternion,this.scale);const e=this.pivot;if(e!==null){const i=e.x,r=e.y,l=e.z,c=this.matrix.elements;c[12]+=i-c[0]*i-c[4]*r-c[8]*l,c[13]+=r-c[1]*i-c[5]*r-c[9]*l,c[14]+=l-c[2]*i-c[6]*r-c[10]*l}this.matrixWorldNeedsUpdate=!0}updateMatrixWorld(e){this.matrixAutoUpdate&&this.updateMatrix(),(this.matrixWorldNeedsUpdate||e)&&(this.matrixWorldAutoUpdate===!0&&(this.parent===null?this.matrixWorld.copy(this.matrix):this.matrixWorld.multiplyMatrices(this.parent.matrixWorld,this.matrix)),this.matrixWorldNeedsUpdate=!1,e=!0);const i=this.children;for(let r=0,l=i.length;r<l;r++)i[r].updateMatrixWorld(e)}updateWorldMatrix(e,i,r=!1){const l=this.parent;if(e===!0&&l!==null&&l.updateWorldMatrix(!0,!1),this.matrixAutoUpdate&&this.updateMatrix(),(this.matrixWorldNeedsUpdate||r)&&(this.matrixWorldAutoUpdate===!0&&(this.parent===null?this.matrixWorld.copy(this.matrix):this.matrixWorld.multiplyMatrices(this.parent.matrixWorld,this.matrix)),this.matrixWorldNeedsUpdate=!1,r=!0),i===!0){const c=this.children;for(let f=0,h=c.length;f<h;f++)c[f].updateWorldMatrix(!1,!0,r)}}toJSON(e){const i=e===void 0||typeof e=="string",r={};i&&(e={geometries:{},materials:{},textures:{},images:{},shapes:{},skeletons:{},animations:{},nodes:{}},r.metadata={version:4.7,type:"Object",generator:"Object3D.toJSON"});const l={};l.uuid=this.uuid,l.type=this.type,l.name=this.name,l.castShadow=this.castShadow,l.receiveShadow=this.receiveShadow,l.visible=this.visible,l.frustumCulled=this.frustumCulled,l.renderOrder=this.renderOrder,l.static=this.static,l.matrixAutoUpdate=this.matrixAutoUpdate,Object.keys(this.userData).length>0&&(l.userData=this.userData),l.layers=this.layers.mask,l.matrix=this.matrix.toArray(),l.up=this.up.toArray(),this.pivot!==null&&(l.pivot=this.pivot.toArray()),this.morphTargetDictionary!==void 0&&(l.morphTargetDictionary=Object.assign({},this.morphTargetDictionary)),this.morphTargetInfluences!==void 0&&(l.morphTargetInfluences=this.morphTargetInfluences.slice()),this.isInstancedMesh&&(l.type="InstancedMesh",l.count=this.count,l.instanceMatrix=this.instanceMatrix.toJSON(),this.instanceColor!==null&&(l.instanceColor=this.instanceColor.toJSON())),this.isBatchedMesh&&(l.type="BatchedMesh",l.perObjectFrustumCulled=this.perObjectFrustumCulled,l.sortObjects=this.sortObjects,l.drawRanges=this._drawRanges,l.reservedRanges=this._reservedRanges,l.geometryInfo=this._geometryInfo.map(h=>({...h,boundingBox:h.boundingBox?h.boundingBox.toJSON():void 0,boundingSphere:h.boundingSphere?h.boundingSphere.toJSON():void 0})),l.instanceInfo=this._instanceInfo.map(h=>({...h})),l.availableInstanceIds=this._availableInstanceIds.slice(),l.availableGeometryIds=this._availableGeometryIds.slice(),l.nextIndexStart=this._nextIndexStart,l.nextVertexStart=this._nextVertexStart,l.geometryCount=this._geometryCount,l.maxInstanceCount=this._maxInstanceCount,l.maxVertexCount=this._maxVertexCount,l.maxIndexCount=this._maxIndexCount,l.geometryInitialized=this._geometryInitialized,l.matricesTexture=this._matricesTexture.toJSON(e),l.indirectTexture=this._indirectTexture.toJSON(e),this._colorsTexture!==null&&(l.colorsTexture=this._colorsTexture.toJSON(e)),this.boundingSphere!==null&&(l.boundingSphere=this.boundingSphere.toJSON()),this.boundingBox!==null&&(l.boundingBox=this.boundingBox.toJSON()));function c(h,m){return h[m.uuid]===void 0&&(h[m.uuid]=m.toJSON(e)),m.uuid}if(this.isScene)this.background&&(this.background.isColor?l.background=this.background.toJSON():this.background.isTexture&&(l.background=this.background.toJSON(e).uuid)),this.environment&&this.environment.isTexture&&this.environment.isRenderTargetTexture!==!0&&(l.environment=this.environment.toJSON(e).uuid);else if(this.isMesh||this.isLine||this.isPoints){l.geometry=c(e.geometries,this.geometry);const h=this.geometry.parameters;if(h!==void 0&&h.shapes!==void 0){const m=h.shapes;if(Array.isArray(m))for(let p=0,g=m.length;p<g;p++){const _=m[p];c(e.shapes,_)}else c(e.shapes,m)}}if(this.isSkinnedMesh&&(l.bindMode=this.bindMode,l.bindMatrix=this.bindMatrix.toArray(),this.skeleton!==void 0&&(c(e.skeletons,this.skeleton),l.skeleton=this.skeleton.uuid)),this.material!==void 0)if(Array.isArray(this.material)){const h=[];for(let m=0,p=this.material.length;m<p;m++)h.push(c(e.materials,this.material[m]));l.material=h}else l.material=c(e.materials,this.material);if(this.children.length>0){l.children=[];for(let h=0;h<this.children.length;h++)l.children.push(this.children[h].toJSON(e).object)}if(this.animations.length>0){l.animations=[];for(let h=0;h<this.animations.length;h++){const m=this.animations[h];l.animations.push(c(e.animations,m))}}if(i){const h=f(e.geometries),m=f(e.materials),p=f(e.textures),g=f(e.images),_=f(e.shapes),v=f(e.skeletons),x=f(e.animations),E=f(e.nodes);h.length>0&&(r.geometries=h),m.length>0&&(r.materials=m),p.length>0&&(r.textures=p),g.length>0&&(r.images=g),_.length>0&&(r.shapes=_),v.length>0&&(r.skeletons=v),x.length>0&&(r.animations=x),E.length>0&&(r.nodes=E)}return r.object=l,r;function f(h){const m=[];for(const p in h){const g=h[p];delete g.metadata,m.push(g)}return m}}clone(e){return new this.constructor().copy(this,e)}copy(e,i=!0){if(this.name=e.name,this.up.copy(e.up),this.position.copy(e.position),this.rotation.order=e.rotation.order,this.quaternion.copy(e.quaternion),this.scale.copy(e.scale),this.pivot=e.pivot!==null?e.pivot.clone():null,this.matrix.copy(e.matrix),this.matrixWorld.copy(e.matrixWorld),this.matrixAutoUpdate=e.matrixAutoUpdate,this.matrixWorldAutoUpdate=e.matrixWorldAutoUpdate,this.matrixWorldNeedsUpdate=e.matrixWorldNeedsUpdate,this.layers.mask=e.layers.mask,this.visible=e.visible,this.castShadow=e.castShadow,this.receiveShadow=e.receiveShadow,this.frustumCulled=e.frustumCulled,this.renderOrder=e.renderOrder,this.static=e.static,this.animations=e.animations.slice(),this.userData=JSON.parse(JSON.stringify(e.userData)),i===!0)for(let r=0;r<e.children.length;r++){const l=e.children[r];this.add(l.clone())}return this}dispose(){this.dispatchEvent({type:"dispose"})}}Ti.DEFAULT_UP=new Q(0,1,0);Ti.DEFAULT_MATRIX_AUTO_UPDATE=!0;Ti.DEFAULT_MATRIX_WORLD_AUTO_UPDATE=!0;class da extends Ti{constructor(){super(),this.isGroup=!0,this.type="Group"}}const $b={type:"move"};class mh{constructor(){this._targetRay=null,this._grip=null,this._hand=null}getHandSpace(){return this._hand===null&&(this._hand=new da,this._hand.matrixAutoUpdate=!1,this._hand.visible=!1,this._hand.joints={},this._hand.inputState={pinching:!1}),this._hand}getTargetRaySpace(){return this._targetRay===null&&(this._targetRay=new da,this._targetRay.matrixAutoUpdate=!1,this._targetRay.visible=!1,this._targetRay.hasLinearVelocity=!1,this._targetRay.linearVelocity=new Q,this._targetRay.hasAngularVelocity=!1,this._targetRay.angularVelocity=new Q),this._targetRay}getGripSpace(){return this._grip===null&&(this._grip=new da,this._grip.matrixAutoUpdate=!1,this._grip.visible=!1,this._grip.hasLinearVelocity=!1,this._grip.linearVelocity=new Q,this._grip.hasAngularVelocity=!1,this._grip.angularVelocity=new Q,this._grip.eventsEnabled=!1),this._grip}dispatchEvent(e){return this._targetRay!==null&&this._targetRay.dispatchEvent(e),this._grip!==null&&this._grip.dispatchEvent(e),this._hand!==null&&this._hand.dispatchEvent(e),this}connect(e){if(e&&e.hand){const i=this._hand;if(i)for(const r of e.hand.values())this._getHandJoint(i,r)}return this.dispatchEvent({type:"connected",data:e}),this}disconnect(e){return this.dispatchEvent({type:"disconnected",data:e}),this._targetRay!==null&&(this._targetRay.visible=!1),this._grip!==null&&(this._grip.visible=!1),this._hand!==null&&(this._hand.visible=!1),this}update(e,i,r){let l=null,c=null,f=null;const h=this._targetRay,m=this._grip,p=this._hand;if(e&&i.session.visibilityState!=="visible-blurred"){if(p&&e.hand){f=!0;for(const D of e.hand.values()){const M=i.getJointPose(D,r),y=this._getHandJoint(p,D);M!==null&&(y.matrix.fromArray(M.transform.matrix),y.matrix.decompose(y.position,y.rotation,y.scale),y.matrixWorldNeedsUpdate=!0,y.jointRadius=M.radius),y.visible=M!==null}const g=p.joints["index-finger-tip"],_=p.joints["thumb-tip"],v=g.position.distanceTo(_.position),x=.02,E=.005;p.inputState.pinching&&v>x+E?(p.inputState.pinching=!1,this.dispatchEvent({type:"pinchend",handedness:e.handedness,target:this})):!p.inputState.pinching&&v<=x-E&&(p.inputState.pinching=!0,this.dispatchEvent({type:"pinchstart",handedness:e.handedness,target:this}))}else m!==null&&e.gripSpace&&(c=i.getPose(e.gripSpace,r),c!==null&&(m.matrix.fromArray(c.transform.matrix),m.matrix.decompose(m.position,m.rotation,m.scale),m.matrixWorldNeedsUpdate=!0,c.linearVelocity?(m.hasLinearVelocity=!0,m.linearVelocity.copy(c.linearVelocity)):m.hasLinearVelocity=!1,c.angularVelocity?(m.hasAngularVelocity=!0,m.angularVelocity.copy(c.angularVelocity)):m.hasAngularVelocity=!1,m.eventsEnabled&&m.dispatchEvent({type:"gripUpdated",data:e,target:this})));h!==null&&(l=i.getPose(e.targetRaySpace,r),l===null&&c!==null&&(l=c),l!==null&&(h.matrix.fromArray(l.transform.matrix),h.matrix.decompose(h.position,h.rotation,h.scale),h.matrixWorldNeedsUpdate=!0,l.linearVelocity?(h.hasLinearVelocity=!0,h.linearVelocity.copy(l.linearVelocity)):h.hasLinearVelocity=!1,l.angularVelocity?(h.hasAngularVelocity=!0,h.angularVelocity.copy(l.angularVelocity)):h.hasAngularVelocity=!1,this.dispatchEvent($b)))}return h!==null&&(h.visible=l!==null),m!==null&&(m.visible=c!==null),p!==null&&(p.visible=f!==null),this}_getHandJoint(e,i){if(e.joints[i.jointName]===void 0){const r=new da;r.matrixAutoUpdate=!1,r.visible=!1,e.joints[i.jointName]=r,e.add(r)}return e.joints[i.jointName]}}const Dx={aliceblue:15792383,antiquewhite:16444375,aqua:65535,aquamarine:8388564,azure:15794175,beige:16119260,bisque:16770244,black:0,blanchedalmond:16772045,blue:255,blueviolet:9055202,brown:10824234,burlywood:14596231,cadetblue:6266528,chartreuse:8388352,chocolate:13789470,coral:16744272,cornflowerblue:6591981,cornsilk:16775388,crimson:14423100,cyan:65535,darkblue:139,darkcyan:35723,darkgoldenrod:12092939,darkgray:11119017,darkgreen:25600,darkgrey:11119017,darkkhaki:12433259,darkmagenta:9109643,darkolivegreen:5597999,darkorange:16747520,darkorchid:10040012,darkred:9109504,darksalmon:15308410,darkseagreen:9419919,darkslateblue:4734347,darkslategray:3100495,darkslategrey:3100495,darkturquoise:52945,darkviolet:9699539,deeppink:16716947,deepskyblue:49151,dimgray:6908265,dimgrey:6908265,dodgerblue:2003199,firebrick:11674146,floralwhite:16775920,forestgreen:2263842,fuchsia:16711935,gainsboro:14474460,ghostwhite:16316671,gold:16766720,goldenrod:14329120,gray:8421504,green:32768,greenyellow:11403055,grey:8421504,honeydew:15794160,hotpink:16738740,indianred:13458524,indigo:4915330,ivory:16777200,khaki:15787660,lavender:15132410,lavenderblush:16773365,lawngreen:8190976,lemonchiffon:16775885,lightblue:11393254,lightcoral:15761536,lightcyan:14745599,lightgoldenrodyellow:16448210,lightgray:13882323,lightgreen:9498256,lightgrey:13882323,lightpink:16758465,lightsalmon:16752762,lightseagreen:2142890,lightskyblue:8900346,lightslategray:7833753,lightslategrey:7833753,lightsteelblue:11584734,lightyellow:16777184,lime:65280,limegreen:3329330,linen:16445670,magenta:16711935,maroon:8388608,mediumaquamarine:6737322,mediumblue:205,mediumorchid:12211667,mediumpurple:9662683,mediumseagreen:3978097,mediumslateblue:8087790,mediumspringgreen:64154,mediumturquoise:4772300,mediumvioletred:13047173,midnightblue:1644912,mintcream:16121850,mistyrose:16770273,moccasin:16770229,navajowhite:16768685,navy:128,oldlace:16643558,olive:8421376,olivedrab:7048739,orange:16753920,orangered:16729344,orchid:14315734,palegoldenrod:15657130,palegreen:10025880,paleturquoise:11529966,palevioletred:14381203,papayawhip:16773077,peachpuff:16767673,peru:13468991,pink:16761035,plum:14524637,powderblue:11591910,purple:8388736,rebeccapurple:6697881,red:16711680,rosybrown:12357519,royalblue:4286945,saddlebrown:9127187,salmon:16416882,sandybrown:16032864,seagreen:3050327,seashell:16774638,sienna:10506797,silver:12632256,skyblue:8900331,slateblue:6970061,slategray:7372944,slategrey:7372944,snow:16775930,springgreen:65407,steelblue:4620980,tan:13808780,teal:32896,thistle:14204888,tomato:16737095,turquoise:4251856,violet:15631086,wheat:16113331,white:16777215,whitesmoke:16119285,yellow:16776960,yellowgreen:10145074},Jr={h:0,s:0,l:0},ou={h:0,s:0,l:0};function gh(s,e,i){return i<0&&(i+=1),i>1&&(i-=1),i<1/6?s+(e-s)*6*i:i<1/2?e:i<2/3?s+(e-s)*6*(2/3-i):s}class Rt{constructor(e,i,r){return this.isColor=!0,this.r=1,this.g=1,this.b=1,this.set(e,i,r)}set(e,i,r){if(i===void 0&&r===void 0){const l=e;l&&l.isColor?this.copy(l):typeof l=="number"?this.setHex(l):typeof l=="string"&&this.setStyle(l)}else this.setRGB(e,i,r);return this}setScalar(e){return this.r=e,this.g=e,this.b=e,this}setHex(e,i=Ei){return e=Math.floor(e),this.r=(e>>16&255)/255,this.g=(e>>8&255)/255,this.b=(e&255)/255,kt.colorSpaceToWorking(this,i),this}setRGB(e,i,r,l=kt.workingColorSpace){return this.r=e,this.g=i,this.b=r,kt.colorSpaceToWorking(this,l),this}setHSL(e,i,r,l=kt.workingColorSpace){if(e=Yp(e,1),i=Ut(i,0,1),r=Ut(r,0,1),i===0)this.r=this.g=this.b=r;else{const c=r<=.5?r*(1+i):r+i-r*i,f=2*r-c;this.r=gh(f,c,e+1/3),this.g=gh(f,c,e),this.b=gh(f,c,e-1/3)}return kt.colorSpaceToWorking(this,l),this}setStyle(e,i=Ei){function r(c){c!==void 0&&parseFloat(c)<1&&ht("Color: Alpha component of "+e+" will be ignored.")}let l;if(l=/^(\w+)\(([^\)]*)\)/.exec(e)){let c;const f=l[1],h=l[2];switch(f){case"rgb":case"rgba":if(c=/^\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*(?:,\s*(\d*\.?\d+)\s*)?$/.exec(h))return r(c[4]),this.setRGB(Math.min(255,parseInt(c[1],10))/255,Math.min(255,parseInt(c[2],10))/255,Math.min(255,parseInt(c[3],10))/255,i);if(c=/^\s*(\d+)\%\s*,\s*(\d+)\%\s*,\s*(\d+)\%\s*(?:,\s*(\d*\.?\d+)\s*)?$/.exec(h))return r(c[4]),this.setRGB(Math.min(100,parseInt(c[1],10))/100,Math.min(100,parseInt(c[2],10))/100,Math.min(100,parseInt(c[3],10))/100,i);break;case"hsl":case"hsla":if(c=/^\s*(\d*\.?\d+)\s*,\s*(\d*\.?\d+)\%\s*,\s*(\d*\.?\d+)\%\s*(?:,\s*(\d*\.?\d+)\s*)?$/.exec(h))return r(c[4]),this.setHSL(parseFloat(c[1])/360,parseFloat(c[2])/100,parseFloat(c[3])/100,i);break;default:ht("Color: Unknown color model "+e)}}else if(l=/^\#([A-Fa-f\d]+)$/.exec(e)){const c=l[1],f=c.length;if(f===3)return this.setRGB(parseInt(c.charAt(0),16)/15,parseInt(c.charAt(1),16)/15,parseInt(c.charAt(2),16)/15,i);if(f===6)return this.setHex(parseInt(c,16),i);ht("Color: Invalid hex color "+e)}else if(e&&e.length>0)return this.setColorName(e,i);return this}setColorName(e,i=Ei){const r=Dx[e.toLowerCase()];return r!==void 0?this.setHex(r,i):ht("Color: Unknown color "+e),this}clone(){return new this.constructor(this.r,this.g,this.b)}copy(e){return this.r=e.r,this.g=e.g,this.b=e.b,this}copySRGBToLinear(e){return this.r=br(e.r),this.g=br(e.g),this.b=br(e.b),this}copyLinearToSRGB(e){return this.r=zo(e.r),this.g=zo(e.g),this.b=zo(e.b),this}convertSRGBToLinear(){return this.copySRGBToLinear(this),this}convertLinearToSRGB(){return this.copyLinearToSRGB(this),this}getHex(e=Ei){return kt.workingToColorSpace(hi.copy(this),e),Math.round(Ut(hi.r*255,0,255))*65536+Math.round(Ut(hi.g*255,0,255))*256+Math.round(Ut(hi.b*255,0,255))}getHexString(e=Ei){return("000000"+this.getHex(e).toString(16)).slice(-6)}getHSL(e,i=kt.workingColorSpace){kt.workingToColorSpace(hi.copy(this),i);const r=hi.r,l=hi.g,c=hi.b,f=Math.max(r,l,c),h=Math.min(r,l,c);let m,p;const g=(h+f)/2;if(h===f)m=0,p=0;else{const _=f-h;switch(p=g<=.5?_/(f+h):_/(2-f-h),f){case r:m=(l-c)/_+(l<c?6:0);break;case l:m=(c-r)/_+2;break;case c:m=(r-l)/_+4;break}m/=6}return e.h=m,e.s=p,e.l=g,e}getRGB(e,i=kt.workingColorSpace){return kt.workingToColorSpace(hi.copy(this),i),e.r=hi.r,e.g=hi.g,e.b=hi.b,e}getStyle(e=Ei){kt.workingToColorSpace(hi.copy(this),e);const i=hi.r,r=hi.g,l=hi.b;return e!==Ei?`color(${e} ${i.toFixed(3)} ${r.toFixed(3)} ${l.toFixed(3)})`:`rgb(${Math.round(i*255)},${Math.round(r*255)},${Math.round(l*255)})`}offsetHSL(e,i,r){return this.getHSL(Jr),this.setHSL(Jr.h+e,Jr.s+i,Jr.l+r)}add(e){return this.r+=e.r,this.g+=e.g,this.b+=e.b,this}addColors(e,i){return this.r=e.r+i.r,this.g=e.g+i.g,this.b=e.b+i.b,this}addScalar(e){return this.r+=e,this.g+=e,this.b+=e,this}sub(e){return this.r=Math.max(0,this.r-e.r),this.g=Math.max(0,this.g-e.g),this.b=Math.max(0,this.b-e.b),this}multiply(e){return this.r*=e.r,this.g*=e.g,this.b*=e.b,this}multiplyScalar(e){return this.r*=e,this.g*=e,this.b*=e,this}lerp(e,i){return this.r+=(e.r-this.r)*i,this.g+=(e.g-this.g)*i,this.b+=(e.b-this.b)*i,this}lerpColors(e,i,r){return this.r=e.r+(i.r-e.r)*r,this.g=e.g+(i.g-e.g)*r,this.b=e.b+(i.b-e.b)*r,this}lerpHSL(e,i){this.getHSL(Jr),e.getHSL(ou);const r=Vl(Jr.h,ou.h,i),l=Vl(Jr.s,ou.s,i),c=Vl(Jr.l,ou.l,i);return this.setHSL(r,l,c),this}setFromVector3(e){return this.r=e.x,this.g=e.y,this.b=e.z,this}applyMatrix3(e){const i=this.r,r=this.g,l=this.b,c=e.elements;return this.r=c[0]*i+c[3]*r+c[6]*l,this.g=c[1]*i+c[4]*r+c[7]*l,this.b=c[2]*i+c[5]*r+c[8]*l,this}equals(e){return e.r===this.r&&e.g===this.g&&e.b===this.b}fromArray(e,i=0){return this.r=e[i],this.g=e[i+1],this.b=e[i+2],this}toArray(e=[],i=0){return e[i]=this.r,e[i+1]=this.g,e[i+2]=this.b,e}fromBufferAttribute(e,i){return this.r=e.getX(i),this.g=e.getY(i),this.b=e.getZ(i),this}toJSON(){return this.getHex()}*[Symbol.iterator](){yield this.r,yield this.g,yield this.b}}const hi=new Rt;Rt.NAMES=Dx;class Ux extends Ti{constructor(){super(),this.isScene=!0,this.type="Scene",this.background=null,this.environment=null,this.fog=null,this.backgroundBlurriness=0,this.backgroundIntensity=1,this.backgroundRotation=new Ps,this.environmentIntensity=1,this.environmentRotation=new Ps,this.overrideMaterial=null,typeof __THREE_DEVTOOLS__<"u"&&__THREE_DEVTOOLS__.dispatchEvent(new CustomEvent("observe",{detail:this}))}copy(e,i){return super.copy(e,i),e.background!==null&&(this.background=e.background.clone()),e.environment!==null&&(this.environment=e.environment.clone()),e.fog!==null&&(this.fog=e.fog.clone()),this.backgroundBlurriness=e.backgroundBlurriness,this.backgroundIntensity=e.backgroundIntensity,this.backgroundRotation.copy(e.backgroundRotation),this.environmentIntensity=e.environmentIntensity,this.environmentRotation.copy(e.environmentRotation),e.overrideMaterial!==null&&(this.overrideMaterial=e.overrideMaterial.clone()),this.matrixAutoUpdate=e.matrixAutoUpdate,this}toJSON(e){const i=super.toJSON(e);return this.fog!==null&&(i.object.fog=this.fog.toJSON()),i.object.backgroundBlurriness=this.backgroundBlurriness,i.object.backgroundIntensity=this.backgroundIntensity,i.object.backgroundRotation=this.backgroundRotation.toArray(),i.object.environmentIntensity=this.environmentIntensity,i.object.environmentRotation=this.environmentRotation.toArray(),i}}const Ea=new Q,pr=new Q,vh=new Q,mr=new Q,yo=new Q,Mo=new Q,f_=new Q,_h=new Q,xh=new Q,Sh=new Q,yh=new Ln,Mh=new Ln,bh=new Ln;class Aa{constructor(e=new Q,i=new Q,r=new Q){this.a=e,this.b=i,this.c=r}static getNormal(e,i,r,l){l.subVectors(r,i),Ea.subVectors(e,i),l.cross(Ea);const c=l.lengthSq();return c>0?l.multiplyScalar(1/Math.sqrt(c)):l.set(0,0,0)}static getBarycoord(e,i,r,l,c){Ea.subVectors(l,i),pr.subVectors(r,i),vh.subVectors(e,i);const f=Ea.dot(Ea),h=Ea.dot(pr),m=Ea.dot(vh),p=pr.dot(pr),g=pr.dot(vh),_=f*p-h*h;if(_===0)return c.set(0,0,0),null;const v=1/_,x=(p*m-h*g)*v,E=(f*g-h*m)*v;return c.set(1-x-E,E,x)}static containsPoint(e,i,r,l){return this.getBarycoord(e,i,r,l,mr)===null?!1:mr.x>=0&&mr.y>=0&&mr.x+mr.y<=1}static getInterpolation(e,i,r,l,c,f,h,m){return this.getBarycoord(e,i,r,l,mr)===null?(m.x=0,m.y=0,"z"in m&&(m.z=0),"w"in m&&(m.w=0),null):(m.setScalar(0),m.addScaledVector(c,mr.x),m.addScaledVector(f,mr.y),m.addScaledVector(h,mr.z),m)}static getInterpolatedAttribute(e,i,r,l,c,f){return yh.setScalar(0),Mh.setScalar(0),bh.setScalar(0),yh.fromBufferAttribute(e,i),Mh.fromBufferAttribute(e,r),bh.fromBufferAttribute(e,l),f.setScalar(0),f.addScaledVector(yh,c.x),f.addScaledVector(Mh,c.y),f.addScaledVector(bh,c.z),f}static isFrontFacing(e,i,r,l){return Ea.subVectors(r,i),pr.subVectors(e,i),Ea.cross(pr).dot(l)<0}set(e,i,r){return this.a.copy(e),this.b.copy(i),this.c.copy(r),this}setFromPointsAndIndices(e,i,r,l){return this.a.copy(e[i]),this.b.copy(e[r]),this.c.copy(e[l]),this}setFromAttributeAndIndices(e,i,r,l){return this.a.fromBufferAttribute(e,i),this.b.fromBufferAttribute(e,r),this.c.fromBufferAttribute(e,l),this}clone(){return new this.constructor().copy(this)}copy(e){return this.a.copy(e.a),this.b.copy(e.b),this.c.copy(e.c),this}getArea(){return Ea.subVectors(this.c,this.b),pr.subVectors(this.a,this.b),Ea.cross(pr).length()*.5}getMidpoint(e){return e.addVectors(this.a,this.b).add(this.c).multiplyScalar(1/3)}getNormal(e){return Aa.getNormal(this.a,this.b,this.c,e)}getPlane(e){return e.setFromCoplanarPoints(this.a,this.b,this.c)}getBarycoord(e,i){return Aa.getBarycoord(e,this.a,this.b,this.c,i)}getInterpolation(e,i,r,l,c){return Aa.getInterpolation(e,this.a,this.b,this.c,i,r,l,c)}containsPoint(e){return Aa.containsPoint(e,this.a,this.b,this.c)}isFrontFacing(e){return Aa.isFrontFacing(this.a,this.b,this.c,e)}intersectsBox(e){return e.intersectsTriangle(this)}closestPointToPoint(e,i){const r=this.a,l=this.b,c=this.c;let f,h;yo.subVectors(l,r),Mo.subVectors(c,r),_h.subVectors(e,r);const m=yo.dot(_h),p=Mo.dot(_h);if(m<=0&&p<=0)return i.copy(r);xh.subVectors(e,l);const g=yo.dot(xh),_=Mo.dot(xh);if(g>=0&&_<=g)return i.copy(l);const v=m*_-g*p;if(v<=0&&m>=0&&g<=0)return f=m/(m-g),i.copy(r).addScaledVector(yo,f);Sh.subVectors(e,c);const x=yo.dot(Sh),E=Mo.dot(Sh);if(E>=0&&x<=E)return i.copy(c);const D=x*p-m*E;if(D<=0&&p>=0&&E<=0)return h=p/(p-E),i.copy(r).addScaledVector(Mo,h);const M=g*E-x*_;if(M<=0&&_-g>=0&&x-E>=0)return f_.subVectors(c,l),h=(_-g)/(_-g+(x-E)),i.copy(l).addScaledVector(f_,h);const y=1/(M+D+v);return f=D*y,h=v*y,i.copy(r).addScaledVector(yo,f).addScaledVector(Mo,h)}equals(e){return e.a.equals(this.a)&&e.b.equals(this.b)&&e.c.equals(this.c)}}class Vo{constructor(e=new Q(1/0,1/0,1/0),i=new Q(-1/0,-1/0,-1/0)){this.isBox3=!0,this.min=e,this.max=i}set(e,i){return this.min.copy(e),this.max.copy(i),this}setFromArray(e){this.makeEmpty();for(let i=0,r=e.length;i<r;i+=3)this.expandByPoint(Ta.fromArray(e,i));return this}setFromBufferAttribute(e){this.makeEmpty();for(let i=0,r=e.count;i<r;i++)this.expandByPoint(Ta.fromBufferAttribute(e,i));return this}setFromPoints(e){this.makeEmpty();for(let i=0,r=e.length;i<r;i++)this.expandByPoint(e[i]);return this}setFromCenterAndSize(e,i){const r=Ta.copy(i).multiplyScalar(.5);return this.min.copy(e).sub(r),this.max.copy(e).add(r),this}setFromObject(e,i=!1){return this.makeEmpty(),this.expandByObject(e,i)}clone(){return new this.constructor().copy(this)}copy(e){return this.min.copy(e.min),this.max.copy(e.max),this}makeEmpty(){return this.min.x=this.min.y=this.min.z=1/0,this.max.x=this.max.y=this.max.z=-1/0,this}isEmpty(){return this.max.x<this.min.x||this.max.y<this.min.y||this.max.z<this.min.z}getCenter(e){return this.isEmpty()?e.set(0,0,0):e.addVectors(this.min,this.max).multiplyScalar(.5)}getSize(e){return this.isEmpty()?e.set(0,0,0):e.subVectors(this.max,this.min)}expandByPoint(e){return this.min.min(e),this.max.max(e),this}expandByVector(e){return this.min.sub(e),this.max.add(e),this}expandByScalar(e){return this.min.addScalar(-e),this.max.addScalar(e),this}expandByObject(e,i=!1){e.updateWorldMatrix(!1,!1);const r=e.geometry;if(r!==void 0){const c=r.getAttribute("position");if(i===!0&&c!==void 0&&e.isInstancedMesh!==!0)for(let f=0,h=c.count;f<h;f++)e.isMesh===!0?e.getVertexPosition(f,Ta):Ta.fromBufferAttribute(c,f),Ta.applyMatrix4(e.matrixWorld),this.expandByPoint(Ta);else e.boundingBox!==void 0?(e.boundingBox===null&&e.computeBoundingBox(),lu.copy(e.boundingBox)):(r.boundingBox===null&&r.computeBoundingBox(),lu.copy(r.boundingBox)),lu.applyMatrix4(e.matrixWorld),this.union(lu)}const l=e.children;for(let c=0,f=l.length;c<f;c++)this.expandByObject(l[c],i);return this}containsPoint(e){return e.x>=this.min.x&&e.x<=this.max.x&&e.y>=this.min.y&&e.y<=this.max.y&&e.z>=this.min.z&&e.z<=this.max.z}containsBox(e){return this.min.x<=e.min.x&&e.max.x<=this.max.x&&this.min.y<=e.min.y&&e.max.y<=this.max.y&&this.min.z<=e.min.z&&e.max.z<=this.max.z}getParameter(e,i){return i.set((e.x-this.min.x)/(this.max.x-this.min.x),(e.y-this.min.y)/(this.max.y-this.min.y),(e.z-this.min.z)/(this.max.z-this.min.z))}intersectsBox(e){return e.max.x>=this.min.x&&e.min.x<=this.max.x&&e.max.y>=this.min.y&&e.min.y<=this.max.y&&e.max.z>=this.min.z&&e.min.z<=this.max.z}intersectsSphere(e){return this.clampPoint(e.center,Ta),Ta.distanceToSquared(e.center)<=e.radius*e.radius}intersectsPlane(e){let i,r;return e.normal.x>0?(i=e.normal.x*this.min.x,r=e.normal.x*this.max.x):(i=e.normal.x*this.max.x,r=e.normal.x*this.min.x),e.normal.y>0?(i+=e.normal.y*this.min.y,r+=e.normal.y*this.max.y):(i+=e.normal.y*this.max.y,r+=e.normal.y*this.min.y),e.normal.z>0?(i+=e.normal.z*this.min.z,r+=e.normal.z*this.max.z):(i+=e.normal.z*this.max.z,r+=e.normal.z*this.min.z),i<=-e.constant&&r>=-e.constant}intersectsTriangle(e){if(this.isEmpty())return!1;this.getCenter(Nl),cu.subVectors(this.max,Nl),bo.subVectors(e.a,Nl),Eo.subVectors(e.b,Nl),To.subVectors(e.c,Nl),$r.subVectors(Eo,bo),es.subVectors(To,Eo),bs.subVectors(bo,To);let i=[0,-$r.z,$r.y,0,-es.z,es.y,0,-bs.z,bs.y,$r.z,0,-$r.x,es.z,0,-es.x,bs.z,0,-bs.x,-$r.y,$r.x,0,-es.y,es.x,0,-bs.y,bs.x,0];return!Eh(i,bo,Eo,To,cu)||(i=[1,0,0,0,1,0,0,0,1],!Eh(i,bo,Eo,To,cu))?!1:(uu.crossVectors($r,es),i=[uu.x,uu.y,uu.z],Eh(i,bo,Eo,To,cu))}clampPoint(e,i){return i.copy(e).clamp(this.min,this.max)}distanceToPoint(e){return this.clampPoint(e,Ta).distanceTo(e)}getBoundingSphere(e){return this.isEmpty()?e.makeEmpty():(this.getCenter(e.center),e.radius=this.getSize(Ta).length()*.5),e}intersect(e){return this.min.max(e.min),this.max.min(e.max),this.isEmpty()&&this.makeEmpty(),this}union(e){return this.min.min(e.min),this.max.max(e.max),this}applyMatrix4(e){return this.isEmpty()?this:(gr[0].set(this.min.x,this.min.y,this.min.z).applyMatrix4(e),gr[1].set(this.min.x,this.min.y,this.max.z).applyMatrix4(e),gr[2].set(this.min.x,this.max.y,this.min.z).applyMatrix4(e),gr[3].set(this.min.x,this.max.y,this.max.z).applyMatrix4(e),gr[4].set(this.max.x,this.min.y,this.min.z).applyMatrix4(e),gr[5].set(this.max.x,this.min.y,this.max.z).applyMatrix4(e),gr[6].set(this.max.x,this.max.y,this.min.z).applyMatrix4(e),gr[7].set(this.max.x,this.max.y,this.max.z).applyMatrix4(e),this.setFromPoints(gr),this)}translate(e){return this.min.add(e),this.max.add(e),this}equals(e){return e.min.equals(this.min)&&e.max.equals(this.max)}toJSON(){return{min:this.min.toArray(),max:this.max.toArray()}}fromJSON(e){return this.min.fromArray(e.min),this.max.fromArray(e.max),this}}const gr=[new Q,new Q,new Q,new Q,new Q,new Q,new Q,new Q],Ta=new Q,lu=new Vo,bo=new Q,Eo=new Q,To=new Q,$r=new Q,es=new Q,bs=new Q,Nl=new Q,cu=new Q,uu=new Q,Es=new Q;function Eh(s,e,i,r,l){for(let c=0,f=s.length-3;c<=f;c+=3){Es.fromArray(s,c);const h=l.x*Math.abs(Es.x)+l.y*Math.abs(Es.y)+l.z*Math.abs(Es.z),m=e.dot(Es),p=i.dot(Es),g=r.dot(Es);if(Math.max(-Math.max(m,p,g),Math.min(m,p,g))>h)return!1}return!0}const Xn=new Q,fu=new Kt;let eE=0;class Fn extends Is{constructor(e,i,r=!1){if(super(),Array.isArray(e))throw new TypeError("THREE.BufferAttribute: array should be a Typed Array.");this.isBufferAttribute=!0,Object.defineProperty(this,"id",{value:eE++}),this.name="",this.array=e,this.itemSize=i,this.count=e!==void 0?e.length/i:0,this.normalized=r,this.usage=Sb,this.updateRanges=[],this.gpuType=Va,this.version=0}onUploadCallback(){}set needsUpdate(e){e===!0&&this.version++}setUsage(e){return this.usage=e,this}addUpdateRange(e,i){this.updateRanges.push({start:e,count:i})}clearUpdateRanges(){this.updateRanges.length=0}copy(e){return this.name=e.name,this.array=new e.array.constructor(e.array),this.itemSize=e.itemSize,this.count=e.count,this.normalized=e.normalized,this.usage=e.usage,this.gpuType=e.gpuType,this}copyAt(e,i,r){e*=this.itemSize,r*=i.itemSize;for(let l=0,c=this.itemSize;l<c;l++)this.array[e+l]=i.array[r+l];return this}copyArray(e){return this.array.set(e),this}applyMatrix3(e){if(this.itemSize===2)for(let i=0,r=this.count;i<r;i++)fu.fromBufferAttribute(this,i),fu.applyMatrix3(e),this.setXY(i,fu.x,fu.y);else if(this.itemSize===3)for(let i=0,r=this.count;i<r;i++)Xn.fromBufferAttribute(this,i),Xn.applyMatrix3(e),this.setXYZ(i,Xn.x,Xn.y,Xn.z);return this}applyMatrix4(e){for(let i=0,r=this.count;i<r;i++)Xn.fromBufferAttribute(this,i),Xn.applyMatrix4(e),this.setXYZ(i,Xn.x,Xn.y,Xn.z);return this}applyNormalMatrix(e){for(let i=0,r=this.count;i<r;i++)Xn.fromBufferAttribute(this,i),Xn.applyNormalMatrix(e),this.setXYZ(i,Xn.x,Xn.y,Xn.z);return this}transformDirection(e){for(let i=0,r=this.count;i<r;i++)Xn.fromBufferAttribute(this,i),Xn.transformDirection(e),this.setXYZ(i,Xn.x,Xn.y,Xn.z);return this}set(e,i=0){return this.array.set(e,i),this}getComponent(e,i){let r=this.array[e*this.itemSize+i];return this.normalized&&(r=Lo(r,this.array)),r}setComponent(e,i,r){return this.normalized&&(r=Mi(r,this.array)),this.array[e*this.itemSize+i]=r,this}getX(e){let i=this.array[e*this.itemSize];return this.normalized&&(i=Lo(i,this.array)),i}setX(e,i){return this.normalized&&(i=Mi(i,this.array)),this.array[e*this.itemSize]=i,this}getY(e){let i=this.array[e*this.itemSize+1];return this.normalized&&(i=Lo(i,this.array)),i}setY(e,i){return this.normalized&&(i=Mi(i,this.array)),this.array[e*this.itemSize+1]=i,this}getZ(e){let i=this.array[e*this.itemSize+2];return this.normalized&&(i=Lo(i,this.array)),i}setZ(e,i){return this.normalized&&(i=Mi(i,this.array)),this.array[e*this.itemSize+2]=i,this}getW(e){let i=this.array[e*this.itemSize+3];return this.normalized&&(i=Lo(i,this.array)),i}setW(e,i){return this.normalized&&(i=Mi(i,this.array)),this.array[e*this.itemSize+3]=i,this}setXY(e,i,r){return e*=this.itemSize,this.normalized&&(i=Mi(i,this.array),r=Mi(r,this.array)),this.array[e+0]=i,this.array[e+1]=r,this}setXYZ(e,i,r,l){return e*=this.itemSize,this.normalized&&(i=Mi(i,this.array),r=Mi(r,this.array),l=Mi(l,this.array)),this.array[e+0]=i,this.array[e+1]=r,this.array[e+2]=l,this}setXYZW(e,i,r,l,c){return e*=this.itemSize,this.normalized&&(i=Mi(i,this.array),r=Mi(r,this.array),l=Mi(l,this.array),c=Mi(c,this.array)),this.array[e+0]=i,this.array[e+1]=r,this.array[e+2]=l,this.array[e+3]=c,this}onUpload(e){return this.onUploadCallback=e,this}clone(){return new this.constructor(this.array,this.itemSize).copy(this)}toJSON(){const e={itemSize:this.itemSize,type:this.array.constructor.name,array:Array.from(this.array),normalized:this.normalized};return e.name=this.name,e.usage=this.usage,e.gpuType=this.gpuType,e}dispose(){this.dispatchEvent({type:"dispose"})}}class Nx extends Fn{constructor(e,i,r){super(new Uint16Array(e),i,r)}}class Lx extends Fn{constructor(e,i,r){super(new Uint32Array(e),i,r)}}class Cn extends Fn{constructor(e,i,r){super(new Float32Array(e),i,r)}}const tE=new Vo,Ll=new Q,Th=new Q;class Fs{constructor(e=new Q,i=-1){this.isSphere=!0,this.center=e,this.radius=i}set(e,i){return this.center.copy(e),this.radius=i,this}setFromPoints(e,i){const r=this.center;i!==void 0?r.copy(i):tE.setFromPoints(e).getCenter(r);let l=0;for(let c=0,f=e.length;c<f;c++)l=Math.max(l,r.distanceToSquared(e[c]));return this.radius=Math.sqrt(l),this}copy(e){return this.center.copy(e.center),this.radius=e.radius,this}isEmpty(){return this.radius<0}makeEmpty(){return this.center.set(0,0,0),this.radius=-1,this}containsPoint(e){return e.distanceToSquared(this.center)<=this.radius*this.radius}distanceToPoint(e){return e.distanceTo(this.center)-this.radius}intersectsSphere(e){const i=this.radius+e.radius;return e.center.distanceToSquared(this.center)<=i*i}intersectsBox(e){return e.intersectsSphere(this)}intersectsPlane(e){return Math.abs(e.distanceToPoint(this.center))<=this.radius}clampPoint(e,i){const r=this.center.distanceToSquared(e);return i.copy(e),r>this.radius*this.radius&&(i.sub(this.center).normalize(),i.multiplyScalar(this.radius).add(this.center)),i}getBoundingBox(e){return this.isEmpty()?(e.makeEmpty(),e):(e.set(this.center,this.center),e.expandByScalar(this.radius),e)}applyMatrix4(e){return this.center.applyMatrix4(e),this.radius=this.radius*e.getMaxScaleOnAxis(),this}translate(e){return this.center.add(e),this}expandByPoint(e){if(this.isEmpty())return this.center.copy(e),this.radius=0,this;Ll.subVectors(e,this.center);const i=Ll.lengthSq();if(i>this.radius*this.radius){const r=Math.sqrt(i),l=(r-this.radius)*.5;this.center.addScaledVector(Ll,l/r),this.radius+=l}return this}union(e){return e.isEmpty()?this:this.isEmpty()?(this.copy(e),this):(this.center.equals(e.center)===!0?this.radius=Math.max(this.radius,e.radius):(Th.subVectors(e.center,this.center).setLength(e.radius),this.expandByPoint(Ll.copy(e.center).add(Th)),this.expandByPoint(Ll.copy(e.center).sub(Th))),this)}equals(e){return e.center.equals(this.center)&&e.radius===this.radius}clone(){return new this.constructor().copy(this)}toJSON(){return{radius:this.radius,center:this.center.toArray()}}fromJSON(e){return this.radius=e.radius,this.center.fromArray(e.center),this}}let nE=0;const fa=new En,Ah=new Ti,Ao=new Q,qi=new Vo,Ol=new Vo,$n=new Q;class zn extends Is{constructor(){super(),this.isBufferGeometry=!0,Object.defineProperty(this,"id",{value:nE++}),this.uuid=Go(),this.name="",this.type="BufferGeometry",this.index=null,this.indirect=null,this.indirectOffset=0,this.attributes={},this.morphAttributes={},this.morphTargetsRelative=!1,this.groups=[],this.boundingBox=null,this.boundingSphere=null,this.drawRange={start:0,count:1/0},this.userData={},this._transformed=!1}getIndex(){return this.index}setIndex(e){return Array.isArray(e)?this.index=new(yb(e)?Lx:Nx)(e,1):this.index=e,this}setIndirect(e,i=0){return this.indirect=e,this.indirectOffset=i,this}getIndirect(){return this.indirect}getAttribute(e){return this.attributes[e]}setAttribute(e,i){return this.attributes[e]=i,this}deleteAttribute(e){return delete this.attributes[e],this}hasAttribute(e){return this.attributes[e]!==void 0}addGroup(e,i,r=0){this.groups.push({start:e,count:i,materialIndex:r})}clearGroups(){this.groups=[]}setDrawRange(e,i){this.drawRange.start=e,this.drawRange.count=i}applyMatrix4(e){const i=this.attributes.position;i!==void 0&&(i.applyMatrix4(e),i.needsUpdate=!0);const r=this.attributes.normal;if(r!==void 0){const c=new yt().getNormalMatrix(e);r.applyNormalMatrix(c),r.needsUpdate=!0}const l=this.attributes.tangent;return l!==void 0&&(l.transformDirection(e),l.needsUpdate=!0),this.boundingBox!==null&&this.computeBoundingBox(),this.boundingSphere!==null&&this.computeBoundingSphere(),this._transformed=!0,this}applyQuaternion(e){return fa.makeRotationFromQuaternion(e),this.applyMatrix4(fa),this}rotateX(e){return fa.makeRotationX(e),this.applyMatrix4(fa),this}rotateY(e){return fa.makeRotationY(e),this.applyMatrix4(fa),this}rotateZ(e){return fa.makeRotationZ(e),this.applyMatrix4(fa),this}translate(e,i,r){return fa.makeTranslation(e,i,r),this.applyMatrix4(fa),this}scale(e,i,r){return fa.makeScale(e,i,r),this.applyMatrix4(fa),this}lookAt(e){return Ah.lookAt(e),Ah.updateMatrix(),this.applyMatrix4(Ah.matrix),this}center(){return this.computeBoundingBox(),this.boundingBox.getCenter(Ao).negate(),this.translate(Ao.x,Ao.y,Ao.z),this}setFromPoints(e){const i=this.getAttribute("position");if(i===void 0){const r=[];for(let l=0,c=e.length;l<c;l++){const f=e[l];r.push(f.x,f.y,f.z||0)}this.setAttribute("position",new Cn(r,3))}else{const r=Math.min(e.length,i.count);for(let l=0;l<r;l++){const c=e[l];i.setXYZ(l,c.x,c.y,c.z||0)}e.length>i.count&&ht("BufferGeometry: Buffer size too small for points data. Use .dispose() and create a new geometry."),i.needsUpdate=!0}return this}computeBoundingBox(){this.boundingBox===null&&(this.boundingBox=new Vo);const e=this.attributes.position,i=this.morphAttributes.position;if(e&&e.isGLBufferAttribute){Zt("BufferGeometry.computeBoundingBox(): GLBufferAttribute requires a manual bounding box.",this),this.boundingBox.set(new Q(-1/0,-1/0,-1/0),new Q(1/0,1/0,1/0));return}if(e!==void 0){if(this.boundingBox.setFromBufferAttribute(e),i)for(let r=0,l=i.length;r<l;r++){const c=i[r];qi.setFromBufferAttribute(c),this.morphTargetsRelative?($n.addVectors(this.boundingBox.min,qi.min),this.boundingBox.expandByPoint($n),$n.addVectors(this.boundingBox.max,qi.max),this.boundingBox.expandByPoint($n)):(this.boundingBox.expandByPoint(qi.min),this.boundingBox.expandByPoint(qi.max))}}else this.boundingBox.makeEmpty();(isNaN(this.boundingBox.min.x)||isNaN(this.boundingBox.min.y)||isNaN(this.boundingBox.min.z))&&Zt('BufferGeometry.computeBoundingBox(): Computed min/max have NaN values. The "position" attribute is likely to have NaN values.',this)}computeBoundingSphere(){this.boundingSphere===null&&(this.boundingSphere=new Fs);const e=this.attributes.position,i=this.morphAttributes.position;if(e&&e.isGLBufferAttribute){Zt("BufferGeometry.computeBoundingSphere(): GLBufferAttribute requires a manual bounding sphere.",this),this.boundingSphere.set(new Q,1/0);return}if(e){const r=this.boundingSphere.center;if(qi.setFromBufferAttribute(e),i)for(let c=0,f=i.length;c<f;c++){const h=i[c];Ol.setFromBufferAttribute(h),this.morphTargetsRelative?($n.addVectors(qi.min,Ol.min),qi.expandByPoint($n),$n.addVectors(qi.max,Ol.max),qi.expandByPoint($n)):(qi.expandByPoint(Ol.min),qi.expandByPoint(Ol.max))}qi.getCenter(r);let l=0;for(let c=0,f=e.count;c<f;c++)$n.fromBufferAttribute(e,c),l=Math.max(l,r.distanceToSquared($n));if(i)for(let c=0,f=i.length;c<f;c++){const h=i[c],m=this.morphTargetsRelative;for(let p=0,g=h.count;p<g;p++)$n.fromBufferAttribute(h,p),m&&(Ao.fromBufferAttribute(e,p),$n.add(Ao)),l=Math.max(l,r.distanceToSquared($n))}this.boundingSphere.radius=Math.sqrt(l),isNaN(this.boundingSphere.radius)&&Zt('BufferGeometry.computeBoundingSphere(): Computed radius is NaN. The "position" attribute is likely to have NaN values.',this)}}computeTangents(){const e=this.index,i=this.attributes;if(e===null||i.position===void 0||i.normal===void 0||i.uv===void 0){Zt("BufferGeometry: .computeTangents() failed. Missing required attributes (index, position, normal or uv)");return}const r=i.position,l=i.normal,c=i.uv;let f=this.getAttribute("tangent");(f===void 0||f.count!==r.count)&&(f=new Fn(new Float32Array(4*r.count),4),this.setAttribute("tangent",f));const h=[],m=[];for(let T=0;T<r.count;T++)h[T]=new Q,m[T]=new Q;const p=new Q,g=new Q,_=new Q,v=new Kt,x=new Kt,E=new Kt,D=new Q,M=new Q;function y(T,O,B){p.fromBufferAttribute(r,T),g.fromBufferAttribute(r,O),_.fromBufferAttribute(r,B),v.fromBufferAttribute(c,T),x.fromBufferAttribute(c,O),E.fromBufferAttribute(c,B),g.sub(p),_.sub(p),x.sub(v),E.sub(v);const k=1/(x.x*E.y-E.x*x.y);isFinite(k)&&(D.copy(g).multiplyScalar(E.y).addScaledVector(_,-x.y).multiplyScalar(k),M.copy(_).multiplyScalar(x.x).addScaledVector(g,-E.x).multiplyScalar(k),h[T].add(D),h[O].add(D),h[B].add(D),m[T].add(M),m[O].add(M),m[B].add(M))}let F=this.groups;F.length===0&&(F=[{start:0,count:e.count}]);for(let T=0,O=F.length;T<O;++T){const B=F[T],k=B.start,J=B.count;for(let se=k,Y=k+J;se<Y;se+=3)y(e.getX(se+0),e.getX(se+1),e.getX(se+2))}const V=new Q,R=new Q,N=new Q,L=new Q;function P(T){N.fromBufferAttribute(l,T),L.copy(N);const O=h[T];V.copy(O),V.sub(N.multiplyScalar(N.dot(O))).normalize(),R.crossVectors(L,O);const k=R.dot(m[T])<0?-1:1;f.setXYZW(T,V.x,V.y,V.z,k)}for(let T=0,O=F.length;T<O;++T){const B=F[T],k=B.start,J=B.count;for(let se=k,Y=k+J;se<Y;se+=3)P(e.getX(se+0)),P(e.getX(se+1)),P(e.getX(se+2))}this._transformed=!0}computeVertexNormals(){const e=this.index,i=this.getAttribute("position");if(i!==void 0){let r=this.getAttribute("normal");if(r===void 0||r.count!==i.count)r=new Fn(new Float32Array(i.count*3),3),this.setAttribute("normal",r);else for(let v=0,x=r.count;v<x;v++)r.setXYZ(v,0,0,0);const l=new Q,c=new Q,f=new Q,h=new Q,m=new Q,p=new Q,g=new Q,_=new Q;if(e)for(let v=0,x=e.count;v<x;v+=3){const E=e.getX(v+0),D=e.getX(v+1),M=e.getX(v+2);l.fromBufferAttribute(i,E),c.fromBufferAttribute(i,D),f.fromBufferAttribute(i,M),g.subVectors(f,c),_.subVectors(l,c),g.cross(_),h.fromBufferAttribute(r,E),m.fromBufferAttribute(r,D),p.fromBufferAttribute(r,M),h.add(g),m.add(g),p.add(g),r.setXYZ(E,h.x,h.y,h.z),r.setXYZ(D,m.x,m.y,m.z),r.setXYZ(M,p.x,p.y,p.z)}else for(let v=0,x=i.count;v<x;v+=3)l.fromBufferAttribute(i,v+0),c.fromBufferAttribute(i,v+1),f.fromBufferAttribute(i,v+2),g.subVectors(f,c),_.subVectors(l,c),g.cross(_),r.setXYZ(v+0,g.x,g.y,g.z),r.setXYZ(v+1,g.x,g.y,g.z),r.setXYZ(v+2,g.x,g.y,g.z);this.normalizeNormals(),r.needsUpdate=!0}}normalizeNormals(){const e=this.attributes.normal;for(let i=0,r=e.count;i<r;i++)$n.fromBufferAttribute(e,i),$n.normalize(),e.setXYZ(i,$n.x,$n.y,$n.z)}toNonIndexed(){function e(h,m){const p=h.array,g=h.itemSize,_=h.normalized,v=new p.constructor(m.length*g);let x=0,E=0;for(let D=0,M=m.length;D<M;D++){h.isInterleavedBufferAttribute?x=m[D]*h.data.stride+h.offset:x=m[D]*g;for(let y=0;y<g;y++)v[E++]=p[x++]}return new Fn(v,g,_)}if(this.index===null)return ht("BufferGeometry.toNonIndexed(): BufferGeometry is already non-indexed."),this;const i=new zn,r=this.index.array,l=this.attributes;for(const h in l){const m=l[h],p=e(m,r);i.setAttribute(h,p)}const c=this.morphAttributes;for(const h in c){const m=[],p=c[h];for(let g=0,_=p.length;g<_;g++){const v=p[g],x=e(v,r);m.push(x)}i.morphAttributes[h]=m}i.morphTargetsRelative=this.morphTargetsRelative;const f=this.groups;for(let h=0,m=f.length;h<m;h++){const p=f[h];i.addGroup(p.start,p.count,p.materialIndex)}return i}toJSON(){const e={metadata:{version:4.7,type:"BufferGeometry",generator:"BufferGeometry.toJSON"}};if(e.uuid=this.uuid,e.type=this.parameters!==void 0&&this._transformed===!0?"BufferGeometry":this.type,e.name=this.name,Object.keys(this.userData).length>0&&(e.userData=this.userData),this.parameters!==void 0&&this._transformed!==!0){const m=this.parameters;for(const p in m)m[p]!==void 0&&(e[p]=m[p]);return e}e.data={attributes:{}};const i=this.index;i!==null&&(e.data.index={type:i.array.constructor.name,array:Array.prototype.slice.call(i.array)});const r=this.attributes;for(const m in r){const p=r[m];e.data.attributes[m]=p.toJSON(e.data)}const l={};let c=!1;for(const m in this.morphAttributes){const p=this.morphAttributes[m],g=[];for(let _=0,v=p.length;_<v;_++){const x=p[_];g.push(x.toJSON(e.data))}g.length>0&&(l[m]=g,c=!0)}c&&(e.data.morphAttributes=l,e.data.morphTargetsRelative=this.morphTargetsRelative);const f=this.groups;f.length>0&&(e.data.groups=JSON.parse(JSON.stringify(f)));const h=this.boundingSphere;return h!==null&&(e.data.boundingSphere=h.toJSON()),e}clone(){return new this.constructor().copy(this)}copy(e){this.index=null,this.attributes={},this.morphAttributes={},this.groups=[],this.boundingBox=null,this.boundingSphere=null;const i={};this.name=e.name;const r=e.index;r!==null&&this.setIndex(r.clone());const l=e.attributes;for(const p in l){const g=l[p];this.setAttribute(p,g.clone(i))}const c=e.morphAttributes;for(const p in c){const g=[],_=c[p];for(let v=0,x=_.length;v<x;v++)g.push(_[v].clone(i));this.morphAttributes[p]=g}this.morphTargetsRelative=e.morphTargetsRelative;const f=e.groups;for(let p=0,g=f.length;p<g;p++){const _=f[p];this.addGroup(_.start,_.count,_.materialIndex)}const h=e.boundingBox;h!==null&&(this.boundingBox=h.clone());const m=e.boundingSphere;return m!==null&&(this.boundingSphere=m.clone()),this.drawRange.start=e.drawRange.start,this.drawRange.count=e.drawRange.count,this.userData=e.userData,this._transformed=e._transformed,this}dispose(){this.dispatchEvent({type:"dispose"})}}const Rh=new Q,iE=new Q,aE=new yt;class ns{constructor(e=new Q(1,0,0),i=0){this.isPlane=!0,this.normal=e,this.constant=i}set(e,i){return this.normal.copy(e),this.constant=i,this}setComponents(e,i,r,l){return this.normal.set(e,i,r),this.constant=l,this}setFromNormalAndCoplanarPoint(e,i){return this.normal.copy(e),this.constant=-i.dot(this.normal),this}setFromCoplanarPoints(e,i,r){const l=Rh.subVectors(r,i).cross(iE.subVectors(e,i)).normalize();return this.setFromNormalAndCoplanarPoint(l,e),this}copy(e){return this.normal.copy(e.normal),this.constant=e.constant,this}normalize(){const e=1/this.normal.length();return this.normal.multiplyScalar(e),this.constant*=e,this}negate(){return this.constant*=-1,this.normal.negate(),this}distanceToPoint(e){return this.normal.dot(e)+this.constant}distanceToSphere(e){return this.distanceToPoint(e.center)-e.radius}projectPoint(e,i){return i.copy(e).addScaledVector(this.normal,-this.distanceToPoint(e))}intersectLine(e,i,r=!0){const l=e.delta(Rh),c=this.normal.dot(l);if(c===0)return this.distanceToPoint(e.start)===0?i.copy(e.start):null;const f=-(e.start.dot(this.normal)+this.constant)/c;return r===!0&&(f<0||f>1)?null:i.copy(e.start).addScaledVector(l,f)}intersectsLine(e){const i=this.distanceToPoint(e.start),r=this.distanceToPoint(e.end);return i<0&&r>0||r<0&&i>0}intersectsBox(e){return e.intersectsPlane(this)}intersectsSphere(e){return e.intersectsPlane(this)}coplanarPoint(e){return e.copy(this.normal).multiplyScalar(-this.constant)}applyMatrix4(e,i){const r=i||aE.getNormalMatrix(e),l=this.coplanarPoint(Rh).applyMatrix4(e),c=this.normal.applyMatrix3(r).normalize();return this.constant=-l.dot(c),this}translate(e){return this.constant-=e.dot(this.normal),this}equals(e){return e.normal.equals(this.normal)&&e.constant===this.constant}clone(){return new this.constructor().copy(this)}toJSON(){return{normal:this.normal.toArray(),constant:this.constant}}fromJSON(e){return this.normal.fromArray(e.normal),this.constant=e.constant,this}}let rE=0;class ko extends Is{constructor(){super(),this.isMaterial=!0,Object.defineProperty(this,"id",{value:rE++}),this.uuid=Go(),this.name="",this.type="Material",this.blending=Io,this.side=Ns,this.vertexColors=!1,this.opacity=1,this.transparent=!1,this.alphaHash=!1,this.blendSrc=ux,this.blendDst=fx,this.blendEquation=No,this.blendSrcAlpha=null,this.blendDstAlpha=null,this.blendEquationAlpha=null,this.blendColor=new Rt(0,0,0),this.blendAlpha=0,this.depthFunc=ql,this.depthTest=!0,this.depthWrite=!0,this.stencilWriteMask=255,this.stencilFunc=hb,this.stencilRef=0,this.stencilFuncMask=255,this.stencilFail=lh,this.stencilZFail=lh,this.stencilZPass=lh,this.stencilWrite=!1,this.clippingPlanes=null,this.clipIntersection=!1,this.clipShadows=!1,this.shadowSide=null,this.colorWrite=!0,this.precision=null,this.polygonOffset=!1,this.polygonOffsetFactor=0,this.polygonOffsetUnits=0,this.dithering=!1,this.alphaToCoverage=!1,this.premultipliedAlpha=!1,this.forceSinglePass=!1,this.allowOverride=!0,this.visible=!0,this.toneMapped=!0,this.userData={},this.version=0,this._alphaTest=0}get alphaTest(){return this._alphaTest}set alphaTest(e){this._alphaTest>0!=e>0&&this.version++,this._alphaTest=e}onBeforeRender(){}onBeforeCompile(){}customProgramCacheKey(){return this.onBeforeCompile.toString()}setValues(e){if(e!==void 0)for(const i in e){const r=e[i];if(r===void 0){ht(`Material: parameter '${i}' has value of undefined.`);continue}const l=this[i];if(l===void 0){ht(`Material: '${i}' is not a property of THREE.${this.type}.`);continue}l&&l.isColor?l.set(r):l&&l.isVector2&&r&&r.isVector2||l&&l.isEuler&&r&&r.isEuler||l&&l.isVector3&&r&&r.isVector3?l.copy(r):this[i]=r}}toJSON(e){const i=e===void 0||typeof e=="string";i&&(e={textures:{},images:{}});const r={metadata:{version:4.7,type:"Material",generator:"Material.toJSON"}};r.uuid=this.uuid,r.type=this.type,r.blending=this.blending,r.side=this.side,r.shadowSide=this.shadowSide,r.vertexColors=this.vertexColors,r.opacity=this.opacity,r.transparent=this.transparent,r.blendSrc=this.blendSrc,r.blendDst=this.blendDst,r.blendEquation=this.blendEquation,r.blendSrcAlpha=this.blendSrcAlpha,r.blendDstAlpha=this.blendDstAlpha,r.blendEquationAlpha=this.blendEquationAlpha,r.blendColor=this.blendColor.getHex(),r.blendAlpha=this.blendAlpha,r.depthFunc=this.depthFunc,r.depthTest=this.depthTest,r.depthWrite=this.depthWrite,r.colorWrite=this.colorWrite,r.clipIntersection=this.clipIntersection,r.clipShadows=this.clipShadows,r.stencilWriteMask=this.stencilWriteMask,r.stencilFunc=this.stencilFunc,r.stencilRef=this.stencilRef,r.stencilFuncMask=this.stencilFuncMask,r.stencilFail=this.stencilFail,r.stencilZFail=this.stencilZFail,r.stencilZPass=this.stencilZPass,r.stencilWrite=this.stencilWrite,r.polygonOffset=this.polygonOffset,r.polygonOffsetFactor=this.polygonOffsetFactor,r.polygonOffsetUnits=this.polygonOffsetUnits,r.dithering=this.dithering,r.alphaTest=this.alphaTest,r.alphaHash=this.alphaHash,r.alphaToCoverage=this.alphaToCoverage,r.premultipliedAlpha=this.premultipliedAlpha,r.forceSinglePass=this.forceSinglePass,r.allowOverride=this.allowOverride,r.visible=this.visible,r.toneMapped=this.toneMapped,r.name=this.name,this.color&&this.color.isColor&&(r.color=this.color.getHex()),this.roughness!==void 0&&(r.roughness=this.roughness),this.metalness!==void 0&&(r.metalness=this.metalness),this.sheen!==void 0&&(r.sheen=this.sheen),this.sheenColor&&this.sheenColor.isColor&&(r.sheenColor=this.sheenColor.getHex()),this.sheenRoughness!==void 0&&(r.sheenRoughness=this.sheenRoughness),this.emissive&&this.emissive.isColor&&(r.emissive=this.emissive.getHex()),this.emissiveIntensity!==void 0&&(r.emissiveIntensity=this.emissiveIntensity),this.specular&&this.specular.isColor&&(r.specular=this.specular.getHex()),this.specularIntensity!==void 0&&(r.specularIntensity=this.specularIntensity),this.specularColor&&this.specularColor.isColor&&(r.specularColor=this.specularColor.getHex()),this.shininess!==void 0&&(r.shininess=this.shininess),this.clearcoat!==void 0&&(r.clearcoat=this.clearcoat),this.clearcoatRoughness!==void 0&&(r.clearcoatRoughness=this.clearcoatRoughness),this.clearcoatMap&&this.clearcoatMap.isTexture&&(r.clearcoatMap=this.clearcoatMap.toJSON(e).uuid),this.clearcoatRoughnessMap&&this.clearcoatRoughnessMap.isTexture&&(r.clearcoatRoughnessMap=this.clearcoatRoughnessMap.toJSON(e).uuid),this.clearcoatNormalMap&&this.clearcoatNormalMap.isTexture&&(r.clearcoatNormalMap=this.clearcoatNormalMap.toJSON(e).uuid,r.clearcoatNormalScale=this.clearcoatNormalScale.toArray()),this.sheenColorMap&&this.sheenColorMap.isTexture&&(r.sheenColorMap=this.sheenColorMap.toJSON(e).uuid),this.sheenRoughnessMap&&this.sheenRoughnessMap.isTexture&&(r.sheenRoughnessMap=this.sheenRoughnessMap.toJSON(e).uuid),this.dispersion!==void 0&&(r.dispersion=this.dispersion),this.retroreflectivity!==void 0&&(r.retroreflectivity=this.retroreflectivity),this.iridescence!==void 0&&(r.iridescence=this.iridescence),this.iridescenceIOR!==void 0&&(r.iridescenceIOR=this.iridescenceIOR),this.iridescenceThicknessRange!==void 0&&(r.iridescenceThicknessRange=this.iridescenceThicknessRange),this.iridescenceMap&&this.iridescenceMap.isTexture&&(r.iridescenceMap=this.iridescenceMap.toJSON(e).uuid),this.iridescenceThicknessMap&&this.iridescenceThicknessMap.isTexture&&(r.iridescenceThicknessMap=this.iridescenceThicknessMap.toJSON(e).uuid),this.anisotropy!==void 0&&(r.anisotropy=this.anisotropy),this.anisotropyRotation!==void 0&&(r.anisotropyRotation=this.anisotropyRotation),this.anisotropyMap&&this.anisotropyMap.isTexture&&(r.anisotropyMap=this.anisotropyMap.toJSON(e).uuid),this.map&&this.map.isTexture&&(r.map=this.map.toJSON(e).uuid),this.matcap&&this.matcap.isTexture&&(r.matcap=this.matcap.toJSON(e).uuid),this.alphaMap&&this.alphaMap.isTexture&&(r.alphaMap=this.alphaMap.toJSON(e).uuid),this.lightMap&&this.lightMap.isTexture&&(r.lightMap=this.lightMap.toJSON(e).uuid,r.lightMapIntensity=this.lightMapIntensity),this.aoMap&&this.aoMap.isTexture&&(r.aoMap=this.aoMap.toJSON(e).uuid,r.aoMapIntensity=this.aoMapIntensity),this.bumpMap&&this.bumpMap.isTexture&&(r.bumpMap=this.bumpMap.toJSON(e).uuid,r.bumpScale=this.bumpScale),this.normalMap&&this.normalMap.isTexture&&(r.normalMap=this.normalMap.toJSON(e).uuid,r.normalMapType=this.normalMapType,r.normalScale=this.normalScale.toArray()),this.displacementMap&&this.displacementMap.isTexture&&(r.displacementMap=this.displacementMap.toJSON(e).uuid,r.displacementScale=this.displacementScale,r.displacementBias=this.displacementBias),this.roughnessMap&&this.roughnessMap.isTexture&&(r.roughnessMap=this.roughnessMap.toJSON(e).uuid),this.metalnessMap&&this.metalnessMap.isTexture&&(r.metalnessMap=this.metalnessMap.toJSON(e).uuid),this.emissiveMap&&this.emissiveMap.isTexture&&(r.emissiveMap=this.emissiveMap.toJSON(e).uuid),this.specularMap&&this.specularMap.isTexture&&(r.specularMap=this.specularMap.toJSON(e).uuid),this.specularIntensityMap&&this.specularIntensityMap.isTexture&&(r.specularIntensityMap=this.specularIntensityMap.toJSON(e).uuid),this.specularColorMap&&this.specularColorMap.isTexture&&(r.specularColorMap=this.specularColorMap.toJSON(e).uuid),this.envMap&&this.envMap.isTexture&&(r.envMap=this.envMap.toJSON(e).uuid,this.combine!==void 0&&(r.combine=this.combine)),this.envMapRotation!==void 0&&(r.envMapRotation=this.envMapRotation.toArray()),this.envMapIntensity!==void 0&&(r.envMapIntensity=this.envMapIntensity),this.reflectivity!==void 0&&(r.reflectivity=this.reflectivity),this.refractionRatio!==void 0&&(r.refractionRatio=this.refractionRatio),this.gradientMap&&this.gradientMap.isTexture&&(r.gradientMap=this.gradientMap.toJSON(e).uuid),this.transmission!==void 0&&(r.transmission=this.transmission),this.transmissionMap&&this.transmissionMap.isTexture&&(r.transmissionMap=this.transmissionMap.toJSON(e).uuid),this.thickness!==void 0&&(r.thickness=this.thickness),this.thicknessMap&&this.thicknessMap.isTexture&&(r.thicknessMap=this.thicknessMap.toJSON(e).uuid),this.attenuationDistance!==void 0&&(r.attenuationDistance=this.attenuationDistance),this.attenuationColor!==void 0&&(r.attenuationColor=this.attenuationColor.getHex()),this.size!==void 0&&(r.size=this.size),this.sizeAttenuation!==void 0&&(r.sizeAttenuation=this.sizeAttenuation),Array.isArray(this.clippingPlanes)&&this.clippingPlanes.length>0&&(r.clippingPlanes=this.clippingPlanes.map(c=>c.toJSON())),this.rotation!==void 0&&(r.rotation=this.rotation),this.depthPacking!==void 0&&(r.depthPacking=this.depthPacking),this.linewidth!==void 0&&(r.linewidth=this.linewidth),this.linecap!==void 0&&(r.linecap=this.linecap),this.linejoin!==void 0&&(r.linejoin=this.linejoin),this.dashSize!==void 0&&(r.dashSize=this.dashSize),this.gapSize!==void 0&&(r.gapSize=this.gapSize),this.scale!==void 0&&(r.scale=this.scale),this.wireframe!==void 0&&(r.wireframe=this.wireframe),this.wireframeLinewidth!==void 0&&(r.wireframeLinewidth=this.wireframeLinewidth),this.wireframeLinecap!==void 0&&(r.wireframeLinecap=this.wireframeLinecap),this.wireframeLinejoin!==void 0&&(r.wireframeLinejoin=this.wireframeLinejoin),this.flatShading!==void 0&&(r.flatShading=this.flatShading),this.fog!==void 0&&(r.fog=this.fog),Object.keys(this.userData).length>0&&(r.userData=this.userData);function l(c){const f=[];for(const h in c){const m=c[h];delete m.metadata,f.push(m)}return f}if(i){const c=l(e.textures),f=l(e.images);c.length>0&&(r.textures=c),f.length>0&&(r.images=f)}return r}fromJSON(e,i){if(e.uuid!==void 0&&(this.uuid=e.uuid),e.name!==void 0&&(this.name=e.name),e.color!==void 0&&this.color!==void 0&&this.color.setHex(e.color),e.roughness!==void 0&&(this.roughness=e.roughness),e.metalness!==void 0&&(this.metalness=e.metalness),e.sheen!==void 0&&(this.sheen=e.sheen),e.sheenColor!==void 0&&(this.sheenColor=new Rt().setHex(e.sheenColor)),e.sheenRoughness!==void 0&&(this.sheenRoughness=e.sheenRoughness),e.emissive!==void 0&&this.emissive!==void 0&&this.emissive.setHex(e.emissive),e.specular!==void 0&&this.specular!==void 0&&this.specular.setHex(e.specular),e.specularIntensity!==void 0&&(this.specularIntensity=e.specularIntensity),e.specularColor!==void 0&&this.specularColor!==void 0&&this.specularColor.setHex(e.specularColor),e.shininess!==void 0&&(this.shininess=e.shininess),e.clearcoat!==void 0&&(this.clearcoat=e.clearcoat),e.clearcoatRoughness!==void 0&&(this.clearcoatRoughness=e.clearcoatRoughness),e.dispersion!==void 0&&(this.dispersion=e.dispersion),e.retroreflectivity!==void 0&&(this.retroreflectivity=e.retroreflectivity),e.iridescence!==void 0&&(this.iridescence=e.iridescence),e.iridescenceIOR!==void 0&&(this.iridescenceIOR=e.iridescenceIOR),e.iridescenceThicknessRange!==void 0&&(this.iridescenceThicknessRange=e.iridescenceThicknessRange),e.transmission!==void 0&&(this.transmission=e.transmission),e.thickness!==void 0&&(this.thickness=e.thickness),e.attenuationDistance!==void 0&&(this.attenuationDistance=e.attenuationDistance),e.attenuationColor!==void 0&&this.attenuationColor!==void 0&&this.attenuationColor.setHex(e.attenuationColor),e.anisotropy!==void 0&&(this.anisotropy=e.anisotropy),e.anisotropyRotation!==void 0&&(this.anisotropyRotation=e.anisotropyRotation),e.fog!==void 0&&(this.fog=e.fog),e.flatShading!==void 0&&(this.flatShading=e.flatShading),e.blending!==void 0&&(this.blending=e.blending),e.combine!==void 0&&(this.combine=e.combine),e.side!==void 0&&(this.side=e.side),e.shadowSide!==void 0&&(this.shadowSide=e.shadowSide),e.opacity!==void 0&&(this.opacity=e.opacity),e.transparent!==void 0&&(this.transparent=e.transparent),e.alphaTest!==void 0&&(this.alphaTest=e.alphaTest),e.alphaHash!==void 0&&(this.alphaHash=e.alphaHash),e.depthFunc!==void 0&&(this.depthFunc=e.depthFunc),e.depthTest!==void 0&&(this.depthTest=e.depthTest),e.depthWrite!==void 0&&(this.depthWrite=e.depthWrite),e.colorWrite!==void 0&&(this.colorWrite=e.colorWrite),e.clippingPlanes!==void 0&&(this.clippingPlanes=e.clippingPlanes.map(r=>new ns().fromJSON(r))),e.clipIntersection!==void 0&&(this.clipIntersection=e.clipIntersection),e.clipShadows!==void 0&&(this.clipShadows=e.clipShadows),e.depthPacking!==void 0&&(this.depthPacking=e.depthPacking),e.blendSrc!==void 0&&(this.blendSrc=e.blendSrc),e.blendDst!==void 0&&(this.blendDst=e.blendDst),e.blendEquation!==void 0&&(this.blendEquation=e.blendEquation),e.blendSrcAlpha!==void 0&&(this.blendSrcAlpha=e.blendSrcAlpha),e.blendDstAlpha!==void 0&&(this.blendDstAlpha=e.blendDstAlpha),e.blendEquationAlpha!==void 0&&(this.blendEquationAlpha=e.blendEquationAlpha),e.blendColor!==void 0&&this.blendColor!==void 0&&this.blendColor.setHex(e.blendColor),e.blendAlpha!==void 0&&(this.blendAlpha=e.blendAlpha),e.stencilWriteMask!==void 0&&(this.stencilWriteMask=e.stencilWriteMask),e.stencilFunc!==void 0&&(this.stencilFunc=e.stencilFunc),e.stencilRef!==void 0&&(this.stencilRef=e.stencilRef),e.stencilFuncMask!==void 0&&(this.stencilFuncMask=e.stencilFuncMask),e.stencilFail!==void 0&&(this.stencilFail=e.stencilFail),e.stencilZFail!==void 0&&(this.stencilZFail=e.stencilZFail),e.stencilZPass!==void 0&&(this.stencilZPass=e.stencilZPass),e.stencilWrite!==void 0&&(this.stencilWrite=e.stencilWrite),e.wireframe!==void 0&&(this.wireframe=e.wireframe),e.wireframeLinewidth!==void 0&&(this.wireframeLinewidth=e.wireframeLinewidth),e.wireframeLinecap!==void 0&&(this.wireframeLinecap=e.wireframeLinecap),e.wireframeLinejoin!==void 0&&(this.wireframeLinejoin=e.wireframeLinejoin),e.rotation!==void 0&&(this.rotation=e.rotation),e.linewidth!==void 0&&(this.linewidth=e.linewidth),e.linecap!==void 0&&(this.linecap=e.linecap),e.linejoin!==void 0&&(this.linejoin=e.linejoin),e.dashSize!==void 0&&(this.dashSize=e.dashSize),e.gapSize!==void 0&&(this.gapSize=e.gapSize),e.scale!==void 0&&(this.scale=e.scale),e.polygonOffset!==void 0&&(this.polygonOffset=e.polygonOffset),e.polygonOffsetFactor!==void 0&&(this.polygonOffsetFactor=e.polygonOffsetFactor),e.polygonOffsetUnits!==void 0&&(this.polygonOffsetUnits=e.polygonOffsetUnits),e.dithering!==void 0&&(this.dithering=e.dithering),e.alphaToCoverage!==void 0&&(this.alphaToCoverage=e.alphaToCoverage),e.premultipliedAlpha!==void 0&&(this.premultipliedAlpha=e.premultipliedAlpha),e.forceSinglePass!==void 0&&(this.forceSinglePass=e.forceSinglePass),e.allowOverride!==void 0&&(this.allowOverride=e.allowOverride),e.visible!==void 0&&(this.visible=e.visible),e.toneMapped!==void 0&&(this.toneMapped=e.toneMapped),e.userData!==void 0&&(this.userData=e.userData),e.vertexColors!==void 0&&(typeof e.vertexColors=="number"?this.vertexColors=e.vertexColors>0:this.vertexColors=e.vertexColors),e.size!==void 0&&(this.size=e.size),e.sizeAttenuation!==void 0&&(this.sizeAttenuation=e.sizeAttenuation),e.map!==void 0&&(this.map=i[e.map]||null),e.matcap!==void 0&&(this.matcap=i[e.matcap]||null),e.alphaMap!==void 0&&(this.alphaMap=i[e.alphaMap]||null),e.bumpMap!==void 0&&(this.bumpMap=i[e.bumpMap]||null),e.bumpScale!==void 0&&(this.bumpScale=e.bumpScale),e.normalMap!==void 0&&(this.normalMap=i[e.normalMap]||null),e.normalMapType!==void 0&&(this.normalMapType=e.normalMapType),e.normalScale!==void 0){let r=e.normalScale;Array.isArray(r)===!1&&(r=[r,r]),this.normalScale=new Kt().fromArray(r)}return e.displacementMap!==void 0&&(this.displacementMap=i[e.displacementMap]||null),e.displacementScale!==void 0&&(this.displacementScale=e.displacementScale),e.displacementBias!==void 0&&(this.displacementBias=e.displacementBias),e.roughnessMap!==void 0&&(this.roughnessMap=i[e.roughnessMap]||null),e.metalnessMap!==void 0&&(this.metalnessMap=i[e.metalnessMap]||null),e.emissiveMap!==void 0&&(this.emissiveMap=i[e.emissiveMap]||null),e.emissiveIntensity!==void 0&&(this.emissiveIntensity=e.emissiveIntensity),e.specularMap!==void 0&&(this.specularMap=i[e.specularMap]||null),e.specularIntensityMap!==void 0&&(this.specularIntensityMap=i[e.specularIntensityMap]||null),e.specularColorMap!==void 0&&(this.specularColorMap=i[e.specularColorMap]||null),e.envMap!==void 0&&(this.envMap=i[e.envMap]||null),e.envMapRotation!==void 0&&this.envMapRotation.fromArray(e.envMapRotation),e.envMapIntensity!==void 0&&(this.envMapIntensity=e.envMapIntensity),e.reflectivity!==void 0&&(this.reflectivity=e.reflectivity),e.refractionRatio!==void 0&&(this.refractionRatio=e.refractionRatio),e.lightMap!==void 0&&(this.lightMap=i[e.lightMap]||null),e.lightMapIntensity!==void 0&&(this.lightMapIntensity=e.lightMapIntensity),e.aoMap!==void 0&&(this.aoMap=i[e.aoMap]||null),e.aoMapIntensity!==void 0&&(this.aoMapIntensity=e.aoMapIntensity),e.gradientMap!==void 0&&(this.gradientMap=i[e.gradientMap]||null),e.clearcoatMap!==void 0&&(this.clearcoatMap=i[e.clearcoatMap]||null),e.clearcoatRoughnessMap!==void 0&&(this.clearcoatRoughnessMap=i[e.clearcoatRoughnessMap]||null),e.clearcoatNormalMap!==void 0&&(this.clearcoatNormalMap=i[e.clearcoatNormalMap]||null),e.clearcoatNormalScale!==void 0&&(this.clearcoatNormalScale=new Kt().fromArray(e.clearcoatNormalScale)),e.iridescenceMap!==void 0&&(this.iridescenceMap=i[e.iridescenceMap]||null),e.iridescenceThicknessMap!==void 0&&(this.iridescenceThicknessMap=i[e.iridescenceThicknessMap]||null),e.transmissionMap!==void 0&&(this.transmissionMap=i[e.transmissionMap]||null),e.thicknessMap!==void 0&&(this.thicknessMap=i[e.thicknessMap]||null),e.anisotropyMap!==void 0&&(this.anisotropyMap=i[e.anisotropyMap]||null),e.sheenColorMap!==void 0&&(this.sheenColorMap=i[e.sheenColorMap]||null),e.sheenRoughnessMap!==void 0&&(this.sheenRoughnessMap=i[e.sheenRoughnessMap]||null),this}clone(){return new this.constructor().copy(this)}copy(e){this.name=e.name,this.blending=e.blending,this.side=e.side,this.vertexColors=e.vertexColors,this.opacity=e.opacity,this.transparent=e.transparent,this.blendSrc=e.blendSrc,this.blendDst=e.blendDst,this.blendEquation=e.blendEquation,this.blendSrcAlpha=e.blendSrcAlpha,this.blendDstAlpha=e.blendDstAlpha,this.blendEquationAlpha=e.blendEquationAlpha,this.blendColor.copy(e.blendColor),this.blendAlpha=e.blendAlpha,this.depthFunc=e.depthFunc,this.depthTest=e.depthTest,this.depthWrite=e.depthWrite,this.stencilWriteMask=e.stencilWriteMask,this.stencilFunc=e.stencilFunc,this.stencilRef=e.stencilRef,this.stencilFuncMask=e.stencilFuncMask,this.stencilFail=e.stencilFail,this.stencilZFail=e.stencilZFail,this.stencilZPass=e.stencilZPass,this.stencilWrite=e.stencilWrite;const i=e.clippingPlanes;let r=null;if(i!==null){const l=i.length;r=new Array(l);for(let c=0;c!==l;++c)r[c]=i[c].clone()}return this.clippingPlanes=r,this.clipIntersection=e.clipIntersection,this.clipShadows=e.clipShadows,this.shadowSide=e.shadowSide,this.colorWrite=e.colorWrite,this.precision=e.precision,this.polygonOffset=e.polygonOffset,this.polygonOffsetFactor=e.polygonOffsetFactor,this.polygonOffsetUnits=e.polygonOffsetUnits,this.dithering=e.dithering,this.alphaTest=e.alphaTest,this.alphaHash=e.alphaHash,this.alphaToCoverage=e.alphaToCoverage,this.premultipliedAlpha=e.premultipliedAlpha,this.forceSinglePass=e.forceSinglePass,this.allowOverride=e.allowOverride,this.visible=e.visible,this.toneMapped=e.toneMapped,this.userData=JSON.parse(JSON.stringify(e.userData)),this}dispose(){this.dispatchEvent({type:"dispose"})}set needsUpdate(e){e===!0&&this.version++}}const vr=new Q,Ch=new Q,du=new Q,hu=new Q;class Ku{constructor(e=new Q,i=new Q(0,0,-1)){this.origin=e,this.direction=i}set(e,i){return this.origin.copy(e),this.direction.copy(i),this}copy(e){return this.origin.copy(e.origin),this.direction.copy(e.direction),this}at(e,i){return i.copy(this.origin).addScaledVector(this.direction,e)}lookAt(e){return this.direction.copy(e).sub(this.origin).normalize(),this}recast(e){return this.origin.copy(this.at(e,vr)),this}closestPointToPoint(e,i){i.subVectors(e,this.origin);const r=i.dot(this.direction);return r<0?i.copy(this.origin):i.copy(this.origin).addScaledVector(this.direction,r)}distanceToPoint(e){return Math.sqrt(this.distanceSqToPoint(e))}distanceSqToPoint(e){const i=vr.subVectors(e,this.origin).dot(this.direction);return i<0?this.origin.distanceToSquared(e):(vr.copy(this.origin).addScaledVector(this.direction,i),vr.distanceToSquared(e))}distanceSqToSegment(e,i,r,l){Ch.copy(e).add(i).multiplyScalar(.5),du.copy(i).sub(e).normalize(),hu.copy(this.origin).sub(Ch);const c=e.distanceTo(i)*.5,f=-this.direction.dot(du),h=hu.dot(this.direction),m=-hu.dot(du),p=hu.lengthSq(),g=Math.abs(1-f*f);let _,v,x,E;if(g>0)if(_=f*m-h,v=f*h-m,E=c*g,_>=0)if(v>=-E)if(v<=E){const D=1/g;_*=D,v*=D,x=_*(_+f*v+2*h)+v*(f*_+v+2*m)+p}else v=c,_=Math.max(0,-(f*v+h)),x=-_*_+v*(v+2*m)+p;else v=-c,_=Math.max(0,-(f*v+h)),x=-_*_+v*(v+2*m)+p;else v<=-E?(_=Math.max(0,-(-f*c+h)),v=_>0?-c:Math.min(Math.max(-c,-m),c),x=-_*_+v*(v+2*m)+p):v<=E?(_=0,v=Math.min(Math.max(-c,-m),c),x=v*(v+2*m)+p):(_=Math.max(0,-(f*c+h)),v=_>0?c:Math.min(Math.max(-c,-m),c),x=-_*_+v*(v+2*m)+p);else v=f>0?-c:c,_=Math.max(0,-(f*v+h)),x=-_*_+v*(v+2*m)+p;return r&&r.copy(this.origin).addScaledVector(this.direction,_),l&&l.copy(Ch).addScaledVector(du,v),x}intersectSphere(e,i){if(e.radius<0)return null;vr.subVectors(e.center,this.origin);const r=vr.dot(this.direction),l=vr.dot(vr)-r*r,c=e.radius*e.radius;if(l>c)return null;const f=Math.sqrt(c-l),h=r-f,m=r+f;return m<0?null:h<0?this.at(m,i):this.at(h,i)}intersectsSphere(e){return e.radius<0?!1:this.distanceSqToPoint(e.center)<=e.radius*e.radius}distanceToPlane(e){const i=e.normal.dot(this.direction);if(i===0)return e.distanceToPoint(this.origin)===0?0:null;const r=-(this.origin.dot(e.normal)+e.constant)/i;return r>=0?r:null}intersectPlane(e,i){const r=this.distanceToPlane(e);return r===null?null:this.at(r,i)}intersectsPlane(e){const i=e.distanceToPoint(this.origin);return i===0||e.normal.dot(this.direction)*i<0}intersectBox(e,i){let r,l,c,f,h,m;const p=1/this.direction.x,g=1/this.direction.y,_=1/this.direction.z,v=this.origin;return p>=0?(r=(e.min.x-v.x)*p,l=(e.max.x-v.x)*p):(r=(e.max.x-v.x)*p,l=(e.min.x-v.x)*p),g>=0?(c=(e.min.y-v.y)*g,f=(e.max.y-v.y)*g):(c=(e.max.y-v.y)*g,f=(e.min.y-v.y)*g),r>f||c>l||((c>r||isNaN(r))&&(r=c),(f<l||isNaN(l))&&(l=f),_>=0?(h=(e.min.z-v.z)*_,m=(e.max.z-v.z)*_):(h=(e.max.z-v.z)*_,m=(e.min.z-v.z)*_),r>m||h>l)||((h>r||r!==r)&&(r=h),(m<l||l!==l)&&(l=m),l<0)?null:this.at(r>=0?r:l,i)}intersectsBox(e){return this.intersectBox(e,vr)!==null}intersectTriangle(e,i,r,l,c){const f=this.origin,h=this.direction,m=h.x,p=h.y,g=h.z,_=e.x-f.x,v=e.y-f.y,x=e.z-f.z,E=i.x-f.x,D=i.y-f.y,M=i.z-f.z,y=r.x-f.x,F=r.y-f.y,V=r.z-f.z,R=Math.abs(m),N=Math.abs(p),L=Math.abs(g);let P,T,O,B,k,J,se,Y,j,z,H,ee;if(R>=N&&R>=L?(O=m,J=_,j=E,ee=y,m>=0?(P=p,T=g,B=v,k=x,se=D,Y=M,z=F,H=V):(P=g,T=p,B=x,k=v,se=M,Y=D,z=V,H=F)):N>=L?(O=p,J=v,j=D,ee=F,p>=0?(P=g,T=m,B=x,k=_,se=M,Y=E,z=V,H=y):(P=m,T=g,B=_,k=x,se=E,Y=M,z=y,H=V)):(O=g,J=x,j=M,ee=V,g>=0?(P=m,T=p,B=_,k=v,se=E,Y=D,z=y,H=F):(P=p,T=m,B=v,k=_,se=D,Y=E,z=F,H=y)),O===0)return null;const oe=P/O,fe=T/O,U=1/O,re=B-oe*J,xe=k-fe*J,Ue=se-oe*j,Ie=Y-fe*j,Xe=z-oe*ee,ue=H-fe*ee,ye=Xe*Ie-ue*Ue,we=re*ue-xe*Xe,at=Ue*xe-Ie*re;if(l){if(ye<0||we<0||at<0)return null}else if((ye<0||we<0||at<0)&&(ye>0||we>0||at>0))return null;const Ge=ye+we+at;if(Ge===0)return null;const mt=U*(ye*J+we*j+at*ee);return(Ge>0?mt<0:mt>0)?null:this.at(mt/Ge,c)}applyMatrix4(e){return this.origin.applyMatrix4(e),this.direction.transformDirection(e),this}equals(e){return e.origin.equals(this.origin)&&e.direction.equals(this.direction)}clone(){return new this.constructor().copy(this)}}class Qu extends ko{constructor(e){super(),this.isMeshBasicMaterial=!0,this.type="MeshBasicMaterial",this.color=new Rt(16777215),this.map=null,this.lightMap=null,this.lightMapIntensity=1,this.aoMap=null,this.aoMapIntensity=1,this.specularMap=null,this.alphaMap=null,this.envMap=null,this.envMapRotation=new Ps,this.combine=dx,this.reflectivity=1,this.refractionRatio=.98,this.wireframe=!1,this.wireframeLinewidth=1,this.wireframeLinecap="round",this.wireframeLinejoin="round",this.fog=!0,this.setValues(e)}copy(e){return super.copy(e),this.color.copy(e.color),this.map=e.map,this.lightMap=e.lightMap,this.lightMapIntensity=e.lightMapIntensity,this.aoMap=e.aoMap,this.aoMapIntensity=e.aoMapIntensity,this.specularMap=e.specularMap,this.alphaMap=e.alphaMap,this.envMap=e.envMap,this.envMapRotation.copy(e.envMapRotation),this.combine=e.combine,this.reflectivity=e.reflectivity,this.refractionRatio=e.refractionRatio,this.wireframe=e.wireframe,this.wireframeLinewidth=e.wireframeLinewidth,this.wireframeLinecap=e.wireframeLinecap,this.wireframeLinejoin=e.wireframeLinejoin,this.fog=e.fog,this}}const d_=new En,Ts=new Ku,pu=new Fs,h_=new Q,mu=new Q,gu=new Q,vu=new Q,wh=new Q,_u=new Q,p_=new Q,xu=new Q;class Ki extends Ti{constructor(e=new zn,i=new Qu){super(),this.isMesh=!0,this.type="Mesh",this.geometry=e,this.material=i,this.morphTargetDictionary=void 0,this.morphTargetInfluences=void 0,this.count=1,this.updateMorphTargets()}copy(e,i){return super.copy(e,i),e.morphTargetInfluences!==void 0&&(this.morphTargetInfluences=e.morphTargetInfluences.slice()),e.morphTargetDictionary!==void 0&&(this.morphTargetDictionary=Object.assign({},e.morphTargetDictionary)),this.material=Array.isArray(e.material)?e.material.slice():e.material,this.geometry=e.geometry,this}updateMorphTargets(){const i=this.geometry.morphAttributes,r=Object.keys(i);if(r.length>0){const l=i[r[0]];if(l!==void 0){this.morphTargetInfluences=[],this.morphTargetDictionary={};for(let c=0,f=l.length;c<f;c++){const h=l[c].name||String(c);this.morphTargetInfluences.push(0),this.morphTargetDictionary[h]=c}}}}getVertexPosition(e,i){const r=this.geometry,l=r.attributes.position,c=r.morphAttributes.position,f=r.morphTargetsRelative;i.fromBufferAttribute(l,e);const h=this.morphTargetInfluences;if(c&&h){_u.set(0,0,0);for(let m=0,p=c.length;m<p;m++){const g=h[m],_=c[m];g!==0&&(wh.fromBufferAttribute(_,e),f?_u.addScaledVector(wh,g):_u.addScaledVector(wh.sub(i),g))}i.add(_u)}return i}intersectsFrustum(e){return e.intersectsObject(this)}raycast(e,i){const r=this.geometry,l=this.material,c=this.matrixWorld;l!==void 0&&(r.boundingSphere===null&&r.computeBoundingSphere(),pu.copy(r.boundingSphere),pu.applyMatrix4(c),Ts.copy(e.ray).recast(e.near),!(pu.containsPoint(Ts.origin)===!1&&(Ts.intersectSphere(pu,h_)===null||Ts.origin.distanceToSquared(h_)>(e.far-e.near)**2))&&(d_.copy(c).invert(),Ts.copy(e.ray).applyMatrix4(d_),!(r.boundingBox!==null&&Ts.intersectsBox(r.boundingBox)===!1)&&this._computeIntersections(e,i,Ts)))}_computeIntersections(e,i,r){let l;const c=this.geometry,f=this.material,h=c.index,m=c.attributes.position,p=c.attributes.uv,g=c.attributes.uv1,_=c.attributes.normal,v=c.groups,x=c.drawRange;if(h!==null)if(Array.isArray(f))for(let E=0,D=v.length;E<D;E++){const M=v[E],y=f[M.materialIndex],F=Math.max(M.start,x.start),V=Math.min(h.count,Math.min(M.start+M.count,x.start+x.count));for(let R=F,N=V;R<N;R+=3){const L=h.getX(R),P=h.getX(R+1),T=h.getX(R+2);l=Su(this,y,e,r,p,g,_,L,P,T),l&&(l.faceIndex=Math.floor(R/3),l.face.materialIndex=M.materialIndex,i.push(l))}}else{const E=Math.max(0,x.start),D=Math.min(h.count,x.start+x.count);for(let M=E,y=D;M<y;M+=3){const F=h.getX(M),V=h.getX(M+1),R=h.getX(M+2);l=Su(this,f,e,r,p,g,_,F,V,R),l&&(l.faceIndex=Math.floor(M/3),i.push(l))}}else if(m!==void 0)if(Array.isArray(f))for(let E=0,D=v.length;E<D;E++){const M=v[E],y=f[M.materialIndex],F=Math.max(M.start,x.start),V=Math.min(m.count,Math.min(M.start+M.count,x.start+x.count));for(let R=F,N=V;R<N;R+=3){const L=R,P=R+1,T=R+2;l=Su(this,y,e,r,p,g,_,L,P,T),l&&(l.faceIndex=Math.floor(R/3),l.face.materialIndex=M.materialIndex,i.push(l))}}else{const E=Math.max(0,x.start),D=Math.min(m.count,x.start+x.count);for(let M=E,y=D;M<y;M+=3){const F=M,V=M+1,R=M+2;l=Su(this,f,e,r,p,g,_,F,V,R),l&&(l.faceIndex=Math.floor(M/3),i.push(l))}}}}function sE(s,e,i,r,l,c,f,h){let m;if(e.side===Oi?m=r.intersectTriangle(f,c,l,!0,h):m=r.intersectTriangle(l,c,f,e.side===Ns,h),m===null)return null;xu.copy(h),xu.applyMatrix4(s.matrixWorld);const p=i.ray.origin.distanceTo(xu);return p<i.near||p>i.far?null:{distance:p,point:xu.clone(),object:s}}function Su(s,e,i,r,l,c,f,h,m,p){s.getVertexPosition(h,mu),s.getVertexPosition(m,gu),s.getVertexPosition(p,vu);const g=sE(s,e,i,r,mu,gu,vu,p_);if(g){const _=new Q;Aa.getBarycoord(p_,mu,gu,vu,_),l&&(g.uv=Aa.getInterpolatedAttribute(l,h,m,p,_,new Kt)),c&&(g.uv1=Aa.getInterpolatedAttribute(c,h,m,p,_,new Kt)),f&&(g.normal=Aa.getInterpolatedAttribute(f,h,m,p,_,new Q),g.normal.dot(r.direction)>0&&g.normal.multiplyScalar(-1));const v={a:h,b:m,c:p,normal:new Q,materialIndex:0};Aa.getNormal(mu,gu,vu,v.normal),g.face=v,g.barycoord=_}return g}class oE extends gi{constructor(e=null,i=1,r=1,l,c,f,h,m,p=li,g=li,_,v){super(null,f,h,m,p,g,l,c,_,v),this.isDataTexture=!0,this.image={data:e,width:i,height:r},this.generateMipmaps=!1,this.flipY=!1,this.unpackAlignment=1}}const As=new Fs,lE=new Kt(.5,.5),yu=new Q;class Ox{constructor(e=new ns,i=new ns,r=new ns,l=new ns,c=new ns,f=new ns){this.planes=[e,i,r,l,c,f]}set(e,i,r,l,c,f){const h=this.planes;return h[0].copy(e),h[1].copy(i),h[2].copy(r),h[3].copy(l),h[4].copy(c),h[5].copy(f),this}copy(e){const i=this.planes;for(let r=0;r<6;r++)i[r].copy(e.planes[r]);return this}setFromProjectionMatrix(e,i=ka,r=!1){const l=this.planes,c=e.elements,f=c[0],h=c[1],m=c[2],p=c[3],g=c[4],_=c[5],v=c[6],x=c[7],E=c[8],D=c[9],M=c[10],y=c[11],F=c[12],V=c[13],R=c[14],N=c[15];if(l[0].setComponents(p-f,x-g,y-E,N-F).normalize(),l[1].setComponents(p+f,x+g,y+E,N+F).normalize(),l[2].setComponents(p+h,x+_,y+D,N+V).normalize(),l[3].setComponents(p-h,x-_,y-D,N-V).normalize(),r)l[4].setComponents(m,v,M,R).normalize(),l[5].setComponents(p-m,x-v,y-M,N-R).normalize();else if(l[4].setComponents(p-m,x-v,y-M,N-R).normalize(),i===ka)l[5].setComponents(p+m,x+v,y+M,N+R).normalize();else if(i===Xu)l[5].setComponents(m,v,M,R).normalize();else throw new Error("THREE.Frustum.setFromProjectionMatrix(): Invalid coordinate system: "+i);return this}intersectsObject(e){if(e.boundingSphere!==void 0)e.boundingSphere===null&&e.computeBoundingSphere(),As.copy(e.boundingSphere).applyMatrix4(e.matrixWorld);else{const i=e.geometry;i.boundingSphere===null&&i.computeBoundingSphere(),As.copy(i.boundingSphere).applyMatrix4(e.matrixWorld)}return this.intersectsSphere(As)}intersectsSprite(e){As.center.set(0,0,0);const i=lE.distanceTo(e.center);return As.radius=.7071067811865476+i,As.applyMatrix4(e.matrixWorld),this.intersectsSphere(As)}intersectsSphere(e){const i=this.planes,r=e.center,l=-e.radius;for(let c=0;c<6;c++)if(i[c].distanceToPoint(r)<l)return!1;return!0}intersectsBox(e){const i=this.planes;for(let r=0;r<6;r++){const l=i[r];if(yu.x=l.normal.x>0?e.max.x:e.min.x,yu.y=l.normal.y>0?e.max.y:e.min.y,yu.z=l.normal.z>0?e.max.z:e.min.z,l.distanceToPoint(yu)<0)return!1}return!0}containsPoint(e){const i=this.planes;for(let r=0;r<6;r++)if(i[r].distanceToPoint(e)<0)return!1;return!0}clone(){return new this.constructor().copy(this)}}class Kp extends ko{constructor(e){super(),this.isLineBasicMaterial=!0,this.type="LineBasicMaterial",this.color=new Rt(16777215),this.map=null,this.linewidth=1,this.linecap="round",this.linejoin="round",this.fog=!0,this.setValues(e)}copy(e){return super.copy(e),this.color.copy(e.color),this.map=e.map,this.linewidth=e.linewidth,this.linecap=e.linecap,this.linejoin=e.linejoin,this.fog=e.fog,this}}const Wu=new Q,qu=new Q,m_=new En,Pl=new Ku,Mu=new Fs,Dh=new Q,g_=new Q;class Qp extends Ti{constructor(e=new zn,i=new Kp){super(),this.isLine=!0,this.type="Line",this.geometry=e,this.material=i,this.morphTargetDictionary=void 0,this.morphTargetInfluences=void 0,this.updateMorphTargets()}copy(e,i){return super.copy(e,i),this.material=Array.isArray(e.material)?e.material.slice():e.material,this.geometry=e.geometry,this}computeLineDistances(){const e=this.geometry;if(e.index===null){const i=e.attributes.position,r=[0];for(let l=1,c=i.count;l<c;l++)Wu.fromBufferAttribute(i,l-1),qu.fromBufferAttribute(i,l),r[l]=r[l-1],r[l]+=Wu.distanceTo(qu);e.setAttribute("lineDistance",new Cn(r,1))}else ht("Line.computeLineDistances(): Computation only possible with non-indexed BufferGeometry.");return this}intersectsFrustum(e){return e.intersectsObject(this)}raycast(e,i){const r=this.geometry,l=this.matrixWorld,c=e.params.Line.threshold,f=r.drawRange;if(r.boundingSphere===null&&r.computeBoundingSphere(),Mu.copy(r.boundingSphere),Mu.applyMatrix4(l),Mu.radius+=c,e.ray.intersectsSphere(Mu)===!1)return;m_.copy(l).invert(),Pl.copy(e.ray).applyMatrix4(m_);const h=c/((this.scale.x+this.scale.y+this.scale.z)/3),m=h*h,p=this.isLineSegments?2:1,g=r.index,v=r.attributes.position;if(g!==null){const x=Math.max(0,f.start),E=Math.min(g.count,f.start+f.count);for(let D=x,M=E-1;D<M;D+=p){const y=g.getX(D),F=g.getX(D+1),V=bu(this,e,Pl,m,y,F,D);V&&i.push(V)}if(this.isLineLoop){const D=g.getX(E-1),M=g.getX(x),y=bu(this,e,Pl,m,D,M,E-1);y&&i.push(y)}}else{const x=Math.max(0,f.start),E=Math.min(v.count,f.start+f.count);for(let D=x,M=E-1;D<M;D+=p){const y=bu(this,e,Pl,m,D,D+1,D);y&&i.push(y)}if(this.isLineLoop){const D=bu(this,e,Pl,m,E-1,x,E-1);D&&i.push(D)}}}updateMorphTargets(){const i=this.geometry.morphAttributes,r=Object.keys(i);if(r.length>0){const l=i[r[0]];if(l!==void 0){this.morphTargetInfluences=[],this.morphTargetDictionary={};for(let c=0,f=l.length;c<f;c++){const h=l[c].name||String(c);this.morphTargetInfluences.push(0),this.morphTargetDictionary[h]=c}}}}}function bu(s,e,i,r,l,c,f){const h=s.geometry.attributes.position;if(Wu.fromBufferAttribute(h,l),qu.fromBufferAttribute(h,c),i.distanceSqToSegment(Wu,qu,Dh,g_)>r)return;Dh.applyMatrix4(s.matrixWorld);const p=e.ray.origin.distanceTo(Dh);if(!(p<e.near||p>e.far))return{distance:p,point:g_.clone().applyMatrix4(s.matrixWorld),index:f,face:null,faceIndex:null,barycoord:null,object:s}}const v_=new Q,__=new Q;class cE extends Qp{constructor(e,i){super(e,i),this.isLineSegments=!0,this.type="LineSegments"}computeLineDistances(){const e=this.geometry;if(e.index===null){const i=e.attributes.position,r=[];for(let l=0,c=i.count;l<c;l+=2)v_.fromBufferAttribute(i,l),__.fromBufferAttribute(i,l+1),r[l]=l===0?0:r[l-1],r[l+1]=r[l]+v_.distanceTo(__);e.setAttribute("lineDistance",new Cn(r,1))}else ht("LineSegments.computeLineDistances(): Computation only possible with non-indexed BufferGeometry.");return this}}class uE extends ko{constructor(e){super(),this.isPointsMaterial=!0,this.type="PointsMaterial",this.color=new Rt(16777215),this.map=null,this.alphaMap=null,this.size=1,this.sizeAttenuation=!0,this.fog=!0,this.setValues(e)}copy(e){return super.copy(e),this.color.copy(e.color),this.map=e.map,this.alphaMap=e.alphaMap,this.size=e.size,this.sizeAttenuation=e.sizeAttenuation,this.fog=e.fog,this}}const x_=new En,wp=new Ku,Eu=new Fs,Tu=new Q;class Ds extends Ti{constructor(e=new zn,i=new uE){super(),this.isPoints=!0,this.type="Points",this.geometry=e,this.material=i,this.morphTargetDictionary=void 0,this.morphTargetInfluences=void 0,this.updateMorphTargets()}copy(e,i){return super.copy(e,i),this.material=Array.isArray(e.material)?e.material.slice():e.material,this.geometry=e.geometry,this}intersectsFrustum(e){return e.intersectsObject(this)}raycast(e,i){const r=this.geometry,l=this.matrixWorld,c=e.params.Points.threshold,f=r.drawRange;if(r.boundingSphere===null&&r.computeBoundingSphere(),Eu.copy(r.boundingSphere),Eu.applyMatrix4(l),Eu.radius+=c,e.ray.intersectsSphere(Eu)===!1)return;x_.copy(l).invert(),wp.copy(e.ray).applyMatrix4(x_);const h=c/((this.scale.x+this.scale.y+this.scale.z)/3),m=h*h,p=r.index,_=r.attributes.position;if(p!==null){const v=Math.max(0,f.start),x=Math.min(p.count,f.start+f.count);for(let E=v,D=x;E<D;E++){const M=p.getX(E);Tu.fromBufferAttribute(_,M),S_(Tu,M,m,l,e,i,this)}}else{const v=Math.max(0,f.start),x=Math.min(_.count,f.start+f.count);for(let E=v,D=x;E<D;E++)Tu.fromBufferAttribute(_,E),S_(Tu,E,m,l,e,i,this)}}updateMorphTargets(){const i=this.geometry.morphAttributes,r=Object.keys(i);if(r.length>0){const l=i[r[0]];if(l!==void 0){this.morphTargetInfluences=[],this.morphTargetDictionary={};for(let c=0,f=l.length;c<f;c++){const h=l[c].name||String(c);this.morphTargetInfluences.push(0),this.morphTargetDictionary[h]=c}}}}}function S_(s,e,i,r,l,c,f){const h=wp.distanceSqToPoint(s);if(h<i){const m=new Q;wp.closestPointToPoint(s,m),m.applyMatrix4(r);const p=l.ray.origin.distanceTo(m);if(p<l.near||p>l.far)return;c.push({distance:p,distanceToRay:Math.sqrt(h),point:m,index:e,face:null,faceIndex:null,barycoord:null,object:f})}}class Px extends gi{constructor(e=[],i=Ls,r,l,c,f,h,m,p,g){super(e,i,r,l,c,f,h,m,p,g),this.isCubeTexture=!0,this.flipY=!1}get images(){return this.image}set images(e){this.image=e}}class Ql extends gi{constructor(e,i,r=Wa,l,c,f,h=li,m=li,p,g=Er,_=1){if(g!==Er&&g!==ws)throw new Error("THREE.DepthTexture: format must be either THREE.DepthFormat or THREE.DepthStencilFormat");const v={width:e,height:i,depth:_};super(v,l,c,f,h,m,g,r,p),this.isDepthTexture=!0,this.flipY=!1,this.generateMipmaps=!1,this.compareFunction=null}copy(e){return super.copy(e),this.source=new jp(Object.assign({},e.image)),this.compareFunction=e.compareFunction,this}toJSON(e){const i=super.toJSON(e);return i.compareFunction=this.compareFunction,i}}class fE extends Ql{constructor(e,i=Wa,r=Ls,l,c,f=li,h=li,m,p=Er){const g={width:e,height:e,depth:1},_=[g,g,g,g,g,g];super(e,e,i,r,l,c,f,h,m,p),this.image=_,this.isCubeDepthTexture=!0,this.isCubeTexture=!0}get images(){return this.image}set images(e){this.image=e}}class Ix extends gi{constructor(e=null){super(),this.sourceTexture=e,this.isExternalTexture=!0}copy(e){return super.copy(e),this.sourceTexture=e.sourceTexture,this}}class $l extends zn{constructor(e=1,i=1,r=1,l=1,c=1,f=1){super(),this.type="BoxGeometry",this.parameters={width:e,height:i,depth:r,widthSegments:l,heightSegments:c,depthSegments:f};const h=this;l=Math.floor(l),c=Math.floor(c),f=Math.floor(f);const m=[],p=[],g=[],_=[];let v=0,x=0;E("z","y","x",-1,-1,r,i,e,f,c,0),E("z","y","x",1,-1,r,i,-e,f,c,1),E("x","z","y",1,1,e,r,i,l,f,2),E("x","z","y",1,-1,e,r,-i,l,f,3),E("x","y","z",1,-1,e,i,r,l,c,4),E("x","y","z",-1,-1,e,i,-r,l,c,5),this.setIndex(m),this.setAttribute("position",new Cn(p,3)),this.setAttribute("normal",new Cn(g,3)),this.setAttribute("uv",new Cn(_,2));function E(D,M,y,F,V,R,N,L,P,T,O){const B=R/P,k=N/T,J=R/2,se=N/2,Y=L/2,j=P+1,z=T+1;let H=0,ee=0;const oe=new Q;for(let fe=0;fe<z;fe++){const U=fe*k-se;for(let re=0;re<j;re++){const xe=re*B-J;oe[D]=xe*F,oe[M]=U*V,oe[y]=Y,p.push(oe.x,oe.y,oe.z),oe[D]=0,oe[M]=0,oe[y]=L>0?1:-1,g.push(oe.x,oe.y,oe.z),_.push(re/P),_.push(1-fe/T),H+=1}}for(let fe=0;fe<T;fe++)for(let U=0;U<P;U++){const re=v+U+j*fe,xe=v+U+j*(fe+1),Ue=v+(U+1)+j*(fe+1),Ie=v+(U+1)+j*fe;m.push(re,xe,Ie),m.push(xe,Ue,Ie),ee+=6}h.addGroup(x,ee,O),x+=ee,v+=H}}copy(e){return super.copy(e),this.parameters=Object.assign({},e.parameters),this}static fromJSON(e){return new $l(e.width,e.height,e.depth,e.widthSegments,e.heightSegments,e.depthSegments)}}class Fx{constructor(){this.type="Curve",this.arcLengthDivisions=200,this.needsUpdate=!1,this.cacheArcLengths=null}getPoint(){ht("Curve: .getPoint() not implemented.")}getPointAt(e,i){const r=this.getUtoTmapping(e);return this.getPoint(r,i)}getPoints(e=5){const i=[];for(let r=0;r<=e;r++)i.push(this.getPoint(r/e));return i}getSpacedPoints(e=5){const i=[];for(let r=0;r<=e;r++)i.push(this.getPointAt(r/e));return i}getLength(){const e=this.getLengths();return e[e.length-1]}getLengths(e=this.arcLengthDivisions){if(this.cacheArcLengths&&this.cacheArcLengths.length===e+1&&!this.needsUpdate)return this.cacheArcLengths;this.needsUpdate=!1;const i=[];let r,l=this.getPoint(0),c=0;i.push(0);for(let f=1;f<=e;f++)r=this.getPoint(f/e),c+=r.distanceTo(l),i.push(c),l=r;return this.cacheArcLengths=i,i}updateArcLengths(){this.needsUpdate=!0,this.getLengths()}getUtoTmapping(e,i=null){const r=this.getLengths();let l=0;const c=r.length;let f;i?f=i:f=e*r[c-1];let h=0,m=c-1,p;for(;h<=m;)if(l=Math.floor(h+(m-h)/2),p=r[l]-f,p<0)h=l+1;else if(p>0)m=l-1;else{m=l;break}if(l=m,r[l]===f)return l/(c-1);const g=r[l],v=r[l+1]-g,x=(f-g)/v;return(l+x)/(c-1)}getTangent(e,i){let l=e-1e-4,c=e+1e-4;l<0&&(l=0),c>1&&(c=1);const f=this.getPoint(l),h=this.getPoint(c),m=i||(f.isVector2?new Kt:new Q);return m.copy(h).sub(f).normalize(),m}getTangentAt(e,i){const r=this.getUtoTmapping(e);return this.getTangent(r,i)}computeFrenetFrames(e,i=!1){const r=new Q,l=[],c=[],f=[],h=new Q,m=new En;for(let x=0;x<=e;x++){const E=x/e;l[x]=this.getTangentAt(E,new Q)}c[0]=new Q,f[0]=new Q;let p=Number.MAX_VALUE;const g=Math.abs(l[0].x),_=Math.abs(l[0].y),v=Math.abs(l[0].z);g<=p&&(p=g,r.set(1,0,0)),_<=p&&(p=_,r.set(0,1,0)),v<=p&&r.set(0,0,1),h.crossVectors(l[0],r).normalize(),c[0].crossVectors(l[0],h),f[0].crossVectors(l[0],c[0]);for(let x=1;x<=e;x++){if(c[x]=c[x-1].clone(),f[x]=f[x-1].clone(),h.crossVectors(l[x-1],l[x]),h.length()>Number.EPSILON){h.normalize();const E=Math.acos(Ut(l[x-1].dot(l[x]),-1,1));c[x].applyMatrix4(m.makeRotationAxis(h,E))}f[x].crossVectors(l[x],c[x])}if(i===!0){let x=Math.acos(Ut(c[0].dot(c[e]),-1,1));x/=e,l[0].dot(h.crossVectors(c[0],c[e]))>0&&(x=-x);for(let E=1;E<=e;E++)c[E].applyMatrix4(m.makeRotationAxis(l[E],x*E)),f[E].crossVectors(l[E],c[E])}return{tangents:l,normals:c,binormals:f}}clone(){return new this.constructor().copy(this)}copy(e){return this.arcLengthDivisions=e.arcLengthDivisions,this}toJSON(){const e={metadata:{version:4.7,type:"Curve",generator:"Curve.toJSON"}};return e.arcLengthDivisions=this.arcLengthDivisions,e.type=this.type,e}fromJSON(e){return this.arcLengthDivisions=e.arcLengthDivisions,this}}function Jp(){let s=0,e=0,i=0,r=0;function l(c,f,h,m){s=c,e=h,i=-3*c+3*f-2*h-m,r=2*c-2*f+h+m}return{initCatmullRom:function(c,f,h,m,p){l(f,h,p*(h-c),p*(m-f))},initNonuniformCatmullRom:function(c,f,h,m,p,g,_){let v=(f-c)/p-(h-c)/(p+g)+(h-f)/g,x=(h-f)/g-(m-f)/(g+_)+(m-h)/_;v*=g,x*=g,l(f,h,v,x)},calc:function(c){const f=c*c,h=f*c;return s+e*c+i*f+r*h}}}const y_=new Q,M_=new Q,Uh=new Jp,Nh=new Jp,Lh=new Jp;class dE extends Fx{constructor(e=[],i=!1,r="centripetal",l=.5){super(),this.isCatmullRomCurve3=!0,this.type="CatmullRomCurve3",this.points=e,this.closed=i,this.curveType=r,this.tension=l}getPoint(e,i=new Q){const r=i,l=this.points,c=l.length,f=(c-(this.closed?0:1))*e;let h=Math.floor(f),m=f-h;this.closed?h+=h>0?0:(Math.floor(Math.abs(h)/c)+1)*c:m===0&&h===c-1&&(h=c-2,m=1);let p,g;this.closed||h>0?p=l[(h-1)%c]:(M_.subVectors(l[0],l[1]).add(l[0]),p=M_);const _=l[h%c],v=l[(h+1)%c];if(this.closed||h+2<c?g=l[(h+2)%c]:(y_.subVectors(l[c-1],l[c-2]).add(l[c-1]),g=y_),this.curveType==="centripetal"||this.curveType==="chordal"){const x=this.curveType==="chordal"?.5:.25;let E=Math.pow(p.distanceToSquared(_),x),D=Math.pow(_.distanceToSquared(v),x),M=Math.pow(v.distanceToSquared(g),x);D<1e-4&&(D=1),E<1e-4&&(E=D),M<1e-4&&(M=D),Uh.initNonuniformCatmullRom(p.x,_.x,v.x,g.x,E,D,M),Nh.initNonuniformCatmullRom(p.y,_.y,v.y,g.y,E,D,M),Lh.initNonuniformCatmullRom(p.z,_.z,v.z,g.z,E,D,M)}else this.curveType==="catmullrom"&&(Uh.initCatmullRom(p.x,_.x,v.x,g.x,this.tension),Nh.initCatmullRom(p.y,_.y,v.y,g.y,this.tension),Lh.initCatmullRom(p.z,_.z,v.z,g.z,this.tension));return r.set(Uh.calc(m),Nh.calc(m),Lh.calc(m)),r}copy(e){super.copy(e),this.points=[];for(let i=0,r=e.points.length;i<r;i++){const l=e.points[i];this.points.push(l.clone())}return this.closed=e.closed,this.curveType=e.curveType,this.tension=e.tension,this}toJSON(){const e=super.toJSON();e.points=[];for(let i=0,r=this.points.length;i<r;i++){const l=this.points[i];e.points.push(l.toArray())}return e.closed=this.closed,e.curveType=this.curveType,e.tension=this.tension,e}fromJSON(e){super.fromJSON(e),this.points=[];for(let i=0,r=e.points.length;i<r;i++){const l=e.points[i];this.points.push(new Q().fromArray(l))}return this.closed=e.closed,this.curveType=e.curveType,this.tension=e.tension,this}}function hE(s,e){const i=1-s;return i*i*e}function pE(s,e){return 2*(1-s)*s*e}function mE(s,e){return s*s*e}function Oh(s,e,i,r){return hE(s,e)+pE(s,i)+mE(s,r)}class gE extends Fx{constructor(e=new Q,i=new Q,r=new Q){super(),this.isQuadraticBezierCurve3=!0,this.type="QuadraticBezierCurve3",this.v0=e,this.v1=i,this.v2=r}getPoint(e,i=new Q){const r=i,l=this.v0,c=this.v1,f=this.v2;return r.set(Oh(e,l.x,c.x,f.x),Oh(e,l.y,c.y,f.y),Oh(e,l.z,c.z,f.z)),r}copy(e){return super.copy(e),this.v0.copy(e.v0),this.v1.copy(e.v1),this.v2.copy(e.v2),this}toJSON(){const e=super.toJSON();return e.v0=this.v0.toArray(),e.v1=this.v1.toArray(),e.v2=this.v2.toArray(),e}fromJSON(e){return super.fromJSON(e),this.v0.fromArray(e.v0),this.v1.fromArray(e.v1),this.v2.fromArray(e.v2),this}}class ec extends zn{constructor(e=1,i=1,r=1,l=1){super(),this.type="PlaneGeometry",this.parameters={width:e,height:i,widthSegments:r,heightSegments:l};const c=e/2,f=i/2,h=Math.floor(r),m=Math.floor(l),p=h+1,g=m+1,_=e/h,v=i/m,x=[],E=[],D=[],M=[];for(let y=0;y<g;y++){const F=y*v-f;for(let V=0;V<p;V++){const R=V*_-c;E.push(R,-F,0),D.push(0,0,1),M.push(V/h),M.push(1-y/m)}}for(let y=0;y<m;y++)for(let F=0;F<h;F++){const V=F+p*y,R=F+p*(y+1),N=F+1+p*(y+1),L=F+1+p*y;x.push(V,R,L),x.push(R,N,L)}this.setIndex(x),this.setAttribute("position",new Cn(E,3)),this.setAttribute("normal",new Cn(D,3)),this.setAttribute("uv",new Cn(M,2))}copy(e){return super.copy(e),this.parameters=Object.assign({},e.parameters),this}static fromJSON(e){return new ec(e.width,e.height,e.widthSegments,e.heightSegments)}}class Jl extends zn{constructor(e=1,i=32,r=16,l=0,c=Math.PI*2,f=0,h=Math.PI){super(),this.type="SphereGeometry",this.parameters={radius:e,widthSegments:i,heightSegments:r,phiStart:l,phiLength:c,thetaStart:f,thetaLength:h},i=Math.max(3,Math.floor(i)),r=Math.max(2,Math.floor(r));const m=Math.min(f+h,Math.PI);let p=0;const g=[],_=new Q,v=new Q,x=[],E=[],D=[],M=[];for(let y=0;y<=r;y++){const F=[],V=y/r,R=f+V*h,N=e*Math.cos(R),L=Math.sqrt(e*e-N*N);let P=0;y===0&&f===0?P=.5/i:y===r&&m===Math.PI&&(P=-.5/i);for(let T=0;T<=i;T++){const O=T/i,B=l+O*c;_.x=-L*Math.cos(B),_.y=N,_.z=L*Math.sin(B),E.push(_.x,_.y,_.z),v.copy(_).normalize(),D.push(v.x,v.y,v.z),M.push(O+P,1-V),F.push(p++)}g.push(F)}for(let y=0;y<r;y++)for(let F=0;F<i;F++){const V=g[y][F+1],R=g[y][F],N=g[y+1][F],L=g[y+1][F+1];(y!==0||f>0)&&x.push(V,R,L),(y!==r-1||m<Math.PI)&&x.push(R,N,L)}this.setIndex(x),this.setAttribute("position",new Cn(E,3)),this.setAttribute("normal",new Cn(D,3)),this.setAttribute("uv",new Cn(M,2))}copy(e){return super.copy(e),this.parameters=Object.assign({},e.parameters),this}static fromJSON(e){return new Jl(e.radius,e.widthSegments,e.heightSegments,e.phiStart,e.phiLength,e.thetaStart,e.thetaLength)}}function Ho(s){const e={};for(const i in s){e[i]={};for(const r in s[i]){const l=s[i][r];if(b_(l))l.isRenderTargetTexture?(ht("UniformsUtils: Textures of render targets cannot be cloned via cloneUniforms() or mergeUniforms()."),e[i][r]=null):e[i][r]=l.clone();else if(Array.isArray(l))if(b_(l[0])){const c=[];for(let f=0,h=l.length;f<h;f++)c[f]=l[f].clone();e[i][r]=c}else e[i][r]=l.slice();else e[i][r]=l}}return e}function bi(s){const e={};for(let i=0;i<s.length;i++){const r=Ho(s[i]);for(const l in r)e[l]=r[l]}return e}function b_(s){return s&&(s.isColor||s.isMatrix3||s.isMatrix4||s.isVector2||s.isVector3||s.isVector4||s.isTexture||s.isQuaternion)}function vE(s){const e=[];for(let i=0;i<s.length;i++)e.push(s[i].clone());return e}function zx(s){const e=s.getRenderTarget();return e===null?s.outputColorSpace:e.isXRRenderTarget===!0?e.texture.colorSpace:kt.workingColorSpace}const _E={clone:Ho,merge:bi};var xE=`void main() {
	gl_Position = projectionMatrix * modelViewMatrix * vec4( position, 1.0 );
}`,SE=`void main() {
	gl_FragColor = vec4( 1.0, 0.0, 0.0, 1.0 );
}`;class Yn extends ko{constructor(e){super(),this.isShaderMaterial=!0,this.type="ShaderMaterial",this.defines={},this.uniforms={},this.uniformsGroups=[],this.vertexShader=xE,this.fragmentShader=SE,this.linewidth=1,this.wireframe=!1,this.wireframeLinewidth=1,this.fog=!1,this.lights=!1,this.clipping=!1,this.forceSinglePass=!0,this.extensions={clipCullDistance:!1,multiDraw:!1},this.defaultAttributeValues={color:[1,1,1],uv:[0,0],uv1:[0,0]},this.index0AttributeName=void 0,this.uniformsNeedUpdate=!1,this.glslVersion=null,e!==void 0&&this.setValues(e)}copy(e){return super.copy(e),this.fragmentShader=e.fragmentShader,this.vertexShader=e.vertexShader,this.uniforms=Ho(e.uniforms),this.uniformsGroups=vE(e.uniformsGroups),this.defines=Object.assign({},e.defines),this.wireframe=e.wireframe,this.wireframeLinewidth=e.wireframeLinewidth,this.fog=e.fog,this.lights=e.lights,this.clipping=e.clipping,this.extensions=Object.assign({},e.extensions),this.glslVersion=e.glslVersion,this.defaultAttributeValues=Object.assign({},e.defaultAttributeValues),this.index0AttributeName=e.index0AttributeName,this.uniformsNeedUpdate=e.uniformsNeedUpdate,this}toJSON(e){const i=super.toJSON(e);i.glslVersion=this.glslVersion,i.uniforms={};for(const l in this.uniforms){const f=this.uniforms[l].value;f&&f.isTexture?i.uniforms[l]={type:"t",value:f.toJSON(e).uuid}:f&&f.isColor?i.uniforms[l]={type:"c",value:f.getHex()}:f&&f.isVector2?i.uniforms[l]={type:"v2",value:f.toArray()}:f&&f.isVector3?i.uniforms[l]={type:"v3",value:f.toArray()}:f&&f.isVector4?i.uniforms[l]={type:"v4",value:f.toArray()}:f&&f.isMatrix3?i.uniforms[l]={type:"m3",value:f.toArray()}:f&&f.isMatrix4?i.uniforms[l]={type:"m4",value:f.toArray()}:i.uniforms[l]={value:f}}Object.keys(this.defines).length>0&&(i.defines=this.defines),i.vertexShader=this.vertexShader,i.fragmentShader=this.fragmentShader,i.lights=this.lights,i.clipping=this.clipping;const r={};for(const l in this.extensions)this.extensions[l]===!0&&(r[l]=!0);return Object.keys(r).length>0&&(i.extensions=r),i}fromJSON(e,i){if(super.fromJSON(e,i),e.uniforms!==void 0)for(const r in e.uniforms){const l=e.uniforms[r];switch(this.uniforms[r]={},l.type){case"t":this.uniforms[r].value=i[l.value]||null;break;case"c":this.uniforms[r].value=new Rt().setHex(l.value);break;case"v2":this.uniforms[r].value=new Kt().fromArray(l.value);break;case"v3":this.uniforms[r].value=new Q().fromArray(l.value);break;case"v4":this.uniforms[r].value=new Ln().fromArray(l.value);break;case"m3":this.uniforms[r].value=new yt().fromArray(l.value);break;case"m4":this.uniforms[r].value=new En().fromArray(l.value);break;default:this.uniforms[r].value=l.value}}if(e.defines!==void 0&&(this.defines=e.defines),e.vertexShader!==void 0&&(this.vertexShader=e.vertexShader),e.fragmentShader!==void 0&&(this.fragmentShader=e.fragmentShader),e.glslVersion!==void 0&&(this.glslVersion=e.glslVersion),e.extensions!==void 0)for(const r in e.extensions)this.extensions[r]=e.extensions[r];return e.lights!==void 0&&(this.lights=e.lights),e.clipping!==void 0&&(this.clipping=e.clipping),this}}class yE extends Yn{constructor(e){super(e),this.isRawShaderMaterial=!0,this.type="RawShaderMaterial"}}class ME extends ko{constructor(e){super(),this.isMeshDepthMaterial=!0,this.type="MeshDepthMaterial",this.depthPacking=fb,this.map=null,this.alphaMap=null,this.displacementMap=null,this.displacementScale=1,this.displacementBias=0,this.wireframe=!1,this.wireframeLinewidth=1,this.setValues(e)}copy(e){return super.copy(e),this.depthPacking=e.depthPacking,this.map=e.map,this.alphaMap=e.alphaMap,this.displacementMap=e.displacementMap,this.displacementScale=e.displacementScale,this.displacementBias=e.displacementBias,this.wireframe=e.wireframe,this.wireframeLinewidth=e.wireframeLinewidth,this}}class bE extends ko{constructor(e){super(),this.isMeshDistanceMaterial=!0,this.type="MeshDistanceMaterial",this.map=null,this.alphaMap=null,this.displacementMap=null,this.displacementScale=1,this.displacementBias=0,this.setValues(e)}copy(e){return super.copy(e),this.map=e.map,this.alphaMap=e.alphaMap,this.displacementMap=e.displacementMap,this.displacementScale=e.displacementScale,this.displacementBias=e.displacementBias,this}}const Ph={enabled:!1,files:{},add:function(s,e){this.enabled!==!1&&(E_(s)||(this.files[s]=e))},get:function(s){if(this.enabled!==!1&&!E_(s))return this.files[s]},remove:function(s){delete this.files[s]},clear:function(){this.files={}}};function E_(s){try{const e=s.slice(s.indexOf(":")+1);return new URL(e).protocol==="blob:"}catch{return!1}}class EE{constructor(e,i,r){const l=this;let c=!1,f=0,h=0,m;const p=[];this.onStart=void 0,this.onLoad=e,this.onProgress=i,this.onError=r,this._abortController=null,this.itemStart=function(g){h++,c===!1&&l.onStart!==void 0&&l.onStart(g,f,h),c=!0},this.itemEnd=function(g){f++,l.onProgress!==void 0&&l.onProgress(g,f,h),f===h&&(c=!1,l.onLoad!==void 0&&l.onLoad())},this.itemError=function(g){l.onError!==void 0&&l.onError(g)},this.resolveURL=function(g){return g=g.normalize("NFC"),m?m(g):g},this.setURLModifier=function(g){return m=g,this},this.addHandler=function(g,_){return p.push(g,_),this},this.removeHandler=function(g){const _=p.indexOf(g);return _!==-1&&p.splice(_,2),this},this.getHandler=function(g){for(let _=0,v=p.length;_<v;_+=2){const x=p[_],E=p[_+1];if(x.global&&(x.lastIndex=0),x.test(g))return E}return null},this.abort=function(){return this.abortController.abort(),this._abortController=null,this}}get abortController(){return this._abortController||(this._abortController=new AbortController),this._abortController}}const TE=new EE;class $p{constructor(e){this.manager=e!==void 0?e:TE,this.crossOrigin="anonymous",this.withCredentials=!1,this.path="",this.resourcePath="",this.requestHeader={},typeof __THREE_DEVTOOLS__<"u"&&__THREE_DEVTOOLS__.dispatchEvent(new CustomEvent("observe",{detail:this}))}load(){}loadAsync(e,i){const r=this;return new Promise(function(l,c){r.load(e,l,i,c)})}parse(){}setCrossOrigin(e){return this.crossOrigin=e,this}setWithCredentials(e){return this.withCredentials=e,this}setPath(e){return this.path=e,this}setResourcePath(e){return this.resourcePath=e,this}setRequestHeader(e){return this.requestHeader=e,this}abort(){return this}}$p.DEFAULT_MATERIAL_NAME="__DEFAULT";const Ro=new WeakMap;class AE extends $p{constructor(e){super(e)}load(e,i,r,l){this.path!==void 0&&(e=this.path+e),e=this.manager.resolveURL(e);const c=this,f=Ph.get(`image:${e}`);if(f!==void 0){if(f.complete===!0)c.manager.itemStart(e),setTimeout(function(){i&&i(f),c.manager.itemEnd(e)},0);else{let _=Ro.get(f);_===void 0&&(_=[],Ro.set(f,_)),_.push({onLoad:i,onError:l})}return f}const h=Zl("img");function m(){g(),i&&i(this);const _=Ro.get(this)||[];for(let v=0;v<_.length;v++){const x=_[v];x.onLoad&&x.onLoad(this)}Ro.delete(this),c.manager.itemEnd(e)}function p(_){g(),l&&l(_),Ph.remove(`image:${e}`);const v=Ro.get(this)||[];for(let x=0;x<v.length;x++){const E=v[x];E.onError&&E.onError(_)}Ro.delete(this),c.manager.itemError(e),c.manager.itemEnd(e)}function g(){h.removeEventListener("load",m,!1),h.removeEventListener("error",p,!1)}return h.addEventListener("load",m,!1),h.addEventListener("error",p,!1),e.slice(0,5)!=="data:"&&this.crossOrigin!==void 0&&(h.crossOrigin=this.crossOrigin),Ph.add(`image:${e}`,h),c.manager.itemStart(e),h.src=e,h}}class RE extends $p{constructor(e){super(e)}load(e,i,r,l){const c=new gi,f=new AE(this.manager);return f.setCrossOrigin(this.crossOrigin),f.setPath(this.path),f.load(e,function(h){c.image=h,c.needsUpdate=!0,i!==void 0&&i(c)},r,l),c}}const Au=new Q,Ru=new ss,Ba=new Q;class Bx extends Ti{constructor(){super(),this.isCamera=!0,this.type="Camera",this.matrixWorldInverse=new En,this.projectionMatrix=new En,this.projectionMatrixInverse=new En,this.coordinateSystem=ka,this._reversedDepth=!1}get reversedDepth(){return this._reversedDepth}copy(e,i){return super.copy(e,i),this.matrixWorldInverse.copy(e.matrixWorldInverse),this.projectionMatrix.copy(e.projectionMatrix),this.projectionMatrixInverse.copy(e.projectionMatrixInverse),this.coordinateSystem=e.coordinateSystem,this}getWorldDirection(e){return super.getWorldDirection(e).negate()}updateMatrixWorld(e){super.updateMatrixWorld(e),this.matrixWorld.decompose(Au,Ru,Ba),Ba.x===1&&Ba.y===1&&Ba.z===1?this.matrixWorldInverse.copy(this.matrixWorld).invert():this.matrixWorldInverse.compose(Au,Ru,Ba.set(1,1,1)).invert()}updateWorldMatrix(e,i,r=!1){super.updateWorldMatrix(e,i,r),this.matrixWorld.decompose(Au,Ru,Ba),Ba.x===1&&Ba.y===1&&Ba.z===1?this.matrixWorldInverse.copy(this.matrixWorld).invert():this.matrixWorldInverse.compose(Au,Ru,Ba.set(1,1,1)).invert()}clone(){return new this.constructor().copy(this)}}const ts=new Q,T_=new Kt,A_=new Kt;class Yi extends Bx{constructor(e=50,i=1,r=.1,l=2e3){super(),this.isPerspectiveCamera=!0,this.type="PerspectiveCamera",this.fov=e,this.zoom=1,this.near=r,this.far=l,this.focus=10,this.aspect=i,this.view=null,this.filmGauge=35,this.filmOffset=0,this.updateProjectionMatrix()}copy(e,i){return super.copy(e,i),this.fov=e.fov,this.zoom=e.zoom,this.near=e.near,this.far=e.far,this.focus=e.focus,this.aspect=e.aspect,this.view=e.view===null?null:Object.assign({},e.view),this.filmGauge=e.filmGauge,this.filmOffset=e.filmOffset,this}setFocalLength(e){const i=.5*this.getFilmHeight()/e;this.fov=Kl*2*Math.atan(i),this.updateProjectionMatrix()}getFocalLength(){const e=Math.tan(Gl*.5*this.fov);return .5*this.getFilmHeight()/e}getEffectiveFOV(){return Kl*2*Math.atan(Math.tan(Gl*.5*this.fov)/this.zoom)}getFilmWidth(){return this.filmGauge*Math.min(this.aspect,1)}getFilmHeight(){return this.filmGauge/Math.max(this.aspect,1)}getViewBounds(e,i,r){ts.set(-1,-1,.5).applyMatrix4(this.projectionMatrixInverse),i.set(ts.x,ts.y).multiplyScalar(-e/ts.z),ts.set(1,1,.5).applyMatrix4(this.projectionMatrixInverse),r.set(ts.x,ts.y).multiplyScalar(-e/ts.z)}getViewSize(e,i){return this.getViewBounds(e,T_,A_),i.subVectors(A_,T_)}setViewOffset(e,i,r,l,c,f){this.aspect=e/i,this.view===null&&(this.view={enabled:!0,fullWidth:1,fullHeight:1,offsetX:0,offsetY:0,width:1,height:1}),this.view.enabled=!0,this.view.fullWidth=e,this.view.fullHeight=i,this.view.offsetX=r,this.view.offsetY=l,this.view.width=c,this.view.height=f,this.updateProjectionMatrix()}clearViewOffset(){this.view!==null&&(this.view.enabled=!1),this.updateProjectionMatrix()}updateProjectionMatrix(){const e=this.near;let i=e*Math.tan(Gl*.5*this.fov)/this.zoom,r=2*i,l=this.aspect*r,c=-.5*l;const f=this.view;if(this.view!==null&&this.view.enabled){const m=f.fullWidth,p=f.fullHeight;c+=f.offsetX*l/m,i-=f.offsetY*r/p,l*=f.width/m,r*=f.height/p}const h=this.filmOffset;h!==0&&(c+=e*h/this.getFilmWidth()),this.projectionMatrix.makePerspective(c,c+l,i,i-r,e,this.far,this.coordinateSystem,this.reversedDepth),this.projectionMatrixInverse.copy(this.projectionMatrix).invert()}toJSON(e){const i=super.toJSON(e);return i.object.fov=this.fov,i.object.zoom=this.zoom,i.object.near=this.near,i.object.far=this.far,i.object.focus=this.focus,i.object.aspect=this.aspect,this.view!==null&&(i.object.view=Object.assign({},this.view)),i.object.filmGauge=this.filmGauge,i.object.filmOffset=this.filmOffset,i}}class Hx extends Bx{constructor(e=-1,i=1,r=1,l=-1,c=.1,f=2e3){super(),this.isOrthographicCamera=!0,this.type="OrthographicCamera",this.zoom=1,this.view=null,this.left=e,this.right=i,this.top=r,this.bottom=l,this.near=c,this.far=f,this.updateProjectionMatrix()}copy(e,i){return super.copy(e,i),this.left=e.left,this.right=e.right,this.top=e.top,this.bottom=e.bottom,this.near=e.near,this.far=e.far,this.zoom=e.zoom,this.view=e.view===null?null:Object.assign({},e.view),this}setViewOffset(e,i,r,l,c,f){this.view===null&&(this.view={enabled:!0,fullWidth:1,fullHeight:1,offsetX:0,offsetY:0,width:1,height:1}),this.view.enabled=!0,this.view.fullWidth=e,this.view.fullHeight=i,this.view.offsetX=r,this.view.offsetY=l,this.view.width=c,this.view.height=f,this.updateProjectionMatrix()}clearViewOffset(){this.view!==null&&(this.view.enabled=!1),this.updateProjectionMatrix()}updateProjectionMatrix(){const e=(this.right-this.left)/(2*this.zoom),i=(this.top-this.bottom)/(2*this.zoom),r=(this.right+this.left)/2,l=(this.top+this.bottom)/2;let c=r-e,f=r+e,h=l+i,m=l-i;if(this.view!==null&&this.view.enabled){const p=(this.right-this.left)/this.view.fullWidth/this.zoom,g=(this.top-this.bottom)/this.view.fullHeight/this.zoom;c+=p*this.view.offsetX,f=c+p*this.view.width,h-=g*this.view.offsetY,m=h-g*this.view.height}this.projectionMatrix.makeOrthographic(c,f,h,m,this.near,this.far,this.coordinateSystem,this.reversedDepth),this.projectionMatrixInverse.copy(this.projectionMatrix).invert()}toJSON(e){const i=super.toJSON(e);return i.object.zoom=this.zoom,i.object.left=this.left,i.object.right=this.right,i.object.top=this.top,i.object.bottom=this.bottom,i.object.near=this.near,i.object.far=this.far,this.view!==null&&(i.object.view=Object.assign({},this.view)),i}}const Co=-90,wo=1;class CE extends Ti{constructor(e,i,r){super(),this.type="CubeCamera",this.renderTarget=r,this.coordinateSystem=null,this.activeMipmapLevel=0;const l=new Yi(Co,wo,e,i);l.layers=this.layers,this.add(l);const c=new Yi(Co,wo,e,i);c.layers=this.layers,this.add(c);const f=new Yi(Co,wo,e,i);f.layers=this.layers,this.add(f);const h=new Yi(Co,wo,e,i);h.layers=this.layers,this.add(h);const m=new Yi(Co,wo,e,i);m.layers=this.layers,this.add(m);const p=new Yi(Co,wo,e,i);p.layers=this.layers,this.add(p)}updateCoordinateSystem(){const e=this.coordinateSystem,i=this.children.concat(),[r,l,c,f,h,m]=i;for(const p of i)this.remove(p);if(e===ka)r.up.set(0,1,0),r.lookAt(1,0,0),l.up.set(0,1,0),l.lookAt(-1,0,0),c.up.set(0,0,-1),c.lookAt(0,1,0),f.up.set(0,0,1),f.lookAt(0,-1,0),h.up.set(0,1,0),h.lookAt(0,0,1),m.up.set(0,1,0),m.lookAt(0,0,-1);else if(e===Xu)r.up.set(0,-1,0),r.lookAt(-1,0,0),l.up.set(0,-1,0),l.lookAt(1,0,0),c.up.set(0,0,1),c.lookAt(0,1,0),f.up.set(0,0,-1),f.lookAt(0,-1,0),h.up.set(0,-1,0),h.lookAt(0,0,1),m.up.set(0,-1,0),m.lookAt(0,0,-1);else throw new Error("THREE.CubeCamera.updateCoordinateSystem(): Invalid coordinate system: "+e);for(const p of i)this.add(p),p.updateMatrixWorld()}update(e,i){this.parent===null&&this.updateMatrixWorld();const{renderTarget:r,activeMipmapLevel:l}=this;this.coordinateSystem!==e.coordinateSystem&&(this.coordinateSystem=e.coordinateSystem,this.updateCoordinateSystem());const[c,f,h,m,p,g]=this.children,_=e.getRenderTarget(),v=e.getActiveCubeFace(),x=e.getActiveMipmapLevel(),E=e.xr.enabled;e.xr.enabled=!1;const D=r.texture.generateMipmaps;r.texture.generateMipmaps=!1;let M=!1;e.isWebGLRenderer===!0?M=e.state.buffers.depth.getReversed():M=e.reversedDepthBuffer,e.setRenderTarget(r,0,l),M&&e.autoClear===!1&&e.clearDepth(),e.render(i,c),e.setRenderTarget(r,1,l),M&&e.autoClear===!1&&e.clearDepth(),e.render(i,f),e.setRenderTarget(r,2,l),M&&e.autoClear===!1&&e.clearDepth(),e.render(i,h),e.setRenderTarget(r,3,l),M&&e.autoClear===!1&&e.clearDepth(),e.render(i,m),e.setRenderTarget(r,4,l),M&&e.autoClear===!1&&e.clearDepth(),e.render(i,p),r.texture.generateMipmaps=D,e.setRenderTarget(r,5,l),M&&e.autoClear===!1&&e.clearDepth(),e.render(i,g),e.setRenderTarget(_,v,x),e.xr.enabled=E,r.texture.needsPMREMUpdate=!0}}class wE extends Yi{constructor(e=[]){super(),this.isArrayCamera=!0,this.isMultiViewCamera=!1,this.cameras=e}}const R_=new En;class DE{constructor(e,i,r=0,l=1/0){this.ray=new Ku(e,i),this.near=r,this.far=l,this.camera=null,this.layers=new Zp,this.params={Mesh:{},Line:{threshold:1},LOD:{},Points:{threshold:1},Sprite:{}}}set(e,i){this.ray.set(e,i)}setFromCamera(e,i){i.isPerspectiveCamera?(this.ray.origin.setFromMatrixPosition(i.matrixWorld),this.ray.direction.set(e.x,e.y,.5).unproject(i).sub(this.ray.origin).normalize(),this.camera=i):i.isOrthographicCamera?(this.ray.origin.set(e.x,e.y,i.projectionMatrix.elements[14]).unproject(i),this.ray.direction.set(0,0,-1).transformDirection(i.matrixWorld),this.camera=i):Zt("Raycaster: Unsupported camera type: "+i.type)}setFromXRController(e){return R_.identity().extractRotation(e.matrixWorld),this.ray.origin.setFromMatrixPosition(e.matrixWorld),this.ray.direction.set(0,0,-1).applyMatrix4(R_),this}intersectObject(e,i=!0,r=[]){return Dp(e,this,r,i),r.sort(C_),r}intersectObjects(e,i=!0,r=[]){for(let l=0,c=e.length;l<c;l++)Dp(e[l],this,r,i);return r.sort(C_),r}}function C_(s,e){return s.distance-e.distance}function Dp(s,e,i,r){let l=!0;if(s.layers.test(e.layers)&&s.raycast(e,i)===!1&&(l=!1),l===!0&&r===!0){const c=s.children;for(let f=0,h=c.length;f<h;f++)Dp(c[f],e,i,!0)}}const lm=class lm{constructor(e,i,r,l){this.elements=[1,0,0,1],e!==void 0&&this.set(e,i,r,l)}identity(){return this.set(1,0,0,1),this}fromArray(e,i=0){for(let r=0;r<4;r++)this.elements[r]=e[r+i];return this}set(e,i,r,l){const c=this.elements;return c[0]=e,c[2]=i,c[1]=r,c[3]=l,this}};lm.prototype.isMatrix2=!0;let w_=lm;function D_(s,e,i,r){const l=UE(r);switch(i){case Tx:return s*e;case Rx:return s*e/l.components*l.byteLength;case Vp:return s*e/l.components*l.byteLength;case Os:return s*e*2/l.components*l.byteLength;case kp:return s*e*2/l.components*l.byteLength;case Ax:return s*e*3/l.components*l.byteLength;case Ra:return s*e*4/l.components*l.byteLength;case Xp:return s*e*4/l.components*l.byteLength;case Nu:case Lu:return Math.floor((s+3)/4)*Math.floor((e+3)/4)*8;case Ou:case Pu:return Math.floor((s+3)/4)*Math.floor((e+3)/4)*16;case ep:case np:return Math.max(s,16)*Math.max(e,8)/4;case $h:case tp:return Math.max(s,8)*Math.max(e,8)/2;case ip:case ap:case sp:case op:return Math.floor((s+3)/4)*Math.floor((e+3)/4)*8;case rp:case Hu:case lp:return Math.floor((s+3)/4)*Math.floor((e+3)/4)*16;case cp:return Math.floor((s+3)/4)*Math.floor((e+3)/4)*16;case up:return Math.floor((s+4)/5)*Math.floor((e+3)/4)*16;case fp:return Math.floor((s+4)/5)*Math.floor((e+4)/5)*16;case dp:return Math.floor((s+5)/6)*Math.floor((e+4)/5)*16;case hp:return Math.floor((s+5)/6)*Math.floor((e+5)/6)*16;case pp:return Math.floor((s+7)/8)*Math.floor((e+4)/5)*16;case mp:return Math.floor((s+7)/8)*Math.floor((e+5)/6)*16;case gp:return Math.floor((s+7)/8)*Math.floor((e+7)/8)*16;case vp:return Math.floor((s+9)/10)*Math.floor((e+4)/5)*16;case _p:return Math.floor((s+9)/10)*Math.floor((e+5)/6)*16;case xp:return Math.floor((s+9)/10)*Math.floor((e+7)/8)*16;case Sp:return Math.floor((s+9)/10)*Math.floor((e+9)/10)*16;case yp:return Math.floor((s+11)/12)*Math.floor((e+9)/10)*16;case Mp:return Math.floor((s+11)/12)*Math.floor((e+11)/12)*16;case bp:case Ep:case Tp:return Math.ceil(s/4)*Math.ceil(e/4)*16;case Ap:case Rp:return Math.ceil(s/4)*Math.ceil(e/4)*8;case Gu:case Cp:return Math.ceil(s/4)*Math.ceil(e/4)*16}throw new Error(`Unable to determine texture byte length for ${i} format.`)}function UE(s){switch(s){case ha:case yx:return{byteLength:1,components:1};case Yl:case Mx:case qa:return{byteLength:2,components:1};case Hp:case Gp:return{byteLength:2,components:4};case Wa:case Bp:case Va:return{byteLength:4,components:1};case bx:case Ex:return{byteLength:4,components:3}}throw new Error(`THREE.TextureUtils: Unknown texture type ${s}.`)}typeof __THREE_DEVTOOLS__<"u"&&__THREE_DEVTOOLS__.dispatchEvent(new CustomEvent("register",{detail:{revision:zp}}));typeof window<"u"&&(window.__THREE__?ht("WARNING: Multiple instances of Three.js being imported."):window.__THREE__=zp);/**
 * @license
 * Copyright 2010-2026 Three.js Authors
 * SPDX-License-Identifier: MIT
 */function Gx(){let s=null,e=!1,i=null,r=null;function l(c,f){r=s.requestAnimationFrame(l),i(c,f)}return{start:function(){e!==!0&&i!==null&&s!==null&&(r=s.requestAnimationFrame(l),e=!0)},stop:function(){s!==null&&s.cancelAnimationFrame(r),e=!1},setAnimationLoop:function(c){i=c},setContext:function(c){s=c}}}function NE(s){const e=new WeakMap;function i(h,m){const p=h.array,g=h.usage,_=p.byteLength,v=s.createBuffer();s.bindBuffer(m,v),s.bufferData(m,p,g),h.onUploadCallback();let x;if(p instanceof Float32Array)x=s.FLOAT;else if(typeof Float16Array<"u"&&p instanceof Float16Array)x=s.HALF_FLOAT;else if(p instanceof Uint16Array)h.isFloat16BufferAttribute?x=s.HALF_FLOAT:x=s.UNSIGNED_SHORT;else if(p instanceof Int16Array)x=s.SHORT;else if(p instanceof Uint32Array)x=s.UNSIGNED_INT;else if(p instanceof Int32Array)x=s.INT;else if(p instanceof Int8Array)x=s.BYTE;else if(p instanceof Uint8Array)x=s.UNSIGNED_BYTE;else if(p instanceof Uint8ClampedArray)x=s.UNSIGNED_BYTE;else throw new Error("THREE.WebGLAttributes: Unsupported buffer data format: "+p);return{buffer:v,type:x,bytesPerElement:p.BYTES_PER_ELEMENT,version:h.version,size:_}}function r(h,m,p){const g=m.array,_=m.updateRanges;if(s.bindBuffer(p,h),_.length===0)s.bufferSubData(p,0,g);else{_.sort((x,E)=>x.start-E.start);let v=0;for(let x=1;x<_.length;x++){const E=_[v],D=_[x];D.start<=E.start+E.count+1?E.count=Math.max(E.count,D.start+D.count-E.start):(++v,_[v]=D)}_.length=v+1;for(let x=0,E=_.length;x<E;x++){const D=_[x];s.bufferSubData(p,D.start*g.BYTES_PER_ELEMENT,g,D.start,D.count)}m.clearUpdateRanges()}m.onUploadCallback()}function l(h){return h.isInterleavedBufferAttribute&&(h=h.data),e.get(h)}function c(h){h.isInterleavedBufferAttribute&&(h=h.data);const m=e.get(h);m&&(s.deleteBuffer(m.buffer),e.delete(h))}function f(h,m){if(h.isInterleavedBufferAttribute&&(h=h.data),h.isGLBufferAttribute){const g=e.get(h);(!g||g.version<h.version)&&e.set(h,{buffer:h.buffer,type:h.type,bytesPerElement:h.elementSize,version:h.version});return}const p=e.get(h);if(p===void 0)e.set(h,i(h,m));else if(p.version<h.version){if(p.size!==h.array.byteLength)throw new Error("THREE.WebGLAttributes: The size of the buffer attribute's array buffer does not match the original size. Resizing buffer attributes is not supported.");r(p.buffer,h,m),p.version=h.version}}return{get:l,remove:c,update:f}}var LE=`#ifdef USE_ALPHAHASH
	if ( diffuseColor.a < getAlphaHashThreshold( vPosition ) ) discard;
#endif`,OE=`#ifdef USE_ALPHAHASH
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
#endif`,PE=`#ifdef USE_ALPHAMAP
	diffuseColor.a *= texture2D( alphaMap, vAlphaMapUv ).g;
#endif`,IE=`#ifdef USE_ALPHAMAP
	uniform sampler2D alphaMap;
#endif`,FE=`#ifdef USE_ALPHATEST
	#ifdef ALPHA_TO_COVERAGE
	diffuseColor.a = smoothstep( alphaTest, alphaTest + fwidth( diffuseColor.a ), diffuseColor.a );
	if ( diffuseColor.a == 0.0 ) discard;
	#else
	if ( diffuseColor.a < alphaTest ) discard;
	#endif
#endif`,zE=`#ifdef USE_ALPHATEST
	uniform float alphaTest;
#endif`,BE=`#ifdef USE_AOMAP
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
#endif`,HE=`#ifdef USE_AOMAP
	uniform sampler2D aoMap;
	uniform float aoMapIntensity;
#endif`,GE=`#ifdef USE_BATCHING
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
#endif`,VE=`#ifdef USE_BATCHING
	mat4 batchingMatrix = getBatchingMatrix( getIndirectIndex( gl_DrawID ) );
#endif`,kE=`vec3 transformed = vec3( position );
#ifdef USE_ALPHAHASH
	vPosition = vec3( position );
#endif`,XE=`vec3 objectNormal = vec3( normal );
#ifdef USE_TANGENT
	vec3 objectTangent = vec3( tangent.xyz );
#endif`,WE=`float G_BlinnPhong_Implicit( ) {
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
} // validated`,qE=`#ifdef USE_IRIDESCENCE
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
#endif`,YE=`#ifdef USE_BUMPMAP
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
#endif`,jE=`#if NUM_CLIPPING_PLANES > 0
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
#endif`,ZE=`#if NUM_CLIPPING_PLANES > 0
	varying vec3 vClipPosition;
	uniform vec4 clippingPlanes[ NUM_CLIPPING_PLANES ];
#endif`,KE=`#if NUM_CLIPPING_PLANES > 0
	varying vec3 vClipPosition;
#endif`,QE=`#if NUM_CLIPPING_PLANES > 0
	vClipPosition = - mvPosition.xyz;
#endif`,JE=`#if defined( USE_COLOR ) || defined( USE_COLOR_ALPHA )
	diffuseColor *= vColor;
#endif`,$E=`#if defined( USE_COLOR ) || defined( USE_COLOR_ALPHA )
	varying vec4 vColor;
#endif`,e1=`#if defined( USE_COLOR ) || defined( USE_COLOR_ALPHA ) || defined( USE_INSTANCING_COLOR ) || defined( USE_BATCHING_COLOR )
	varying vec4 vColor;
#endif`,t1=`#if defined( USE_COLOR ) || defined( USE_COLOR_ALPHA ) || defined( USE_INSTANCING_COLOR ) || defined( USE_BATCHING_COLOR )
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
#endif`,n1=`#define PI 3.141592653589793
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
} // validated`,i1=`#ifdef ENVMAP_TYPE_CUBE_UV
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
#endif`,a1=`vec3 transformedNormal = objectNormal;
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
#endif`,r1=`#ifdef USE_DISPLACEMENTMAP
	uniform sampler2D displacementMap;
	uniform float displacementScale;
	uniform float displacementBias;
#endif`,s1=`#ifdef USE_DISPLACEMENTMAP
	transformed += normalize( objectNormal ) * ( texture2D( displacementMap, vDisplacementMapUv ).x * displacementScale + displacementBias );
#endif`,o1=`#ifdef USE_EMISSIVEMAP
	vec4 emissiveColor = texture2D( emissiveMap, vEmissiveMapUv );
	#ifdef DECODE_VIDEO_TEXTURE_EMISSIVE
		emissiveColor = sRGBTransferEOTF( emissiveColor );
	#endif
	totalEmissiveRadiance *= emissiveColor.rgb;
#endif`,l1=`#ifdef USE_EMISSIVEMAP
	uniform sampler2D emissiveMap;
#endif`,c1="gl_FragColor = linearToOutputTexel( gl_FragColor );",u1=`vec4 LinearTransferOETF( in vec4 value ) {
	return value;
}
vec4 sRGBTransferEOTF( in vec4 value ) {
	return vec4( mix( pow( value.rgb * 0.9478672986 + vec3( 0.0521327014 ), vec3( 2.4 ) ), value.rgb * 0.0773993808, vec3( lessThanEqual( value.rgb, vec3( 0.04045 ) ) ) ), value.a );
}
vec4 sRGBTransferOETF( in vec4 value ) {
	return vec4( mix( pow( value.rgb, vec3( 0.41666 ) ) * 1.055 - vec3( 0.055 ), value.rgb * 12.92, vec3( lessThanEqual( value.rgb, vec3( 0.0031308 ) ) ) ), value.a );
}`,f1=`#ifdef USE_ENVMAP
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
#endif`,d1=`#ifdef USE_ENVMAP
	uniform float envMapIntensity;
	uniform mat3 envMapRotation;
	#ifdef ENVMAP_TYPE_CUBE
		uniform samplerCube envMap;
	#else
		uniform sampler2D envMap;
	#endif
#endif`,h1=`#ifdef USE_ENVMAP
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
#endif`,p1=`#ifdef USE_ENVMAP
	#if defined( USE_BUMPMAP ) || defined( USE_NORMALMAP ) || defined( PHONG ) || defined( LAMBERT )
		#define ENV_WORLDPOS
	#endif
	#ifdef ENV_WORLDPOS
		
		varying vec3 vWorldPosition;
	#else
		varying vec3 vReflect;
		uniform float refractionRatio;
	#endif
#endif`,m1=`#ifdef USE_ENVMAP
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
#endif`,g1=`#ifdef USE_FOG
	vFogDepth = - mvPosition.z;
#endif`,v1=`#ifdef USE_FOG
	varying float vFogDepth;
#endif`,_1=`#ifdef USE_FOG
	#ifdef FOG_EXP2
		float fogFactor = 1.0 - exp( - fogDensity * fogDensity * vFogDepth * vFogDepth );
	#else
		float fogFactor = smoothstep( fogNear, fogFar, vFogDepth );
	#endif
	gl_FragColor.rgb = mix( gl_FragColor.rgb, fogColor, fogFactor );
#endif`,x1=`#ifdef USE_FOG
	uniform vec3 fogColor;
	varying float vFogDepth;
	#ifdef FOG_EXP2
		uniform float fogDensity;
	#else
		uniform float fogNear;
		uniform float fogFar;
	#endif
#endif`,S1=`#ifdef USE_GRADIENTMAP
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
}`,y1=`#ifdef USE_LIGHTMAP
	uniform sampler2D lightMap;
	uniform float lightMapIntensity;
#endif`,M1=`LambertMaterial material;
material.diffuseColor = diffuseColor.rgb;
material.specularStrength = specularStrength;`,b1=`varying vec3 vViewPosition;
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
#define RE_IndirectDiffuse		RE_IndirectDiffuse_Lambert`,E1=`uniform bool receiveShadow;
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
#include <lightprobes_pars_fragment>`,T1=`#ifdef USE_ENVMAP
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
#endif`,A1=`ToonMaterial material;
material.diffuseColor = diffuseColor.rgb;`,R1=`varying vec3 vViewPosition;
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
#define RE_IndirectDiffuse		RE_IndirectDiffuse_Toon`,C1=`BlinnPhongMaterial material;
material.diffuseColor = diffuseColor.rgb;
material.specularColor = specular;
material.specularShininess = shininess;
material.specularStrength = specularStrength;`,w1=`varying vec3 vViewPosition;
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
#define RE_IndirectDiffuse		RE_IndirectDiffuse_BlinnPhong`,D1=`PhysicalMaterial material;
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
#endif`,U1=`uniform sampler2D dfgLUT;
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
}`,N1=`
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
#endif`,L1=`#if defined( RE_IndirectDiffuse )
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
#endif`,O1=`#if defined( RE_IndirectDiffuse )
	#if defined( LAMBERT ) || defined( PHONG )
		irradiance += iblIrradiance;
	#endif
	RE_IndirectDiffuse( irradiance, geometryPosition, geometryNormal, geometryViewDir, geometryClearcoatNormal, material, reflectedLight );
#endif
#if defined( RE_IndirectSpecular )
	RE_IndirectSpecular( radiance, iblIrradiance, clearcoatRadiance, geometryPosition, geometryNormal, geometryViewDir, geometryClearcoatNormal, material, reflectedLight );
#endif`,P1=`#ifdef USE_LIGHT_PROBES_GRID
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
#endif`,I1=`#if defined( USE_LOGARITHMIC_DEPTH_BUFFER )
	gl_FragDepth = vIsPerspective == 0.0 ? gl_FragCoord.z : log2( vFragDepth ) * logDepthBufFC * 0.5;
#endif`,F1=`#if defined( USE_LOGARITHMIC_DEPTH_BUFFER )
	uniform float logDepthBufFC;
	varying float vFragDepth;
	varying float vIsPerspective;
#endif`,z1=`#ifdef USE_LOGARITHMIC_DEPTH_BUFFER
	varying float vFragDepth;
	varying float vIsPerspective;
#endif`,B1=`#ifdef USE_LOGARITHMIC_DEPTH_BUFFER
	vFragDepth = 1.0 + gl_Position.w;
	vIsPerspective = float( isPerspectiveMatrix( projectionMatrix ) );
#endif`,H1=`#ifdef USE_MAP
	vec4 sampledDiffuseColor = texture2D( map, vMapUv );
	#ifdef DECODE_VIDEO_TEXTURE
		sampledDiffuseColor = sRGBTransferEOTF( sampledDiffuseColor );
	#endif
	diffuseColor *= sampledDiffuseColor;
#endif`,G1=`#ifdef USE_MAP
	uniform sampler2D map;
#endif`,V1=`#if defined( USE_MAP ) || defined( USE_ALPHAMAP )
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
#endif`,k1=`#if defined( USE_POINTS_UV )
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
#endif`,X1=`float metalnessFactor = metalness;
#ifdef USE_METALNESSMAP
	vec4 texelMetalness = texture2D( metalnessMap, vMetalnessMapUv );
	metalnessFactor *= texelMetalness.b;
#endif`,W1=`#ifdef USE_METALNESSMAP
	uniform sampler2D metalnessMap;
#endif`,q1=`#ifdef USE_INSTANCING_MORPH
	float morphTargetInfluences[ MORPHTARGETS_COUNT ];
	float morphTargetBaseInfluence = texelFetch( morphTexture, ivec2( 0, gl_InstanceID ), 0 ).r;
	for ( int i = 0; i < MORPHTARGETS_COUNT; i ++ ) {
		morphTargetInfluences[i] =  texelFetch( morphTexture, ivec2( i + 1, gl_InstanceID ), 0 ).r;
	}
#endif`,Y1=`#if defined( USE_MORPHCOLORS )
	vColor *= morphTargetBaseInfluence;
	for ( int i = 0; i < MORPHTARGETS_COUNT; i ++ ) {
		#if defined( USE_COLOR_ALPHA )
			if ( morphTargetInfluences[ i ] != 0.0 ) vColor += getMorph( gl_VertexID, i, 2 ) * morphTargetInfluences[ i ];
		#elif defined( USE_COLOR )
			if ( morphTargetInfluences[ i ] != 0.0 ) vColor += getMorph( gl_VertexID, i, 2 ).rgb * morphTargetInfluences[ i ];
		#endif
	}
#endif`,j1=`#ifdef USE_MORPHNORMALS
	objectNormal *= morphTargetBaseInfluence;
	for ( int i = 0; i < MORPHTARGETS_COUNT; i ++ ) {
		if ( morphTargetInfluences[ i ] != 0.0 ) objectNormal += getMorph( gl_VertexID, i, 1 ).xyz * morphTargetInfluences[ i ];
	}
#endif`,Z1=`#ifdef USE_MORPHTARGETS
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
#endif`,K1=`#ifdef USE_MORPHTARGETS
	transformed *= morphTargetBaseInfluence;
	for ( int i = 0; i < MORPHTARGETS_COUNT; i ++ ) {
		if ( morphTargetInfluences[ i ] != 0.0 ) transformed += getMorph( gl_VertexID, i, 0 ).xyz * morphTargetInfluences[ i ];
	}
#endif`,Q1=`float faceDirection = gl_FrontFacing ? 1.0 : - 1.0;
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
vec3 nonPerturbedNormal = normal;`,J1=`#ifdef USE_NORMALMAP_OBJECTSPACE
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
#endif`,$1=`#ifndef FLAT_SHADED
	varying vec3 vNormal;
	#ifdef USE_TANGENT
		varying vec3 vTangent;
		varying vec3 vBitangent;
	#endif
#endif`,eT=`#ifndef FLAT_SHADED
	varying vec3 vNormal;
	#ifdef USE_TANGENT
		varying vec3 vTangent;
		varying vec3 vBitangent;
	#endif
#endif`,tT=`#ifndef FLAT_SHADED
	vNormal = normalize( transformedNormal );
	#ifdef USE_TANGENT
		vTangent = normalize( transformedTangent );
		vBitangent = normalize( cross( vNormal, vTangent ) * tangent.w );
		#ifdef FLIP_SIDED
			vBitangent = - vBitangent;
		#endif
	#endif
#endif`,nT=`#ifdef USE_NORMALMAP
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
#endif`,iT=`#ifdef USE_CLEARCOAT
	vec3 clearcoatNormal = nonPerturbedNormal;
#endif`,aT=`#ifdef USE_CLEARCOAT_NORMALMAP
	vec3 clearcoatMapN = texture2D( clearcoatNormalMap, vClearcoatNormalMapUv ).xyz * 2.0 - 1.0;
	clearcoatMapN.xy *= clearcoatNormalScale;
	clearcoatNormal = normalize( tbn2 * clearcoatMapN );
#endif`,rT=`#ifdef USE_CLEARCOATMAP
	uniform sampler2D clearcoatMap;
#endif
#ifdef USE_CLEARCOAT_NORMALMAP
	uniform sampler2D clearcoatNormalMap;
	uniform vec2 clearcoatNormalScale;
#endif
#ifdef USE_CLEARCOAT_ROUGHNESSMAP
	uniform sampler2D clearcoatRoughnessMap;
#endif`,sT=`#ifdef USE_IRIDESCENCEMAP
	uniform sampler2D iridescenceMap;
#endif
#ifdef USE_IRIDESCENCE_THICKNESSMAP
	uniform sampler2D iridescenceThicknessMap;
#endif`,oT=`#ifdef OPAQUE
diffuseColor.a = 1.0;
#endif
#ifdef USE_TRANSMISSION
diffuseColor.a *= material.transmissionAlpha;
#endif
gl_FragColor = vec4( outgoingLight, diffuseColor.a );`,lT=`vec3 packNormalToRGB( const in vec3 normal ) {
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
}`,cT=`#ifdef PREMULTIPLIED_ALPHA
	gl_FragColor.rgb *= gl_FragColor.a;
#endif`,uT=`vec4 mvPosition = vec4( transformed, 1.0 );
#ifdef USE_BATCHING
	mvPosition = batchingMatrix * mvPosition;
#endif
#ifdef USE_INSTANCING
	mvPosition = instanceMatrix * mvPosition;
#endif
mvPosition = modelViewMatrix * mvPosition;
gl_Position = projectionMatrix * mvPosition;`,fT=`#ifdef DITHERING
	gl_FragColor.rgb = dithering( gl_FragColor.rgb );
#endif`,dT=`#ifdef DITHERING
	vec3 dithering( vec3 color ) {
		float grid_position = rand( gl_FragCoord.xy );
		vec3 dither_shift_RGB = vec3( 0.25 / 255.0, -0.25 / 255.0, 0.25 / 255.0 );
		dither_shift_RGB = mix( 2.0 * dither_shift_RGB, -2.0 * dither_shift_RGB, grid_position );
		return color + dither_shift_RGB;
	}
#endif`,hT=`float roughnessFactor = roughness;
#ifdef USE_ROUGHNESSMAP
	vec4 texelRoughness = texture2D( roughnessMap, vRoughnessMapUv );
	roughnessFactor *= texelRoughness.g;
#endif`,pT=`#ifdef USE_ROUGHNESSMAP
	uniform sampler2D roughnessMap;
#endif`,mT=`#if NUM_SPOT_LIGHT_COORDS > 0
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
#endif`,gT=`#if NUM_SPOT_LIGHT_COORDS > 0
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
#endif`,vT=`#if ( defined( USE_SHADOWMAP ) && ( NUM_DIR_LIGHT_SHADOWS > 0 || NUM_SUN_LIGHT_SHADOWS > 0 || NUM_POINT_LIGHT_SHADOWS > 0 ) ) || ( NUM_SPOT_LIGHT_COORDS > 0 )
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
#endif`,_T=`float getShadowMask() {
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
#endif`,ST=`#ifdef USE_SKINNING
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
#endif`,yT=`#ifdef USE_SKINNING
	vec4 skinVertex = bindMatrix * vec4( transformed, 1.0 );
	vec4 skinned = vec4( 0.0 );
	skinned += boneMatX * skinVertex * skinWeight.x;
	skinned += boneMatY * skinVertex * skinWeight.y;
	skinned += boneMatZ * skinVertex * skinWeight.z;
	skinned += boneMatW * skinVertex * skinWeight.w;
	transformed = ( bindMatrixInverse * skinned ).xyz;
#endif`,MT=`#ifdef USE_SKINNING
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
#endif`,bT=`float specularStrength;
#ifdef USE_SPECULARMAP
	vec4 texelSpecular = texture2D( specularMap, vSpecularMapUv );
	specularStrength = texelSpecular.r;
#else
	specularStrength = 1.0;
#endif`,ET=`#ifdef USE_SPECULARMAP
	uniform sampler2D specularMap;
#endif`,TT=`#if defined( TONE_MAPPING )
	gl_FragColor.rgb = toneMapping( gl_FragColor.rgb );
#endif`,AT=`#ifndef saturate
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
vec3 CustomToneMapping( vec3 color ) { return color; }`,RT=`#ifdef USE_TRANSMISSION
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
#endif`,CT=`#ifdef USE_TRANSMISSION
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
#endif`,DT=`#if defined( USE_UV ) || defined( USE_ANISOTROPY )
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
#endif`,UT=`#if defined( USE_UV ) || defined( USE_ANISOTROPY )
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
#endif`,NT=`#if defined( USE_ENVMAP ) || defined( DISTANCE ) || defined ( USE_SHADOWMAP ) || defined ( USE_TRANSMISSION ) || NUM_SPOT_LIGHT_COORDS > 0
	vec4 worldPosition = vec4( transformed, 1.0 );
	#ifdef USE_BATCHING
		worldPosition = batchingMatrix * worldPosition;
	#endif
	#ifdef USE_INSTANCING
		worldPosition = instanceMatrix * worldPosition;
	#endif
	worldPosition = modelMatrix * worldPosition;
#endif`;const LT=`varying vec2 vUv;
uniform mat3 uvTransform;
void main() {
	vUv = ( uvTransform * vec3( uv, 1 ) ).xy;
	gl_Position = vec4( position.xy, 1.0, 1.0 );
}`,OT=`uniform sampler2D t2D;
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
}`,PT=`varying vec3 vWorldDirection;
#include <common>
void main() {
	vWorldDirection = transformDirection( position, modelMatrix );
	#include <begin_vertex>
	#include <project_vertex>
	gl_Position.z = gl_Position.w;
}`,IT=`#ifdef ENVMAP_TYPE_CUBE
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
}`,FT=`varying vec3 vWorldDirection;
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
}`,BT=`#include <common>
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
}`,HT=`#if DEPTH_PACKING == 3200
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
}`,GT=`#define DISTANCE
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
}`,VT=`#define DISTANCE
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
}`,kT=`varying vec3 vWorldDirection;
#include <common>
void main() {
	vWorldDirection = transformDirection( position, modelMatrix );
	#include <begin_vertex>
	#include <project_vertex>
}`,XT=`uniform sampler2D tEquirect;
varying vec3 vWorldDirection;
#include <common>
void main() {
	vec3 direction = normalize( vWorldDirection );
	vec2 sampleUV = equirectUv( direction );
	gl_FragColor = texture2D( tEquirect, sampleUV );
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
}`,WT=`uniform float scale;
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
}`,qT=`uniform vec3 diffuse;
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
}`,YT=`#include <common>
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
}`,jT=`uniform vec3 diffuse;
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
}`,ZT=`#define LAMBERT
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
}`,KT=`#define LAMBERT
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
}`,QT=`#define MATCAP
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
}`,JT=`#define MATCAP
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
}`,$T=`#define NORMAL
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
}`,eA=`#define NORMAL
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
}`,tA=`#define PHONG
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
}`,nA=`#define PHONG
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
}`,iA=`#define STANDARD
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
}`,aA=`#define STANDARD
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
}`,rA=`#define TOON
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
}`,sA=`#define TOON
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
}`,oA=`uniform float size;
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
}`,lA=`uniform vec3 diffuse;
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
}`,cA=`#include <common>
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
}`,uA=`uniform vec3 color;
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
}`,fA=`uniform float rotation;
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
}`,dA=`uniform vec3 diffuse;
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
}`,wt={alphahash_fragment:LE,alphahash_pars_fragment:OE,alphamap_fragment:PE,alphamap_pars_fragment:IE,alphatest_fragment:FE,alphatest_pars_fragment:zE,aomap_fragment:BE,aomap_pars_fragment:HE,batching_pars_vertex:GE,batching_vertex:VE,begin_vertex:kE,beginnormal_vertex:XE,bsdfs:WE,iridescence_fragment:qE,bumpmap_pars_fragment:YE,clipping_planes_fragment:jE,clipping_planes_pars_fragment:ZE,clipping_planes_pars_vertex:KE,clipping_planes_vertex:QE,color_fragment:JE,color_pars_fragment:$E,color_pars_vertex:e1,color_vertex:t1,common:n1,cube_uv_reflection_fragment:i1,defaultnormal_vertex:a1,displacementmap_pars_vertex:r1,displacementmap_vertex:s1,emissivemap_fragment:o1,emissivemap_pars_fragment:l1,colorspace_fragment:c1,colorspace_pars_fragment:u1,envmap_fragment:f1,envmap_common_pars_fragment:d1,envmap_pars_fragment:h1,envmap_pars_vertex:p1,envmap_physical_pars_fragment:T1,envmap_vertex:m1,fog_vertex:g1,fog_pars_vertex:v1,fog_fragment:_1,fog_pars_fragment:x1,gradientmap_pars_fragment:S1,lightmap_pars_fragment:y1,lights_lambert_fragment:M1,lights_lambert_pars_fragment:b1,lights_pars_begin:E1,lights_toon_fragment:A1,lights_toon_pars_fragment:R1,lights_phong_fragment:C1,lights_phong_pars_fragment:w1,lights_physical_fragment:D1,lights_physical_pars_fragment:U1,lights_fragment_begin:N1,lights_fragment_maps:L1,lights_fragment_end:O1,lightprobes_pars_fragment:P1,logdepthbuf_fragment:I1,logdepthbuf_pars_fragment:F1,logdepthbuf_pars_vertex:z1,logdepthbuf_vertex:B1,map_fragment:H1,map_pars_fragment:G1,map_particle_fragment:V1,map_particle_pars_fragment:k1,metalnessmap_fragment:X1,metalnessmap_pars_fragment:W1,morphinstance_vertex:q1,morphcolor_vertex:Y1,morphnormal_vertex:j1,morphtarget_pars_vertex:Z1,morphtarget_vertex:K1,normal_fragment_begin:Q1,normal_fragment_maps:J1,normal_pars_fragment:$1,normal_pars_vertex:eT,normal_vertex:tT,normalmap_pars_fragment:nT,clearcoat_normal_fragment_begin:iT,clearcoat_normal_fragment_maps:aT,clearcoat_pars_fragment:rT,iridescence_pars_fragment:sT,opaque_fragment:oT,packing:lT,premultiplied_alpha_fragment:cT,project_vertex:uT,dithering_fragment:fT,dithering_pars_fragment:dT,roughnessmap_fragment:hT,roughnessmap_pars_fragment:pT,shadowmap_pars_fragment:mT,shadowmap_pars_vertex:gT,shadowmap_vertex:vT,shadowmask_pars_fragment:_T,skinbase_vertex:xT,skinning_pars_vertex:ST,skinning_vertex:yT,skinnormal_vertex:MT,specularmap_fragment:bT,specularmap_pars_fragment:ET,tonemapping_fragment:TT,tonemapping_pars_fragment:AT,transmission_fragment:RT,transmission_pars_fragment:CT,uv_pars_fragment:wT,uv_pars_vertex:DT,uv_vertex:UT,worldpos_vertex:NT,background_vert:LT,background_frag:OT,backgroundCube_vert:PT,backgroundCube_frag:IT,cube_vert:FT,cube_frag:zT,depth_vert:BT,depth_frag:HT,distance_vert:GT,distance_frag:VT,equirect_vert:kT,equirect_frag:XT,linedashed_vert:WT,linedashed_frag:qT,meshbasic_vert:YT,meshbasic_frag:jT,meshlambert_vert:ZT,meshlambert_frag:KT,meshmatcap_vert:QT,meshmatcap_frag:JT,meshnormal_vert:$T,meshnormal_frag:eA,meshphong_vert:tA,meshphong_frag:nA,meshphysical_vert:iA,meshphysical_frag:aA,meshtoon_vert:rA,meshtoon_frag:sA,points_vert:oA,points_frag:lA,shadow_vert:cA,shadow_frag:uA,sprite_vert:fA,sprite_frag:dA},je={common:{diffuse:{value:new Rt(16777215)},opacity:{value:1},map:{value:null},mapTransform:{value:new yt},alphaMap:{value:null},alphaMapTransform:{value:new yt},alphaTest:{value:0}},specularmap:{specularMap:{value:null},specularMapTransform:{value:new yt}},envmap:{envMap:{value:null},envMapRotation:{value:new yt},reflectivity:{value:1},ior:{value:1.5},refractionRatio:{value:.98},dfgLUT:{value:null}},aomap:{aoMap:{value:null},aoMapIntensity:{value:1},aoMapTransform:{value:new yt}},lightmap:{lightMap:{value:null},lightMapIntensity:{value:1},lightMapTransform:{value:new yt}},bumpmap:{bumpMap:{value:null},bumpMapTransform:{value:new yt},bumpScale:{value:1}},normalmap:{normalMap:{value:null},normalMapTransform:{value:new yt},normalScale:{value:new Kt(1,1)}},displacementmap:{displacementMap:{value:null},displacementMapTransform:{value:new yt},displacementScale:{value:1},displacementBias:{value:0}},emissivemap:{emissiveMap:{value:null},emissiveMapTransform:{value:new yt}},metalnessmap:{metalnessMap:{value:null},metalnessMapTransform:{value:new yt}},roughnessmap:{roughnessMap:{value:null},roughnessMapTransform:{value:new yt}},gradientmap:{gradientMap:{value:null}},fog:{fogDensity:{value:25e-5},fogNear:{value:1},fogFar:{value:2e3},fogColor:{value:new Rt(16777215)}},lights:{ambientLightColor:{value:[]},lightProbe:{value:[]},sunLights:{value:[],properties:{direction:{},color:{}}},sunLightShadows:{value:[],properties:{shadowIntensity:1,shadowBias:{},shadowNormalBias:{},shadowRadius:{},shadowMapSize:{}}},sunShadowMatrix:{value:[]},sunShadowCascade:{value:[]},directionalLights:{value:[],properties:{direction:{},color:{}}},directionalLightShadows:{value:[],properties:{shadowIntensity:1,shadowBias:{},shadowNormalBias:{},shadowRadius:{},shadowMapSize:{}}},directionalShadowMatrix:{value:[]},spotLights:{value:[],properties:{color:{},position:{},direction:{},distance:{},coneCos:{},penumbraCos:{},decay:{}}},spotLightShadows:{value:[],properties:{shadowIntensity:1,shadowBias:{},shadowNormalBias:{},shadowRadius:{},shadowMapSize:{}}},spotLightMap:{value:[]},spotLightMatrix:{value:[]},pointLights:{value:[],properties:{color:{},position:{},decay:{},distance:{}}},pointLightShadows:{value:[],properties:{shadowIntensity:1,shadowBias:{},shadowNormalBias:{},shadowRadius:{},shadowMapSize:{},shadowCameraNear:{},shadowCameraFar:{}}},pointShadowMatrix:{value:[]},hemisphereLights:{value:[],properties:{direction:{},skyColor:{},groundColor:{}}},rectAreaLights:{value:[],properties:{color:{},position:{},width:{},height:{}}},ltc_1:{value:null},ltc_2:{value:null},probesSH:{value:null},probesMin:{value:new Q},probesMax:{value:new Q},probesResolution:{value:new Q}},points:{diffuse:{value:new Rt(16777215)},opacity:{value:1},size:{value:1},scale:{value:1},map:{value:null},alphaMap:{value:null},alphaMapTransform:{value:new yt},alphaTest:{value:0},uvTransform:{value:new yt}},sprite:{diffuse:{value:new Rt(16777215)},opacity:{value:1},center:{value:new Kt(.5,.5)},rotation:{value:0},map:{value:null},mapTransform:{value:new yt},alphaMap:{value:null},alphaMapTransform:{value:new yt},alphaTest:{value:0}}},Ga={basic:{uniforms:bi([je.common,je.specularmap,je.envmap,je.aomap,je.lightmap,je.fog]),vertexShader:wt.meshbasic_vert,fragmentShader:wt.meshbasic_frag},lambert:{uniforms:bi([je.common,je.specularmap,je.envmap,je.aomap,je.lightmap,je.emissivemap,je.bumpmap,je.normalmap,je.displacementmap,je.fog,je.lights,{emissive:{value:new Rt(0)},envMapIntensity:{value:1}}]),vertexShader:wt.meshlambert_vert,fragmentShader:wt.meshlambert_frag},phong:{uniforms:bi([je.common,je.specularmap,je.envmap,je.aomap,je.lightmap,je.emissivemap,je.bumpmap,je.normalmap,je.displacementmap,je.fog,je.lights,{emissive:{value:new Rt(0)},specular:{value:new Rt(1118481)},shininess:{value:30},envMapIntensity:{value:1}}]),vertexShader:wt.meshphong_vert,fragmentShader:wt.meshphong_frag},standard:{uniforms:bi([je.common,je.envmap,je.aomap,je.lightmap,je.emissivemap,je.bumpmap,je.normalmap,je.displacementmap,je.roughnessmap,je.metalnessmap,je.fog,je.lights,{emissive:{value:new Rt(0)},roughness:{value:1},metalness:{value:0},envMapIntensity:{value:1}}]),vertexShader:wt.meshphysical_vert,fragmentShader:wt.meshphysical_frag},toon:{uniforms:bi([je.common,je.aomap,je.lightmap,je.emissivemap,je.bumpmap,je.normalmap,je.displacementmap,je.gradientmap,je.fog,je.lights,{emissive:{value:new Rt(0)}}]),vertexShader:wt.meshtoon_vert,fragmentShader:wt.meshtoon_frag},matcap:{uniforms:bi([je.common,je.bumpmap,je.normalmap,je.displacementmap,je.fog,{matcap:{value:null}}]),vertexShader:wt.meshmatcap_vert,fragmentShader:wt.meshmatcap_frag},points:{uniforms:bi([je.points,je.fog]),vertexShader:wt.points_vert,fragmentShader:wt.points_frag},dashed:{uniforms:bi([je.common,je.fog,{scale:{value:1},dashSize:{value:1},totalSize:{value:2}}]),vertexShader:wt.linedashed_vert,fragmentShader:wt.linedashed_frag},depth:{uniforms:bi([je.common,je.displacementmap]),vertexShader:wt.depth_vert,fragmentShader:wt.depth_frag},normal:{uniforms:bi([je.common,je.bumpmap,je.normalmap,je.displacementmap,{opacity:{value:1}}]),vertexShader:wt.meshnormal_vert,fragmentShader:wt.meshnormal_frag},sprite:{uniforms:bi([je.sprite,je.fog]),vertexShader:wt.sprite_vert,fragmentShader:wt.sprite_frag},background:{uniforms:{uvTransform:{value:new yt},t2D:{value:null},backgroundIntensity:{value:1}},vertexShader:wt.background_vert,fragmentShader:wt.background_frag},backgroundCube:{uniforms:{envMap:{value:null},backgroundBlurriness:{value:0},backgroundIntensity:{value:1},backgroundRotation:{value:new yt}},vertexShader:wt.backgroundCube_vert,fragmentShader:wt.backgroundCube_frag},cube:{uniforms:{tCube:{value:null},tFlip:{value:-1},opacity:{value:1}},vertexShader:wt.cube_vert,fragmentShader:wt.cube_frag},equirect:{uniforms:{tEquirect:{value:null}},vertexShader:wt.equirect_vert,fragmentShader:wt.equirect_frag},distance:{uniforms:bi([je.common,je.displacementmap,{referencePosition:{value:new Q},nearDistance:{value:1},farDistance:{value:1e3}}]),vertexShader:wt.distance_vert,fragmentShader:wt.distance_frag},shadow:{uniforms:bi([je.lights,je.fog,{color:{value:new Rt(0)},opacity:{value:1}}]),vertexShader:wt.shadow_vert,fragmentShader:wt.shadow_frag}};Ga.physical={uniforms:bi([Ga.standard.uniforms,{clearcoat:{value:0},clearcoatMap:{value:null},clearcoatMapTransform:{value:new yt},clearcoatNormalMap:{value:null},clearcoatNormalMapTransform:{value:new yt},clearcoatNormalScale:{value:new Kt(1,1)},clearcoatRoughness:{value:0},clearcoatRoughnessMap:{value:null},clearcoatRoughnessMapTransform:{value:new yt},dispersion:{value:0},retroreflectivity:{value:0},iridescence:{value:0},iridescenceMap:{value:null},iridescenceMapTransform:{value:new yt},iridescenceIOR:{value:1.3},iridescenceThicknessMinimum:{value:100},iridescenceThicknessMaximum:{value:400},iridescenceThicknessMap:{value:null},iridescenceThicknessMapTransform:{value:new yt},sheen:{value:0},sheenColor:{value:new Rt(0)},sheenColorMap:{value:null},sheenColorMapTransform:{value:new yt},sheenRoughness:{value:1},sheenRoughnessMap:{value:null},sheenRoughnessMapTransform:{value:new yt},transmission:{value:0},transmissionMap:{value:null},transmissionMapTransform:{value:new yt},transmissionSamplerSize:{value:new Kt},transmissionSamplerMap:{value:null},thickness:{value:0},thicknessMap:{value:null},thicknessMapTransform:{value:new yt},attenuationDistance:{value:0},attenuationColor:{value:new Rt(0)},specularColor:{value:new Rt(1,1,1)},specularColorMap:{value:null},specularColorMapTransform:{value:new yt},specularIntensity:{value:1},specularIntensityMap:{value:null},specularIntensityMapTransform:{value:new yt},anisotropyVector:{value:new Kt},anisotropyMap:{value:null},anisotropyMapTransform:{value:new yt}}]),vertexShader:wt.meshphysical_vert,fragmentShader:wt.meshphysical_frag};const Cu={r:0,b:0,g:0},hA=new En,Vx=new yt;Vx.set(-1,0,0,0,1,0,0,0,1);function pA(s,e,i,r,l,c){const f=new Rt(0);let h=l===!0?0:1,m,p,g=null,_=0,v=null;function x(F){let V=F.isScene===!0?F.background:null;if(V&&V.isTexture){const R=F.backgroundBlurriness>0;V=e.get(V,R)}return V}function E(F){let V=!1;const R=x(F);R===null?M(f,h):R&&R.isColor&&(M(R,1),V=!0);const N=s.xr.getEnvironmentBlendMode();N==="additive"?i.buffers.color.setClear(0,0,0,1,c):N==="alpha-blend"&&i.buffers.color.setClear(0,0,0,0,c),(s.autoClear||V)&&(i.buffers.depth.setTest(!0),i.buffers.depth.setMask(!0),i.buffers.color.setMask(!0),s.clear(s.autoClearColor,s.autoClearDepth,s.autoClearStencil))}function D(F,V){const R=x(V);R&&(R.isCubeTexture||R.mapping===Zu)?(p===void 0&&(p=new Ki(new $l(1,1,1),new Yn({name:"BackgroundCubeMaterial",uniforms:Ho(Ga.backgroundCube.uniforms),vertexShader:Ga.backgroundCube.vertexShader,fragmentShader:Ga.backgroundCube.fragmentShader,side:Oi,depthTest:!1,depthWrite:!1,fog:!1,allowOverride:!1})),p.geometry.deleteAttribute("normal"),p.geometry.deleteAttribute("uv"),p.onBeforeRender=function(N,L,P){this.matrixWorld.copyPosition(P.matrixWorld)},Object.defineProperty(p.material,"envMap",{get:function(){return this.uniforms.envMap.value}}),r.update(p)),p.material.uniforms.envMap.value=R,p.material.uniforms.backgroundBlurriness.value=V.backgroundBlurriness,p.material.uniforms.backgroundIntensity.value=V.backgroundIntensity,p.material.uniforms.backgroundRotation.value.setFromMatrix4(hA.makeRotationFromEuler(V.backgroundRotation)).transpose(),R.isCubeTexture&&R.isRenderTargetTexture===!1&&p.material.uniforms.backgroundRotation.value.premultiply(Vx),p.material.toneMapped=kt.getTransfer(R.colorSpace)!==cn,(g!==R||_!==R.version||v!==s.toneMapping)&&(p.material.needsUpdate=!0,g=R,_=R.version,v=s.toneMapping),p.layers.enableAll(),F.unshift(p,p.geometry,p.material,0,0,null)):R&&R.isTexture&&(m===void 0&&(m=new Ki(new ec(2,2),new Yn({name:"BackgroundMaterial",uniforms:Ho(Ga.background.uniforms),vertexShader:Ga.background.vertexShader,fragmentShader:Ga.background.fragmentShader,side:Ns,depthTest:!1,depthWrite:!1,fog:!1,allowOverride:!1})),m.geometry.deleteAttribute("normal"),Object.defineProperty(m.material,"map",{get:function(){return this.uniforms.t2D.value}}),r.update(m)),m.material.uniforms.t2D.value=R,m.material.uniforms.backgroundIntensity.value=V.backgroundIntensity,m.material.toneMapped=kt.getTransfer(R.colorSpace)!==cn,R.matrixAutoUpdate===!0&&R.updateMatrix(),m.material.uniforms.uvTransform.value.copy(R.matrix),(g!==R||_!==R.version||v!==s.toneMapping)&&(m.material.needsUpdate=!0,g=R,_=R.version,v=s.toneMapping),m.layers.enableAll(),F.unshift(m,m.geometry,m.material,0,0,null))}function M(F,V){F.getRGB(Cu,zx(s)),i.buffers.color.setClear(Cu.r,Cu.g,Cu.b,V,c)}function y(){p!==void 0&&(p.geometry.dispose(),p.material.dispose(),p=void 0),m!==void 0&&(m.geometry.dispose(),m.material.dispose(),m=void 0)}return{getClearColor:function(){return f},setClearColor:function(F,V=1){f.set(F),h=V,M(f,h)},getClearAlpha:function(){return h},setClearAlpha:function(F){h=F,M(f,h)},render:E,addToRenderList:D,dispose:y}}function mA(s,e){const i=s.getParameter(s.MAX_VERTEX_ATTRIBS),r={},l=v(null);let c=l,f=!1;function h(k,J,se,Y,j){let z=!1;const H=_(k,Y,se,J);c!==H&&(c=H,p(c.object)),z=x(k,Y,se,j),z&&E(k,Y,se,j),j!==null&&e.update(j,s.ELEMENT_ARRAY_BUFFER),(z||f)&&(f=!1,R(k,J,se,Y),j!==null&&s.bindBuffer(s.ELEMENT_ARRAY_BUFFER,e.get(j).buffer))}function m(){return s.createVertexArray()}function p(k){return s.bindVertexArray(k)}function g(k){return s.deleteVertexArray(k)}function _(k,J,se,Y){const j=Y.wireframe===!0;let z=r[J.id];z===void 0&&(z={},r[J.id]=z);const H=k.isInstancedMesh===!0?k.id:0;let ee=z[H];ee===void 0&&(ee={},z[H]=ee);let oe=ee[se.id];oe===void 0&&(oe={},ee[se.id]=oe);let fe=oe[j];return fe===void 0&&(fe=v(m()),oe[j]=fe),fe}function v(k){const J=[],se=[],Y=[];for(let j=0;j<i;j++)J[j]=0,se[j]=0,Y[j]=0;return{geometry:null,program:null,wireframe:!1,newAttributes:J,enabledAttributes:se,attributeDivisors:Y,object:k,attributes:{},index:null}}function x(k,J,se,Y){const j=c.attributes,z=J.attributes;let H=0;const ee=se.getAttributes();for(const oe in ee)if(ee[oe].location>=0){const U=j[oe];let re=z[oe];if(re===void 0&&(oe==="instanceMatrix"&&k.instanceMatrix&&(re=k.instanceMatrix),oe==="instanceColor"&&k.instanceColor&&(re=k.instanceColor)),U===void 0||U.attribute!==re||re&&U.data!==re.data)return!0;H++}return c.attributesNum!==H||c.index!==Y}function E(k,J,se,Y){const j={},z=J.attributes;let H=0;const ee=se.getAttributes();for(const oe in ee)if(ee[oe].location>=0){let U=z[oe];U===void 0&&(oe==="instanceMatrix"&&k.instanceMatrix&&(U=k.instanceMatrix),oe==="instanceColor"&&k.instanceColor&&(U=k.instanceColor));const re={};re.attribute=U,U&&U.data&&(re.data=U.data),j[oe]=re,H++}c.attributes=j,c.attributesNum=H,c.index=Y}function D(){const k=c.newAttributes;for(let J=0,se=k.length;J<se;J++)k[J]=0}function M(k){y(k,0)}function y(k,J){const se=c.newAttributes,Y=c.enabledAttributes,j=c.attributeDivisors;se[k]=1,Y[k]===0&&(s.enableVertexAttribArray(k),Y[k]=1),j[k]!==J&&(s.vertexAttribDivisor(k,J),j[k]=J)}function F(){const k=c.newAttributes,J=c.enabledAttributes;for(let se=0,Y=J.length;se<Y;se++)J[se]!==k[se]&&(s.disableVertexAttribArray(se),J[se]=0)}function V(k,J,se,Y,j,z,H){H===!0?s.vertexAttribIPointer(k,J,se,j,z):s.vertexAttribPointer(k,J,se,Y,j,z)}function R(k,J,se,Y){D();const j=Y.attributes,z=se.getAttributes(),H=J.defaultAttributeValues;for(const ee in z){const oe=z[ee];if(oe.location>=0){let fe=j[ee];if(fe===void 0&&(ee==="instanceMatrix"&&k.instanceMatrix&&(fe=k.instanceMatrix),ee==="instanceColor"&&k.instanceColor&&(fe=k.instanceColor)),fe!==void 0){const U=fe.normalized,re=fe.itemSize,xe=e.get(fe);if(xe===void 0)continue;const Ue=xe.buffer,Ie=xe.type,Xe=xe.bytesPerElement,ue=Ie===s.INT||Ie===s.UNSIGNED_INT||fe.gpuType===Bp;if(fe.isInterleavedBufferAttribute){const ye=fe.data,we=ye.stride,at=fe.offset;if(ye.isInstancedInterleavedBuffer){for(let Ge=0;Ge<oe.locationSize;Ge++)y(oe.location+Ge,ye.meshPerAttribute);k.isInstancedMesh!==!0&&Y._maxInstanceCount===void 0&&(Y._maxInstanceCount=ye.meshPerAttribute*ye.count)}else for(let Ge=0;Ge<oe.locationSize;Ge++)M(oe.location+Ge);s.bindBuffer(s.ARRAY_BUFFER,Ue);for(let Ge=0;Ge<oe.locationSize;Ge++)V(oe.location+Ge,re/oe.locationSize,Ie,U,we*Xe,(at+re/oe.locationSize*Ge)*Xe,ue)}else{if(fe.isInstancedBufferAttribute){for(let ye=0;ye<oe.locationSize;ye++)y(oe.location+ye,fe.meshPerAttribute);k.isInstancedMesh!==!0&&Y._maxInstanceCount===void 0&&(Y._maxInstanceCount=fe.meshPerAttribute*fe.count)}else for(let ye=0;ye<oe.locationSize;ye++)M(oe.location+ye);s.bindBuffer(s.ARRAY_BUFFER,Ue);for(let ye=0;ye<oe.locationSize;ye++)V(oe.location+ye,re/oe.locationSize,Ie,U,re*Xe,re/oe.locationSize*ye*Xe,ue)}}else if(H!==void 0){const U=H[ee];if(U!==void 0)switch(U.length){case 2:s.vertexAttrib2fv(oe.location,U);break;case 3:s.vertexAttrib3fv(oe.location,U);break;case 4:s.vertexAttrib4fv(oe.location,U);break;default:s.vertexAttrib1fv(oe.location,U)}}}}F()}function N(){O();for(const k in r){const J=r[k];for(const se in J){const Y=J[se];for(const j in Y){const z=Y[j];for(const H in z)g(z[H].object),delete z[H];delete Y[j]}}delete r[k]}}function L(k){if(r[k.id]===void 0)return;const J=r[k.id];for(const se in J){const Y=J[se];for(const j in Y){const z=Y[j];for(const H in z)g(z[H].object),delete z[H];delete Y[j]}}delete r[k.id]}function P(k){for(const J in r){const se=r[J];for(const Y in se){const j=se[Y];if(j[k.id]===void 0)continue;const z=j[k.id];for(const H in z)g(z[H].object),delete z[H];delete j[k.id]}}}function T(k){for(const J in r){const se=r[J],Y=k.isInstancedMesh===!0?k.id:0,j=se[Y];if(j!==void 0){for(const z in j){const H=j[z];for(const ee in H)g(H[ee].object),delete H[ee];delete j[z]}delete se[Y],Object.keys(se).length===0&&delete r[J]}}}function O(){B(),f=!0,c!==l&&(c=l,p(c.object))}function B(){l.geometry=null,l.program=null,l.wireframe=!1}return{setup:h,reset:O,resetDefaultState:B,dispose:N,releaseStatesOfGeometry:L,releaseStatesOfObject:T,releaseStatesOfProgram:P,initAttributes:D,enableAttribute:M,disableUnusedAttributes:F}}function gA(s,e,i){let r;function l(m){r=m}function c(m,p){s.drawArrays(r,m,p),i.update(p,r,1)}function f(m,p,g){g!==0&&(s.drawArraysInstanced(r,m,p,g),i.update(p,r,g))}function h(m,p,g){if(g===0)return;e.get("WEBGL_multi_draw").multiDrawArraysWEBGL(r,m,0,p,0,g);let v=0;for(let x=0;x<g;x++)v+=p[x];i.update(v,r,1)}this.setMode=l,this.render=c,this.renderInstances=f,this.renderMultiDraw=h}function vA(s,e,i,r){let l;function c(){if(l!==void 0)return l;if(e.has("EXT_texture_filter_anisotropic")===!0){const P=e.get("EXT_texture_filter_anisotropic");l=s.getParameter(P.MAX_TEXTURE_MAX_ANISOTROPY_EXT)}else l=0;return l}function f(P){return!(P!==Ra&&r.convert(P)!==s.getParameter(s.IMPLEMENTATION_COLOR_READ_FORMAT))}function h(P){const T=P===qa&&(e.has("EXT_color_buffer_half_float")||e.has("EXT_color_buffer_float"));return!(P!==ha&&P!==Va&&!T&&r.convert(P)!==s.getParameter(s.IMPLEMENTATION_COLOR_READ_TYPE))}function m(P){if(P==="highp"){if(s.getShaderPrecisionFormat(s.VERTEX_SHADER,s.HIGH_FLOAT).precision>0&&s.getShaderPrecisionFormat(s.FRAGMENT_SHADER,s.HIGH_FLOAT).precision>0)return"highp";P="mediump"}return P==="mediump"&&s.getShaderPrecisionFormat(s.VERTEX_SHADER,s.MEDIUM_FLOAT).precision>0&&s.getShaderPrecisionFormat(s.FRAGMENT_SHADER,s.MEDIUM_FLOAT).precision>0?"mediump":"lowp"}let p=i.precision!==void 0?i.precision:"highp";const g=m(p);g!==p&&(ht("WebGLRenderer:",p,"not supported, using",g,"instead."),p=g);const _=i.logarithmicDepthBuffer===!0,v=i.reversedDepthBuffer===!0&&e.has("EXT_clip_control");i.reversedDepthBuffer===!0&&v===!1&&ht("WebGLRenderer: Unable to use reversed depth buffer due to missing EXT_clip_control extension. Fallback to default depth buffer.");const x=s.getParameter(s.MAX_TEXTURE_IMAGE_UNITS),E=s.getParameter(s.MAX_VERTEX_TEXTURE_IMAGE_UNITS),D=s.getParameter(s.MAX_TEXTURE_SIZE),M=s.getParameter(s.MAX_CUBE_MAP_TEXTURE_SIZE),y=s.getParameter(s.MAX_VERTEX_ATTRIBS),F=s.getParameter(s.MAX_VERTEX_UNIFORM_VECTORS),V=s.getParameter(s.MAX_VARYING_VECTORS),R=s.getParameter(s.MAX_FRAGMENT_UNIFORM_VECTORS),N=s.getParameter(s.MAX_SAMPLES),L=s.getParameter(s.SAMPLES);return{isWebGL2:!0,getMaxAnisotropy:c,getMaxPrecision:m,textureFormatReadable:f,textureTypeReadable:h,precision:p,logarithmicDepthBuffer:_,reversedDepthBuffer:v,maxTextures:x,maxVertexTextures:E,maxTextureSize:D,maxCubemapSize:M,maxAttributes:y,maxVertexUniforms:F,maxVaryings:V,maxFragmentUniforms:R,maxSamples:N,samples:L}}function _A(s){const e=this;let i=null,r=0,l=!1,c=!1;const f=new ns,h=new yt,m={value:null,needsUpdate:!1};this.uniform=m,this.numPlanes=0,this.numIntersection=0,this.init=function(_,v){const x=_.length!==0||v||r!==0||l;return l=v,r=_.length,x},this.beginShadows=function(){c=!0,g(null)},this.endShadows=function(){c=!1},this.setGlobalState=function(_,v){i=g(_,v,0)},this.setState=function(_,v,x){const E=_.clippingPlanes,D=_.clipIntersection,M=_.clipShadows,y=s.get(_);if(!l||E===null||E.length===0||c&&!M)c?g(null):p();else{const F=c?0:r,V=F*4;let R=y.clippingState||null;m.value=R,R=g(E,v,V,x);for(let N=0;N!==V;++N)R[N]=i[N];y.clippingState=R,this.numIntersection=D?this.numPlanes:0,this.numPlanes+=F}};function p(){m.value!==i&&(m.value=i,m.needsUpdate=r>0),e.numPlanes=r,e.numIntersection=0}function g(_,v,x,E){const D=_!==null?_.length:0;let M=null;if(D!==0){if(M=m.value,E!==!0||M===null){const y=x+D*4,F=v.matrixWorldInverse;h.getNormalMatrix(F),(M===null||M.length<y)&&(M=new Float32Array(y));for(let V=0,R=x;V!==D;++V,R+=4)f.copy(_[V]).applyMatrix4(F,h),f.normal.toArray(M,R),M[R+3]=f.constant}m.value=M,m.needsUpdate=!0}return e.numPlanes=D,e.numIntersection=0,M}}const Po=4,xA=6,SA=20,yA=256,Il=new Hx,U_=new Rt;let Ih=null,Fh=0,zh=0,Bh=!1;const MA=new Q,Rs=new Q;class N_{constructor(e){this._renderer=e,this._pingPongRenderTarget=null,this._lodMax=0,this._cubeSize=0,this._sizeLods=[],this._lodMeshes=[],this._backgroundBox=null,this._cubemapMaterial=null,this._equirectMaterial=null,this._blurMaterial=null,this._ggxMaterial=null}fromScene(e,i=0,r=.1,l=100,c={}){const{size:f=256,position:h=MA}=c;Ih=this._renderer.getRenderTarget(),Fh=this._renderer.getActiveCubeFace(),zh=this._renderer.getActiveMipmapLevel(),Bh=this._renderer.xr.enabled,this._renderer.xr.enabled=!1,this._setSize(f);const m=this._allocateTargets();return m.depthBuffer=!0,this._sceneToCubeUV(e,r,l,m,h),i>0&&this._blur(m,0,0,i),this._applyPMREM(m),this._cleanup(m),m}fromEquirectangular(e,i=null){return this._fromTexture(e,i)}fromCubemap(e,i=null){return this._fromTexture(e,i)}compileCubemapShader(){this._cubemapMaterial===null&&(this._cubemapMaterial=P_(),this._compileMaterial(this._cubemapMaterial))}compileEquirectangularShader(){this._equirectMaterial===null&&(this._equirectMaterial=O_(),this._compileMaterial(this._equirectMaterial))}dispose(){this._dispose(),this._cubemapMaterial!==null&&this._cubemapMaterial.dispose(),this._equirectMaterial!==null&&this._equirectMaterial.dispose(),this._backgroundBox!==null&&(this._backgroundBox.geometry.dispose(),this._backgroundBox.material.dispose())}_setSize(e){this._lodMax=Math.floor(Math.log2(e)),this._cubeSize=Math.pow(2,this._lodMax)}_dispose(){this._blurMaterial!==null&&this._blurMaterial.dispose(),this._ggxMaterial!==null&&this._ggxMaterial.dispose(),this._pingPongRenderTarget!==null&&this._pingPongRenderTarget.dispose();for(let e=0;e<this._lodMeshes.length;e++)this._lodMeshes[e].geometry.dispose()}_cleanup(e){this._renderer.setRenderTarget(Ih,Fh,zh),this._renderer.xr.enabled=Bh,e.scissorTest=!1,Do(e,0,0,e.width,e.height)}_fromTexture(e,i){e.mapping===Ls||e.mapping===Bo?this._setSize(e.image.length===0?16:e.image[0].width||e.image[0].image.width):this._setSize(e.image.width/4),Ih=this._renderer.getRenderTarget(),Fh=this._renderer.getActiveCubeFace(),zh=this._renderer.getActiveMipmapLevel(),Bh=this._renderer.xr.enabled,this._renderer.xr.enabled=!1;const r=i||this._allocateTargets();return this._textureToCubeUV(e,r),this._applyPMREM(r),this._cleanup(r),r}_allocateTargets(){const e=3*Math.max(this._cubeSize,112),i=4*this._cubeSize,r={magFilter:mi,minFilter:mi,generateMipmaps:!1,type:qa,format:Ra,colorSpace:Vu,depthBuffer:!1},l=L_(e,i,r);if(this._pingPongRenderTarget===null||this._pingPongRenderTarget.width!==e||this._pingPongRenderTarget.height!==i){this._pingPongRenderTarget!==null&&this._dispose(),this._pingPongRenderTarget=L_(e,i,r);const{_lodMax:c}=this;({lodMeshes:this._lodMeshes,sizeLods:this._sizeLods}=bA(c)),this._blurMaterial=TA(c,e,i),this._ggxMaterial=EA(c,e,i)}return l}_compileMaterial(e){const i=new Ki(new zn,e);this._renderer.compile(i,Il)}_sceneToCubeUV(e,i,r,l,c){const m=new Yi(90,1,i,r),p=[1,-1,1,1,1,1],g=[1,1,1,-1,-1,-1],_=this._renderer,v=_.autoClear,x=_.toneMapping;_.getClearColor(U_),_.toneMapping=Xa,_.autoClear=!1,_.state.buffers.depth.getReversed()&&(_.setRenderTarget(l),_.clearDepth(),_.setRenderTarget(null)),this._backgroundBox===null&&(this._backgroundBox=new Ki(new $l,new Qu({name:"PMREM.Background",side:Oi,depthWrite:!1,depthTest:!1})));const D=this._backgroundBox,M=D.material;let y=!1;const F=e.background;F?F.isColor&&(M.color.copy(F),e.background=null,y=!0):(M.color.copy(U_),y=!0);for(let V=0;V<6;V++){const R=V%3;R===0?(m.up.set(0,p[V],0),m.position.set(c.x,c.y,c.z),m.lookAt(c.x+g[V],c.y,c.z)):R===1?(m.up.set(0,0,p[V]),m.position.set(c.x,c.y,c.z),m.lookAt(c.x,c.y+g[V],c.z)):(m.up.set(0,p[V],0),m.position.set(c.x,c.y,c.z),m.lookAt(c.x,c.y,c.z+g[V]));const N=this._cubeSize;Do(l,R*N,V>2?N:0,N,N),_.setRenderTarget(l),y&&_.render(D,m),_.render(e,m)}_.toneMapping=x,_.autoClear=v,e.background=F}_textureToCubeUV(e,i){const r=this._renderer,l=e.mapping===Ls||e.mapping===Bo;l?(this._cubemapMaterial===null&&(this._cubemapMaterial=P_()),this._cubemapMaterial.uniforms.flipEnvMap.value=e.isRenderTargetTexture===!1?-1:1):this._equirectMaterial===null&&(this._equirectMaterial=O_());const c=l?this._cubemapMaterial:this._equirectMaterial,f=this._lodMeshes[0];f.material=c;const h=c.uniforms;h.envMap.value=e;const m=this._cubeSize;Do(i,0,0,3*m,2*m),r.setRenderTarget(i),r.render(f,Il)}_applyPMREM(e){const i=this._renderer,r=i.autoClear;i.autoClear=!1;const l=this._lodMeshes.length;for(let c=1;c<l;c++)this._applyGGXFilter(e,c-1,c);i.autoClear=r}_applyGGXFilter(e,i,r){const l=this._renderer,c=this._pingPongRenderTarget,f=this._ggxMaterial,h=this._lodMeshes[r];h.material=f;const m=f.uniforms,p=r/(this._lodMeshes.length-1),g=i/(this._lodMeshes.length-1),_=Math.sqrt(p*p-g*g),v=p*1.25,x=_*v,{_lodMax:E}=this,D=this._sizeLods[r],M=3*D*(r>E-Po?r-E+Po:0),y=4*(this._cubeSize-D);m.envMap.value=e.texture,m.roughness.value=x,m.mipInt.value=E-i,Do(c,M,y,3*D,2*D),l.setRenderTarget(c),l.render(h,Il),m.envMap.value=c.texture,m.roughness.value=0,m.mipInt.value=E-r,Do(e,M,y,3*D,2*D),l.setRenderTarget(e),l.render(h,Il)}_blur(e,i,r,l){const c=this._pingPongRenderTarget,f=Math.min(l,Math.PI)/Math.SQRT2;this._blurPass(e,c,i,r,f),this._blurPass(c,e,r,r,f)}_blurPass(e,i,r,l,c){const f=this._renderer,h=this._blurMaterial,m=this._lodMeshes[l];m.material=h;const p=h.uniforms;p.envMap.value=e.texture,p.sigma.value=c,p.mipInt.value=this._lodMax-r;const g=this._sizeLods[l],_=3*g*(l>this._lodMax-Po?l-this._lodMax+Po:0),v=4*(this._cubeSize-g);Do(i,_,v,3*g,2*g),f.setRenderTarget(i),f.render(m,Il)}}function bA(s){const e=[],i=[];let r=s;const l=s-Po+1+xA;for(let c=0;c<l;c++){const f=Math.pow(2,r);e.push(f);const h=1/(f-2),m=-h,p=1+h,g=[m,m,p,m,p,p,m,m,p,p,m,p],_=6,v=6,x=3,E=new Float32Array(x*v*_),D=new Float32Array(x*v*_);for(let y=0;y<_;y++){const F=y%3*2/3-1,V=y>2?0:-1,R=[F,V,0,F+2/3,V,0,F+2/3,V+1,0,F,V,0,F+2/3,V+1,0,F,V+1,0];E.set(R,x*v*y);for(let N=0;N<v;N++){const L=g[N*2]*2-1,P=g[N*2+1]*2-1;y===0?Rs.set(1,P,L):y===1?Rs.set(-L,1,-P):y===2?Rs.set(-L,P,1):y===3?Rs.set(-1,P,-L):y===4?Rs.set(-L,-1,P):Rs.set(L,P,-1),Rs.toArray(D,(y*v+N)*x)}}const M=new zn;M.setAttribute("position",new Fn(E,x)),M.setAttribute("outputDirection",new Fn(D,x)),i.push(new Ki(M,null)),r>Po&&r--}return{lodMeshes:i,sizeLods:e}}function L_(s,e,i){const r=new wa(s,e,i);return r.texture.mapping=Zu,r.texture.name="PMREM.cubeUv",r.scissorTest=!0,r}function Do(s,e,i,r,l){s.viewport.set(e,i,r,l),s.scissor.set(e,i,r,l)}function EA(s,e,i){return new Yn({name:"PMREMGGXConvolution",defines:{GGX_SAMPLES:yA,CUBEUV_TEXEL_WIDTH:1/e,CUBEUV_TEXEL_HEIGHT:1/i,CUBEUV_MAX_MIP:`${s}.0`},uniforms:{envMap:{value:null},roughness:{value:0},mipInt:{value:0}},vertexShader:Ju(),fragmentShader:`

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
		`,blending:Mr,depthTest:!1,depthWrite:!1})}function TA(s,e,i){return new Yn({name:"SphericalGaussianBlur",defines:{SAMPLES:SA,CUBEUV_TEXEL_WIDTH:1/e,CUBEUV_TEXEL_HEIGHT:1/i,CUBEUV_MAX_MIP:`${s}.0`},uniforms:{envMap:{value:null},sigma:{value:0},mipInt:{value:0}},vertexShader:Ju(),fragmentShader:`

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
		`,blending:Mr,depthTest:!1,depthWrite:!1})}function O_(){return new Yn({name:"EquirectangularToCubeUV",uniforms:{envMap:{value:null}},vertexShader:Ju(),fragmentShader:`

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
		`,blending:Mr,depthTest:!1,depthWrite:!1})}function P_(){return new Yn({name:"CubemapToCubeUV",uniforms:{envMap:{value:null},flipEnvMap:{value:-1}},vertexShader:Ju(),fragmentShader:`

			precision mediump float;
			precision mediump int;

			uniform float flipEnvMap;

			varying vec3 vOutputDirection;

			uniform samplerCube envMap;

			void main() {

				gl_FragColor = textureCube( envMap, vec3( flipEnvMap * vOutputDirection.x, vOutputDirection.yz ) );

			}
		`,blending:Mr,depthTest:!1,depthWrite:!1})}function Ju(){return`

		precision mediump float;
		precision mediump int;

		attribute vec3 outputDirection;

		varying vec3 vOutputDirection;

		void main() {

			vOutputDirection = outputDirection;
			gl_Position = vec4( position, 1.0 );

		}
	`}class kx extends wa{constructor(e=1,i={}){super(e,e,i),this.isWebGLCubeRenderTarget=!0;const r={width:e,height:e,depth:1},l=[r,r,r,r,r,r];this.texture=new Px(l),this._setTextureOptions(i),this.texture.isRenderTargetTexture=!0}fromEquirectangularTexture(e,i){this.texture.type=i.type,this.texture.colorSpace=i.colorSpace,this.texture.generateMipmaps=i.generateMipmaps,this.texture.minFilter=i.minFilter,this.texture.magFilter=i.magFilter;const r={uniforms:{tEquirect:{value:null}},vertexShader:`

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
			`},l=new $l(5,5,5),c=new Yn({name:"CubemapFromEquirect",uniforms:Ho(r.uniforms),vertexShader:r.vertexShader,fragmentShader:r.fragmentShader,side:Oi,blending:Mr});c.uniforms.tEquirect.value=i;const f=new Ki(l,c),h=i.minFilter;return i.minFilter===Cs&&(i.minFilter=mi),new CE(1,10,this).update(e,f),i.minFilter=h,f.geometry.dispose(),f.material.dispose(),this}clear(e,i=!0,r=!0,l=!0){const c=e.getRenderTarget();for(let f=0;f<6;f++)e.setRenderTarget(this,f),e.clear(i,r,l);e.setRenderTarget(c)}}function AA(s){let e=new WeakMap,i=new WeakMap,r=null;function l(v,x=!1){return v==null?null:x?f(v):c(v)}function c(v){if(v&&v.isTexture){const x=v.mapping;if(x===rh||x===sh)if(e.has(v)){const E=e.get(v).texture;return h(E,v.mapping)}else{const E=v.image;if(E&&E.height>0){const D=new kx(E.height);return D.fromEquirectangularTexture(s,v),e.set(v,D),v.addEventListener("dispose",p),h(D.texture,v.mapping)}else return null}}return v}function f(v){if(v&&v.isTexture){const x=v.mapping,E=x===rh||x===sh,D=x===Ls||x===Bo;if(E||D){let M=i.get(v);const y=M!==void 0?M.texture.pmremVersion:0;if(v.isRenderTargetTexture&&v.pmremVersion!==y)return r===null&&(r=new N_(s)),M=E?r.fromEquirectangular(v,M):r.fromCubemap(v,M),M.texture.pmremVersion=v.pmremVersion,i.set(v,M),M.texture;if(M!==void 0)return M.texture;{const F=v.image;return E&&F&&F.height>0||D&&F&&m(F)?(r===null&&(r=new N_(s)),M=E?r.fromEquirectangular(v):r.fromCubemap(v),M.texture.pmremVersion=v.pmremVersion,i.set(v,M),v.addEventListener("dispose",g),M.texture):null}}}return v}function h(v,x){return x===rh?v.mapping=Ls:x===sh&&(v.mapping=Bo),v}function m(v){let x=0;const E=6;for(let D=0;D<E;D++)v[D]!==void 0&&x++;return x===E}function p(v){const x=v.target;x.removeEventListener("dispose",p);const E=e.get(x);E!==void 0&&(e.delete(x),E.dispose())}function g(v){const x=v.target;x.removeEventListener("dispose",g);const E=i.get(x);E!==void 0&&(i.delete(x),E.dispose())}function _(){e=new WeakMap,i=new WeakMap,r!==null&&(r.dispose(),r=null)}return{get:l,dispose:_}}function RA(s){const e={};function i(r){if(e[r]!==void 0)return e[r];const l=s.getExtension(r);return e[r]=l,l}return{has:function(r){return i(r)!==null},init:function(){i("EXT_color_buffer_float"),i("WEBGL_clip_cull_distance"),i("OES_texture_float_linear"),i("EXT_color_buffer_half_float"),i("WEBGL_multisampled_render_to_texture"),i("WEBGL_render_shared_exponent")},get:function(r){const l=i(r);return l===null&&Fo("WebGLRenderer: "+r+" extension not supported."),l}}}function CA(s,e,i,r){const l={},c=new WeakMap;function f(_){const v=_.target;v.index!==null&&e.remove(v.index);for(const E in v.attributes)e.remove(v.attributes[E]);v.removeEventListener("dispose",f),delete l[v.id];const x=c.get(v);x&&(e.remove(x),c.delete(v)),r.releaseStatesOfGeometry(v),v.isInstancedBufferGeometry===!0&&delete v._maxInstanceCount,i.memory.geometries--}function h(_,v){return l[v.id]===!0||(v.addEventListener("dispose",f),l[v.id]=!0,i.memory.geometries++),v}function m(_){const v=_.attributes;for(const x in v)e.update(v[x],s.ARRAY_BUFFER)}function p(_){const v=[],x=_.index,E=_.attributes.position;let D=0;if(E===void 0)return;if(x!==null){const F=x.array;D=x.version;for(let V=0,R=F.length;V<R;V+=3){const N=F[V+0],L=F[V+1],P=F[V+2];v.push(N,L,L,P,P,N)}}else{const F=E.array;D=E.version;for(let V=0,R=F.length/3-1;V<R;V+=3){const N=V+0,L=V+1,P=V+2;v.push(N,L,L,P,P,N)}}const M=new(E.count>=65535?Lx:Nx)(v,1);M.version=D;const y=c.get(_);y&&e.remove(y),c.set(_,M)}function g(_){const v=c.get(_);if(v){const x=_.index;x!==null&&v.version<x.version&&p(_)}else p(_);return c.get(_)}return{get:h,update:m,getWireframeAttribute:g}}function wA(s,e,i){let r;function l(_){r=_}let c,f;function h(_){c=_.type,f=_.bytesPerElement}function m(_,v){s.drawElements(r,v,c,_*f),i.update(v,r,1)}function p(_,v,x){x!==0&&(s.drawElementsInstanced(r,v,c,_*f,x),i.update(v,r,x))}function g(_,v,x){if(x===0)return;e.get("WEBGL_multi_draw").multiDrawElementsWEBGL(r,v,0,c,_,0,x);let D=0;for(let M=0;M<x;M++)D+=v[M];i.update(D,r,1)}this.setMode=l,this.setIndex=h,this.render=m,this.renderInstances=p,this.renderMultiDraw=g}function DA(s){const e={geometries:0,textures:0},i={frame:0,calls:0,triangles:0,points:0,lines:0};function r(c,f,h){switch(i.calls++,f){case s.TRIANGLES:i.triangles+=h*(c/3);break;case s.LINES:i.lines+=h*(c/2);break;case s.LINE_STRIP:i.lines+=h*(c-1);break;case s.LINE_LOOP:i.lines+=h*c;break;case s.POINTS:i.points+=h*c;break;default:Zt("WebGLInfo: Unknown draw mode:",f);break}}function l(){i.calls=0,i.triangles=0,i.points=0,i.lines=0}return{memory:e,render:i,programs:null,autoReset:!0,reset:l,update:r}}function UA(s,e,i){const r=new WeakMap,l=new Ln;function c(f,h,m){const p=f.morphTargetInfluences,g=h.morphAttributes.position||h.morphAttributes.normal||h.morphAttributes.color,_=g!==void 0?g.length:0;let v=r.get(h);if(v===void 0||v.count!==_){let B=function(){T.dispose(),r.delete(h),h.removeEventListener("dispose",B)};var x=B;v!==void 0&&v.texture.dispose();const E=h.morphAttributes.position!==void 0,D=h.morphAttributes.normal!==void 0,M=h.morphAttributes.color!==void 0,y=h.morphAttributes.position||[],F=h.morphAttributes.normal||[],V=h.morphAttributes.color||[];let R=0;E===!0&&(R=1),D===!0&&(R=2),M===!0&&(R=3);let N=h.attributes.position.count*R,L=1;N>e.maxTextureSize&&(L=Math.ceil(N/e.maxTextureSize),N=e.maxTextureSize);const P=new Float32Array(N*L*4*_),T=new wx(P,N,L,_);T.type=Va,T.needsUpdate=!0;const O=R*4;for(let k=0;k<_;k++){const J=y[k],se=F[k],Y=V[k],j=N*L*4*k;for(let z=0;z<J.count;z++){const H=z*O;E===!0&&(l.fromBufferAttribute(J,z),P[j+H+0]=l.x,P[j+H+1]=l.y,P[j+H+2]=l.z,P[j+H+3]=0),D===!0&&(l.fromBufferAttribute(se,z),P[j+H+4]=l.x,P[j+H+5]=l.y,P[j+H+6]=l.z,P[j+H+7]=0),M===!0&&(l.fromBufferAttribute(Y,z),P[j+H+8]=l.x,P[j+H+9]=l.y,P[j+H+10]=l.z,P[j+H+11]=Y.itemSize===4?l.w:1)}}v={count:_,texture:T,size:new Kt(N,L)},r.set(h,v),h.addEventListener("dispose",B)}if(f.isInstancedMesh===!0&&f.morphTexture!==null)m.getUniforms().setValue(s,"morphTexture",f.morphTexture,i);else{let E=0;for(let M=0;M<p.length;M++)E+=p[M];const D=h.morphTargetsRelative?1:1-E;m.getUniforms().setValue(s,"morphTargetBaseInfluence",D),m.getUniforms().setValue(s,"morphTargetInfluences",p)}m.getUniforms().setValue(s,"morphTargetsTexture",v.texture,i),m.getUniforms().setValue(s,"morphTargetsTextureSize",v.size)}return{update:c}}function NA(s,e,i,r,l){let c=new WeakMap;function f(p){const g=l.render.frame,_=p.geometry,v=e.get(p,_);if(c.get(v)!==g&&(e.update(v),c.set(v,g)),p.isInstancedMesh&&(p.hasEventListener("dispose",m)===!1&&p.addEventListener("dispose",m),c.get(p)!==g&&(i.update(p.instanceMatrix,s.ARRAY_BUFFER),p.instanceColor!==null&&i.update(p.instanceColor,s.ARRAY_BUFFER),c.set(p,g))),p.isSkinnedMesh){const x=p.skeleton;c.get(x)!==g&&(x.update(),c.set(x,g))}return v}function h(){c=new WeakMap}function m(p){const g=p.target;g.removeEventListener("dispose",m),r.releaseStatesOfObject(g),i.remove(g.instanceMatrix),g.instanceColor!==null&&i.remove(g.instanceColor)}return{update:f,dispose:h}}const LA={[hx]:"LINEAR_TONE_MAPPING",[px]:"REINHARD_TONE_MAPPING",[mx]:"CINEON_TONE_MAPPING",[gx]:"ACES_FILMIC_TONE_MAPPING",[_x]:"AGX_TONE_MAPPING",[xx]:"NEUTRAL_TONE_MAPPING",[vx]:"CUSTOM_TONE_MAPPING"};function OA(s,e,i,r,l,c){const f=new wa(e,i,{type:s,depthBuffer:l,stencilBuffer:c,samples:r?4:0,storeMultisampledDepthBuffer:!1,storeMultisampledStencilBuffer:!1,resolveDepthBuffer:!1,resolveStencilBuffer:!1});let h=null,m=null;const p=new zn;p.setAttribute("position",new Cn([-1,3,0,-1,-1,0,3,-1,0],3)),p.setAttribute("uv",new Cn([0,2,0,0,2,0],2));const g=new yE({uniforms:{tDiffuse:{value:null}},vertexShader:`
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
			}`,depthTest:!1,depthWrite:!1}),_=new Ki(p,g),v=new Hx(-1,1,1,-1,0,1);let x=null,E=null,D=!1,M,y=null,F=[],V=!1;this.setSize=function(R,N){f.setSize(R,N),h!==null&&h.setSize(R,N),m!==null&&m.setSize(R,N);for(let L=0;L<F.length;L++){const P=F[L];P.setSize&&P.setSize(R,N)}},this.setEffects=function(R){F=R,V=F.length>0&&F[0].isRenderPass===!0;const N=f.width,L=f.height;F.length>0&&h===null&&(h=new wa(N,L,{type:qa,depthBuffer:!1,stencilBuffer:!1}),m=new wa(N,L,{type:qa,depthBuffer:!1,stencilBuffer:!1}));for(let P=0;P<F.length;P++){const T=F[P];T.setSize&&T.setSize(N,L)}},this.begin=function(R,N){if(D||R.toneMapping===Xa&&F.length===0)return!1;if(y=N,N!==null){const L=N.width,P=N.height;(f.width!==L||f.height!==P)&&this.setSize(L,P)}return V===!1&&R.setRenderTarget(f),M=R.toneMapping,R.toneMapping=Xa,!0},this.hasRenderPass=function(){return V},this.end=function(R,N){R.toneMapping=M,D=!0;let L=f,P=h;for(let T=0;T<F.length;T++){const O=F[T];O.enabled!==!1&&(O.render(R,P,L,N),O.needsSwap!==!1&&(L=P,P=P===h?m:h))}if(x!==R.outputColorSpace||E!==R.toneMapping){x=R.outputColorSpace,E=R.toneMapping,g.defines={},kt.getTransfer(x)===cn&&(g.defines.SRGB_TRANSFER="");const T=LA[E];T&&(g.defines[T]=""),g.needsUpdate=!0}g.uniforms.tDiffuse.value=L.texture,R.setRenderTarget(y),R.render(_,v),y=null,D=!1},this.isCompositing=function(){return D},this.dispose=function(){f.dispose(),h!==null&&h.dispose(),m!==null&&m.dispose(),p.dispose(),g.dispose()}}const Xx=new gi,Up=new Ql(1,1),Wx=new wx,qx=new qb,Yx=new Px,I_=[],F_=[],z_=new Float32Array(16),B_=new Float32Array(9),H_=new Float32Array(4);function Xo(s,e,i){const r=s[0];if(r<=0||r>0)return s;const l=e*i;let c=I_[l];if(c===void 0&&(c=new Float32Array(l),I_[l]=c),e!==0){r.toArray(c,0);for(let f=1,h=0;f!==e;++f)h+=i,s[f].toArray(c,h)}return c}function jn(s,e){if(s.length!==e.length)return!1;for(let i=0,r=s.length;i<r;i++)if(s[i]!==e[i])return!1;return!0}function Zn(s,e){for(let i=0,r=e.length;i<r;i++)s[i]=e[i]}function $u(s,e){let i=F_[e];i===void 0&&(i=new Int32Array(e),F_[e]=i);for(let r=0;r!==e;++r)i[r]=s.allocateTextureUnit();return i}function PA(s,e){const i=this.cache;i[0]!==e&&(s.uniform1f(this.addr,e),i[0]=e)}function IA(s,e){const i=this.cache;if(e.x!==void 0)(i[0]!==e.x||i[1]!==e.y)&&(s.uniform2f(this.addr,e.x,e.y),i[0]=e.x,i[1]=e.y);else{if(jn(i,e))return;s.uniform2fv(this.addr,e),Zn(i,e)}}function FA(s,e){const i=this.cache;if(e.x!==void 0)(i[0]!==e.x||i[1]!==e.y||i[2]!==e.z)&&(s.uniform3f(this.addr,e.x,e.y,e.z),i[0]=e.x,i[1]=e.y,i[2]=e.z);else if(e.r!==void 0)(i[0]!==e.r||i[1]!==e.g||i[2]!==e.b)&&(s.uniform3f(this.addr,e.r,e.g,e.b),i[0]=e.r,i[1]=e.g,i[2]=e.b);else{if(jn(i,e))return;s.uniform3fv(this.addr,e),Zn(i,e)}}function zA(s,e){const i=this.cache;if(e.x!==void 0)(i[0]!==e.x||i[1]!==e.y||i[2]!==e.z||i[3]!==e.w)&&(s.uniform4f(this.addr,e.x,e.y,e.z,e.w),i[0]=e.x,i[1]=e.y,i[2]=e.z,i[3]=e.w);else{if(jn(i,e))return;s.uniform4fv(this.addr,e),Zn(i,e)}}function BA(s,e){const i=this.cache,r=e.elements;if(r===void 0){if(jn(i,e))return;s.uniformMatrix2fv(this.addr,!1,e),Zn(i,e)}else{if(jn(i,r))return;H_.set(r),s.uniformMatrix2fv(this.addr,!1,H_),Zn(i,r)}}function HA(s,e){const i=this.cache,r=e.elements;if(r===void 0){if(jn(i,e))return;s.uniformMatrix3fv(this.addr,!1,e),Zn(i,e)}else{if(jn(i,r))return;B_.set(r),s.uniformMatrix3fv(this.addr,!1,B_),Zn(i,r)}}function GA(s,e){const i=this.cache,r=e.elements;if(r===void 0){if(jn(i,e))return;s.uniformMatrix4fv(this.addr,!1,e),Zn(i,e)}else{if(jn(i,r))return;z_.set(r),s.uniformMatrix4fv(this.addr,!1,z_),Zn(i,r)}}function VA(s,e){const i=this.cache;i[0]!==e&&(s.uniform1i(this.addr,e),i[0]=e)}function kA(s,e){const i=this.cache;if(e.x!==void 0)(i[0]!==e.x||i[1]!==e.y)&&(s.uniform2i(this.addr,e.x,e.y),i[0]=e.x,i[1]=e.y);else{if(jn(i,e))return;s.uniform2iv(this.addr,e),Zn(i,e)}}function XA(s,e){const i=this.cache;if(e.x!==void 0)(i[0]!==e.x||i[1]!==e.y||i[2]!==e.z)&&(s.uniform3i(this.addr,e.x,e.y,e.z),i[0]=e.x,i[1]=e.y,i[2]=e.z);else{if(jn(i,e))return;s.uniform3iv(this.addr,e),Zn(i,e)}}function WA(s,e){const i=this.cache;if(e.x!==void 0)(i[0]!==e.x||i[1]!==e.y||i[2]!==e.z||i[3]!==e.w)&&(s.uniform4i(this.addr,e.x,e.y,e.z,e.w),i[0]=e.x,i[1]=e.y,i[2]=e.z,i[3]=e.w);else{if(jn(i,e))return;s.uniform4iv(this.addr,e),Zn(i,e)}}function qA(s,e){const i=this.cache;i[0]!==e&&(s.uniform1ui(this.addr,e),i[0]=e)}function YA(s,e){const i=this.cache;if(e.x!==void 0)(i[0]!==e.x||i[1]!==e.y)&&(s.uniform2ui(this.addr,e.x,e.y),i[0]=e.x,i[1]=e.y);else{if(jn(i,e))return;s.uniform2uiv(this.addr,e),Zn(i,e)}}function jA(s,e){const i=this.cache;if(e.x!==void 0)(i[0]!==e.x||i[1]!==e.y||i[2]!==e.z)&&(s.uniform3ui(this.addr,e.x,e.y,e.z),i[0]=e.x,i[1]=e.y,i[2]=e.z);else{if(jn(i,e))return;s.uniform3uiv(this.addr,e),Zn(i,e)}}function ZA(s,e){const i=this.cache;if(e.x!==void 0)(i[0]!==e.x||i[1]!==e.y||i[2]!==e.z||i[3]!==e.w)&&(s.uniform4ui(this.addr,e.x,e.y,e.z,e.w),i[0]=e.x,i[1]=e.y,i[2]=e.z,i[3]=e.w);else{if(jn(i,e))return;s.uniform4uiv(this.addr,e),Zn(i,e)}}function KA(s,e,i){const r=this.cache,l=i.allocateTextureUnit();r[0]!==l&&(s.uniform1i(this.addr,l),r[0]=l);let c;this.type===s.SAMPLER_2D_SHADOW?(Up.compareFunction=i.isReversedDepthBuffer()?qp:Wp,c=Up):c=Xx,i.setTexture2D(e||c,l)}function QA(s,e,i){const r=this.cache,l=i.allocateTextureUnit();r[0]!==l&&(s.uniform1i(this.addr,l),r[0]=l),i.setTexture3D(e||qx,l)}function JA(s,e,i){const r=this.cache,l=i.allocateTextureUnit();r[0]!==l&&(s.uniform1i(this.addr,l),r[0]=l),i.setTextureCube(e||Yx,l)}function $A(s,e,i){const r=this.cache,l=i.allocateTextureUnit();r[0]!==l&&(s.uniform1i(this.addr,l),r[0]=l),i.setTexture2DArray(e||Wx,l)}function eR(s){switch(s){case 5126:return PA;case 35664:return IA;case 35665:return FA;case 35666:return zA;case 35674:return BA;case 35675:return HA;case 35676:return GA;case 5124:case 35670:return VA;case 35667:case 35671:return kA;case 35668:case 35672:return XA;case 35669:case 35673:return WA;case 5125:return qA;case 36294:return YA;case 36295:return jA;case 36296:return ZA;case 35678:case 36198:case 36298:case 36306:case 35682:return KA;case 35679:case 36299:case 36307:return QA;case 35680:case 36300:case 36308:case 36293:return JA;case 36289:case 36303:case 36311:case 36292:return $A}}function tR(s,e){s.uniform1fv(this.addr,e)}function nR(s,e){const i=Xo(e,this.size,2);s.uniform2fv(this.addr,i)}function iR(s,e){const i=Xo(e,this.size,3);s.uniform3fv(this.addr,i)}function aR(s,e){const i=Xo(e,this.size,4);s.uniform4fv(this.addr,i)}function rR(s,e){const i=Xo(e,this.size,4);s.uniformMatrix2fv(this.addr,!1,i)}function sR(s,e){const i=Xo(e,this.size,9);s.uniformMatrix3fv(this.addr,!1,i)}function oR(s,e){const i=Xo(e,this.size,16);s.uniformMatrix4fv(this.addr,!1,i)}function lR(s,e){s.uniform1iv(this.addr,e)}function cR(s,e){s.uniform2iv(this.addr,e)}function uR(s,e){s.uniform3iv(this.addr,e)}function fR(s,e){s.uniform4iv(this.addr,e)}function dR(s,e){s.uniform1uiv(this.addr,e)}function hR(s,e){s.uniform2uiv(this.addr,e)}function pR(s,e){s.uniform3uiv(this.addr,e)}function mR(s,e){s.uniform4uiv(this.addr,e)}function gR(s,e,i){const r=this.cache,l=e.length,c=$u(i,l);jn(r,c)||(s.uniform1iv(this.addr,c),Zn(r,c));let f;this.type===s.SAMPLER_2D_SHADOW?f=Up:f=Xx;for(let h=0;h!==l;++h)i.setTexture2D(e[h]||f,c[h])}function vR(s,e,i){const r=this.cache,l=e.length,c=$u(i,l);jn(r,c)||(s.uniform1iv(this.addr,c),Zn(r,c));for(let f=0;f!==l;++f)i.setTexture3D(e[f]||qx,c[f])}function _R(s,e,i){const r=this.cache,l=e.length,c=$u(i,l);jn(r,c)||(s.uniform1iv(this.addr,c),Zn(r,c));for(let f=0;f!==l;++f)i.setTextureCube(e[f]||Yx,c[f])}function xR(s,e,i){const r=this.cache,l=e.length,c=$u(i,l);jn(r,c)||(s.uniform1iv(this.addr,c),Zn(r,c));for(let f=0;f!==l;++f)i.setTexture2DArray(e[f]||Wx,c[f])}function SR(s){switch(s){case 5126:return tR;case 35664:return nR;case 35665:return iR;case 35666:return aR;case 35674:return rR;case 35675:return sR;case 35676:return oR;case 5124:case 35670:return lR;case 35667:case 35671:return cR;case 35668:case 35672:return uR;case 35669:case 35673:return fR;case 5125:return dR;case 36294:return hR;case 36295:return pR;case 36296:return mR;case 35678:case 36198:case 36298:case 36306:case 35682:return gR;case 35679:case 36299:case 36307:return vR;case 35680:case 36300:case 36308:case 36293:return _R;case 36289:case 36303:case 36311:case 36292:return xR}}class yR{constructor(e,i,r){this.id=e,this.addr=r,this.cache=[],this.type=i.type,this.setValue=eR(i.type)}}class MR{constructor(e,i,r){this.id=e,this.addr=r,this.cache=[],this.type=i.type,this.size=i.size,this.setValue=SR(i.type)}}class bR{constructor(e){this.id=e,this.seq=[],this.map={}}setValue(e,i,r){const l=this.seq;for(let c=0,f=l.length;c!==f;++c){const h=l[c];h.setValue(e,i[h.id],r)}}}const Hh=/(\w+)(\])?(\[|\.)?/g;function G_(s,e){s.seq.push(e),s.map[e.id]=e}function ER(s,e,i){const r=s.name,l=r.length;for(Hh.lastIndex=0;;){const c=Hh.exec(r),f=Hh.lastIndex;let h=c[1];const m=c[2]==="]",p=c[3];if(m&&(h=h|0),p===void 0||p==="["&&f+2===l){G_(i,p===void 0?new yR(h,s,e):new MR(h,s,e));break}else{let _=i.map[h];_===void 0&&(_=new bR(h),G_(i,_)),i=_}}}class Iu{constructor(e,i){this.seq=[],this.map={};const r=e.getProgramParameter(i,e.ACTIVE_UNIFORMS);for(let f=0;f<r;++f){const h=e.getActiveUniform(i,f),m=e.getUniformLocation(i,h.name);ER(h,m,this)}const l=[],c=[];for(const f of this.seq)f.type===e.SAMPLER_2D_SHADOW||f.type===e.SAMPLER_CUBE_SHADOW||f.type===e.SAMPLER_2D_ARRAY_SHADOW?l.push(f):c.push(f);l.length>0&&(this.seq=l.concat(c))}setValue(e,i,r,l){const c=this.map[i];c!==void 0&&c.setValue(e,r,l)}setOptional(e,i,r){const l=i[r];l!==void 0&&this.setValue(e,r,l)}static upload(e,i,r,l){for(let c=0,f=i.length;c!==f;++c){const h=i[c],m=r[h.id];m.needsUpdate!==!1&&h.setValue(e,m.value,l)}}static seqWithValue(e,i){const r=[];for(let l=0,c=e.length;l!==c;++l){const f=e[l];f.id in i&&r.push(f)}return r}}function V_(s,e,i){const r=s.createShader(e);return s.shaderSource(r,i),s.compileShader(r),r}const TR=37297;let AR=0;function RR(s,e){const i=s.split(`
`),r=[],l=Math.max(e-6,0),c=Math.min(e+6,i.length);for(let f=l;f<c;f++){const h=f+1;r.push(`${h===e?">":" "} ${h}: ${i[f]}`)}return r.join(`
`)}const k_=new yt;function CR(s){kt._getMatrix(k_,kt.workingColorSpace,s);const e=`mat3( ${k_.elements.map(i=>i.toFixed(4))} )`;switch(kt.getTransfer(s)){case ku:return[e,"LinearTransferOETF"];case cn:return[e,"sRGBTransferOETF"];default:return ht("WebGLProgram: Unsupported color space: ",s),[e,"LinearTransferOETF"]}}function X_(s,e,i){const r=s.getShaderParameter(e,s.COMPILE_STATUS),c=(s.getShaderInfoLog(e)||"").trim();if(r&&c==="")return"";const f=/ERROR: 0:(\d+)/.exec(c);if(f){const h=parseInt(f[1]);return i.toUpperCase()+`

`+c+`

`+RR(s.getShaderSource(e),h)}else return c}function wR(s,e){const i=CR(e);return[`vec4 ${s}( vec4 value ) {`,`	return ${i[1]}( vec4( value.rgb * ${i[0]}, value.a ) );`,"}"].join(`
`)}const DR={[hx]:"Linear",[px]:"Reinhard",[mx]:"Cineon",[gx]:"ACESFilmic",[_x]:"AgX",[xx]:"Neutral",[vx]:"Custom"};function UR(s,e){const i=DR[e];return i===void 0?(ht("WebGLProgram: Unsupported toneMapping:",e),"vec3 "+s+"( vec3 color ) { return LinearToneMapping( color ); }"):"vec3 "+s+"( vec3 color ) { return "+i+"ToneMapping( color ); }"}const wu=new Q;function NR(){kt.getLuminanceCoefficients(wu);const s=wu.x.toFixed(4),e=wu.y.toFixed(4),i=wu.z.toFixed(4);return["float luminance( const in vec3 rgb ) {",`	const vec3 weights = vec3( ${s}, ${e}, ${i} );`,"	return dot( weights, rgb );","}"].join(`
`)}function LR(s){return[s.extensionClipCullDistance?"#extension GL_ANGLE_clip_cull_distance : require":"",s.extensionMultiDraw?"#extension GL_ANGLE_multi_draw : require":""].filter(Hl).join(`
`)}function OR(s){const e=[];for(const i in s){const r=s[i];r!==!1&&e.push("#define "+i+" "+r)}return e.join(`
`)}function PR(s,e){const i={},r=s.getProgramParameter(e,s.ACTIVE_ATTRIBUTES);for(let l=0;l<r;l++){const c=s.getActiveAttrib(e,l),f=c.name;let h=1;c.type===s.FLOAT_MAT2&&(h=2),c.type===s.FLOAT_MAT3&&(h=3),c.type===s.FLOAT_MAT4&&(h=4),i[f]={type:c.type,location:s.getAttribLocation(e,f),locationSize:h}}return i}function Hl(s){return s!==""}function W_(s,e){const i=e.numSpotLightShadows+e.numSpotLightMaps-e.numSpotLightShadowsWithMaps;return s.replace(/NUM_SUN_LIGHTS/g,e.numSunLights).replace(/NUM_DIR_LIGHTS/g,e.numDirLights).replace(/NUM_SPOT_LIGHTS/g,e.numSpotLights).replace(/NUM_SPOT_LIGHT_MAPS/g,e.numSpotLightMaps).replace(/NUM_SPOT_LIGHT_COORDS/g,i).replace(/NUM_RECT_AREA_LIGHTS/g,e.numRectAreaLights).replace(/NUM_POINT_LIGHTS/g,e.numPointLights).replace(/NUM_HEMI_LIGHTS/g,e.numHemiLights).replace(/NUM_SUN_LIGHT_SHADOWS/g,e.numSunLightShadows).replace(/NUM_DIR_LIGHT_SHADOWS/g,e.numDirLightShadows).replace(/NUM_SPOT_LIGHT_SHADOWS_WITH_MAPS/g,e.numSpotLightShadowsWithMaps).replace(/NUM_SPOT_LIGHT_SHADOWS/g,e.numSpotLightShadows).replace(/NUM_POINT_LIGHT_SHADOWS/g,e.numPointLightShadows)}function q_(s,e){return s.replace(/NUM_CLIPPING_PLANES/g,e.numClippingPlanes).replace(/UNION_CLIPPING_PLANES/g,e.numClippingPlanes-e.numClipIntersection)}const IR=/^[ \t]*#include +<([\w\d./]+)>/gm;function Np(s){return s.replace(IR,zR)}const FR=new Map;function zR(s,e){let i=wt[e];if(i===void 0){const r=FR.get(e);if(r!==void 0)i=wt[r],ht('WebGLRenderer: Shader chunk "%s" has been deprecated. Use "%s" instead.',e,r);else throw new Error("THREE.WebGLProgram: Can not resolve #include <"+e+">")}return Np(i)}const BR=/#pragma unroll_loop_start\s+for\s*\(\s*int\s+i\s*=\s*(\d+)\s*;\s*i\s*<\s*(\d+)\s*;\s*i\s*\+\+\s*\)\s*{([\s\S]+?)}\s+#pragma unroll_loop_end/g;function Y_(s){return s.replace(BR,HR)}function HR(s,e,i,r){let l="";for(let c=parseInt(e);c<parseInt(i);c++)l+=r.replace(/\[\s*i\s*\]/g,"[ "+c+" ]").replace(/UNROLLED_LOOP_INDEX/g,c);return l}function j_(s){let e=`precision ${s.precision} float;
	precision ${s.precision} int;
	precision ${s.precision} sampler2D;
	precision ${s.precision} samplerCube;
	precision ${s.precision} sampler3D;
	precision ${s.precision} sampler2DArray;
	precision ${s.precision} sampler2DShadow;
	precision ${s.precision} samplerCubeShadow;
	precision ${s.precision} sampler2DArrayShadow;
	precision ${s.precision} isampler2D;
	precision ${s.precision} isampler3D;
	precision ${s.precision} isamplerCube;
	precision ${s.precision} isampler2DArray;
	precision ${s.precision} usampler2D;
	precision ${s.precision} usampler3D;
	precision ${s.precision} usamplerCube;
	precision ${s.precision} usampler2DArray;
	`;return s.precision==="highp"?e+=`
#define HIGH_PRECISION`:s.precision==="mediump"?e+=`
#define MEDIUM_PRECISION`:s.precision==="lowp"&&(e+=`
#define LOW_PRECISION`),e}const GR={[Uu]:"SHADOWMAP_TYPE_PCF",[Bl]:"SHADOWMAP_TYPE_VSM"};function VR(s){return GR[s.shadowMapType]||"SHADOWMAP_TYPE_BASIC"}const kR={[Ls]:"ENVMAP_TYPE_CUBE",[Bo]:"ENVMAP_TYPE_CUBE",[Zu]:"ENVMAP_TYPE_CUBE_UV"};function XR(s){return s.envMap===!1?"ENVMAP_TYPE_CUBE":kR[s.envMapMode]||"ENVMAP_TYPE_CUBE"}const WR={[Bo]:"ENVMAP_MODE_REFRACTION"};function qR(s){return s.envMap===!1?"ENVMAP_MODE_REFLECTION":WR[s.envMapMode]||"ENVMAP_MODE_REFLECTION"}const YR={[dx]:"ENVMAP_BLENDING_MULTIPLY",[lb]:"ENVMAP_BLENDING_MIX",[cb]:"ENVMAP_BLENDING_ADD"};function jR(s){return s.envMap===!1?"ENVMAP_BLENDING_NONE":YR[s.combine]||"ENVMAP_BLENDING_NONE"}function ZR(s){const e=s.envMapCubeUVHeight;if(e===null)return null;const i=Math.log2(e)-2,r=1/e;return{texelWidth:1/(3*Math.max(Math.pow(2,i),112)),texelHeight:r,maxMip:i}}function KR(s,e,i,r){const l=s.getContext(),c=i.defines;let f=i.vertexShader,h=i.fragmentShader;const m=VR(i),p=XR(i),g=qR(i),_=jR(i),v=ZR(i),x=LR(i),E=OR(c),D=l.createProgram();let M,y,F=i.glslVersion?"#version "+i.glslVersion+`
`:"";i.isRawShaderMaterial?(M=["#define SHADER_TYPE "+i.shaderType,"#define SHADER_NAME "+i.shaderName,E].filter(Hl).join(`
`),M.length>0&&(M+=`
`),y=["#define SHADER_TYPE "+i.shaderType,"#define SHADER_NAME "+i.shaderName,E].filter(Hl).join(`
`),y.length>0&&(y+=`
`)):(M=[j_(i),"#define SHADER_TYPE "+i.shaderType,"#define SHADER_NAME "+i.shaderName,E,i.extensionClipCullDistance?"#define USE_CLIP_DISTANCE":"",i.batching?"#define USE_BATCHING":"",i.batchingColor?"#define USE_BATCHING_COLOR":"",i.instancing?"#define USE_INSTANCING":"",i.instancingColor?"#define USE_INSTANCING_COLOR":"",i.instancingMorph?"#define USE_INSTANCING_MORPH":"",i.useFog&&i.fog?"#define USE_FOG":"",i.useFog&&i.fogExp2?"#define FOG_EXP2":"",i.map?"#define USE_MAP":"",i.envMap?"#define USE_ENVMAP":"",i.envMap?"#define "+g:"",i.lightMap?"#define USE_LIGHTMAP":"",i.aoMap?"#define USE_AOMAP":"",i.bumpMap?"#define USE_BUMPMAP":"",i.normalMap?"#define USE_NORMALMAP":"",i.normalMapObjectSpace?"#define USE_NORMALMAP_OBJECTSPACE":"",i.normalMapTangentSpace?"#define USE_NORMALMAP_TANGENTSPACE":"",i.displacementMap?"#define USE_DISPLACEMENTMAP":"",i.emissiveMap?"#define USE_EMISSIVEMAP":"",i.anisotropy?"#define USE_ANISOTROPY":"",i.anisotropyMap?"#define USE_ANISOTROPYMAP":"",i.clearcoatMap?"#define USE_CLEARCOATMAP":"",i.clearcoatRoughnessMap?"#define USE_CLEARCOAT_ROUGHNESSMAP":"",i.clearcoatNormalMap?"#define USE_CLEARCOAT_NORMALMAP":"",i.iridescenceMap?"#define USE_IRIDESCENCEMAP":"",i.iridescenceThicknessMap?"#define USE_IRIDESCENCE_THICKNESSMAP":"",i.specularMap?"#define USE_SPECULARMAP":"",i.specularColorMap?"#define USE_SPECULAR_COLORMAP":"",i.specularIntensityMap?"#define USE_SPECULAR_INTENSITYMAP":"",i.roughnessMap?"#define USE_ROUGHNESSMAP":"",i.metalnessMap?"#define USE_METALNESSMAP":"",i.alphaMap?"#define USE_ALPHAMAP":"",i.alphaHash?"#define USE_ALPHAHASH":"",i.transmission?"#define USE_TRANSMISSION":"",i.transmissionMap?"#define USE_TRANSMISSIONMAP":"",i.thicknessMap?"#define USE_THICKNESSMAP":"",i.sheenColorMap?"#define USE_SHEEN_COLORMAP":"",i.sheenRoughnessMap?"#define USE_SHEEN_ROUGHNESSMAP":"",i.mapUv?"#define MAP_UV "+i.mapUv:"",i.alphaMapUv?"#define ALPHAMAP_UV "+i.alphaMapUv:"",i.lightMapUv?"#define LIGHTMAP_UV "+i.lightMapUv:"",i.aoMapUv?"#define AOMAP_UV "+i.aoMapUv:"",i.emissiveMapUv?"#define EMISSIVEMAP_UV "+i.emissiveMapUv:"",i.bumpMapUv?"#define BUMPMAP_UV "+i.bumpMapUv:"",i.normalMapUv?"#define NORMALMAP_UV "+i.normalMapUv:"",i.displacementMapUv?"#define DISPLACEMENTMAP_UV "+i.displacementMapUv:"",i.metalnessMapUv?"#define METALNESSMAP_UV "+i.metalnessMapUv:"",i.roughnessMapUv?"#define ROUGHNESSMAP_UV "+i.roughnessMapUv:"",i.anisotropyMapUv?"#define ANISOTROPYMAP_UV "+i.anisotropyMapUv:"",i.clearcoatMapUv?"#define CLEARCOATMAP_UV "+i.clearcoatMapUv:"",i.clearcoatNormalMapUv?"#define CLEARCOAT_NORMALMAP_UV "+i.clearcoatNormalMapUv:"",i.clearcoatRoughnessMapUv?"#define CLEARCOAT_ROUGHNESSMAP_UV "+i.clearcoatRoughnessMapUv:"",i.iridescenceMapUv?"#define IRIDESCENCEMAP_UV "+i.iridescenceMapUv:"",i.iridescenceThicknessMapUv?"#define IRIDESCENCE_THICKNESSMAP_UV "+i.iridescenceThicknessMapUv:"",i.sheenColorMapUv?"#define SHEEN_COLORMAP_UV "+i.sheenColorMapUv:"",i.sheenRoughnessMapUv?"#define SHEEN_ROUGHNESSMAP_UV "+i.sheenRoughnessMapUv:"",i.specularMapUv?"#define SPECULARMAP_UV "+i.specularMapUv:"",i.specularColorMapUv?"#define SPECULAR_COLORMAP_UV "+i.specularColorMapUv:"",i.specularIntensityMapUv?"#define SPECULAR_INTENSITYMAP_UV "+i.specularIntensityMapUv:"",i.transmissionMapUv?"#define TRANSMISSIONMAP_UV "+i.transmissionMapUv:"",i.thicknessMapUv?"#define THICKNESSMAP_UV "+i.thicknessMapUv:"",i.vertexTangents&&i.flatShading===!1?"#define USE_TANGENT":"",i.vertexNormals?"#define HAS_NORMAL":"",i.vertexColors?"#define USE_COLOR":"",i.vertexAlphas?"#define USE_COLOR_ALPHA":"",i.vertexUv1s?"#define USE_UV1":"",i.vertexUv2s?"#define USE_UV2":"",i.vertexUv3s?"#define USE_UV3":"",i.pointsUvs?"#define USE_POINTS_UV":"",i.flatShading?"#define FLAT_SHADED":"",i.skinning?"#define USE_SKINNING":"",i.morphTargets?"#define USE_MORPHTARGETS":"",i.morphNormals&&i.flatShading===!1?"#define USE_MORPHNORMALS":"",i.morphColors?"#define USE_MORPHCOLORS":"",i.morphTargetsCount>0?"#define MORPHTARGETS_TEXTURE_STRIDE "+i.morphTextureStride:"",i.morphTargetsCount>0?"#define MORPHTARGETS_COUNT "+i.morphTargetsCount:"",i.doubleSided?"#define DOUBLE_SIDED":"",i.flipSided?"#define FLIP_SIDED":"",i.shadowMapEnabled?"#define USE_SHADOWMAP":"",i.shadowMapEnabled?"#define "+m:"",i.sizeAttenuation?"#define USE_SIZEATTENUATION":"",i.numLightProbes>0?"#define USE_LIGHT_PROBES":"",i.logarithmicDepthBuffer?"#define USE_LOGARITHMIC_DEPTH_BUFFER":"",i.reversedDepthBuffer?"#define USE_REVERSED_DEPTH_BUFFER":"","uniform mat4 modelMatrix;","uniform mat4 modelViewMatrix;","uniform mat4 projectionMatrix;","uniform mat4 viewMatrix;","uniform mat3 normalMatrix;","uniform vec3 cameraPosition;","uniform bool isOrthographic;","#ifdef USE_INSTANCING","	attribute mat4 instanceMatrix;","#endif","#ifdef USE_INSTANCING_COLOR","	attribute vec3 instanceColor;","#endif","#ifdef USE_INSTANCING_MORPH","	uniform sampler2D morphTexture;","#endif","attribute vec3 position;","attribute vec3 normal;","attribute vec2 uv;","#ifdef USE_UV1","	attribute vec2 uv1;","#endif","#ifdef USE_UV2","	attribute vec2 uv2;","#endif","#ifdef USE_UV3","	attribute vec2 uv3;","#endif","#ifdef USE_TANGENT","	attribute vec4 tangent;","#endif","#if defined( USE_COLOR_ALPHA )","	attribute vec4 color;","#elif defined( USE_COLOR )","	attribute vec3 color;","#endif","#ifdef USE_SKINNING","	attribute vec4 skinIndex;","	attribute vec4 skinWeight;","#endif",`
`].filter(Hl).join(`
`),y=[j_(i),"#define SHADER_TYPE "+i.shaderType,"#define SHADER_NAME "+i.shaderName,E,i.useFog&&i.fog?"#define USE_FOG":"",i.useFog&&i.fogExp2?"#define FOG_EXP2":"",i.alphaToCoverage?"#define ALPHA_TO_COVERAGE":"",i.map?"#define USE_MAP":"",i.matcap?"#define USE_MATCAP":"",i.envMap?"#define USE_ENVMAP":"",i.envMap?"#define "+p:"",i.envMap?"#define "+g:"",i.envMap?"#define "+_:"",v?"#define CUBEUV_TEXEL_WIDTH "+v.texelWidth:"",v?"#define CUBEUV_TEXEL_HEIGHT "+v.texelHeight:"",v?"#define CUBEUV_MAX_MIP "+v.maxMip+".0":"",i.lightMap?"#define USE_LIGHTMAP":"",i.aoMap?"#define USE_AOMAP":"",i.bumpMap?"#define USE_BUMPMAP":"",i.normalMap?"#define USE_NORMALMAP":"",i.normalMapObjectSpace?"#define USE_NORMALMAP_OBJECTSPACE":"",i.normalMapTangentSpace?"#define USE_NORMALMAP_TANGENTSPACE":"",i.packedNormalMap?"#define USE_PACKED_NORMALMAP":"",i.emissiveMap?"#define USE_EMISSIVEMAP":"",i.anisotropy?"#define USE_ANISOTROPY":"",i.anisotropyMap?"#define USE_ANISOTROPYMAP":"",i.clearcoat?"#define USE_CLEARCOAT":"",i.clearcoatMap?"#define USE_CLEARCOATMAP":"",i.clearcoatRoughnessMap?"#define USE_CLEARCOAT_ROUGHNESSMAP":"",i.clearcoatNormalMap?"#define USE_CLEARCOAT_NORMALMAP":"",i.dispersion?"#define USE_DISPERSION":"",i.retroreflection?"#define USE_RETROREFLECTION":"",i.iridescence?"#define USE_IRIDESCENCE":"",i.iridescenceMap?"#define USE_IRIDESCENCEMAP":"",i.iridescenceThicknessMap?"#define USE_IRIDESCENCE_THICKNESSMAP":"",i.specularMap?"#define USE_SPECULARMAP":"",i.specularColorMap?"#define USE_SPECULAR_COLORMAP":"",i.specularIntensityMap?"#define USE_SPECULAR_INTENSITYMAP":"",i.roughnessMap?"#define USE_ROUGHNESSMAP":"",i.metalnessMap?"#define USE_METALNESSMAP":"",i.alphaMap?"#define USE_ALPHAMAP":"",i.alphaTest?"#define USE_ALPHATEST":"",i.alphaHash?"#define USE_ALPHAHASH":"",i.sheen?"#define USE_SHEEN":"",i.sheenColorMap?"#define USE_SHEEN_COLORMAP":"",i.sheenRoughnessMap?"#define USE_SHEEN_ROUGHNESSMAP":"",i.transmission?"#define USE_TRANSMISSION":"",i.transmissionMap?"#define USE_TRANSMISSIONMAP":"",i.thicknessMap?"#define USE_THICKNESSMAP":"",i.vertexTangents&&i.flatShading===!1?"#define USE_TANGENT":"",i.vertexColors||i.instancingColor?"#define USE_COLOR":"",i.vertexAlphas||i.batchingColor?"#define USE_COLOR_ALPHA":"",i.vertexUv1s?"#define USE_UV1":"",i.vertexUv2s?"#define USE_UV2":"",i.vertexUv3s?"#define USE_UV3":"",i.pointsUvs?"#define USE_POINTS_UV":"",i.gradientMap?"#define USE_GRADIENTMAP":"",i.flatShading?"#define FLAT_SHADED":"",i.doubleSided?"#define DOUBLE_SIDED":"",i.flipSided?"#define FLIP_SIDED":"",i.shadowMapEnabled?"#define USE_SHADOWMAP":"",i.shadowMapEnabled?"#define "+m:"",i.premultipliedAlpha?"#define PREMULTIPLIED_ALPHA":"",i.numLightProbes>0?"#define USE_LIGHT_PROBES":"",i.numLightProbeGrids>0?"#define USE_LIGHT_PROBES_GRID":"",i.decodeVideoTexture?"#define DECODE_VIDEO_TEXTURE":"",i.decodeVideoTextureEmissive?"#define DECODE_VIDEO_TEXTURE_EMISSIVE":"",i.logarithmicDepthBuffer?"#define USE_LOGARITHMIC_DEPTH_BUFFER":"",i.reversedDepthBuffer?"#define USE_REVERSED_DEPTH_BUFFER":"","uniform mat4 viewMatrix;","uniform vec3 cameraPosition;","uniform bool isOrthographic;",i.toneMapping!==Xa?"#define TONE_MAPPING":"",i.toneMapping!==Xa?wt.tonemapping_pars_fragment:"",i.toneMapping!==Xa?UR("toneMapping",i.toneMapping):"",i.dithering?"#define DITHERING":"",i.opaque?"#define OPAQUE":"",wt.colorspace_pars_fragment,wR("linearToOutputTexel",i.outputColorSpace),NR(),i.useDepthPacking?"#define DEPTH_PACKING "+i.depthPacking:"",`
`].filter(Hl).join(`
`)),f=Np(f),f=W_(f,i),f=q_(f,i),h=Np(h),h=W_(h,i),h=q_(h,i),f=Y_(f),h=Y_(h),i.isRawShaderMaterial!==!0&&(F=`#version 300 es
`,M=[x,"#define attribute in","#define varying out","#define texture2D texture"].join(`
`)+`
`+M,y=["#define varying in",i.glslVersion===Qv?"":"layout(location = 0) out highp vec4 pc_fragColor;",i.glslVersion===Qv?"":"#define gl_FragColor pc_fragColor","#define gl_FragDepthEXT gl_FragDepth","#define texture2D texture","#define textureCube texture","#define texture2DProj textureProj","#define texture2DLodEXT textureLod","#define texture2DProjLodEXT textureProjLod","#define textureCubeLodEXT textureLod","#define texture2DGradEXT textureGrad","#define texture2DProjGradEXT textureProjGrad","#define textureCubeGradEXT textureGrad"].join(`
`)+`
`+y);const V=F+M+f,R=F+y+h,N=V_(l,l.VERTEX_SHADER,V),L=V_(l,l.FRAGMENT_SHADER,R);l.attachShader(D,N),l.attachShader(D,L),i.index0AttributeName!==void 0?l.bindAttribLocation(D,0,i.index0AttributeName):i.hasPositionAttribute===!0&&l.bindAttribLocation(D,0,"position"),l.linkProgram(D);function P(k){if(s.debug.checkShaderErrors){const J=l.getProgramInfoLog(D)||"",se=l.getShaderInfoLog(N)||"",Y=l.getShaderInfoLog(L)||"",j=J.trim(),z=se.trim(),H=Y.trim();let ee=!0,oe=!0;if(l.getProgramParameter(D,l.LINK_STATUS)===!1)if(ee=!1,typeof s.debug.onShaderError=="function")s.debug.onShaderError(l,D,N,L);else{const fe=X_(l,N,"vertex"),U=X_(l,L,"fragment");Zt("WebGLProgram: Shader Error "+l.getError()+" - VALIDATE_STATUS "+l.getProgramParameter(D,l.VALIDATE_STATUS)+`

Material Name: `+k.name+`
Material Type: `+k.type+`

Program Info Log: `+j+`
`+fe+`
`+U)}else j!==""?ht("WebGLProgram: Program Info Log:",j):(z===""||H==="")&&(oe=!1);oe&&(k.diagnostics={runnable:ee,programLog:j,vertexShader:{log:z,prefix:M},fragmentShader:{log:H,prefix:y}})}l.deleteShader(N),l.deleteShader(L),T=new Iu(l,D),O=PR(l,D)}let T;this.getUniforms=function(){return T===void 0&&P(this),T};let O;this.getAttributes=function(){return O===void 0&&P(this),O};let B=i.rendererExtensionParallelShaderCompile===!1;return this.isReady=function(){return B===!1&&(B=l.getProgramParameter(D,TR)),B},this.destroy=function(){r.releaseStatesOfProgram(this),l.deleteProgram(D),this.program=void 0},this.type=i.shaderType,this.name=i.shaderName,this.id=AR++,this.cacheKey=e,this.usedTimes=1,this.program=D,this.vertexShader=N,this.fragmentShader=L,this}let QR=0;class JR{constructor(){this.shaderCache=new Map,this.materialCache=new Map}update(e,i,r){const l=this._getShaderCacheForMaterial(e);return l.has(i)===!1&&(l.add(i),i.usedTimes++),l.has(r)===!1&&(l.add(r),r.usedTimes++),this}remove(e){const i=this.materialCache.get(e);for(const r of i)r.usedTimes--,r.usedTimes===0&&this.shaderCache.delete(r.code);return this.materialCache.delete(e),this}getVertexShaderStage(e){return this._getShaderStage(e.vertexShader)}getFragmentShaderStage(e){return this._getShaderStage(e.fragmentShader)}dispose(){this.shaderCache.clear(),this.materialCache.clear()}_getShaderCacheForMaterial(e){const i=this.materialCache;let r=i.get(e);return r===void 0&&(r=new Set,i.set(e,r)),r}_getShaderStage(e){const i=this.shaderCache;let r=i.get(e);return r===void 0&&(r=new $R(e),i.set(e,r)),r}}class $R{constructor(e){this.id=QR++,this.code=e,this.usedTimes=0}}function eC(s){return s===Os||s===Hu||s===Gu}function tC(s,e,i,r,l,c){const f=new Zp,h=new JR,m=new Set,p=[],g=new Map,_=r.logarithmicDepthBuffer;let v=r.precision;const x={MeshDepthMaterial:"depth",MeshDistanceMaterial:"distance",MeshNormalMaterial:"normal",MeshBasicMaterial:"basic",MeshLambertMaterial:"lambert",MeshPhongMaterial:"phong",MeshToonMaterial:"toon",MeshStandardMaterial:"physical",MeshPhysicalMaterial:"physical",MeshMatcapMaterial:"matcap",LineBasicMaterial:"basic",LineDashedMaterial:"dashed",PointsMaterial:"points",ShadowMaterial:"shadow",SpriteMaterial:"sprite"};function E(T){return m.add(T),T===0?"uv":`uv${T}`}function D(T,O,B,k,J,se){const Y=k.fog,j=J.geometry,z=T.isMeshStandardMaterial||T.isMeshLambertMaterial||T.isMeshPhongMaterial?k.environment:null,H=T.isMeshStandardMaterial||T.isMeshLambertMaterial&&!T.envMap||T.isMeshPhongMaterial&&!T.envMap,ee=e.get(T.envMap||z,H),oe=ee&&ee.mapping===Zu?ee.image.height:null,fe=x[T.type];T.precision!==null&&(v=r.getMaxPrecision(T.precision),v!==T.precision&&ht("WebGLProgram.getParameters:",T.precision,"not supported, using",v,"instead."));const U=j.morphAttributes.position||j.morphAttributes.normal||j.morphAttributes.color,re=U!==void 0?U.length:0;let xe=0;j.morphAttributes.position!==void 0&&(xe=1),j.morphAttributes.normal!==void 0&&(xe=2),j.morphAttributes.color!==void 0&&(xe=3);let Ue,Ie,Xe,ue;if(fe){const Qt=Ga[fe];Ue=Qt.vertexShader,Ie=Qt.fragmentShader}else{Ue=T.vertexShader,Ie=T.fragmentShader;const Qt=h.getVertexShaderStage(T),Nt=h.getFragmentShaderStage(T);h.update(T,Qt,Nt),Xe=Qt.id,ue=Nt.id}const ye=s.getRenderTarget(),we=s.state.buffers.depth.getReversed(),at=J.isInstancedMesh===!0,Ge=J.isBatchedMesh===!0,mt=!!T.map,un=!!T.matcap,ut=!!ee,vt=!!T.aoMap,Mt=!!T.lightMap,pt=!!T.bumpMap&&T.wireframe===!1,_t=!!T.normalMap,Gt=!!T.displacementMap,_n=!!T.emissiveMap,Xt=!!T.metalnessMap,fn=!!T.roughnessMap,Z=T.anisotropy>0,Ft=T.clearcoat>0,Dt=T.dispersion>0,I=T.retroreflectivity>0,b=T.iridescence>0,K=T.sheen>0,ce=T.transmission>0,ve=Z&&!!T.anisotropyMap,ne=Ft&&!!T.clearcoatMap,Ae=Ft&&!!T.clearcoatNormalMap,pe=Ft&&!!T.clearcoatRoughnessMap,Se=b&&!!T.iridescenceMap,Ne=b&&!!T.iridescenceThicknessMap,Ze=K&&!!T.sheenColorMap,He=K&&!!T.sheenRoughnessMap,Fe=!!T.specularMap,rt=!!T.specularColorMap,lt=!!T.specularIntensityMap,dt=ce&&!!T.transmissionMap,W=ce&&!!T.thicknessMap,Oe=!!T.gradientMap,Me=!!T.alphaMap,Pe=T.alphaTest>0,Ve=!!T.alphaHash,Re=!!T.extensions;let et=Xa;T.toneMapped&&(ye===null||ye.isXRRenderTarget===!0)&&(et=s.toneMapping);const Je={shaderID:fe,shaderType:T.type,shaderName:T.name,vertexShader:Ue,fragmentShader:Ie,defines:T.defines,customVertexShaderID:Xe,customFragmentShaderID:ue,isRawShaderMaterial:T.isRawShaderMaterial===!0,glslVersion:T.glslVersion,precision:v,batching:Ge,batchingColor:Ge&&J._colorsTexture!==null,instancing:at,instancingColor:at&&J.instanceColor!==null,instancingMorph:at&&J.morphTexture!==null,outputColorSpace:ye===null?s.outputColorSpace:ye.isXRRenderTarget===!0?ye.texture.colorSpace:kt.workingColorSpace,alphaToCoverage:!!T.alphaToCoverage,map:mt,matcap:un,envMap:ut,envMapMode:ut&&ee.mapping,envMapCubeUVHeight:oe,aoMap:vt,lightMap:Mt,bumpMap:pt,normalMap:_t,displacementMap:Gt,emissiveMap:_n,normalMapObjectSpace:_t&&T.normalMapType===db,normalMapTangentSpace:_t&&T.normalMapType===Kv,packedNormalMap:_t&&T.normalMapType===Kv&&eC(T.normalMap.format),metalnessMap:Xt,roughnessMap:fn,anisotropy:Z,anisotropyMap:ve,clearcoat:Ft,clearcoatMap:ne,clearcoatNormalMap:Ae,clearcoatRoughnessMap:pe,dispersion:Dt,retroreflection:I,iridescence:b,iridescenceMap:Se,iridescenceThicknessMap:Ne,sheen:K,sheenColorMap:Ze,sheenRoughnessMap:He,specularMap:Fe,specularColorMap:rt,specularIntensityMap:lt,transmission:ce,transmissionMap:dt,thicknessMap:W,gradientMap:Oe,opaque:T.transparent===!1&&T.blending===Io&&T.alphaToCoverage===!1,alphaMap:Me,alphaTest:Pe,alphaHash:Ve,combine:T.combine,mapUv:mt&&E(T.map.channel),aoMapUv:vt&&E(T.aoMap.channel),lightMapUv:Mt&&E(T.lightMap.channel),bumpMapUv:pt&&E(T.bumpMap.channel),normalMapUv:_t&&E(T.normalMap.channel),displacementMapUv:Gt&&E(T.displacementMap.channel),emissiveMapUv:_n&&E(T.emissiveMap.channel),metalnessMapUv:Xt&&E(T.metalnessMap.channel),roughnessMapUv:fn&&E(T.roughnessMap.channel),anisotropyMapUv:ve&&E(T.anisotropyMap.channel),clearcoatMapUv:ne&&E(T.clearcoatMap.channel),clearcoatNormalMapUv:Ae&&E(T.clearcoatNormalMap.channel),clearcoatRoughnessMapUv:pe&&E(T.clearcoatRoughnessMap.channel),iridescenceMapUv:Se&&E(T.iridescenceMap.channel),iridescenceThicknessMapUv:Ne&&E(T.iridescenceThicknessMap.channel),sheenColorMapUv:Ze&&E(T.sheenColorMap.channel),sheenRoughnessMapUv:He&&E(T.sheenRoughnessMap.channel),specularMapUv:Fe&&E(T.specularMap.channel),specularColorMapUv:rt&&E(T.specularColorMap.channel),specularIntensityMapUv:lt&&E(T.specularIntensityMap.channel),transmissionMapUv:dt&&E(T.transmissionMap.channel),thicknessMapUv:W&&E(T.thicknessMap.channel),alphaMapUv:Me&&E(T.alphaMap.channel),vertexTangents:!!j.attributes.tangent&&(_t||Z),vertexNormals:!!j.attributes.normal,vertexColors:T.vertexColors,vertexAlphas:T.vertexColors===!0&&!!j.attributes.color&&j.attributes.color.itemSize===4,pointsUvs:J.isPoints===!0&&!!j.attributes.uv&&(mt||Me),fog:!!Y,useFog:T.fog===!0,fogExp2:!!Y&&Y.isFogExp2,flatShading:T.wireframe===!1&&(T.flatShading===!0||j.attributes.normal===void 0&&_t===!1&&(T.isMeshLambertMaterial||T.isMeshPhongMaterial||T.isMeshStandardMaterial||T.isMeshPhysicalMaterial)),sizeAttenuation:T.sizeAttenuation===!0,logarithmicDepthBuffer:_,reversedDepthBuffer:we,skinning:J.isSkinnedMesh===!0,hasPositionAttribute:j.attributes.position!==void 0,morphTargets:j.morphAttributes.position!==void 0,morphNormals:j.morphAttributes.normal!==void 0,morphColors:j.morphAttributes.color!==void 0,morphTargetsCount:re,morphTextureStride:xe,numSunLights:O.sun.length,numDirLights:O.directional.length,numPointLights:O.point.length,numSpotLights:O.spot.length,numSpotLightMaps:O.spotLightMap.length,numRectAreaLights:O.rectArea.length,numHemiLights:O.hemi.length,numSunLightShadows:O.sunShadowMap.length,numDirLightShadows:O.directionalShadowMap.length,numPointLightShadows:O.pointShadowMap.length,numSpotLightShadows:O.spotShadowMap.length,numSpotLightShadowsWithMaps:O.numSpotLightShadowsWithMaps,numLightProbes:O.numLightProbes,numLightProbeGrids:se.length,numClippingPlanes:c.numPlanes,numClipIntersection:c.numIntersection,dithering:T.dithering,shadowMapEnabled:s.shadowMap.enabled&&B.length>0,shadowMapType:s.shadowMap.type,toneMapping:et,decodeVideoTexture:mt&&T.map.isVideoTexture===!0&&kt.getTransfer(T.map.colorSpace)===cn,decodeVideoTextureEmissive:_n&&T.emissiveMap.isVideoTexture===!0&&kt.getTransfer(T.emissiveMap.colorSpace)===cn,premultipliedAlpha:T.premultipliedAlpha,doubleSided:T.side===xr,flipSided:T.side===Oi,useDepthPacking:T.depthPacking>=0,depthPacking:T.depthPacking||0,index0AttributeName:T.index0AttributeName,extensionClipCullDistance:Re&&T.extensions.clipCullDistance===!0&&i.has("WEBGL_clip_cull_distance"),extensionMultiDraw:(Re&&T.extensions.multiDraw===!0||Ge)&&i.has("WEBGL_multi_draw"),rendererExtensionParallelShaderCompile:i.has("KHR_parallel_shader_compile"),customProgramCacheKey:T.customProgramCacheKey()};return Je.vertexUv1s=m.has(1),Je.vertexUv2s=m.has(2),Je.vertexUv3s=m.has(3),m.clear(),Je}function M(T){const O=[];if(T.shaderID?O.push(T.shaderID):(O.push(T.customVertexShaderID),O.push(T.customFragmentShaderID)),T.defines!==void 0)for(const B in T.defines)O.push(B),O.push(T.defines[B]);return T.isRawShaderMaterial===!1&&(y(O,T),F(O,T),O.push(s.outputColorSpace)),O.push(T.customProgramCacheKey),O.join()}function y(T,O){T.push(O.precision),T.push(O.outputColorSpace),T.push(O.envMapMode),T.push(O.envMapCubeUVHeight),T.push(O.mapUv),T.push(O.alphaMapUv),T.push(O.lightMapUv),T.push(O.aoMapUv),T.push(O.bumpMapUv),T.push(O.normalMapUv),T.push(O.displacementMapUv),T.push(O.emissiveMapUv),T.push(O.metalnessMapUv),T.push(O.roughnessMapUv),T.push(O.anisotropyMapUv),T.push(O.clearcoatMapUv),T.push(O.clearcoatNormalMapUv),T.push(O.clearcoatRoughnessMapUv),T.push(O.iridescenceMapUv),T.push(O.iridescenceThicknessMapUv),T.push(O.sheenColorMapUv),T.push(O.sheenRoughnessMapUv),T.push(O.specularMapUv),T.push(O.specularColorMapUv),T.push(O.specularIntensityMapUv),T.push(O.transmissionMapUv),T.push(O.thicknessMapUv),T.push(O.combine),T.push(O.fogExp2),T.push(O.sizeAttenuation),T.push(O.morphTargetsCount),T.push(O.morphAttributeCount),T.push(O.numSunLights),T.push(O.numDirLights),T.push(O.numPointLights),T.push(O.numSpotLights),T.push(O.numSpotLightMaps),T.push(O.numHemiLights),T.push(O.numRectAreaLights),T.push(O.numSunLightShadows),T.push(O.numDirLightShadows),T.push(O.numPointLightShadows),T.push(O.numSpotLightShadows),T.push(O.numSpotLightShadowsWithMaps),T.push(O.numLightProbes),T.push(O.shadowMapType),T.push(O.toneMapping),T.push(O.numClippingPlanes),T.push(O.numClipIntersection),T.push(O.depthPacking)}function F(T,O){f.disableAll(),O.instancing&&f.enable(0),O.instancingColor&&f.enable(1),O.instancingMorph&&f.enable(2),O.matcap&&f.enable(3),O.envMap&&f.enable(4),O.normalMapObjectSpace&&f.enable(5),O.normalMapTangentSpace&&f.enable(6),O.clearcoat&&f.enable(7),O.iridescence&&f.enable(8),O.alphaTest&&f.enable(9),O.vertexColors&&f.enable(10),O.vertexAlphas&&f.enable(11),O.vertexUv1s&&f.enable(12),O.vertexUv2s&&f.enable(13),O.vertexUv3s&&f.enable(14),O.vertexTangents&&f.enable(15),O.anisotropy&&f.enable(16),O.alphaHash&&f.enable(17),O.batching&&f.enable(18),O.dispersion&&f.enable(19),O.retroreflection&&f.enable(24),O.batchingColor&&f.enable(20),O.gradientMap&&f.enable(21),O.packedNormalMap&&f.enable(22),O.vertexNormals&&f.enable(23),T.push(f.mask),f.disableAll(),O.fog&&f.enable(0),O.useFog&&f.enable(1),O.flatShading&&f.enable(2),O.logarithmicDepthBuffer&&f.enable(3),O.reversedDepthBuffer&&f.enable(4),O.skinning&&f.enable(5),O.morphTargets&&f.enable(6),O.morphNormals&&f.enable(7),O.morphColors&&f.enable(8),O.premultipliedAlpha&&f.enable(9),O.shadowMapEnabled&&f.enable(10),O.doubleSided&&f.enable(11),O.flipSided&&f.enable(12),O.useDepthPacking&&f.enable(13),O.dithering&&f.enable(14),O.transmission&&f.enable(15),O.sheen&&f.enable(16),O.opaque&&f.enable(17),O.pointsUvs&&f.enable(18),O.decodeVideoTexture&&f.enable(19),O.decodeVideoTextureEmissive&&f.enable(20),O.alphaToCoverage&&f.enable(21),O.numLightProbeGrids>0&&f.enable(22),O.hasPositionAttribute&&f.enable(23),T.push(f.mask)}function V(T){const O=x[T.type];let B;if(O){const k=Ga[O];B=_E.clone(k.uniforms)}else B=T.uniforms;return B}function R(T,O){let B=g.get(O);return B!==void 0?++B.usedTimes:(B=new KR(s,O,T,l),p.push(B),g.set(O,B)),B}function N(T){if(--T.usedTimes===0){const O=p.indexOf(T);p[O]=p[p.length-1],p.pop(),g.delete(T.cacheKey),T.destroy()}}function L(T){h.remove(T)}function P(){h.dispose()}return{getParameters:D,getProgramCacheKey:M,getUniforms:V,acquireProgram:R,releaseProgram:N,releaseShaderCache:L,programs:p,dispose:P}}function nC(){let s=new WeakMap;function e(f){return s.has(f)}function i(f){let h=s.get(f);return h===void 0&&(h={},s.set(f,h)),h}function r(f){s.delete(f)}function l(f,h,m){s.get(f)[h]=m}function c(){s=new WeakMap}return{has:e,get:i,remove:r,update:l,dispose:c}}function iC(s,e){return s.groupOrder!==e.groupOrder?s.groupOrder-e.groupOrder:s.renderOrder!==e.renderOrder?s.renderOrder-e.renderOrder:s.material.id!==e.material.id?s.material.id-e.material.id:s.materialVariant!==e.materialVariant?s.materialVariant-e.materialVariant:s.z!==e.z?s.z-e.z:s.id-e.id}function Z_(s,e){return s.groupOrder!==e.groupOrder?s.groupOrder-e.groupOrder:s.renderOrder!==e.renderOrder?s.renderOrder-e.renderOrder:s.z!==e.z?e.z-s.z:s.id-e.id}function K_(){const s=[];let e=0;const i=[],r=[],l=[];function c(){e=0,i.length=0,r.length=0,l.length=0}function f(v){let x=0;return v.isInstancedMesh&&(x+=2),v.isSkinnedMesh&&(x+=1),x}function h(v,x,E,D,M,y){let F=s[e];return F===void 0?(F={id:v.id,object:v,geometry:x,material:E,materialVariant:f(v),groupOrder:D,renderOrder:v.renderOrder,z:M,group:y},s[e]=F):(F.id=v.id,F.object=v,F.geometry=x,F.material=E,F.materialVariant=f(v),F.groupOrder=D,F.renderOrder=v.renderOrder,F.z=M,F.group=y),e++,F}function m(v,x,E,D,M,y,F){F.reversedDepth===!0&&(M=-M);const V=h(v,x,E,D,M,y);E.transmission>0?r.push(V):E.transparent===!0?l.push(V):i.push(V)}function p(v,x,E,D,M,y){const F=h(v,x,E,D,M,y);E.transmission>0?r.unshift(F):E.transparent===!0?l.unshift(F):i.unshift(F)}function g(v,x){i.length>1&&i.sort(v||iC),r.length>1&&r.sort(x||Z_),l.length>1&&l.sort(x||Z_)}function _(){for(let v=e,x=s.length;v<x;v++){const E=s[v];if(E.id===null)break;E.id=null,E.object=null,E.geometry=null,E.material=null,E.group=null}}return{opaque:i,transmissive:r,transparent:l,init:c,push:m,unshift:p,finish:_,sort:g}}function aC(){let s=new WeakMap;function e(r,l){const c=s.get(r);let f;return c===void 0?(f=new K_,s.set(r,[f])):l>=c.length?(f=new K_,c.push(f)):f=c[l],f}function i(){s=new WeakMap}return{get:e,dispose:i}}function rC(){const s={};return{get:function(e){if(s[e.id]!==void 0)return s[e.id];let i;switch(e.type){case"SunLight":case"DirectionalLight":i={direction:new Q,color:new Rt};break;case"SpotLight":i={position:new Q,direction:new Q,color:new Rt,distance:0,coneCos:0,penumbraCos:0,decay:0};break;case"PointLight":i={position:new Q,color:new Rt,distance:0,decay:0};break;case"HemisphereLight":i={direction:new Q,skyColor:new Rt,groundColor:new Rt};break;case"RectAreaLight":i={color:new Rt,position:new Q,halfWidth:new Q,halfHeight:new Q};break}return s[e.id]=i,i}}}function sC(){const s={};return{get:function(e){if(s[e.id]!==void 0)return s[e.id];let i;switch(e.type){case"SunLight":case"DirectionalLight":i={shadowIntensity:1,shadowBias:0,shadowNormalBias:0,shadowRadius:1,shadowMapSize:new Kt};break;case"SpotLight":i={shadowIntensity:1,shadowBias:0,shadowNormalBias:0,shadowRadius:1,shadowMapSize:new Kt};break;case"PointLight":i={shadowIntensity:1,shadowBias:0,shadowNormalBias:0,shadowRadius:1,shadowMapSize:new Kt,shadowCameraNear:1,shadowCameraFar:1e3};break}return s[e.id]=i,i}}}let oC=0;function lC(s,e){return(e.castShadow?2:0)-(s.castShadow?2:0)+(e.map?1:0)-(s.map?1:0)}function cC(s){const e=new rC,i=sC(),r={version:0,hash:{sunLength:-1,directionalLength:-1,pointLength:-1,spotLength:-1,rectAreaLength:-1,hemiLength:-1,numSunShadows:-1,numDirectionalShadows:-1,numPointShadows:-1,numSpotShadows:-1,numSpotMaps:-1,numLightProbes:-1},ambient:[0,0,0],probe:[],sun:[],sunShadow:[],sunShadowMap:[],sunShadowMatrix:[],sunShadowCascade:[],directional:[],directionalShadow:[],directionalShadowMap:[],directionalShadowMatrix:[],spot:[],spotLightMap:[],spotShadow:[],spotShadowMap:[],spotLightMatrix:[],rectArea:[],rectAreaLTC1:null,rectAreaLTC2:null,point:[],pointShadow:[],pointShadowMap:[],pointShadowMatrix:[],hemi:[],numSpotLightShadowsWithMaps:0,numLightProbes:0};for(let p=0;p<9;p++)r.probe.push(new Q);const l=new Q,c=new En,f=new En;function h(p){let g=0,_=0,v=0;for(let J=0;J<9;J++)r.probe[J].set(0,0,0);let x=0,E=0,D=0,M=0,y=0,F=0,V=0,R=0,N=0,L=0,P=0,T=0,O=0,B=0;p.sort(lC);for(let J=0,se=p.length;J<se;J++){const Y=p[J],j=Y.color,z=Y.intensity,H=Y.distance;let ee=null;if(Y.shadow&&Y.shadow.map&&(Y.shadow.map.texture.format===Os?ee=Y.shadow.map.texture:ee=Y.shadow.map.depthTexture||Y.shadow.map.texture),Y.isAmbientLight)g+=j.r*z,_+=j.g*z,v+=j.b*z;else if(Y.isLightProbe){for(let oe=0;oe<9;oe++)r.probe[oe].addScaledVector(Y.sh.coefficients[oe],z);B++}else if(Y.isSunLight){const oe=e.get(Y);if(oe.color.copy(Y.color).multiplyScalar(Y.intensity),Y.castShadow){const fe=Y.shadow,U=i.get(Y);U.shadowIntensity=fe.intensity,U.shadowBias=fe.bias,U.shadowNormalBias=fe.normalBias,U.shadowRadius=fe.radius,U.shadowMapSize.copy(fe.mapSize).multiply(fe.getFrameExtents()),r.sunShadow[E]=U,r.sunShadowMap[E]=ee;const re=fe.getViewportCount();for(let xe=0;xe<re;xe++)r.sunShadowMatrix[D+xe]=fe.getMatrix(xe),r.sunShadowCascade[D+xe]=fe._cascadeData[xe];D+=re,E++}r.sun[x]=oe,x++}else if(Y.isDirectionalLight){const oe=e.get(Y);if(oe.color.copy(Y.color).multiplyScalar(Y.intensity),Y.castShadow){const fe=Y.shadow,U=i.get(Y);U.shadowIntensity=fe.intensity,U.shadowBias=fe.bias,U.shadowNormalBias=fe.normalBias,U.shadowRadius=fe.radius,U.shadowMapSize=fe.mapSize,r.directionalShadow[M]=U,r.directionalShadowMap[M]=ee,r.directionalShadowMatrix[M]=Y.shadow.matrix,N++}r.directional[M]=oe,M++}else if(Y.isSpotLight){const oe=e.get(Y);oe.position.setFromMatrixPosition(Y.matrixWorld),oe.color.copy(j).multiplyScalar(z),oe.distance=H,oe.coneCos=Math.cos(Y.angle),oe.penumbraCos=Math.cos(Y.angle*(1-Y.penumbra)),oe.decay=Y.decay,r.spot[F]=oe;const fe=Y.shadow;if(Y.map&&(r.spotLightMap[T]=Y.map,T++,fe.updateMatrices(Y),Y.castShadow&&O++),r.spotLightMatrix[F]=fe.matrix,Y.castShadow){const U=i.get(Y);U.shadowIntensity=fe.intensity,U.shadowBias=fe.bias,U.shadowNormalBias=fe.normalBias,U.shadowRadius=fe.radius,U.shadowMapSize=fe.mapSize,r.spotShadow[F]=U,r.spotShadowMap[F]=ee,P++}F++}else if(Y.isRectAreaLight){const oe=e.get(Y);oe.color.copy(j).multiplyScalar(z),oe.halfWidth.set(Y.width*.5,0,0),oe.halfHeight.set(0,Y.height*.5,0),r.rectArea[V]=oe,V++}else if(Y.isPointLight){const oe=e.get(Y);if(oe.color.copy(Y.color).multiplyScalar(Y.intensity),oe.distance=Y.distance,oe.decay=Y.decay,Y.castShadow){const fe=Y.shadow,U=i.get(Y);U.shadowIntensity=fe.intensity,U.shadowBias=fe.bias,U.shadowNormalBias=fe.normalBias,U.shadowRadius=fe.radius,U.shadowMapSize=fe.mapSize,U.shadowCameraNear=fe.camera.near,U.shadowCameraFar=fe.camera.far,r.pointShadow[y]=U,r.pointShadowMap[y]=ee,r.pointShadowMatrix[y]=Y.shadow.matrix,L++}r.point[y]=oe,y++}else if(Y.isHemisphereLight){const oe=e.get(Y);oe.skyColor.copy(Y.color).multiplyScalar(z),oe.groundColor.copy(Y.groundColor).multiplyScalar(z),r.hemi[R]=oe,R++}}V>0&&(s.has("OES_texture_float_linear")===!0?(r.rectAreaLTC1=je.LTC_FLOAT_1,r.rectAreaLTC2=je.LTC_FLOAT_2):(r.rectAreaLTC1=je.LTC_HALF_1,r.rectAreaLTC2=je.LTC_HALF_2)),r.ambient[0]=g,r.ambient[1]=_,r.ambient[2]=v;const k=r.hash;(k.sunLength!==x||k.directionalLength!==M||k.pointLength!==y||k.spotLength!==F||k.rectAreaLength!==V||k.hemiLength!==R||k.numSunShadows!==E||k.numDirectionalShadows!==N||k.numPointShadows!==L||k.numSpotShadows!==P||k.numSpotMaps!==T||k.numLightProbes!==B)&&(r.sun.length=x,r.directional.length=M,r.spot.length=F,r.rectArea.length=V,r.point.length=y,r.hemi.length=R,r.sunShadow.length=E,r.sunShadowMap.length=E,r.sunShadowMatrix.length=D,r.sunShadowCascade.length=D,r.directionalShadow.length=N,r.directionalShadowMap.length=N,r.directionalShadowMatrix.length=N,r.pointShadow.length=L,r.pointShadowMap.length=L,r.pointShadowMatrix.length=L,r.spotShadow.length=P,r.spotShadowMap.length=P,r.spotLightMatrix.length=P+T-O,r.spotLightMap.length=T,r.numSpotLightShadowsWithMaps=O,r.numLightProbes=B,k.sunLength=x,k.directionalLength=M,k.pointLength=y,k.spotLength=F,k.rectAreaLength=V,k.hemiLength=R,k.numSunShadows=E,k.numDirectionalShadows=N,k.numPointShadows=L,k.numSpotShadows=P,k.numSpotMaps=T,k.numLightProbes=B,r.version=oC++)}function m(p,g){let _=0,v=0,x=0,E=0,D=0,M=0;const y=g.matrixWorldInverse;for(let F=0,V=p.length;F<V;F++){const R=p[F];if(R.isSunLight){const N=r.sun[_];N.direction.setFromMatrixPosition(R.matrixWorld),N.direction.transformDirection(y),_++}else if(R.isDirectionalLight){const N=r.directional[v];N.direction.setFromMatrixPosition(R.matrixWorld),l.setFromMatrixPosition(R.target.matrixWorld),N.direction.sub(l),N.direction.transformDirection(y),v++}else if(R.isSpotLight){const N=r.spot[E];N.position.setFromMatrixPosition(R.matrixWorld),N.position.applyMatrix4(y),N.direction.setFromMatrixPosition(R.matrixWorld),l.setFromMatrixPosition(R.target.matrixWorld),N.direction.sub(l),N.direction.transformDirection(y),E++}else if(R.isRectAreaLight){const N=r.rectArea[D];N.position.setFromMatrixPosition(R.matrixWorld),N.position.applyMatrix4(y),f.identity(),c.copy(R.matrixWorld),c.premultiply(y),f.extractRotation(c),N.halfWidth.set(R.width*.5,0,0),N.halfHeight.set(0,R.height*.5,0),N.halfWidth.applyMatrix4(f),N.halfHeight.applyMatrix4(f),D++}else if(R.isPointLight){const N=r.point[x];N.position.setFromMatrixPosition(R.matrixWorld),N.position.applyMatrix4(y),x++}else if(R.isHemisphereLight){const N=r.hemi[M];N.direction.setFromMatrixPosition(R.matrixWorld),N.direction.transformDirection(y),M++}}}return{setup:h,setupView:m,state:r}}function Q_(s){const e=new cC(s),i=[],r=[],l=[];function c(v){_.camera=v,i.length=0,r.length=0,l.length=0}function f(v){i.push(v)}function h(v){r.push(v)}function m(v){l.push(v)}function p(){e.setup(i)}function g(v){e.setupView(i,v)}const _={lightsArray:i,shadowsArray:r,lightProbeGridArray:l,camera:null,lights:e,transmissionRenderTarget:{},textureUnits:0};return{init:c,state:_,setupLights:p,setupLightsView:g,pushLight:f,pushShadow:h,pushLightProbeGrid:m}}function uC(s){let e=new WeakMap;function i(l,c=0){const f=e.get(l);let h;return f===void 0?(h=new Q_(s),e.set(l,[h])):c>=f.length?(h=new Q_(s),f.push(h)):h=f[c],h}function r(){e=new WeakMap}return{get:i,dispose:r}}const fC=`void main() {
	gl_Position = vec4( position, 1.0 );
}`,dC=`uniform sampler2D shadow_pass;
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
}`,hC=[new Q(1,0,0),new Q(-1,0,0),new Q(0,1,0),new Q(0,-1,0),new Q(0,0,1),new Q(0,0,-1)],pC=[new Q(0,-1,0),new Q(0,-1,0),new Q(0,0,1),new Q(0,0,-1),new Q(0,-1,0),new Q(0,-1,0)],J_=new En,Fl=new Q,Gh=new Q;function mC(s,e,i){let r=new Ox;const l=new Kt,c=new Kt,f=new Ln,h=new ME,m=new bE,p={},g=i.maxTextureSize,_={[Ns]:Oi,[Oi]:Ns,[xr]:xr},v=new Yn({defines:{VSM_SAMPLES:8},uniforms:{shadow_pass:{value:null},resolution:{value:new Kt},radius:{value:4}},vertexShader:fC,fragmentShader:dC}),x=v.clone();x.defines.HORIZONTAL_PASS=1;const E=new zn;E.setAttribute("position",new Fn(new Float32Array([-1,-1,.5,3,-1,.5,-1,3,.5]),3));const D=new Ki(E,v),M=this;this.enabled=!1,this.autoUpdate=!0,this.needsUpdate=!1,this.type=Uu;let y=this.type;this.render=function(L,P,T){if(M.enabled===!1||M.autoUpdate===!1&&M.needsUpdate===!1||L.length===0)return;this.type===kM&&(ht("WebGLShadowMap: PCFSoftShadowMap has been removed. Using PCFShadowMap instead."),this.type=Uu);const O=s.getRenderTarget(),B=s.getActiveCubeFace(),k=s.getActiveMipmapLevel(),J=s.state;J.setBlending(Mr),J.buffers.depth.getReversed()===!0?J.buffers.color.setClear(0,0,0,0):J.buffers.color.setClear(1,1,1,1),J.buffers.depth.setTest(!0),J.setScissorTest(!1);const se=y!==this.type;se&&P.traverse(function(Y){Y.material&&(Array.isArray(Y.material)?Y.material.forEach(j=>j.needsUpdate=!0):Y.material.needsUpdate=!0)});for(let Y=0,j=L.length;Y<j;Y++){const z=L[Y],H=z.shadow;if(H===void 0){ht("WebGLShadowMap:",z,"has no shadow.");continue}if(H.autoUpdate===!1&&H.needsUpdate===!1)continue;l.copy(H.mapSize);const ee=H.getFrameExtents();l.multiply(ee),c.copy(H.mapSize),(l.x>g||l.y>g)&&(l.x>g&&(c.x=Math.floor(g/ee.x),l.x=c.x*ee.x,H.mapSize.x=c.x),l.y>g&&(c.y=Math.floor(g/ee.y),l.y=c.y*ee.y,H.mapSize.y=c.y));const oe=s.state.buffers.depth.getReversed();if(H.camera._reversedDepth=oe,H.map===null||se===!0){if(H.map!==null&&(H.map.depthTexture!==null&&(H.map.depthTexture.dispose(),H.map.depthTexture=null),H.map.dispose()),this.type===Bl){if(z.isPointLight){ht("WebGLShadowMap: VSM shadow maps are not supported for PointLights. Use PCF or BasicShadowMap instead.");continue}H.map=new wa(l.x,l.y,{format:Os,type:qa,minFilter:mi,magFilter:mi,generateMipmaps:!1}),H.map.texture.name=z.name+".shadowMap",H.map.depthTexture=new Ql(l.x,l.y,Va),H.map.depthTexture.name=z.name+".shadowMapDepth",H.map.depthTexture.format=Er,H.map.depthTexture.compareFunction=null,H.map.depthTexture.minFilter=li,H.map.depthTexture.magFilter=li}else z.isPointLight?(H.map=new kx(l.x),H.map.depthTexture=new fE(l.x,Wa)):(H.map=new wa(l.x,l.y),H.map.depthTexture=new Ql(l.x,l.y,Wa)),H.map.depthTexture.name=z.name+".shadowMap",H.map.depthTexture.format=Er,this.type===Uu?(H.map.depthTexture.compareFunction=oe?qp:Wp,H.map.depthTexture.minFilter=mi,H.map.depthTexture.magFilter=mi):(H.map.depthTexture.compareFunction=null,H.map.depthTexture.minFilter=li,H.map.depthTexture.magFilter=li);H.camera.updateProjectionMatrix()}H.map.isWebGLCubeRenderTarget!==!0&&(H.map.width!==l.x||H.map.height!==l.y)&&H.map.setSize(l.x,l.y);const fe=H.map.isWebGLCubeRenderTarget?6:H.getViewportCount();z.isPointLight!==!0&&H.updateMatrices(z,T);for(let U=0;U<fe;U++){const re=H.getCamera(U);if(z.isPointLight){const xe=H.camera,Ue=H.matrix,Ie=z.distance||xe.far;Ie!==xe.far&&(xe.far=Ie,xe.updateProjectionMatrix()),Fl.setFromMatrixPosition(z.matrixWorld),xe.position.copy(Fl),Gh.copy(xe.position),Gh.add(hC[U]),xe.up.copy(pC[U]),xe.lookAt(Gh),xe.updateMatrixWorld(),Ue.makeTranslation(-Fl.x,-Fl.y,-Fl.z),J_.multiplyMatrices(xe.projectionMatrix,xe.matrixWorldInverse),H._frustum.setFromProjectionMatrix(J_,xe.coordinateSystem,xe.reversedDepth)}if(H.map.isWebGLCubeRenderTarget)s.setRenderTarget(H.map,U),s.clear();else{U===0&&(s.setRenderTarget(H.map),s.clear());const xe=H.getViewport(U);f.set(c.x*xe.x,c.y*xe.y,c.x*xe.z,c.y*xe.w),J.viewport(f)}r=H.getFrustum(U),R(P,T,re,z,this.type)}H.isPointLightShadow!==!0&&this.type===Bl&&F(H,T),H.needsUpdate=!1}y=this.type,M.needsUpdate=!1,s.setRenderTarget(O,B,k)};function F(L,P){const T=e.update(D);v.defines.VSM_SAMPLES!==L.blurSamples&&(v.defines.VSM_SAMPLES=L.blurSamples,x.defines.VSM_SAMPLES=L.blurSamples,v.needsUpdate=!0,x.needsUpdate=!0),L.mapPass===null?L.mapPass=new wa(l.x,l.y,{format:Os,type:qa}):(L.mapPass.width!==L.map.width||L.mapPass.height!==L.map.height)&&L.mapPass.setSize(L.map.width,L.map.height),v.uniforms.shadow_pass.value=L.map.depthTexture,v.uniforms.resolution.value.set(L.map.width,L.map.height),v.uniforms.radius.value=L.radius,s.setRenderTarget(L.mapPass),s.clear(),s.renderBufferDirect(P,null,T,v,D,null),x.uniforms.shadow_pass.value=L.mapPass.texture,x.uniforms.resolution.value.set(L.map.width,L.map.height),x.uniforms.radius.value=L.radius,s.setRenderTarget(L.map),s.clear(),s.renderBufferDirect(P,null,T,x,D,null)}function V(L,P,T,O){let B=null;const k=T.isPointLight===!0?L.customDistanceMaterial:L.customDepthMaterial;if(k!==void 0)B=k;else if(B=T.isPointLight===!0?m:h,s.localClippingEnabled&&P.clipShadows===!0&&Array.isArray(P.clippingPlanes)&&P.clippingPlanes.length!==0||P.displacementMap&&P.displacementScale!==0||P.alphaMap&&P.alphaTest>0||P.map&&P.alphaTest>0||P.alphaToCoverage===!0){const J=B.uuid,se=P.uuid;let Y=p[J];Y===void 0&&(Y={},p[J]=Y);let j=Y[se];j===void 0&&(j=B.clone(),Y[se]=j,P.addEventListener("dispose",N)),B=j}if(B.visible=P.visible,B.wireframe=P.wireframe,O===Bl?B.side=P.shadowSide!==null?P.shadowSide:P.side:B.side=P.shadowSide!==null?P.shadowSide:_[P.side],B.alphaMap=P.alphaMap,B.alphaTest=P.alphaToCoverage===!0?.5:P.alphaTest,B.map=P.map,B.clipShadows=P.clipShadows,B.clippingPlanes=P.clippingPlanes,B.clipIntersection=P.clipIntersection,B.displacementMap=P.displacementMap,B.displacementScale=P.displacementScale,B.displacementBias=P.displacementBias,B.wireframeLinewidth=P.wireframeLinewidth,B.linewidth=P.linewidth,T.isPointLight===!0&&B.isMeshDistanceMaterial===!0){const J=s.properties.get(B);J.light=T}return B}function R(L,P,T,O,B){if(L.visible===!1)return;if(L.layers.test(P.layers)&&(L.isMesh||L.isLine||L.isPoints)&&(L.castShadow||L.receiveShadow&&B===Bl)&&(!L.frustumCulled||L.intersectsFrustum(r))){L.modelViewMatrix.multiplyMatrices(T.matrixWorldInverse,L.matrixWorld);const se=e.update(L),Y=L.material;if(Array.isArray(Y)){const j=se.groups;for(let z=0,H=j.length;z<H;z++){const ee=j[z],oe=Y[ee.materialIndex];if(oe&&oe.visible){const fe=V(L,oe,O,B);L.onBeforeShadow(s,L,P,T,se,fe,ee),s.renderBufferDirect(T,null,se,fe,L,ee),L.onAfterShadow(s,L,P,T,se,fe,ee)}}}else if(Y.visible){const j=V(L,Y,O,B);L.onBeforeShadow(s,L,P,T,se,j,null),s.renderBufferDirect(T,null,se,j,L,null),L.onAfterShadow(s,L,P,T,se,j,null)}}const J=L.children;for(let se=0,Y=J.length;se<Y;se++)R(J[se],P,T,O,B)}function N(L){L.target.removeEventListener("dispose",N);for(const T in p){const O=p[T],B=L.target.uuid;B in O&&(O[B].dispose(),delete O[B])}}}function gC(s,e){function i(){let W=!1;const Oe=new Ln;let Me=null;const Pe=new Ln(0,0,0,0);return{setMask:function(Ve){Me!==Ve&&!W&&(s.colorMask(Ve,Ve,Ve,Ve),Me=Ve)},setLocked:function(Ve){W=Ve},setClear:function(Ve,Re,et,Je,Qt){Qt===!0&&(Ve*=Je,Re*=Je,et*=Je),Oe.set(Ve,Re,et,Je),Pe.equals(Oe)===!1&&(s.clearColor(Ve,Re,et,Je),Pe.copy(Oe))},reset:function(){W=!1,Me=null,Pe.set(-1,0,0,0)}}}function r(){let W=!1,Oe=!1,Me=null,Pe=null,Ve=null;return{setReversed:function(Re){if(Oe!==Re){const et=e.get("EXT_clip_control");Re?et.clipControlEXT(et.LOWER_LEFT_EXT,et.ZERO_TO_ONE_EXT):et.clipControlEXT(et.LOWER_LEFT_EXT,et.NEGATIVE_ONE_TO_ONE_EXT),Oe=Re;const Je=Ve;Ve=null,this.setClear(Je)}},getReversed:function(){return Oe},setTest:function(Re){Re?ye(s.DEPTH_TEST):we(s.DEPTH_TEST)},setMask:function(Re){Me!==Re&&!W&&(s.depthMask(Re),Me=Re)},setFunc:function(Re){if(Oe&&(Re=Eb[Re]),Pe!==Re){switch(Re){case Xh:s.depthFunc(s.NEVER);break;case Wh:s.depthFunc(s.ALWAYS);break;case qh:s.depthFunc(s.LESS);break;case ql:s.depthFunc(s.LEQUAL);break;case Yh:s.depthFunc(s.EQUAL);break;case jh:s.depthFunc(s.GEQUAL);break;case Zh:s.depthFunc(s.GREATER);break;case Kh:s.depthFunc(s.NOTEQUAL);break;default:s.depthFunc(s.LEQUAL)}Pe=Re}},setLocked:function(Re){W=Re},setClear:function(Re){Ve!==Re&&(Ve=Re,Oe&&(Re=1-Re),s.clearDepth(Re))},reset:function(){W=!1,Me=null,Pe=null,Ve=null,Oe=!1}}}function l(){let W=!1,Oe=null,Me=null,Pe=null,Ve=null,Re=null,et=null,Je=null,Qt=null;return{setTest:function(Nt){W||(Nt?ye(s.STENCIL_TEST):we(s.STENCIL_TEST))},setMask:function(Nt){Oe!==Nt&&!W&&(s.stencilMask(Nt),Oe=Nt)},setFunc:function(Nt,ei,ti){(Me!==Nt||Pe!==ei||Ve!==ti)&&(s.stencilFunc(Nt,ei,ti),Me=Nt,Pe=ei,Ve=ti)},setOp:function(Nt,ei,ti){(Re!==Nt||et!==ei||Je!==ti)&&(s.stencilOp(Nt,ei,ti),Re=Nt,et=ei,Je=ti)},setLocked:function(Nt){W=Nt},setClear:function(Nt){Qt!==Nt&&(s.clearStencil(Nt),Qt=Nt)},reset:function(){W=!1,Oe=null,Me=null,Pe=null,Ve=null,Re=null,et=null,Je=null,Qt=null}}}const c=new i,f=new r,h=new l,m=new WeakMap,p=new WeakMap;let g={},_={},v={},x=new WeakMap,E=[],D=null,M=!1,y=null,F=null,V=null,R=null,N=null,L=null,P=null,T=new Rt(0,0,0),O=0,B=!1,k=null,J=null,se=null,Y=null,j=null;const z=s.getParameter(s.MAX_COMBINED_TEXTURE_IMAGE_UNITS);let H=!1,ee=0;const oe=s.getParameter(s.VERSION);oe.indexOf("WebGL")!==-1?(ee=parseFloat(/^WebGL (\d)/.exec(oe)[1]),H=ee>=1):oe.indexOf("OpenGL ES")!==-1&&(ee=parseFloat(/^OpenGL ES (\d)/.exec(oe)[1]),H=ee>=2);let fe=null,U={};const re=s.getParameter(s.SCISSOR_BOX),xe=s.getParameter(s.VIEWPORT),Ue=new Ln().fromArray(re),Ie=new Ln().fromArray(xe);function Xe(W,Oe,Me,Pe){const Ve=new Uint8Array(4),Re=s.createTexture();s.bindTexture(W,Re),s.texParameteri(W,s.TEXTURE_MIN_FILTER,s.NEAREST),s.texParameteri(W,s.TEXTURE_MAG_FILTER,s.NEAREST);for(let et=0;et<Me;et++)W===s.TEXTURE_3D||W===s.TEXTURE_2D_ARRAY?s.texImage3D(Oe,0,s.RGBA,1,1,Pe,0,s.RGBA,s.UNSIGNED_BYTE,Ve):s.texImage2D(Oe+et,0,s.RGBA,1,1,0,s.RGBA,s.UNSIGNED_BYTE,Ve);return Re}const ue={};ue[s.TEXTURE_2D]=Xe(s.TEXTURE_2D,s.TEXTURE_2D,1),ue[s.TEXTURE_CUBE_MAP]=Xe(s.TEXTURE_CUBE_MAP,s.TEXTURE_CUBE_MAP_POSITIVE_X,6),ue[s.TEXTURE_2D_ARRAY]=Xe(s.TEXTURE_2D_ARRAY,s.TEXTURE_2D_ARRAY,1,1),ue[s.TEXTURE_3D]=Xe(s.TEXTURE_3D,s.TEXTURE_3D,1,1),c.setClear(0,0,0,1),f.setClear(1),h.setClear(0),ye(s.DEPTH_TEST),f.setFunc(ql),pt(!1),_t(Yv),ye(s.CULL_FACE),vt(Mr);function ye(W){g[W]!==!0&&(s.enable(W),g[W]=!0)}function we(W){g[W]!==!1&&(s.disable(W),g[W]=!1)}function at(W,Oe){return v[W]!==Oe?(s.bindFramebuffer(W,Oe),v[W]=Oe,W===s.DRAW_FRAMEBUFFER&&(v[s.FRAMEBUFFER]=Oe),W===s.FRAMEBUFFER&&(v[s.DRAW_FRAMEBUFFER]=Oe),!0):!1}function Ge(W,Oe){let Me=E,Pe=!1;if(W){Me=x.get(Oe),Me===void 0&&(Me=[],x.set(Oe,Me));const Ve=W.textures;if(Me.length!==Ve.length||Me[0]!==s.COLOR_ATTACHMENT0){for(let Re=0,et=Ve.length;Re<et;Re++)Me[Re]=s.COLOR_ATTACHMENT0+Re;Me.length=Ve.length,Pe=!0}}else Me[0]!==s.BACK&&(Me[0]=s.BACK,Pe=!0);Pe&&s.drawBuffers(Me)}function mt(W){return D!==W?(s.useProgram(W),D=W,!0):!1}const un={[No]:s.FUNC_ADD,[WM]:s.FUNC_SUBTRACT,[qM]:s.FUNC_REVERSE_SUBTRACT};un[YM]=s.MIN,un[jM]=s.MAX;const ut={[ZM]:s.ZERO,[KM]:s.ONE,[QM]:s.SRC_COLOR,[ux]:s.SRC_ALPHA,[ib]:s.SRC_ALPHA_SATURATE,[tb]:s.DST_COLOR,[$M]:s.DST_ALPHA,[JM]:s.ONE_MINUS_SRC_COLOR,[fx]:s.ONE_MINUS_SRC_ALPHA,[nb]:s.ONE_MINUS_DST_COLOR,[eb]:s.ONE_MINUS_DST_ALPHA,[ab]:s.CONSTANT_COLOR,[rb]:s.ONE_MINUS_CONSTANT_COLOR,[sb]:s.CONSTANT_ALPHA,[ob]:s.ONE_MINUS_CONSTANT_ALPHA};function vt(W,Oe,Me,Pe,Ve,Re,et,Je,Qt,Nt){if(W===Mr){M===!0&&(we(s.BLEND),M=!1);return}if(M===!1&&(ye(s.BLEND),M=!0),W!==XM){if(W!==y||Nt!==B){if((F!==No||N!==No)&&(s.blendEquation(s.FUNC_ADD),F=No,N=No),Nt)switch(W){case Io:s.blendFuncSeparate(s.ONE,s.ONE_MINUS_SRC_ALPHA,s.ONE,s.ONE_MINUS_SRC_ALPHA);break;case Ca:s.blendFunc(s.ONE,s.ONE);break;case jv:s.blendFuncSeparate(s.ZERO,s.ONE_MINUS_SRC_COLOR,s.ZERO,s.ONE);break;case Zv:s.blendFuncSeparate(s.DST_COLOR,s.ONE_MINUS_SRC_ALPHA,s.ZERO,s.ONE);break;default:Zt("WebGLState: Invalid blending: ",W);break}else switch(W){case Io:s.blendFuncSeparate(s.SRC_ALPHA,s.ONE_MINUS_SRC_ALPHA,s.ONE,s.ONE_MINUS_SRC_ALPHA);break;case Ca:s.blendFuncSeparate(s.SRC_ALPHA,s.ONE,s.ONE,s.ONE);break;case jv:Zt("WebGLState: SubtractiveBlending requires material.premultipliedAlpha = true");break;case Zv:Zt("WebGLState: MultiplyBlending requires material.premultipliedAlpha = true");break;default:Zt("WebGLState: Invalid blending: ",W);break}V=null,R=null,L=null,P=null,T.set(0,0,0),O=0,y=W,B=Nt}return}Ve=Ve||Oe,Re=Re||Me,et=et||Pe,(Oe!==F||Ve!==N)&&(s.blendEquationSeparate(un[Oe],un[Ve]),F=Oe,N=Ve),(Me!==V||Pe!==R||Re!==L||et!==P)&&(s.blendFuncSeparate(ut[Me],ut[Pe],ut[Re],ut[et]),V=Me,R=Pe,L=Re,P=et),(Je.equals(T)===!1||Qt!==O)&&(s.blendColor(Je.r,Je.g,Je.b,Qt),T.copy(Je),O=Qt),y=W,B=!1}function Mt(W,Oe){W.side===xr?we(s.CULL_FACE):ye(s.CULL_FACE);let Me=W.side===Oi;Oe&&(Me=!Me),pt(Me),W.blending===Io&&W.transparent===!1?vt(Mr):vt(W.blending,W.blendEquation,W.blendSrc,W.blendDst,W.blendEquationAlpha,W.blendSrcAlpha,W.blendDstAlpha,W.blendColor,W.blendAlpha,W.premultipliedAlpha),f.setFunc(W.depthFunc),f.setTest(W.depthTest),f.setMask(W.depthWrite),c.setMask(W.colorWrite);const Pe=W.stencilWrite;h.setTest(Pe),Pe&&(h.setMask(W.stencilWriteMask),h.setFunc(W.stencilFunc,W.stencilRef,W.stencilFuncMask),h.setOp(W.stencilFail,W.stencilZFail,W.stencilZPass)),_n(W.polygonOffset,W.polygonOffsetFactor,W.polygonOffsetUnits),W.alphaToCoverage===!0?ye(s.SAMPLE_ALPHA_TO_COVERAGE):we(s.SAMPLE_ALPHA_TO_COVERAGE)}function pt(W){k!==W&&(W?s.frontFace(s.CW):s.frontFace(s.CCW),k=W)}function _t(W){W!==GM?(ye(s.CULL_FACE),W!==J&&(W===Yv?s.cullFace(s.BACK):W===VM?s.cullFace(s.FRONT):s.cullFace(s.FRONT_AND_BACK))):we(s.CULL_FACE),J=W}function Gt(W){W!==se&&(H&&s.lineWidth(W),se=W)}function _n(W,Oe,Me){W?(ye(s.POLYGON_OFFSET_FILL),(Y!==Oe||j!==Me)&&(Y=Oe,j=Me,f.getReversed()&&(Oe=-Oe),s.polygonOffset(Oe,Me))):we(s.POLYGON_OFFSET_FILL)}function Xt(W){W?ye(s.SCISSOR_TEST):we(s.SCISSOR_TEST)}function fn(W){W===void 0&&(W=s.TEXTURE0+z-1),fe!==W&&(s.activeTexture(W),fe=W)}function Z(W,Oe,Me){Me===void 0&&(fe===null?Me=s.TEXTURE0+z-1:Me=fe);let Pe=U[Me];Pe===void 0&&(Pe={type:void 0,texture:void 0},U[Me]=Pe),(Pe.type!==W||Pe.texture!==Oe)&&(fe!==Me&&(s.activeTexture(Me),fe=Me),s.bindTexture(W,Oe||ue[W]),Pe.type=W,Pe.texture=Oe)}function Ft(){const W=U[fe];W!==void 0&&W.type!==void 0&&(s.bindTexture(W.type,null),W.type=void 0,W.texture=void 0)}function Dt(){try{s.compressedTexImage2D(...arguments)}catch(W){Zt("WebGLState:",W)}}function I(){try{s.compressedTexImage3D(...arguments)}catch(W){Zt("WebGLState:",W)}}function b(){try{s.texSubImage2D(...arguments)}catch(W){Zt("WebGLState:",W)}}function K(){try{s.texSubImage3D(...arguments)}catch(W){Zt("WebGLState:",W)}}function ce(){try{s.compressedTexSubImage2D(...arguments)}catch(W){Zt("WebGLState:",W)}}function ve(){try{s.compressedTexSubImage3D(...arguments)}catch(W){Zt("WebGLState:",W)}}function ne(){try{s.texStorage2D(...arguments)}catch(W){Zt("WebGLState:",W)}}function Ae(){try{s.texStorage3D(...arguments)}catch(W){Zt("WebGLState:",W)}}function pe(){try{s.texImage2D(...arguments)}catch(W){Zt("WebGLState:",W)}}function Se(){try{s.texImage3D(...arguments)}catch(W){Zt("WebGLState:",W)}}function Ne(W){return _[W]!==void 0?_[W]:s.getParameter(W)}function Ze(W,Oe){_[W]!==Oe&&(s.pixelStorei(W,Oe),_[W]=Oe)}function He(W){Ue.equals(W)===!1&&(s.scissor(W.x,W.y,W.z,W.w),Ue.copy(W))}function Fe(W){Ie.equals(W)===!1&&(s.viewport(W.x,W.y,W.z,W.w),Ie.copy(W))}function rt(W,Oe){let Me=p.get(Oe);Me===void 0&&(Me=new WeakMap,p.set(Oe,Me));let Pe=Me.get(W);Pe===void 0&&(Pe=s.getUniformBlockIndex(Oe,W.name),Me.set(W,Pe))}function lt(W,Oe){const Pe=p.get(Oe).get(W);m.get(Oe)!==Pe&&(s.uniformBlockBinding(Oe,Pe,W.__bindingPointIndex),m.set(Oe,Pe))}function dt(){s.disable(s.BLEND),s.disable(s.CULL_FACE),s.disable(s.DEPTH_TEST),s.disable(s.POLYGON_OFFSET_FILL),s.disable(s.SCISSOR_TEST),s.disable(s.STENCIL_TEST),s.disable(s.SAMPLE_ALPHA_TO_COVERAGE),s.blendEquation(s.FUNC_ADD),s.blendFunc(s.ONE,s.ZERO),s.blendFuncSeparate(s.ONE,s.ZERO,s.ONE,s.ZERO),s.blendColor(0,0,0,0),s.colorMask(!0,!0,!0,!0),s.clearColor(0,0,0,0),s.depthMask(!0),s.depthFunc(s.LESS),f.setReversed(!1),s.clearDepth(1),s.stencilMask(4294967295),s.stencilFunc(s.ALWAYS,0,4294967295),s.stencilOp(s.KEEP,s.KEEP,s.KEEP),s.clearStencil(0),s.cullFace(s.BACK),s.frontFace(s.CCW),s.polygonOffset(0,0),s.activeTexture(s.TEXTURE0),s.bindFramebuffer(s.FRAMEBUFFER,null),s.bindFramebuffer(s.DRAW_FRAMEBUFFER,null),s.bindFramebuffer(s.READ_FRAMEBUFFER,null),s.useProgram(null),s.lineWidth(1),s.scissor(0,0,s.canvas.width,s.canvas.height),s.viewport(0,0,s.canvas.width,s.canvas.height),s.pixelStorei(s.PACK_ALIGNMENT,4),s.pixelStorei(s.UNPACK_ALIGNMENT,4),s.pixelStorei(s.UNPACK_FLIP_Y_WEBGL,!1),s.pixelStorei(s.UNPACK_PREMULTIPLY_ALPHA_WEBGL,!1),s.pixelStorei(s.UNPACK_COLORSPACE_CONVERSION_WEBGL,s.BROWSER_DEFAULT_WEBGL),s.pixelStorei(s.PACK_ROW_LENGTH,0),s.pixelStorei(s.PACK_SKIP_PIXELS,0),s.pixelStorei(s.PACK_SKIP_ROWS,0),s.pixelStorei(s.UNPACK_ROW_LENGTH,0),s.pixelStorei(s.UNPACK_IMAGE_HEIGHT,0),s.pixelStorei(s.UNPACK_SKIP_PIXELS,0),s.pixelStorei(s.UNPACK_SKIP_ROWS,0),s.pixelStorei(s.UNPACK_SKIP_IMAGES,0),g={},_={},fe=null,U={},v={},x=new WeakMap,E=[],D=null,M=!1,y=null,F=null,V=null,R=null,N=null,L=null,P=null,T=new Rt(0,0,0),O=0,B=!1,k=null,J=null,se=null,Y=null,j=null,Ue.set(0,0,s.canvas.width,s.canvas.height),Ie.set(0,0,s.canvas.width,s.canvas.height),c.reset(),f.reset(),h.reset()}return{buffers:{color:c,depth:f,stencil:h},enable:ye,disable:we,bindFramebuffer:at,drawBuffers:Ge,useProgram:mt,setBlending:vt,setMaterial:Mt,setFlipSided:pt,setCullFace:_t,setLineWidth:Gt,setPolygonOffset:_n,setScissorTest:Xt,activeTexture:fn,bindTexture:Z,unbindTexture:Ft,compressedTexImage2D:Dt,compressedTexImage3D:I,texImage2D:pe,texImage3D:Se,pixelStorei:Ze,getParameter:Ne,updateUBOMapping:rt,uniformBlockBinding:lt,texStorage2D:ne,texStorage3D:Ae,texSubImage2D:b,texSubImage3D:K,compressedTexSubImage2D:ce,compressedTexSubImage3D:ve,scissor:He,viewport:Fe,reset:dt}}function vC(s,e,i,r,l,c,f){const h=e.has("WEBGL_multisampled_render_to_texture")?e.get("WEBGL_multisampled_render_to_texture"):null,m=typeof navigator>"u"?!1:/OculusBrowser/g.test(navigator.userAgent),p=new Kt,g=new WeakMap,_=new Set;let v;const x=new WeakMap;let E=!1;try{E=typeof OffscreenCanvas<"u"&&new OffscreenCanvas(1,1).getContext("2d")!==null}catch{}function D(I,b){return E?new OffscreenCanvas(I,b):Zl("canvas")}function M(I,b,K){let ce=1;const ve=Dt(I);if((ve.width>K||ve.height>K)&&(ce=K/Math.max(ve.width,ve.height)),ce<1)if(typeof HTMLImageElement<"u"&&I instanceof HTMLImageElement||typeof HTMLCanvasElement<"u"&&I instanceof HTMLCanvasElement||typeof ImageBitmap<"u"&&I instanceof ImageBitmap||typeof VideoFrame<"u"&&I instanceof VideoFrame){const ne=Math.floor(ce*ve.width),Ae=Math.floor(ce*ve.height);v===void 0&&(v=D(ne,Ae));const pe=b?D(ne,Ae):v;return pe.width=ne,pe.height=Ae,pe.getContext("2d").drawImage(I,0,0,ne,Ae),ht("WebGLRenderer: Texture has been resized from ("+ve.width+"x"+ve.height+") to ("+ne+"x"+Ae+")."),pe}else return"data"in I&&ht("WebGLRenderer: Image in DataTexture is too big ("+ve.width+"x"+ve.height+")."),I;return I}function y(I){return I.generateMipmaps}function F(I){s.generateMipmap(I)}function V(I){return I.isWebGLCubeRenderTarget?s.TEXTURE_CUBE_MAP:I.isWebGL3DRenderTarget?s.TEXTURE_3D:I.isWebGLArrayRenderTarget||I.isCompressedArrayTexture?s.TEXTURE_2D_ARRAY:s.TEXTURE_2D}function R(I,b,K,ce,ve,ne=!1){if(I!==null){if(s[I]!==void 0)return s[I];ht("WebGLRenderer: Attempt to use non-existing WebGL internal format '"+I+"'")}let Ae;ce&&(Ae=e.get("EXT_texture_norm16"),Ae||ht("WebGLRenderer: Unable to use normalized textures without EXT_texture_norm16 extension"));let pe=b;if(b===s.RED&&(K===s.FLOAT&&(pe=s.R32F),K===s.HALF_FLOAT&&(pe=s.R16F),K===s.UNSIGNED_BYTE&&(pe=s.R8),K===s.UNSIGNED_SHORT&&Ae&&(pe=Ae.R16_EXT),K===s.SHORT&&Ae&&(pe=Ae.R16_SNORM_EXT)),b===s.RED_INTEGER&&(K===s.UNSIGNED_BYTE&&(pe=s.R8UI),K===s.UNSIGNED_SHORT&&(pe=s.R16UI),K===s.UNSIGNED_INT&&(pe=s.R32UI),K===s.BYTE&&(pe=s.R8I),K===s.SHORT&&(pe=s.R16I),K===s.INT&&(pe=s.R32I)),b===s.RG&&(K===s.FLOAT&&(pe=s.RG32F),K===s.HALF_FLOAT&&(pe=s.RG16F),K===s.UNSIGNED_BYTE&&(pe=s.RG8),K===s.UNSIGNED_SHORT&&Ae&&(pe=Ae.RG16_EXT),K===s.SHORT&&Ae&&(pe=Ae.RG16_SNORM_EXT)),b===s.RG_INTEGER&&(K===s.UNSIGNED_BYTE&&(pe=s.RG8UI),K===s.UNSIGNED_SHORT&&(pe=s.RG16UI),K===s.UNSIGNED_INT&&(pe=s.RG32UI),K===s.BYTE&&(pe=s.RG8I),K===s.SHORT&&(pe=s.RG16I),K===s.INT&&(pe=s.RG32I)),b===s.RGB_INTEGER&&(K===s.UNSIGNED_BYTE&&(pe=s.RGB8UI),K===s.UNSIGNED_SHORT&&(pe=s.RGB16UI),K===s.UNSIGNED_INT&&(pe=s.RGB32UI),K===s.BYTE&&(pe=s.RGB8I),K===s.SHORT&&(pe=s.RGB16I),K===s.INT&&(pe=s.RGB32I)),b===s.RGBA_INTEGER&&(K===s.UNSIGNED_BYTE&&(pe=s.RGBA8UI),K===s.UNSIGNED_SHORT&&(pe=s.RGBA16UI),K===s.UNSIGNED_INT&&(pe=s.RGBA32UI),K===s.BYTE&&(pe=s.RGBA8I),K===s.SHORT&&(pe=s.RGBA16I),K===s.INT&&(pe=s.RGBA32I)),b===s.RGB&&(K===s.UNSIGNED_SHORT&&Ae&&(pe=Ae.RGB16_EXT),K===s.SHORT&&Ae&&(pe=Ae.RGB16_SNORM_EXT),K===s.UNSIGNED_INT_5_9_9_9_REV&&(pe=s.RGB9_E5),K===s.UNSIGNED_INT_10F_11F_11F_REV&&(pe=s.R11F_G11F_B10F)),b===s.RGBA){const Se=ne?ku:kt.getTransfer(ve);K===s.FLOAT&&(pe=s.RGBA32F),K===s.HALF_FLOAT&&(pe=s.RGBA16F),K===s.UNSIGNED_BYTE&&(pe=Se===cn?s.SRGB8_ALPHA8:s.RGBA8),K===s.UNSIGNED_SHORT&&Ae&&(pe=Ae.RGBA16_EXT),K===s.SHORT&&Ae&&(pe=Ae.RGBA16_SNORM_EXT),K===s.UNSIGNED_SHORT_4_4_4_4&&(pe=s.RGBA4),K===s.UNSIGNED_SHORT_5_5_5_1&&(pe=s.RGB5_A1)}return(pe===s.R16F||pe===s.R32F||pe===s.RG16F||pe===s.RG32F||pe===s.RGBA16F||pe===s.RGBA32F)&&e.get("EXT_color_buffer_float"),pe}function N(I,b){let K;return I?b===null||b===Wa||b===jl?K=s.DEPTH24_STENCIL8:b===Va?K=s.DEPTH32F_STENCIL8:b===Yl&&(K=s.DEPTH24_STENCIL8,ht("DepthTexture: 16 bit depth attachment is not supported with stencil. Using 24-bit attachment.")):b===null||b===Wa||b===jl?K=s.DEPTH_COMPONENT24:b===Va?K=s.DEPTH_COMPONENT32F:b===Yl&&(K=s.DEPTH_COMPONENT16),K}function L(I,b){return y(I)===!0||I.isFramebufferTexture&&I.minFilter!==li&&I.minFilter!==mi?Math.log2(Math.max(b.width,b.height))+1:I.mipmaps!==void 0&&I.mipmaps.length>0?I.mipmaps.length:I.isCompressedTexture&&Array.isArray(I.image)?b.mipmaps.length:1}function P(I){const b=I.target;b.removeEventListener("dispose",P),O(b),b.isVideoTexture&&g.delete(b),b.isHTMLTexture&&_.delete(b)}function T(I){const b=I.target;b.removeEventListener("dispose",T),k(b)}function O(I){const b=r.get(I);if(b.__webglInit===void 0)return;const K=I.source,ce=x.get(K);if(ce){const ve=ce[b.__cacheKey];ve.usedTimes--,ve.usedTimes===0&&B(I),Object.keys(ce).length===0&&x.delete(K)}r.remove(I)}function B(I){const b=r.get(I);s.deleteTexture(b.__webglTexture);const K=I.source,ce=x.get(K);delete ce[b.__cacheKey],f.memory.textures--}function k(I){const b=r.get(I);if(I.depthTexture&&(I.depthTexture.dispose(),r.remove(I.depthTexture)),I.isWebGLCubeRenderTarget)for(let ce=0;ce<6;ce++){if(Array.isArray(b.__webglFramebuffer[ce]))for(let ve=0;ve<b.__webglFramebuffer[ce].length;ve++)s.deleteFramebuffer(b.__webglFramebuffer[ce][ve]);else s.deleteFramebuffer(b.__webglFramebuffer[ce]);b.__webglDepthbuffer&&s.deleteRenderbuffer(b.__webglDepthbuffer[ce])}else{if(Array.isArray(b.__webglFramebuffer))for(let ce=0;ce<b.__webglFramebuffer.length;ce++)s.deleteFramebuffer(b.__webglFramebuffer[ce]);else s.deleteFramebuffer(b.__webglFramebuffer);if(b.__webglDepthbuffer&&s.deleteRenderbuffer(b.__webglDepthbuffer),b.__webglMultisampledFramebuffer&&s.deleteFramebuffer(b.__webglMultisampledFramebuffer),b.__webglColorRenderbuffer)for(let ce=0;ce<b.__webglColorRenderbuffer.length;ce++)b.__webglColorRenderbuffer[ce]&&s.deleteRenderbuffer(b.__webglColorRenderbuffer[ce]);b.__webglDepthRenderbuffer&&s.deleteRenderbuffer(b.__webglDepthRenderbuffer)}const K=I.textures;for(let ce=0,ve=K.length;ce<ve;ce++){const ne=r.get(K[ce]);ne.__webglTexture&&(s.deleteTexture(ne.__webglTexture),f.memory.textures--),r.remove(K[ce])}r.remove(I)}let J=0;function se(){J=0}function Y(){return J}function j(I){J=I}function z(){const I=J;return I>=l.maxTextures&&ht("WebGLTextures: Trying to use "+(I+1)+" texture units while this GPU supports only "+l.maxTextures),J+=1,I}function H(I){const b=[];return b.push(I.wrapS),b.push(I.wrapT),b.push(I.wrapR||0),b.push(I.magFilter),b.push(I.minFilter),b.push(I.anisotropy),b.push(I.internalFormat),b.push(I.format),b.push(I.type),b.push(I.generateMipmaps),b.push(I.premultiplyAlpha),b.push(I.flipY),b.push(I.unpackAlignment),b.push(I.colorSpace),b.join()}function ee(I,b){const K=r.get(I);if(I.isVideoTexture&&Z(I),I.isRenderTargetTexture===!1&&I.isExternalTexture!==!0&&I.version>0&&K.__version!==I.version){const ce=I.image;if(ce===null)ht("WebGLRenderer: Texture marked for update but no image data found.");else if(ce.complete===!1)ht("WebGLRenderer: Texture marked for update but image is incomplete");else{we(K,I,b);return}}else I.isExternalTexture&&(K.__webglTexture=I.sourceTexture?I.sourceTexture:null);i.bindTexture(s.TEXTURE_2D,K.__webglTexture,s.TEXTURE0+b)}function oe(I,b){const K=r.get(I);if(I.isRenderTargetTexture===!1&&I.version>0&&K.__version!==I.version){we(K,I,b);return}else I.isExternalTexture&&(K.__webglTexture=I.sourceTexture?I.sourceTexture:null);i.bindTexture(s.TEXTURE_2D_ARRAY,K.__webglTexture,s.TEXTURE0+b)}function fe(I,b){const K=r.get(I);if(I.isRenderTargetTexture===!1&&I.version>0&&K.__version!==I.version){we(K,I,b);return}i.bindTexture(s.TEXTURE_3D,K.__webglTexture,s.TEXTURE0+b)}function U(I,b){const K=r.get(I);if(I.isCubeDepthTexture!==!0&&I.version>0&&K.__version!==I.version){at(K,I,b);return}i.bindTexture(s.TEXTURE_CUBE_MAP,K.__webglTexture,s.TEXTURE0+b)}const re={[Qh]:s.REPEAT,[Sr]:s.CLAMP_TO_EDGE,[Jh]:s.MIRRORED_REPEAT},xe={[li]:s.NEAREST,[ub]:s.NEAREST_MIPMAP_NEAREST,[au]:s.NEAREST_MIPMAP_LINEAR,[mi]:s.LINEAR,[oh]:s.LINEAR_MIPMAP_NEAREST,[Cs]:s.LINEAR_MIPMAP_LINEAR},Ue={[pb]:s.NEVER,[xb]:s.ALWAYS,[mb]:s.LESS,[Wp]:s.LEQUAL,[gb]:s.EQUAL,[qp]:s.GEQUAL,[vb]:s.GREATER,[_b]:s.NOTEQUAL};function Ie(I,b){if(b.type===Va&&e.has("OES_texture_float_linear")===!1&&(b.magFilter===mi||b.magFilter===oh||b.magFilter===au||b.magFilter===Cs||b.minFilter===mi||b.minFilter===oh||b.minFilter===au||b.minFilter===Cs)&&ht("WebGLRenderer: Unable to use linear filtering with floating point textures. OES_texture_float_linear not supported on this device."),s.texParameteri(I,s.TEXTURE_WRAP_S,re[b.wrapS]),s.texParameteri(I,s.TEXTURE_WRAP_T,re[b.wrapT]),(I===s.TEXTURE_3D||I===s.TEXTURE_2D_ARRAY)&&s.texParameteri(I,s.TEXTURE_WRAP_R,re[b.wrapR]),s.texParameteri(I,s.TEXTURE_MAG_FILTER,xe[b.magFilter]),s.texParameteri(I,s.TEXTURE_MIN_FILTER,xe[b.minFilter]),b.compareFunction&&(s.texParameteri(I,s.TEXTURE_COMPARE_MODE,s.COMPARE_REF_TO_TEXTURE),s.texParameteri(I,s.TEXTURE_COMPARE_FUNC,Ue[b.compareFunction])),e.has("EXT_texture_filter_anisotropic")===!0){if(b.magFilter===li||b.minFilter!==au&&b.minFilter!==Cs||b.type===Va&&e.has("OES_texture_float_linear")===!1)return;if(b.anisotropy>1||r.get(b).__currentAnisotropy){const K=e.get("EXT_texture_filter_anisotropic");s.texParameterf(I,K.TEXTURE_MAX_ANISOTROPY_EXT,Math.min(b.anisotropy,l.getMaxAnisotropy())),r.get(b).__currentAnisotropy=b.anisotropy}}}function Xe(I,b){let K=!1;I.__webglInit===void 0&&(I.__webglInit=!0,b.addEventListener("dispose",P));const ce=b.source;let ve=x.get(ce);ve===void 0&&(ve={},x.set(ce,ve));const ne=H(b);if(ne!==I.__cacheKey){ve[ne]===void 0&&(ve[ne]={texture:s.createTexture(),usedTimes:0},f.memory.textures++,K=!0),ve[ne].usedTimes++;const Ae=ve[I.__cacheKey];Ae!==void 0&&(ve[I.__cacheKey].usedTimes--,Ae.usedTimes===0&&B(b)),I.__cacheKey=ne,I.__webglTexture=ve[ne].texture}return K}function ue(I,b,K){return Math.floor(Math.floor(I/K)/b)}function ye(I,b,K,ce){const ne=I.updateRanges;if(ne.length===0)i.texSubImage2D(s.TEXTURE_2D,0,0,0,b.width,b.height,K,ce,b.data);else{ne.sort((Ze,He)=>Ze.start-He.start);let Ae=0;for(let Ze=1;Ze<ne.length;Ze++){const He=ne[Ae],Fe=ne[Ze],rt=He.start+He.count,lt=ue(Fe.start,b.width,4),dt=ue(He.start,b.width,4);Fe.start<=rt+1&&lt===dt&&ue(Fe.start+Fe.count-1,b.width,4)===lt?He.count=Math.max(He.count,Fe.start+Fe.count-He.start):(++Ae,ne[Ae]=Fe)}ne.length=Ae+1;const pe=i.getParameter(s.UNPACK_ROW_LENGTH),Se=i.getParameter(s.UNPACK_SKIP_PIXELS),Ne=i.getParameter(s.UNPACK_SKIP_ROWS);i.pixelStorei(s.UNPACK_ROW_LENGTH,b.width);for(let Ze=0,He=ne.length;Ze<He;Ze++){const Fe=ne[Ze],rt=Math.floor(Fe.start/4),lt=Math.ceil(Fe.count/4),dt=rt%b.width,W=Math.floor(rt/b.width),Oe=lt,Me=1;i.pixelStorei(s.UNPACK_SKIP_PIXELS,dt),i.pixelStorei(s.UNPACK_SKIP_ROWS,W),i.texSubImage2D(s.TEXTURE_2D,0,dt,W,Oe,Me,K,ce,b.data)}I.clearUpdateRanges(),i.pixelStorei(s.UNPACK_ROW_LENGTH,pe),i.pixelStorei(s.UNPACK_SKIP_PIXELS,Se),i.pixelStorei(s.UNPACK_SKIP_ROWS,Ne)}}function we(I,b,K){let ce=s.TEXTURE_2D;(b.isDataArrayTexture||b.isCompressedArrayTexture)&&(ce=s.TEXTURE_2D_ARRAY),b.isData3DTexture&&(ce=s.TEXTURE_3D);const ve=Xe(I,b),ne=b.source;i.bindTexture(ce,I.__webglTexture,s.TEXTURE0+K);const Ae=r.get(ne);if(ne.version!==Ae.__version||ve===!0){if(i.activeTexture(s.TEXTURE0+K),(typeof ImageBitmap<"u"&&b.image instanceof ImageBitmap)===!1){const Me=kt.getPrimaries(kt.workingColorSpace),Pe=b.colorSpace===is?null:kt.getPrimaries(b.colorSpace),Ve=b.colorSpace===is||Me===Pe?s.NONE:s.BROWSER_DEFAULT_WEBGL;i.pixelStorei(s.UNPACK_FLIP_Y_WEBGL,b.flipY),i.pixelStorei(s.UNPACK_PREMULTIPLY_ALPHA_WEBGL,b.premultiplyAlpha),i.pixelStorei(s.UNPACK_COLORSPACE_CONVERSION_WEBGL,Ve)}i.pixelStorei(s.UNPACK_ALIGNMENT,b.unpackAlignment);let Se=M(b.image,!1,l.maxTextureSize);Se=Ft(b,Se);const Ne=c.convert(b.format,b.colorSpace),Ze=c.convert(b.type);let He=R(b.internalFormat,Ne,Ze,b.normalized,b.colorSpace,b.isVideoTexture);Ie(ce,b);let Fe;const rt=b.mipmaps,lt=b.isVideoTexture!==!0,dt=Ae.__version===void 0||ve===!0,W=ne.dataReady,Oe=L(b,Se);if(b.isDepthTexture)He=N(b.format===ws,b.type),dt&&(lt?i.texStorage2D(s.TEXTURE_2D,1,He,Se.width,Se.height):i.texImage2D(s.TEXTURE_2D,0,He,Se.width,Se.height,0,Ne,Ze,null));else if(b.isDataTexture)if(rt.length>0){lt&&dt&&i.texStorage2D(s.TEXTURE_2D,Oe,He,rt[0].width,rt[0].height);for(let Me=0,Pe=rt.length;Me<Pe;Me++)Fe=rt[Me],lt?W&&i.texSubImage2D(s.TEXTURE_2D,Me,0,0,Fe.width,Fe.height,Ne,Ze,Fe.data):i.texImage2D(s.TEXTURE_2D,Me,He,Fe.width,Fe.height,0,Ne,Ze,Fe.data);b.generateMipmaps=!1}else lt?(dt&&i.texStorage2D(s.TEXTURE_2D,Oe,He,Se.width,Se.height),W&&ye(b,Se,Ne,Ze)):i.texImage2D(s.TEXTURE_2D,0,He,Se.width,Se.height,0,Ne,Ze,Se.data);else if(b.isCompressedTexture)if(b.isCompressedArrayTexture){lt&&dt&&i.texStorage3D(s.TEXTURE_2D_ARRAY,Oe,He,rt[0].width,rt[0].height,Se.depth);for(let Me=0,Pe=rt.length;Me<Pe;Me++)if(Fe=rt[Me],b.format!==Ra)if(Ne!==null)if(lt){if(W)if(b.layerUpdates.size>0){const Ve=D_(Fe.width,Fe.height,b.format,b.type);for(const Re of b.layerUpdates){const et=Fe.data.subarray(Re*Ve/Fe.data.BYTES_PER_ELEMENT,(Re+1)*Ve/Fe.data.BYTES_PER_ELEMENT);i.compressedTexSubImage3D(s.TEXTURE_2D_ARRAY,Me,0,0,Re,Fe.width,Fe.height,1,Ne,et)}}else i.compressedTexSubImage3D(s.TEXTURE_2D_ARRAY,Me,0,0,0,Fe.width,Fe.height,Se.depth,Ne,Fe.data)}else i.compressedTexImage3D(s.TEXTURE_2D_ARRAY,Me,He,Fe.width,Fe.height,Se.depth,0,Fe.data,0,0);else ht("WebGLRenderer: Attempt to load unsupported compressed texture format in .uploadTexture()");else lt?W&&i.texSubImage3D(s.TEXTURE_2D_ARRAY,Me,0,0,0,Fe.width,Fe.height,Se.depth,Ne,Ze,Fe.data):i.texImage3D(s.TEXTURE_2D_ARRAY,Me,He,Fe.width,Fe.height,Se.depth,0,Ne,Ze,Fe.data);b.layerUpdates.size>0&&b.clearLayerUpdates()}else{lt&&dt&&i.texStorage2D(s.TEXTURE_2D,Oe,He,rt[0].width,rt[0].height);for(let Me=0,Pe=rt.length;Me<Pe;Me++)Fe=rt[Me],b.format!==Ra?Ne!==null?lt?W&&i.compressedTexSubImage2D(s.TEXTURE_2D,Me,0,0,Fe.width,Fe.height,Ne,Fe.data):i.compressedTexImage2D(s.TEXTURE_2D,Me,He,Fe.width,Fe.height,0,Fe.data):ht("WebGLRenderer: Attempt to load unsupported compressed texture format in .uploadTexture()"):lt?W&&i.texSubImage2D(s.TEXTURE_2D,Me,0,0,Fe.width,Fe.height,Ne,Ze,Fe.data):i.texImage2D(s.TEXTURE_2D,Me,He,Fe.width,Fe.height,0,Ne,Ze,Fe.data)}else if(b.isDataArrayTexture)if(lt){if(dt&&i.texStorage3D(s.TEXTURE_2D_ARRAY,Oe,He,Se.width,Se.height,Se.depth),W)if(b.layerUpdates.size>0){const Me=D_(Se.width,Se.height,b.format,b.type);for(const Pe of b.layerUpdates){const Ve=Se.data.subarray(Pe*Me/Se.data.BYTES_PER_ELEMENT,(Pe+1)*Me/Se.data.BYTES_PER_ELEMENT);i.texSubImage3D(s.TEXTURE_2D_ARRAY,0,0,0,Pe,Se.width,Se.height,1,Ne,Ze,Ve)}b.clearLayerUpdates()}else i.texSubImage3D(s.TEXTURE_2D_ARRAY,0,0,0,0,Se.width,Se.height,Se.depth,Ne,Ze,Se.data)}else i.texImage3D(s.TEXTURE_2D_ARRAY,0,He,Se.width,Se.height,Se.depth,0,Ne,Ze,Se.data);else if(b.isData3DTexture)lt?(dt&&i.texStorage3D(s.TEXTURE_3D,Oe,He,Se.width,Se.height,Se.depth),W&&i.texSubImage3D(s.TEXTURE_3D,0,0,0,0,Se.width,Se.height,Se.depth,Ne,Ze,Se.data)):i.texImage3D(s.TEXTURE_3D,0,He,Se.width,Se.height,Se.depth,0,Ne,Ze,Se.data);else if(b.isFramebufferTexture){if(dt)if(lt)i.texStorage2D(s.TEXTURE_2D,Oe,He,Se.width,Se.height);else{let Me=Se.width,Pe=Se.height;for(let Ve=0;Ve<Oe;Ve++)i.texImage2D(s.TEXTURE_2D,Ve,He,Me,Pe,0,Ne,Ze,null),Me>>=1,Pe>>=1}}else if(b.isHTMLTexture){if("texElementImage2D"in s){const Me=s.canvas;if(Me.hasAttribute("layoutsubtree")||Me.setAttribute("layoutsubtree","true"),Se.parentNode!==Me){Me.appendChild(Se),_.add(b),Me.onpaint=Pe=>{const Ve=Pe.changedElements;for(const Re of _)Ve.includes(Re.image)&&(Re.needsUpdate=!0)},Me.requestPaint();return}if(s.texElementImage2D.length===3)s.texElementImage2D(s.TEXTURE_2D,s.RGBA8,Se);else{const Ve=s.RGBA,Re=s.RGBA,et=s.UNSIGNED_BYTE;s.texElementImage2D(s.TEXTURE_2D,0,Ve,Re,et,Se)}s.texParameteri(s.TEXTURE_2D,s.TEXTURE_MIN_FILTER,s.LINEAR),s.texParameteri(s.TEXTURE_2D,s.TEXTURE_WRAP_S,s.CLAMP_TO_EDGE),s.texParameteri(s.TEXTURE_2D,s.TEXTURE_WRAP_T,s.CLAMP_TO_EDGE)}}else if(rt.length>0){if(lt&&dt){const Me=Dt(rt[0]);i.texStorage2D(s.TEXTURE_2D,Oe,He,Me.width,Me.height)}for(let Me=0,Pe=rt.length;Me<Pe;Me++)Fe=rt[Me],lt?W&&i.texSubImage2D(s.TEXTURE_2D,Me,0,0,Ne,Ze,Fe):i.texImage2D(s.TEXTURE_2D,Me,He,Ne,Ze,Fe);b.generateMipmaps=!1}else if(lt){if(dt){const Me=Dt(Se);i.texStorage2D(s.TEXTURE_2D,Oe,He,Me.width,Me.height)}W&&i.texSubImage2D(s.TEXTURE_2D,0,0,0,Ne,Ze,Se)}else i.texImage2D(s.TEXTURE_2D,0,He,Ne,Ze,Se);y(b)&&F(ce),Ae.__version=ne.version,b.onUpdate&&b.onUpdate(b)}I.__version=b.version}function at(I,b,K){if(b.image.length!==6)return;const ce=Xe(I,b),ve=b.source;i.bindTexture(s.TEXTURE_CUBE_MAP,I.__webglTexture,s.TEXTURE0+K);const ne=r.get(ve);if(ve.version!==ne.__version||ce===!0){i.activeTexture(s.TEXTURE0+K);const Ae=kt.getPrimaries(kt.workingColorSpace),pe=b.colorSpace===is?null:kt.getPrimaries(b.colorSpace),Se=b.colorSpace===is||Ae===pe?s.NONE:s.BROWSER_DEFAULT_WEBGL;i.pixelStorei(s.UNPACK_FLIP_Y_WEBGL,b.flipY),i.pixelStorei(s.UNPACK_PREMULTIPLY_ALPHA_WEBGL,b.premultiplyAlpha),i.pixelStorei(s.UNPACK_ALIGNMENT,b.unpackAlignment),i.pixelStorei(s.UNPACK_COLORSPACE_CONVERSION_WEBGL,Se);const Ne=b.isCompressedTexture||b.image[0].isCompressedTexture,Ze=b.image[0]&&b.image[0].isDataTexture,He=[];for(let Re=0;Re<6;Re++)!Ne&&!Ze?He[Re]=M(b.image[Re],!0,l.maxCubemapSize):He[Re]=Ze?b.image[Re].image:b.image[Re],He[Re]=Ft(b,He[Re]);const Fe=He[0],rt=c.convert(b.format,b.colorSpace),lt=c.convert(b.type),dt=R(b.internalFormat,rt,lt,b.normalized,b.colorSpace),W=b.isVideoTexture!==!0,Oe=ne.__version===void 0||ce===!0,Me=ve.dataReady;let Pe=L(b,Fe);Ie(s.TEXTURE_CUBE_MAP,b);let Ve;if(Ne){W&&Oe&&i.texStorage2D(s.TEXTURE_CUBE_MAP,Pe,dt,Fe.width,Fe.height);for(let Re=0;Re<6;Re++){Ve=He[Re].mipmaps;for(let et=0;et<Ve.length;et++){const Je=Ve[et];b.format!==Ra?rt!==null?W?Me&&i.compressedTexSubImage2D(s.TEXTURE_CUBE_MAP_POSITIVE_X+Re,et,0,0,Je.width,Je.height,rt,Je.data):i.compressedTexImage2D(s.TEXTURE_CUBE_MAP_POSITIVE_X+Re,et,dt,Je.width,Je.height,0,Je.data):ht("WebGLRenderer: Attempt to load unsupported compressed texture format in .setTextureCube()"):W?Me&&i.texSubImage2D(s.TEXTURE_CUBE_MAP_POSITIVE_X+Re,et,0,0,Je.width,Je.height,rt,lt,Je.data):i.texImage2D(s.TEXTURE_CUBE_MAP_POSITIVE_X+Re,et,dt,Je.width,Je.height,0,rt,lt,Je.data)}}}else{if(Ve=b.mipmaps,W&&Oe){Ve.length>0&&Pe++;const Re=Dt(He[0]);i.texStorage2D(s.TEXTURE_CUBE_MAP,Pe,dt,Re.width,Re.height)}for(let Re=0;Re<6;Re++)if(Ze){W?Me&&i.texSubImage2D(s.TEXTURE_CUBE_MAP_POSITIVE_X+Re,0,0,0,He[Re].width,He[Re].height,rt,lt,He[Re].data):i.texImage2D(s.TEXTURE_CUBE_MAP_POSITIVE_X+Re,0,dt,He[Re].width,He[Re].height,0,rt,lt,He[Re].data);for(let et=0;et<Ve.length;et++){const Qt=Ve[et].image[Re].image;W?Me&&i.texSubImage2D(s.TEXTURE_CUBE_MAP_POSITIVE_X+Re,et+1,0,0,Qt.width,Qt.height,rt,lt,Qt.data):i.texImage2D(s.TEXTURE_CUBE_MAP_POSITIVE_X+Re,et+1,dt,Qt.width,Qt.height,0,rt,lt,Qt.data)}}else{W?Me&&i.texSubImage2D(s.TEXTURE_CUBE_MAP_POSITIVE_X+Re,0,0,0,rt,lt,He[Re]):i.texImage2D(s.TEXTURE_CUBE_MAP_POSITIVE_X+Re,0,dt,rt,lt,He[Re]);for(let et=0;et<Ve.length;et++){const Je=Ve[et];W?Me&&i.texSubImage2D(s.TEXTURE_CUBE_MAP_POSITIVE_X+Re,et+1,0,0,rt,lt,Je.image[Re]):i.texImage2D(s.TEXTURE_CUBE_MAP_POSITIVE_X+Re,et+1,dt,rt,lt,Je.image[Re])}}}y(b)&&F(s.TEXTURE_CUBE_MAP),ne.__version=ve.version,b.onUpdate&&b.onUpdate(b)}I.__version=b.version}function Ge(I,b,K,ce,ve,ne){const Ae=c.convert(K.format,K.colorSpace),pe=c.convert(K.type),Se=R(K.internalFormat,Ae,pe,K.normalized,K.colorSpace),Ne=r.get(b),Ze=r.get(K);if(Ze.__renderTarget=b,!Ne.__hasExternalTextures){const He=Math.max(1,b.width>>ne),Fe=Math.max(1,b.height>>ne);ve===s.TEXTURE_3D||ve===s.TEXTURE_2D_ARRAY?i.texImage3D(ve,ne,Se,He,Fe,b.depth,0,Ae,pe,null):i.texImage2D(ve,ne,Se,He,Fe,0,Ae,pe,null)}i.bindFramebuffer(s.FRAMEBUFFER,I),fn(b)?h.framebufferTexture2DMultisampleEXT(s.FRAMEBUFFER,ce,ve,Ze.__webglTexture,0,Xt(b)):(ve===s.TEXTURE_2D||ve>=s.TEXTURE_CUBE_MAP_POSITIVE_X&&ve<=s.TEXTURE_CUBE_MAP_NEGATIVE_Z)&&s.framebufferTexture2D(s.FRAMEBUFFER,ce,ve,Ze.__webglTexture,ne),i.bindFramebuffer(s.FRAMEBUFFER,null)}function mt(I,b,K){if(s.bindRenderbuffer(s.RENDERBUFFER,I),b.depthBuffer){const ce=b.depthTexture,ve=ce&&ce.isDepthTexture?ce.type:null,ne=N(b.stencilBuffer,ve),Ae=b.stencilBuffer?s.DEPTH_STENCIL_ATTACHMENT:s.DEPTH_ATTACHMENT;fn(b)?h.renderbufferStorageMultisampleEXT(s.RENDERBUFFER,Xt(b),ne,b.width,b.height):K?s.renderbufferStorageMultisample(s.RENDERBUFFER,Xt(b),ne,b.width,b.height):s.renderbufferStorage(s.RENDERBUFFER,ne,b.width,b.height),s.framebufferRenderbuffer(s.FRAMEBUFFER,Ae,s.RENDERBUFFER,I)}else{const ce=b.textures;for(let ve=0;ve<ce.length;ve++){const ne=ce[ve],Ae=c.convert(ne.format,ne.colorSpace),pe=c.convert(ne.type),Se=R(ne.internalFormat,Ae,pe,ne.normalized,ne.colorSpace);fn(b)?h.renderbufferStorageMultisampleEXT(s.RENDERBUFFER,Xt(b),Se,b.width,b.height):K?s.renderbufferStorageMultisample(s.RENDERBUFFER,Xt(b),Se,b.width,b.height):s.renderbufferStorage(s.RENDERBUFFER,Se,b.width,b.height)}}s.bindRenderbuffer(s.RENDERBUFFER,null)}function un(I,b,K){const ce=b.isWebGLCubeRenderTarget===!0;if(i.bindFramebuffer(s.FRAMEBUFFER,I),!(b.depthTexture&&b.depthTexture.isDepthTexture))throw new Error("THREE.WebGLTextures: renderTarget.depthTexture must be an instance of THREE.DepthTexture.");const ve=r.get(b.depthTexture);if(ve.__renderTarget=b,(!ve.__webglTexture||b.depthTexture.image.width!==b.width||b.depthTexture.image.height!==b.height)&&(b.depthTexture.image.width=b.width,b.depthTexture.image.height=b.height,b.depthTexture.needsUpdate=!0),ce){if(ve.__webglInit===void 0&&(ve.__webglInit=!0,b.depthTexture.addEventListener("dispose",P)),ve.__webglTexture===void 0){ve.__webglTexture=s.createTexture(),i.bindTexture(s.TEXTURE_CUBE_MAP,ve.__webglTexture),Ie(s.TEXTURE_CUBE_MAP,b.depthTexture);const Ne=c.convert(b.depthTexture.format),Ze=c.convert(b.depthTexture.type);let He;b.depthTexture.format===Er?He=s.DEPTH_COMPONENT24:b.depthTexture.format===ws&&(He=s.DEPTH24_STENCIL8);for(let Fe=0;Fe<6;Fe++)s.texImage2D(s.TEXTURE_CUBE_MAP_POSITIVE_X+Fe,0,He,b.width,b.height,0,Ne,Ze,null)}}else ee(b.depthTexture,0);const ne=ve.__webglTexture,Ae=Xt(b),pe=ce?s.TEXTURE_CUBE_MAP_POSITIVE_X+K:s.TEXTURE_2D,Se=b.depthTexture.format===ws?s.DEPTH_STENCIL_ATTACHMENT:s.DEPTH_ATTACHMENT;if(b.depthTexture.format===Er)fn(b)?h.framebufferTexture2DMultisampleEXT(s.FRAMEBUFFER,Se,pe,ne,0,Ae):s.framebufferTexture2D(s.FRAMEBUFFER,Se,pe,ne,0);else if(b.depthTexture.format===ws)fn(b)?h.framebufferTexture2DMultisampleEXT(s.FRAMEBUFFER,Se,pe,ne,0,Ae):s.framebufferTexture2D(s.FRAMEBUFFER,Se,pe,ne,0);else throw new Error("THREE.WebGLTextures: Unknown depthTexture format.")}function ut(I){const b=r.get(I),K=I.isWebGLCubeRenderTarget===!0;if(b.__boundDepthTexture!==I.depthTexture){const ce=I.depthTexture;if(b.__depthDisposeCallback&&b.__depthDisposeCallback(),ce){const ve=()=>{delete b.__boundDepthTexture,delete b.__depthDisposeCallback,ce.removeEventListener("dispose",ve)};ce.addEventListener("dispose",ve),b.__depthDisposeCallback=ve}b.__boundDepthTexture=ce}if(I.depthTexture&&!b.__autoAllocateDepthBuffer)if(K)for(let ce=0;ce<6;ce++)un(b.__webglFramebuffer[ce],I,ce);else{const ce=I.texture.mipmaps;ce&&ce.length>0?un(b.__webglFramebuffer[0],I,0):un(b.__webglFramebuffer,I,0)}else if(K){b.__webglDepthbuffer=[];for(let ce=0;ce<6;ce++)if(i.bindFramebuffer(s.FRAMEBUFFER,b.__webglFramebuffer[ce]),b.__webglDepthbuffer[ce]===void 0)b.__webglDepthbuffer[ce]=s.createRenderbuffer(),mt(b.__webglDepthbuffer[ce],I,!1);else{const ve=I.stencilBuffer?s.DEPTH_STENCIL_ATTACHMENT:s.DEPTH_ATTACHMENT,ne=b.__webglDepthbuffer[ce];s.bindRenderbuffer(s.RENDERBUFFER,ne),s.framebufferRenderbuffer(s.FRAMEBUFFER,ve,s.RENDERBUFFER,ne)}}else{const ce=I.texture.mipmaps;if(ce&&ce.length>0?i.bindFramebuffer(s.FRAMEBUFFER,b.__webglFramebuffer[0]):i.bindFramebuffer(s.FRAMEBUFFER,b.__webglFramebuffer),b.__webglDepthbuffer===void 0)b.__webglDepthbuffer=s.createRenderbuffer(),mt(b.__webglDepthbuffer,I,!1);else{const ve=I.stencilBuffer?s.DEPTH_STENCIL_ATTACHMENT:s.DEPTH_ATTACHMENT,ne=b.__webglDepthbuffer;s.bindRenderbuffer(s.RENDERBUFFER,ne),s.framebufferRenderbuffer(s.FRAMEBUFFER,ve,s.RENDERBUFFER,ne)}}i.bindFramebuffer(s.FRAMEBUFFER,null)}function vt(I,b,K){const ce=r.get(I);b!==void 0&&Ge(ce.__webglFramebuffer,I,I.texture,s.COLOR_ATTACHMENT0,s.TEXTURE_2D,0),K!==void 0&&ut(I)}function Mt(I){const b=I.texture,K=r.get(I),ce=r.get(b);I.addEventListener("dispose",T);const ve=I.textures,ne=I.isWebGLCubeRenderTarget===!0,Ae=ve.length>1;if(Ae||(ce.__webglTexture===void 0&&(ce.__webglTexture=s.createTexture()),ce.__version=b.version,f.memory.textures++),ne){K.__webglFramebuffer=[];for(let pe=0;pe<6;pe++)if(b.mipmaps&&b.mipmaps.length>0){K.__webglFramebuffer[pe]=[];for(let Se=0;Se<b.mipmaps.length;Se++)K.__webglFramebuffer[pe][Se]=s.createFramebuffer()}else K.__webglFramebuffer[pe]=s.createFramebuffer()}else{if(b.mipmaps&&b.mipmaps.length>0){K.__webglFramebuffer=[];for(let pe=0;pe<b.mipmaps.length;pe++)K.__webglFramebuffer[pe]=s.createFramebuffer()}else K.__webglFramebuffer=s.createFramebuffer();if(Ae)for(let pe=0,Se=ve.length;pe<Se;pe++){const Ne=r.get(ve[pe]);Ne.__webglTexture===void 0&&(Ne.__webglTexture=s.createTexture(),f.memory.textures++)}if(I.samples>0&&fn(I)===!1){K.__webglMultisampledFramebuffer=s.createFramebuffer(),K.__webglColorRenderbuffer=[],i.bindFramebuffer(s.FRAMEBUFFER,K.__webglMultisampledFramebuffer);for(let pe=0;pe<ve.length;pe++){const Se=ve[pe];K.__webglColorRenderbuffer[pe]=s.createRenderbuffer(),s.bindRenderbuffer(s.RENDERBUFFER,K.__webglColorRenderbuffer[pe]);const Ne=c.convert(Se.format,Se.colorSpace),Ze=c.convert(Se.type),He=R(Se.internalFormat,Ne,Ze,Se.normalized,Se.colorSpace,I.isXRRenderTarget===!0),Fe=Xt(I);s.renderbufferStorageMultisample(s.RENDERBUFFER,Fe,He,I.width,I.height),s.framebufferRenderbuffer(s.FRAMEBUFFER,s.COLOR_ATTACHMENT0+pe,s.RENDERBUFFER,K.__webglColorRenderbuffer[pe])}s.bindRenderbuffer(s.RENDERBUFFER,null),I.depthBuffer&&(K.__webglDepthRenderbuffer=s.createRenderbuffer(),mt(K.__webglDepthRenderbuffer,I,!0)),i.bindFramebuffer(s.FRAMEBUFFER,null)}}if(ne){i.bindTexture(s.TEXTURE_CUBE_MAP,ce.__webglTexture),Ie(s.TEXTURE_CUBE_MAP,b);for(let pe=0;pe<6;pe++)if(b.mipmaps&&b.mipmaps.length>0)for(let Se=0;Se<b.mipmaps.length;Se++)Ge(K.__webglFramebuffer[pe][Se],I,b,s.COLOR_ATTACHMENT0,s.TEXTURE_CUBE_MAP_POSITIVE_X+pe,Se);else Ge(K.__webglFramebuffer[pe],I,b,s.COLOR_ATTACHMENT0,s.TEXTURE_CUBE_MAP_POSITIVE_X+pe,0);y(b)&&F(s.TEXTURE_CUBE_MAP),i.unbindTexture()}else if(Ae){for(let pe=0,Se=ve.length;pe<Se;pe++){const Ne=ve[pe],Ze=r.get(Ne);let He=s.TEXTURE_2D;(I.isWebGL3DRenderTarget||I.isWebGLArrayRenderTarget)&&(He=I.isWebGL3DRenderTarget?s.TEXTURE_3D:s.TEXTURE_2D_ARRAY),i.bindTexture(He,Ze.__webglTexture),Ie(He,Ne),Ge(K.__webglFramebuffer,I,Ne,s.COLOR_ATTACHMENT0+pe,He,0),y(Ne)&&F(He)}i.unbindTexture()}else{let pe=s.TEXTURE_2D;if((I.isWebGL3DRenderTarget||I.isWebGLArrayRenderTarget)&&(pe=I.isWebGL3DRenderTarget?s.TEXTURE_3D:s.TEXTURE_2D_ARRAY),i.bindTexture(pe,ce.__webglTexture),Ie(pe,b),b.mipmaps&&b.mipmaps.length>0)for(let Se=0;Se<b.mipmaps.length;Se++)Ge(K.__webglFramebuffer[Se],I,b,s.COLOR_ATTACHMENT0,pe,Se);else Ge(K.__webglFramebuffer,I,b,s.COLOR_ATTACHMENT0,pe,0);y(b)&&F(pe),i.unbindTexture()}I.depthBuffer&&ut(I)}function pt(I){const b=I.textures;for(let K=0,ce=b.length;K<ce;K++){const ve=b[K];if(y(ve)){const ne=V(I),Ae=r.get(ve).__webglTexture;i.bindTexture(ne,Ae),F(ne),i.unbindTexture()}}}const _t=[],Gt=[];function _n(I){if(I.samples>0){if(fn(I)===!1){const b=I.textures,K=I.width,ce=I.height;let ve=s.COLOR_BUFFER_BIT;const ne=I.stencilBuffer?s.DEPTH_STENCIL_ATTACHMENT:s.DEPTH_ATTACHMENT,Ae=r.get(I),pe=b.length>1;if(pe)for(let Ne=0;Ne<b.length;Ne++)i.bindFramebuffer(s.FRAMEBUFFER,Ae.__webglMultisampledFramebuffer),s.framebufferRenderbuffer(s.FRAMEBUFFER,s.COLOR_ATTACHMENT0+Ne,s.RENDERBUFFER,null),i.bindFramebuffer(s.FRAMEBUFFER,Ae.__webglFramebuffer),s.framebufferTexture2D(s.DRAW_FRAMEBUFFER,s.COLOR_ATTACHMENT0+Ne,s.TEXTURE_2D,null,0);i.bindFramebuffer(s.READ_FRAMEBUFFER,Ae.__webglMultisampledFramebuffer);const Se=I.texture.mipmaps;Se&&Se.length>0?i.bindFramebuffer(s.DRAW_FRAMEBUFFER,Ae.__webglFramebuffer[0]):i.bindFramebuffer(s.DRAW_FRAMEBUFFER,Ae.__webglFramebuffer);for(let Ne=0;Ne<b.length;Ne++){if(I.resolveDepthBuffer&&(I.depthBuffer&&(ve|=s.DEPTH_BUFFER_BIT),I.stencilBuffer&&I.resolveStencilBuffer&&(ve|=s.STENCIL_BUFFER_BIT)),pe){s.framebufferRenderbuffer(s.READ_FRAMEBUFFER,s.COLOR_ATTACHMENT0,s.RENDERBUFFER,Ae.__webglColorRenderbuffer[Ne]);const Ze=r.get(b[Ne]).__webglTexture;s.framebufferTexture2D(s.DRAW_FRAMEBUFFER,s.COLOR_ATTACHMENT0,s.TEXTURE_2D,Ze,0)}s.blitFramebuffer(0,0,K,ce,0,0,K,ce,ve,s.NEAREST),m===!0&&(_t.length=0,Gt.length=0,_t.push(s.COLOR_ATTACHMENT0+Ne),I.depthBuffer&&I.storeMultisampledDepthBuffer===!1&&(_t.push(ne),Gt.push(ne),s.invalidateFramebuffer(s.DRAW_FRAMEBUFFER,Gt)),s.invalidateFramebuffer(s.READ_FRAMEBUFFER,_t))}if(i.bindFramebuffer(s.READ_FRAMEBUFFER,null),i.bindFramebuffer(s.DRAW_FRAMEBUFFER,null),pe)for(let Ne=0;Ne<b.length;Ne++){i.bindFramebuffer(s.FRAMEBUFFER,Ae.__webglMultisampledFramebuffer),s.framebufferRenderbuffer(s.FRAMEBUFFER,s.COLOR_ATTACHMENT0+Ne,s.RENDERBUFFER,Ae.__webglColorRenderbuffer[Ne]);const Ze=r.get(b[Ne]).__webglTexture;i.bindFramebuffer(s.FRAMEBUFFER,Ae.__webglFramebuffer),s.framebufferTexture2D(s.DRAW_FRAMEBUFFER,s.COLOR_ATTACHMENT0+Ne,s.TEXTURE_2D,Ze,0)}i.bindFramebuffer(s.DRAW_FRAMEBUFFER,Ae.__webglMultisampledFramebuffer)}else if(I.depthBuffer&&I.storeMultisampledDepthBuffer===!1&&m){const b=I.stencilBuffer?s.DEPTH_STENCIL_ATTACHMENT:s.DEPTH_ATTACHMENT;s.invalidateFramebuffer(s.DRAW_FRAMEBUFFER,[b])}}}function Xt(I){return Math.min(l.maxSamples,I.samples)}function fn(I){const b=r.get(I);return I.samples>0&&e.has("WEBGL_multisampled_render_to_texture")===!0&&b.__useRenderToTexture!==!1}function Z(I){const b=f.render.frame;g.get(I)!==b&&(g.set(I,b),I.update())}function Ft(I,b){const K=I.colorSpace,ce=I.format,ve=I.type;return I.isCompressedTexture===!0||I.isVideoTexture===!0||K!==Vu&&K!==is&&(kt.getTransfer(K)===cn?(ce!==Ra||ve!==ha)&&ht("WebGLTextures: sRGB encoded textures have to use RGBAFormat and UnsignedByteType."):Zt("WebGLTextures: Unsupported texture color space:",K)),b}function Dt(I){return typeof HTMLImageElement<"u"&&I instanceof HTMLImageElement?(p.width=I.naturalWidth||I.width,p.height=I.naturalHeight||I.height):typeof VideoFrame<"u"&&I instanceof VideoFrame?(p.width=I.displayWidth,p.height=I.displayHeight):(p.width=I.width,p.height=I.height),p}this.allocateTextureUnit=z,this.resetTextureUnits=se,this.getTextureUnits=Y,this.setTextureUnits=j,this.setTexture2D=ee,this.setTexture2DArray=oe,this.setTexture3D=fe,this.setTextureCube=U,this.rebindTextures=vt,this.setupRenderTarget=Mt,this.updateRenderTargetMipmap=pt,this.updateMultisampleRenderTarget=_n,this.setupDepthRenderbuffer=ut,this.setupFrameBufferTexture=Ge,this.useMultisampledRTT=fn,this.isReversedDepthBuffer=function(){return i.buffers.depth.getReversed()}}function _C(s,e){function i(r,l=is){let c;const f=kt.getTransfer(l);if(r===ha)return s.UNSIGNED_BYTE;if(r===Hp)return s.UNSIGNED_SHORT_4_4_4_4;if(r===Gp)return s.UNSIGNED_SHORT_5_5_5_1;if(r===bx)return s.UNSIGNED_INT_5_9_9_9_REV;if(r===Ex)return s.UNSIGNED_INT_10F_11F_11F_REV;if(r===yx)return s.BYTE;if(r===Mx)return s.SHORT;if(r===Yl)return s.UNSIGNED_SHORT;if(r===Bp)return s.INT;if(r===Wa)return s.UNSIGNED_INT;if(r===Va)return s.FLOAT;if(r===qa)return s.HALF_FLOAT;if(r===Tx)return s.ALPHA;if(r===Ax)return s.RGB;if(r===Ra)return s.RGBA;if(r===Er)return s.DEPTH_COMPONENT;if(r===ws)return s.DEPTH_STENCIL;if(r===Rx)return s.RED;if(r===Vp)return s.RED_INTEGER;if(r===Os)return s.RG;if(r===kp)return s.RG_INTEGER;if(r===Xp)return s.RGBA_INTEGER;if(r===Nu||r===Lu||r===Ou||r===Pu)if(f===cn)if(c=e.get("WEBGL_compressed_texture_s3tc_srgb"),c!==null){if(r===Nu)return c.COMPRESSED_SRGB_S3TC_DXT1_EXT;if(r===Lu)return c.COMPRESSED_SRGB_ALPHA_S3TC_DXT1_EXT;if(r===Ou)return c.COMPRESSED_SRGB_ALPHA_S3TC_DXT3_EXT;if(r===Pu)return c.COMPRESSED_SRGB_ALPHA_S3TC_DXT5_EXT}else return null;else if(c=e.get("WEBGL_compressed_texture_s3tc"),c!==null){if(r===Nu)return c.COMPRESSED_RGB_S3TC_DXT1_EXT;if(r===Lu)return c.COMPRESSED_RGBA_S3TC_DXT1_EXT;if(r===Ou)return c.COMPRESSED_RGBA_S3TC_DXT3_EXT;if(r===Pu)return c.COMPRESSED_RGBA_S3TC_DXT5_EXT}else return null;if(r===$h||r===ep||r===tp||r===np)if(c=e.get("WEBGL_compressed_texture_pvrtc"),c!==null){if(r===$h)return c.COMPRESSED_RGB_PVRTC_4BPPV1_IMG;if(r===ep)return c.COMPRESSED_RGB_PVRTC_2BPPV1_IMG;if(r===tp)return c.COMPRESSED_RGBA_PVRTC_4BPPV1_IMG;if(r===np)return c.COMPRESSED_RGBA_PVRTC_2BPPV1_IMG}else return null;if(r===ip||r===ap||r===rp||r===sp||r===op||r===Hu||r===lp)if(c=e.get("WEBGL_compressed_texture_etc"),c!==null){if(r===ip||r===ap)return f===cn?c.COMPRESSED_SRGB8_ETC2:c.COMPRESSED_RGB8_ETC2;if(r===rp)return f===cn?c.COMPRESSED_SRGB8_ALPHA8_ETC2_EAC:c.COMPRESSED_RGBA8_ETC2_EAC;if(r===sp)return c.COMPRESSED_R11_EAC;if(r===op)return c.COMPRESSED_SIGNED_R11_EAC;if(r===Hu)return c.COMPRESSED_RG11_EAC;if(r===lp)return c.COMPRESSED_SIGNED_RG11_EAC}else return null;if(r===cp||r===up||r===fp||r===dp||r===hp||r===pp||r===mp||r===gp||r===vp||r===_p||r===xp||r===Sp||r===yp||r===Mp)if(c=e.get("WEBGL_compressed_texture_astc"),c!==null){if(r===cp)return f===cn?c.COMPRESSED_SRGB8_ALPHA8_ASTC_4x4_KHR:c.COMPRESSED_RGBA_ASTC_4x4_KHR;if(r===up)return f===cn?c.COMPRESSED_SRGB8_ALPHA8_ASTC_5x4_KHR:c.COMPRESSED_RGBA_ASTC_5x4_KHR;if(r===fp)return f===cn?c.COMPRESSED_SRGB8_ALPHA8_ASTC_5x5_KHR:c.COMPRESSED_RGBA_ASTC_5x5_KHR;if(r===dp)return f===cn?c.COMPRESSED_SRGB8_ALPHA8_ASTC_6x5_KHR:c.COMPRESSED_RGBA_ASTC_6x5_KHR;if(r===hp)return f===cn?c.COMPRESSED_SRGB8_ALPHA8_ASTC_6x6_KHR:c.COMPRESSED_RGBA_ASTC_6x6_KHR;if(r===pp)return f===cn?c.COMPRESSED_SRGB8_ALPHA8_ASTC_8x5_KHR:c.COMPRESSED_RGBA_ASTC_8x5_KHR;if(r===mp)return f===cn?c.COMPRESSED_SRGB8_ALPHA8_ASTC_8x6_KHR:c.COMPRESSED_RGBA_ASTC_8x6_KHR;if(r===gp)return f===cn?c.COMPRESSED_SRGB8_ALPHA8_ASTC_8x8_KHR:c.COMPRESSED_RGBA_ASTC_8x8_KHR;if(r===vp)return f===cn?c.COMPRESSED_SRGB8_ALPHA8_ASTC_10x5_KHR:c.COMPRESSED_RGBA_ASTC_10x5_KHR;if(r===_p)return f===cn?c.COMPRESSED_SRGB8_ALPHA8_ASTC_10x6_KHR:c.COMPRESSED_RGBA_ASTC_10x6_KHR;if(r===xp)return f===cn?c.COMPRESSED_SRGB8_ALPHA8_ASTC_10x8_KHR:c.COMPRESSED_RGBA_ASTC_10x8_KHR;if(r===Sp)return f===cn?c.COMPRESSED_SRGB8_ALPHA8_ASTC_10x10_KHR:c.COMPRESSED_RGBA_ASTC_10x10_KHR;if(r===yp)return f===cn?c.COMPRESSED_SRGB8_ALPHA8_ASTC_12x10_KHR:c.COMPRESSED_RGBA_ASTC_12x10_KHR;if(r===Mp)return f===cn?c.COMPRESSED_SRGB8_ALPHA8_ASTC_12x12_KHR:c.COMPRESSED_RGBA_ASTC_12x12_KHR}else return null;if(r===bp||r===Ep||r===Tp)if(c=e.get("EXT_texture_compression_bptc"),c!==null){if(r===bp)return f===cn?c.COMPRESSED_SRGB_ALPHA_BPTC_UNORM_EXT:c.COMPRESSED_RGBA_BPTC_UNORM_EXT;if(r===Ep)return c.COMPRESSED_RGB_BPTC_SIGNED_FLOAT_EXT;if(r===Tp)return c.COMPRESSED_RGB_BPTC_UNSIGNED_FLOAT_EXT}else return null;if(r===Ap||r===Rp||r===Gu||r===Cp)if(c=e.get("EXT_texture_compression_rgtc"),c!==null){if(r===Ap)return c.COMPRESSED_RED_RGTC1_EXT;if(r===Rp)return c.COMPRESSED_SIGNED_RED_RGTC1_EXT;if(r===Gu)return c.COMPRESSED_RED_GREEN_RGTC2_EXT;if(r===Cp)return c.COMPRESSED_SIGNED_RED_GREEN_RGTC2_EXT}else return null;return r===jl?s.UNSIGNED_INT_24_8:s[r]!==void 0?s[r]:null}return{convert:i}}const xC=`
void main() {

	gl_Position = vec4( position, 1.0 );

}`,SC=`
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

}`;class yC{constructor(){this.texture=null,this.mesh=null,this.depthNear=0,this.depthFar=0}init(e,i){if(this.texture===null){const r=new Ix(e.texture);(e.depthNear!==i.depthNear||e.depthFar!==i.depthFar)&&(this.depthNear=e.depthNear,this.depthFar=e.depthFar),this.texture=r}}getMesh(e){if(this.texture!==null&&this.mesh===null){const i=e.cameras[0].viewport,r=new Yn({vertexShader:xC,fragmentShader:SC,uniforms:{depthColor:{value:this.texture},depthWidth:{value:i.z},depthHeight:{value:i.w}}});this.mesh=new Ki(new ec(20,20),r)}return this.mesh}reset(){this.texture=null,this.mesh=null}getDepthTexture(){return this.texture}}class MC extends Is{constructor(e,i){super();const r=this;let l=null,c=1,f=null,h="local-floor",m=1,p=null,g=null,_=null,v=null,x=null,E=null;const D=typeof XRWebGLBinding<"u",M=new yC,y={},F=i.getContextAttributes();let V=null,R=null;const N=[],L=[],P=new Kt;let T=null,O=null;const B=new Yi;B.viewport=new Ln;const k=new Yi;k.viewport=new Ln;const J=[B,k],se=new wE;let Y=null,j=null;this.cameraAutoUpdate=!0,this.enabled=!1,this.isPresenting=!1,this.getController=function(ue){let ye=N[ue];return ye===void 0&&(ye=new mh,N[ue]=ye),ye.getTargetRaySpace()},this.getControllerGrip=function(ue){let ye=N[ue];return ye===void 0&&(ye=new mh,N[ue]=ye),ye.getGripSpace()},this.getHand=function(ue){let ye=N[ue];return ye===void 0&&(ye=new mh,N[ue]=ye),ye.getHandSpace()};function z(ue){const ye=L.indexOf(ue.inputSource);if(ye===-1)return;const we=N[ye];we!==void 0&&(we.update(ue.inputSource,ue.frame,p||f),we.dispatchEvent({type:ue.type,data:ue.inputSource}))}function H(){l.removeEventListener("select",z),l.removeEventListener("selectstart",z),l.removeEventListener("selectend",z),l.removeEventListener("squeeze",z),l.removeEventListener("squeezestart",z),l.removeEventListener("squeezeend",z),l.removeEventListener("end",H),l.removeEventListener("inputsourceschange",ee);for(let ue=0;ue<N.length;ue++){const ye=L[ue];ye!==null&&(L[ue]=null,N[ue].disconnect(ye))}Y=null,j=null,M.reset();for(const ue in y)delete y[ue];if(e.setRenderTarget(V),x=null,v=null,_=null,l=null,R=null,Xe.stop(),r.isPresenting=!1,e.setPixelRatio(T),e.setSize(P.width,P.height,!1),O!==null){const ue=O.camera;ue.fov=O.fov,ue.zoom=O.zoom,ue.updateProjectionMatrix(),O=null}r.dispatchEvent({type:"sessionend"})}this.setFramebufferScaleFactor=function(ue){c=ue,r.isPresenting===!0&&ht("WebXRManager: Cannot change framebuffer scale while presenting.")},this.setReferenceSpaceType=function(ue){h=ue,r.isPresenting===!0&&ht("WebXRManager: Cannot change reference space type while presenting.")},this.getReferenceSpace=function(){return p||f},this.setReferenceSpace=function(ue){p=ue},this.getBaseLayer=function(){return v!==null?v:x},this.getBinding=function(){return _===null&&D&&(_=new XRWebGLBinding(l,i)),_},this.getFrame=function(){return E},this.getSession=function(){return l},this.setSession=async function(ue){if(l=ue,l!==null){if(V=e.getRenderTarget(),l.addEventListener("select",z),l.addEventListener("selectstart",z),l.addEventListener("selectend",z),l.addEventListener("squeeze",z),l.addEventListener("squeezestart",z),l.addEventListener("squeezeend",z),l.addEventListener("end",H),l.addEventListener("inputsourceschange",ee),F.xrCompatible!==!0&&await i.makeXRCompatible(),T=e.getPixelRatio(),e.getSize(P),D&&"createProjectionLayer"in XRWebGLBinding.prototype){let we=null,at=null,Ge=null;F.depth&&(Ge=F.stencil?i.DEPTH24_STENCIL8:i.DEPTH_COMPONENT24,we=F.stencil?ws:Er,at=F.stencil?jl:Wa);const mt={colorFormat:i.RGBA8,depthFormat:Ge,scaleFactor:c};_=this.getBinding(),v=_.createProjectionLayer(mt),l.updateRenderState({layers:[v]}),e.setPixelRatio(1),e.setSize(v.textureWidth,v.textureHeight,!1),R=new wa(v.textureWidth,v.textureHeight,{format:Ra,type:ha,depthTexture:new Ql(v.textureWidth,v.textureHeight,at,void 0,void 0,void 0,void 0,void 0,void 0,we),stencilBuffer:F.stencil,colorSpace:e.outputColorSpace,samples:F.antialias?4:0,resolveDepthBuffer:v.ignoreDepthValues===!1,resolveStencilBuffer:v.ignoreDepthValues===!1,storeMultisampledDepthBuffer:v.ignoreDepthValues===!1,storeMultisampledStencilBuffer:v.ignoreDepthValues===!1})}else{const we={antialias:F.antialias,alpha:!0,depth:F.depth,stencil:F.stencil,framebufferScaleFactor:c};x=new XRWebGLLayer(l,i,we),l.updateRenderState({baseLayer:x}),e.setPixelRatio(1),e.setSize(x.framebufferWidth,x.framebufferHeight,!1),R=new wa(x.framebufferWidth,x.framebufferHeight,{format:Ra,type:ha,colorSpace:e.outputColorSpace,stencilBuffer:F.stencil,resolveDepthBuffer:x.ignoreDepthValues===!1,resolveStencilBuffer:x.ignoreDepthValues===!1,storeMultisampledDepthBuffer:x.ignoreDepthValues===!1,storeMultisampledStencilBuffer:x.ignoreDepthValues===!1})}R.isXRRenderTarget=!0,this.setFoveation(m),p=null,f=await l.requestReferenceSpace(h),Xe.setContext(l),Xe.start(),r.isPresenting=!0,r.dispatchEvent({type:"sessionstart"})}},this.getEnvironmentBlendMode=function(){if(l!==null)return l.environmentBlendMode},this.getDepthTexture=function(){return M.getDepthTexture()};function ee(ue){for(let ye=0;ye<ue.removed.length;ye++){const we=ue.removed[ye],at=L.indexOf(we);at>=0&&(L[at]=null,N[at].disconnect(we))}for(let ye=0;ye<ue.added.length;ye++){const we=ue.added[ye];let at=L.indexOf(we);if(at===-1){for(let mt=0;mt<N.length;mt++)if(mt>=L.length){L.push(we),at=mt;break}else if(L[mt]===null){L[mt]=we,at=mt;break}if(at===-1)break}const Ge=N[at];Ge&&Ge.connect(we)}}const oe=new Q,fe=new Q;function U(ue,ye,we){oe.setFromMatrixPosition(ye.matrixWorld),fe.setFromMatrixPosition(we.matrixWorld);const at=oe.distanceTo(fe),Ge=ye.projectionMatrix.elements,mt=we.projectionMatrix.elements,un=Ge[14]/(Ge[10]-1),ut=Ge[14]/(Ge[10]+1),vt=(Ge[9]+1)/Ge[5],Mt=(Ge[9]-1)/Ge[5],pt=(Ge[8]-1)/Ge[0],_t=(mt[8]+1)/mt[0],Gt=un*pt,_n=un*_t,Xt=at/(-pt+_t),fn=Xt*-pt;if(ye.matrixWorld.decompose(ue.position,ue.quaternion,ue.scale),ue.translateX(fn),ue.translateZ(Xt),ue.matrixWorld.compose(ue.position,ue.quaternion,ue.scale),ue.matrixWorldInverse.copy(ue.matrixWorld).invert(),Ge[10]===-1)ue.projectionMatrix.copy(ye.projectionMatrix),ue.projectionMatrixInverse.copy(ye.projectionMatrixInverse);else{const Z=un+Xt,Ft=ut+Xt,Dt=Gt-fn,I=_n+(at-fn),b=vt*ut/Ft*Z,K=Mt*ut/Ft*Z;ue.projectionMatrix.makePerspective(Dt,I,b,K,Z,Ft),ue.projectionMatrixInverse.copy(ue.projectionMatrix).invert()}}function re(ue,ye){ye===null?ue.matrixWorld.copy(ue.matrix):ue.matrixWorld.multiplyMatrices(ye.matrixWorld,ue.matrix),ue.matrixWorldInverse.copy(ue.matrixWorld).invert()}this.updateCamera=function(ue){if(l===null)return;let ye=ue.near,we=ue.far;M.texture!==null&&(M.depthNear>0&&(ye=M.depthNear),M.depthFar>0&&(we=M.depthFar)),se.near=k.near=B.near=ye,se.far=k.far=B.far=we,(Y!==se.near||j!==se.far)&&(l.updateRenderState({depthNear:se.near,depthFar:se.far}),Y=se.near,j=se.far),se.layers.mask=ue.layers.mask|6,B.layers.mask=se.layers.mask&-5,k.layers.mask=se.layers.mask&-3;const at=ue.parent,Ge=se.cameras;re(se,at);for(let mt=0;mt<Ge.length;mt++)re(Ge[mt],at);Ge.length===2?U(se,B,k):se.projectionMatrix.copy(B.projectionMatrix),O===null&&ue.isPerspectiveCamera&&(O={camera:ue,fov:ue.fov,zoom:ue.zoom}),xe(ue,se,at)};function xe(ue,ye,we){we===null?ue.matrix.copy(ye.matrixWorld):(ue.matrix.copy(we.matrixWorld),ue.matrix.invert(),ue.matrix.multiply(ye.matrixWorld)),ue.matrix.decompose(ue.position,ue.quaternion,ue.scale),ue.updateMatrixWorld(!0),ue.projectionMatrix.copy(ye.projectionMatrix),ue.projectionMatrixInverse.copy(ye.projectionMatrixInverse),ue.isPerspectiveCamera&&(ue.fov=Kl*2*Math.atan(1/ue.projectionMatrix.elements[5]),ue.zoom=1)}this.getCamera=function(){return se},this.getFoveation=function(){if(!(v===null&&x===null))return m},this.setFoveation=function(ue){m=ue,v!==null&&(v.fixedFoveation=ue),x!==null&&x.fixedFoveation!==void 0&&(x.fixedFoveation=ue)},this.hasDepthSensing=function(){return M.texture!==null},this.getDepthSensingMesh=function(){return M.getMesh(se)},this.getCameraTexture=function(ue){return y[ue]};let Ue=null;function Ie(ue,ye){if(g=ye.getViewerPose(p||f),E=ye,g!==null){const we=g.views;x!==null&&(e.setRenderTargetFramebuffer(R,x.framebuffer),e.setRenderTarget(R));let at=!1;we.length!==se.cameras.length&&(se.cameras.length=0,at=!0);for(let ut=0;ut<we.length;ut++){const vt=we[ut];let Mt=null;if(x!==null)Mt=x.getViewport(vt);else{const _t=_.getViewSubImage(v,vt);Mt=_t.viewport,ut===0&&(e.setRenderTargetTextures(R,_t.colorTexture,_t.depthStencilTexture),e.setRenderTarget(R))}let pt=J[ut];pt===void 0&&(pt=new Yi,pt.layers.enable(ut),pt.viewport=new Ln,J[ut]=pt),pt.matrix.fromArray(vt.transform.matrix),pt.matrix.decompose(pt.position,pt.quaternion,pt.scale),pt.projectionMatrix.fromArray(vt.projectionMatrix),pt.projectionMatrixInverse.copy(pt.projectionMatrix).invert(),pt.viewport.set(Mt.x,Mt.y,Mt.width,Mt.height),ut===0&&(se.matrix.copy(pt.matrix),se.matrix.decompose(se.position,se.quaternion,se.scale)),at===!0&&se.cameras.push(pt)}const Ge=l.enabledFeatures;if(Ge&&Ge.includes("depth-sensing")&&l.depthUsage=="gpu-optimized"&&D){_=r.getBinding();const ut=_.getDepthInformation(we[0]);ut&&ut.isValid&&ut.texture&&M.init(ut,l.renderState)}if(Ge&&Ge.includes("camera-access")&&D){e.state.unbindTexture(),_=r.getBinding();for(let ut=0;ut<we.length;ut++){const vt=we[ut].camera;if(vt){let Mt=y[vt];Mt||(Mt=new Ix,y[vt]=Mt);const pt=_.getCameraImage(vt);Mt.sourceTexture=pt}}}}for(let we=0;we<N.length;we++){const at=L[we],Ge=N[we];at!==null&&Ge!==void 0&&Ge.update(at,ye,p||f)}Ue&&Ue(ue,ye),ye.detectedPlanes&&r.dispatchEvent({type:"planesdetected",data:ye}),E=null}const Xe=new Gx;Xe.setAnimationLoop(Ie),this.setAnimationLoop=function(ue){Ue=ue},this.dispose=function(){}}}const bC=new En,jx=new yt;jx.set(-1,0,0,0,1,0,0,0,1);function EC(s,e){function i(M,y){M.matrixAutoUpdate===!0&&M.updateMatrix(),y.value.copy(M.matrix)}function r(M,y){y.color.getRGB(M.fogColor.value,zx(s)),y.isFog?(M.fogNear.value=y.near,M.fogFar.value=y.far):y.isFogExp2&&(M.fogDensity.value=y.density)}function l(M,y,F,V,R){y.isNodeMaterial?y.uniformsNeedUpdate=!1:y.isMeshBasicMaterial?c(M,y):y.isMeshLambertMaterial?(c(M,y),y.envMap&&(M.envMapIntensity.value=y.envMapIntensity)):y.isMeshToonMaterial?(c(M,y),_(M,y)):y.isMeshPhongMaterial?(c(M,y),g(M,y),y.envMap&&(M.envMapIntensity.value=y.envMapIntensity)):y.isMeshStandardMaterial?(c(M,y),v(M,y),y.isMeshPhysicalMaterial&&x(M,y,R)):y.isMeshMatcapMaterial?(c(M,y),E(M,y)):y.isMeshDepthMaterial?c(M,y):y.isMeshDistanceMaterial?(c(M,y),D(M,y)):y.isMeshNormalMaterial?c(M,y):y.isLineBasicMaterial?(f(M,y),y.isLineDashedMaterial&&h(M,y)):y.isPointsMaterial?m(M,y,F,V):y.isSpriteMaterial?p(M,y):y.isShadowMaterial?(M.color.value.copy(y.color),M.opacity.value=y.opacity):y.isShaderMaterial&&(y.uniformsNeedUpdate=!1)}function c(M,y){M.opacity.value=y.opacity,y.color&&M.diffuse.value.copy(y.color),y.emissive&&M.emissive.value.copy(y.emissive).multiplyScalar(y.emissiveIntensity),y.map&&(M.map.value=y.map,i(y.map,M.mapTransform)),y.alphaMap&&(M.alphaMap.value=y.alphaMap,i(y.alphaMap,M.alphaMapTransform)),y.bumpMap&&(M.bumpMap.value=y.bumpMap,i(y.bumpMap,M.bumpMapTransform),M.bumpScale.value=y.bumpScale,y.side===Oi&&(M.bumpScale.value*=-1)),y.normalMap&&(M.normalMap.value=y.normalMap,i(y.normalMap,M.normalMapTransform),M.normalScale.value.copy(y.normalScale),y.side===Oi&&M.normalScale.value.negate()),y.displacementMap&&(M.displacementMap.value=y.displacementMap,i(y.displacementMap,M.displacementMapTransform),M.displacementScale.value=y.displacementScale,M.displacementBias.value=y.displacementBias),y.emissiveMap&&(M.emissiveMap.value=y.emissiveMap,i(y.emissiveMap,M.emissiveMapTransform)),y.specularMap&&(M.specularMap.value=y.specularMap,i(y.specularMap,M.specularMapTransform)),y.alphaTest>0&&(M.alphaTest.value=y.alphaTest);const F=e.get(y),V=F.envMap,R=F.envMapRotation;V&&(M.envMap.value=V,M.envMapRotation.value.setFromMatrix4(bC.makeRotationFromEuler(R)).transpose(),V.isCubeTexture&&V.isRenderTargetTexture===!1&&M.envMapRotation.value.premultiply(jx),M.reflectivity.value=y.reflectivity,M.ior.value=y.ior,M.refractionRatio.value=y.refractionRatio),y.lightMap&&(M.lightMap.value=y.lightMap,M.lightMapIntensity.value=y.lightMapIntensity,i(y.lightMap,M.lightMapTransform)),y.aoMap&&(M.aoMap.value=y.aoMap,M.aoMapIntensity.value=y.aoMapIntensity,i(y.aoMap,M.aoMapTransform))}function f(M,y){M.diffuse.value.copy(y.color),M.opacity.value=y.opacity,y.map&&(M.map.value=y.map,i(y.map,M.mapTransform))}function h(M,y){M.dashSize.value=y.dashSize,M.totalSize.value=y.dashSize+y.gapSize,M.scale.value=y.scale}function m(M,y,F,V){M.diffuse.value.copy(y.color),M.opacity.value=y.opacity,M.size.value=y.size*F,M.scale.value=V*.5,y.map&&(M.map.value=y.map,i(y.map,M.uvTransform)),y.alphaMap&&(M.alphaMap.value=y.alphaMap,i(y.alphaMap,M.alphaMapTransform)),y.alphaTest>0&&(M.alphaTest.value=y.alphaTest)}function p(M,y){M.diffuse.value.copy(y.color),M.opacity.value=y.opacity,M.rotation.value=y.rotation,y.map&&(M.map.value=y.map,i(y.map,M.mapTransform)),y.alphaMap&&(M.alphaMap.value=y.alphaMap,i(y.alphaMap,M.alphaMapTransform)),y.alphaTest>0&&(M.alphaTest.value=y.alphaTest)}function g(M,y){M.specular.value.copy(y.specular),M.shininess.value=Math.max(y.shininess,1e-4)}function _(M,y){y.gradientMap&&(M.gradientMap.value=y.gradientMap)}function v(M,y){M.metalness.value=y.metalness,y.metalnessMap&&(M.metalnessMap.value=y.metalnessMap,i(y.metalnessMap,M.metalnessMapTransform)),M.roughness.value=y.roughness,y.roughnessMap&&(M.roughnessMap.value=y.roughnessMap,i(y.roughnessMap,M.roughnessMapTransform)),y.envMap&&(M.envMapIntensity.value=y.envMapIntensity)}function x(M,y,F){M.ior.value=y.ior,y.sheen>0&&(M.sheenColor.value.copy(y.sheenColor).multiplyScalar(y.sheen),M.sheenRoughness.value=y.sheenRoughness,y.sheenColorMap&&(M.sheenColorMap.value=y.sheenColorMap,i(y.sheenColorMap,M.sheenColorMapTransform)),y.sheenRoughnessMap&&(M.sheenRoughnessMap.value=y.sheenRoughnessMap,i(y.sheenRoughnessMap,M.sheenRoughnessMapTransform))),y.clearcoat>0&&(M.clearcoat.value=y.clearcoat,M.clearcoatRoughness.value=y.clearcoatRoughness,y.clearcoatMap&&(M.clearcoatMap.value=y.clearcoatMap,i(y.clearcoatMap,M.clearcoatMapTransform)),y.clearcoatRoughnessMap&&(M.clearcoatRoughnessMap.value=y.clearcoatRoughnessMap,i(y.clearcoatRoughnessMap,M.clearcoatRoughnessMapTransform)),y.clearcoatNormalMap&&(M.clearcoatNormalMap.value=y.clearcoatNormalMap,i(y.clearcoatNormalMap,M.clearcoatNormalMapTransform),M.clearcoatNormalScale.value.copy(y.clearcoatNormalScale),y.side===Oi&&M.clearcoatNormalScale.value.negate())),y.dispersion>0&&(M.dispersion.value=y.dispersion),y.retroreflectivity>0&&(M.retroreflectivity.value=y.retroreflectivity),y.iridescence>0&&(M.iridescence.value=y.iridescence,M.iridescenceIOR.value=y.iridescenceIOR,M.iridescenceThicknessMinimum.value=y.iridescenceThicknessRange[0],M.iridescenceThicknessMaximum.value=y.iridescenceThicknessRange[1],y.iridescenceMap&&(M.iridescenceMap.value=y.iridescenceMap,i(y.iridescenceMap,M.iridescenceMapTransform)),y.iridescenceThicknessMap&&(M.iridescenceThicknessMap.value=y.iridescenceThicknessMap,i(y.iridescenceThicknessMap,M.iridescenceThicknessMapTransform))),y.transmission>0&&(M.transmission.value=y.transmission,M.transmissionSamplerMap.value=F.texture,M.transmissionSamplerSize.value.set(F.width,F.height),y.transmissionMap&&(M.transmissionMap.value=y.transmissionMap,i(y.transmissionMap,M.transmissionMapTransform)),M.thickness.value=y.thickness,y.thicknessMap&&(M.thicknessMap.value=y.thicknessMap,i(y.thicknessMap,M.thicknessMapTransform)),M.attenuationDistance.value=y.attenuationDistance,M.attenuationColor.value.copy(y.attenuationColor)),y.anisotropy>0&&(M.anisotropyVector.value.set(y.anisotropy*Math.cos(y.anisotropyRotation),y.anisotropy*Math.sin(y.anisotropyRotation)),y.anisotropyMap&&(M.anisotropyMap.value=y.anisotropyMap,i(y.anisotropyMap,M.anisotropyMapTransform))),M.specularIntensity.value=y.specularIntensity,M.specularColor.value.copy(y.specularColor),y.specularColorMap&&(M.specularColorMap.value=y.specularColorMap,i(y.specularColorMap,M.specularColorMapTransform)),y.specularIntensityMap&&(M.specularIntensityMap.value=y.specularIntensityMap,i(y.specularIntensityMap,M.specularIntensityMapTransform))}function E(M,y){y.matcap&&(M.matcap.value=y.matcap)}function D(M,y){const F=e.get(y).light;M.referencePosition.value.setFromMatrixPosition(F.matrixWorld),M.nearDistance.value=F.shadow.camera.near,M.farDistance.value=F.shadow.camera.far}return{refreshFogUniforms:r,refreshMaterialUniforms:l}}function TC(s,e,i,r){let l={},c={},f=[];const h=s.getParameter(s.MAX_UNIFORM_BUFFER_BINDINGS);function m(R,N){const L=N.program;r.uniformBlockBinding(R,L)}function p(R,N){let L=l[R.id];L===void 0&&(M(R),L=g(R),l[R.id]=L,R.addEventListener("dispose",F));const P=N.program;r.updateUBOMapping(R,P);const T=e.render.frame;c[R.id]!==T&&(v(R),c[R.id]=T)}function g(R){const N=_();R.__bindingPointIndex=N;const L=s.createBuffer(),P=R.__size,T=R.usage;return s.bindBuffer(s.UNIFORM_BUFFER,L),s.bufferData(s.UNIFORM_BUFFER,P,T),s.bindBuffer(s.UNIFORM_BUFFER,null),s.bindBufferBase(s.UNIFORM_BUFFER,N,L),L}function _(){for(let R=0;R<h;R++)if(f.indexOf(R)===-1)return f.push(R),R;return Zt("WebGLRenderer: Maximum number of simultaneously usable uniforms groups reached."),0}function v(R){const N=l[R.id],L=R.uniforms,P=R.__cache;s.bindBuffer(s.UNIFORM_BUFFER,N);for(let T=0,O=L.length;T<O;T++){const B=L[T];if(Array.isArray(B))for(let k=0,J=B.length;k<J;k++)x(B[k],T,k,P);else x(B,T,0,P)}s.bindBuffer(s.UNIFORM_BUFFER,null)}function x(R,N,L,P){if(D(R,N,L,P)===!0){const T=R.__offset,O=R.value;if(Array.isArray(O)){let B=0;for(let k=0;k<O.length;k++){const J=O[k],se=y(J);E(J,R.__data,B),typeof J!="number"&&typeof J!="boolean"&&!J.isMatrix3&&!ArrayBuffer.isView(J)&&(B+=se.storage/Float32Array.BYTES_PER_ELEMENT)}}else E(O,R.__data,0);s.bufferSubData(s.UNIFORM_BUFFER,T,R.__data)}}function E(R,N,L){typeof R=="number"||typeof R=="boolean"?N[0]=R:R.isMatrix3?(N[0]=R.elements[0],N[1]=R.elements[1],N[2]=R.elements[2],N[3]=0,N[4]=R.elements[3],N[5]=R.elements[4],N[6]=R.elements[5],N[7]=0,N[8]=R.elements[6],N[9]=R.elements[7],N[10]=R.elements[8],N[11]=0):ArrayBuffer.isView(R)?N.set(new R.constructor(R.buffer,R.byteOffset,N.length)):R.toArray(N,L)}function D(R,N,L,P){const T=R.value,O=N+"_"+L;if(P[O]===void 0)return typeof T=="number"||typeof T=="boolean"?P[O]=T:ArrayBuffer.isView(T)?P[O]=T.slice():P[O]=T.clone(),!0;{const B=P[O];if(typeof T=="number"||typeof T=="boolean"){if(B!==T)return P[O]=T,!0}else{if(ArrayBuffer.isView(T))return!0;if(B.equals(T)===!1)return B.copy(T),!0}}return!1}function M(R){const N=R.uniforms;let L=0;const P=16;for(let O=0,B=N.length;O<B;O++){const k=Array.isArray(N[O])?N[O]:[N[O]];for(let J=0,se=k.length;J<se;J++){const Y=k[J],j=Array.isArray(Y.value)?Y.value:[Y.value];for(let z=0,H=j.length;z<H;z++){const ee=j[z],oe=y(ee),fe=L%P,U=fe%oe.boundary,re=fe+U;L+=U,re!==0&&P-re<oe.storage&&(L+=P-re),Y.__data=new Float32Array(oe.storage/Float32Array.BYTES_PER_ELEMENT),Y.__offset=L,L+=oe.storage}}}const T=L%P;return T>0&&(L+=P-T),R.__size=L,R.__cache={},this}function y(R){const N={boundary:0,storage:0};return typeof R=="number"||typeof R=="boolean"?(N.boundary=4,N.storage=4):R.isVector2?(N.boundary=8,N.storage=8):R.isVector3||R.isColor?(N.boundary=16,N.storage=12):R.isVector4?(N.boundary=16,N.storage=16):R.isMatrix3?(N.boundary=48,N.storage=48):R.isMatrix4?(N.boundary=64,N.storage=64):R.isTexture?ht("WebGLRenderer: Texture samplers can not be part of an uniforms group."):ArrayBuffer.isView(R)?(N.boundary=16,N.storage=R.byteLength):ht("WebGLRenderer: Unsupported uniform value type.",R),N}function F(R){const N=R.target;N.removeEventListener("dispose",F);const L=f.indexOf(N.__bindingPointIndex);f.splice(L,1),s.deleteBuffer(l[N.id]),delete l[N.id],delete c[N.id]}function V(){for(const R in l)s.deleteBuffer(l[R]);f=[],l={},c={}}return{bind:m,update:p,dispose:V}}const AC=new Uint16Array([12469,15057,12620,14925,13266,14620,13807,14376,14323,13990,14545,13625,14713,13328,14840,12882,14931,12528,14996,12233,15039,11829,15066,11525,15080,11295,15085,10976,15082,10705,15073,10495,13880,14564,13898,14542,13977,14430,14158,14124,14393,13732,14556,13410,14702,12996,14814,12596,14891,12291,14937,11834,14957,11489,14958,11194,14943,10803,14921,10506,14893,10278,14858,9960,14484,14039,14487,14025,14499,13941,14524,13740,14574,13468,14654,13106,14743,12678,14818,12344,14867,11893,14889,11509,14893,11180,14881,10751,14852,10428,14812,10128,14765,9754,14712,9466,14764,13480,14764,13475,14766,13440,14766,13347,14769,13070,14786,12713,14816,12387,14844,11957,14860,11549,14868,11215,14855,10751,14825,10403,14782,10044,14729,9651,14666,9352,14599,9029,14967,12835,14966,12831,14963,12804,14954,12723,14936,12564,14917,12347,14900,11958,14886,11569,14878,11247,14859,10765,14828,10401,14784,10011,14727,9600,14660,9289,14586,8893,14508,8533,15111,12234,15110,12234,15104,12216,15092,12156,15067,12010,15028,11776,14981,11500,14942,11205,14902,10752,14861,10393,14812,9991,14752,9570,14682,9252,14603,8808,14519,8445,14431,8145,15209,11449,15208,11451,15202,11451,15190,11438,15163,11384,15117,11274,15055,10979,14994,10648,14932,10343,14871,9936,14803,9532,14729,9218,14645,8742,14556,8381,14461,8020,14365,7603,15273,10603,15272,10607,15267,10619,15256,10631,15231,10614,15182,10535,15118,10389,15042,10167,14963,9787,14883,9447,14800,9115,14710,8665,14615,8318,14514,7911,14411,7507,14279,7198,15314,9675,15313,9683,15309,9712,15298,9759,15277,9797,15229,9773,15166,9668,15084,9487,14995,9274,14898,8910,14800,8539,14697,8234,14590,7790,14479,7409,14367,7067,14178,6621,15337,8619,15337,8631,15333,8677,15325,8769,15305,8871,15264,8940,15202,8909,15119,8775,15022,8565,14916,8328,14804,8009,14688,7614,14569,7287,14448,6888,14321,6483,14088,6171,15350,7402,15350,7419,15347,7480,15340,7613,15322,7804,15287,7973,15229,8057,15148,8012,15046,7846,14933,7611,14810,7357,14682,7069,14552,6656,14421,6316,14251,5948,14007,5528,15356,5942,15356,5977,15353,6119,15348,6294,15332,6551,15302,6824,15249,7044,15171,7122,15070,7050,14949,6861,14818,6611,14679,6349,14538,6067,14398,5651,14189,5311,13935,4958,15359,4123,15359,4153,15356,4296,15353,4646,15338,5160,15311,5508,15263,5829,15188,6042,15088,6094,14966,6001,14826,5796,14678,5543,14527,5287,14377,4985,14133,4586,13869,4257,15360,1563,15360,1642,15358,2076,15354,2636,15341,3350,15317,4019,15273,4429,15203,4732,15105,4911,14981,4932,14836,4818,14679,4621,14517,4386,14359,4156,14083,3795,13808,3437,15360,122,15360,137,15358,285,15355,636,15344,1274,15322,2177,15281,2765,15215,3223,15120,3451,14995,3569,14846,3567,14681,3466,14511,3305,14344,3121,14037,2800,13753,2467,15360,0,15360,1,15359,21,15355,89,15346,253,15325,479,15287,796,15225,1148,15133,1492,15008,1749,14856,1882,14685,1886,14506,1783,14324,1608,13996,1398,13702,1183]);let Ha=null;function RC(){return Ha===null&&(Ha=new oE(AC,16,16,Os,qa),Ha.name="DFG_LUT",Ha.minFilter=mi,Ha.magFilter=mi,Ha.wrapS=Sr,Ha.wrapT=Sr,Ha.generateMipmaps=!1,Ha.needsUpdate=!0),Ha}class Zx{constructor(e={}){const{canvas:i=Mb(),context:r=null,depth:l=!0,stencil:c=!1,alpha:f=!1,antialias:h=!1,premultipliedAlpha:m=!0,preserveDrawingBuffer:p=!1,powerPreference:g="default",failIfMajorPerformanceCaveat:_=!1,reversedDepthBuffer:v=!1,outputBufferType:x=ha}=e;this.isWebGLRenderer=!0;let E;if(r!==null){if(typeof WebGLRenderingContext<"u"&&r instanceof WebGLRenderingContext)throw new Error("THREE.WebGLRenderer: WebGL 1 is not supported since r163.");E=r.getContextAttributes().alpha}else E=f;const D=x,M=new Set([Xp,kp,Vp]),y=new Set([ha,Wa,Yl,jl,Hp,Gp]),F=new Uint32Array(4),V=new Int32Array(4),R=new Q;let N=null,L=null;const P=[],T=[];let O=null;this.domElement=i,this.debug={checkShaderErrors:!0,diagnostics:{keywords:!1},onShaderError:null},this.autoClear=!0,this.autoClearColor=!0,this.autoClearDepth=!0,this.autoClearStencil=!0,this.sortObjects=!0,this.clippingPlanes=[],this.localClippingEnabled=!1,this.toneMapping=Xa,this.toneMappingExposure=1,this.transmissionResolutionScale=1;const B=this;let k=!1,J=null,se=null,Y=null,j=null;this._outputColorSpace=Ei;let z=0,H=0,ee=null,oe=-1,fe=null;const U=new Ln,re=new Ln;let xe=null;const Ue=new Rt(0);let Ie=0,Xe=i.width,ue=i.height,ye=1,we=null,at=null;const Ge=new Ln(0,0,Xe,ue),mt=new Ln(0,0,Xe,ue);let un=!1;const ut=new Ox;let vt=!1,Mt=!1;const pt=new En,_t=new Q,Gt=new Ln,_n={background:null,fog:null,environment:null,overrideMaterial:null,isScene:!0};let Xt=!1;function fn(){return ee===null?ye:1}let Z=r;function Ft(A,X){return i.getContext(A,X)}let Dt,I,b,K,ce,ve,ne,Ae,pe,Se,Ne,Ze,He,Fe,rt,lt,dt,W,Oe,Me,Pe,Ve,Re;try{const A={alpha:!0,depth:l,stencil:c,antialias:h,premultipliedAlpha:m,preserveDrawingBuffer:p,powerPreference:g,failIfMajorPerformanceCaveat:_};if("setAttribute"in i&&i.setAttribute("data-engine",`three.js r${zp}`),i.addEventListener("webglcontextlost",Qt,!1),i.addEventListener("webglcontextrestored",Nt,!1),i.addEventListener("webglcontextcreationerror",ei,!1),Z===null){const X="webgl2";if(Z=Ft(X,A),Z===null)throw Ft(X)?new Error("THREE.WebGLRenderer: Error creating WebGL context with your selected attributes."):new Error("THREE.WebGLRenderer: Error creating WebGL context.")}et()}catch(A){throw i.removeEventListener("webglcontextlost",Qt,!1),i.removeEventListener("webglcontextrestored",Nt,!1),i.removeEventListener("webglcontextcreationerror",ei,!1),Zt("WebGLRenderer: "+A.message),A}function et(){Dt=new RA(Z),Dt.init(),Pe=new _C(Z,Dt),I=new vA(Z,Dt,e,Pe),b=new gC(Z,Dt),I.reversedDepthBuffer&&v&&b.buffers.depth.setReversed(!0),se=Z.createFramebuffer(),Y=Z.createFramebuffer(),j=Z.createFramebuffer(),K=new DA(Z),ce=new nC,ve=new vC(Z,Dt,b,ce,I,Pe,K),ne=new AA(B),Ae=new NE(Z),Ve=new mA(Z,Ae),pe=new CA(Z,Ae,K,Ve),Se=new NA(Z,pe,Ae,Ve,K),W=new UA(Z,I,ve),rt=new _A(ce),Ne=new tC(B,ne,Dt,I,Ve,rt),Ze=new EC(B,ce),He=new aC,Fe=new uC(Dt),dt=new pA(B,ne,b,Se,E,m),lt=new mC(B,Se,I),Re=new TC(Z,K,I,b),Oe=new gA(Z,Dt,K),Me=new wA(Z,Dt,K),K.programs=Ne.programs,B.capabilities=I,B.extensions=Dt,B.properties=ce,B.renderLists=He,B.shadowMap=lt,B.state=b,B.info=K}D!==ha&&(O=new OA(D,i.width,i.height,h,l,c));const Je=new MC(B,Z);this.xr=Je,this.getContext=function(){return Z},this.getContextAttributes=function(){return Z.getContextAttributes()},this.forceContextLoss=function(){const A=Dt.get("WEBGL_lose_context");A&&A.loseContext()},this.forceContextRestore=function(){const A=Dt.get("WEBGL_lose_context");A&&A.restoreContext()},this.getPixelRatio=function(){return ye},this.setPixelRatio=function(A){A!==void 0&&(ye=A,this.setSize(Xe,ue,!1))},this.getSize=function(A){return A.set(Xe,ue)},this.setSize=function(A,X,ge=!0){if(Je.isPresenting){ht("WebGLRenderer: Can't change size while VR device is presenting.");return}Xe=A,ue=X,i.width=Math.floor(A*ye),i.height=Math.floor(X*ye),ge===!0&&(i.style.width=A+"px",i.style.height=X+"px"),O!==null&&O.setSize(i.width,i.height),this.setViewport(0,0,A,X)},this.getDrawingBufferSize=function(A){return A.set(Xe*ye,ue*ye).floor()},this.setDrawingBufferSize=function(A,X,ge){Xe=A,ue=X,ye=ge,i.width=Math.floor(A*ge),i.height=Math.floor(X*ge),this.setViewport(0,0,A,X)},this.setEffects=function(A){if(D===ha){Zt("WebGLRenderer: setEffects() requires outputBufferType set to HalfFloatType or FloatType.");return}if(A){for(let X=0;X<A.length;X++)if(A[X].isOutputPass===!0){ht("WebGLRenderer: OutputPass is not needed in setEffects(). Tone mapping and color space conversion are applied automatically.");break}}O.setEffects(A||[])},this.getCurrentViewport=function(A){return A.copy(U)},this.getViewport=function(A){return A.copy(Ge)},this.setViewport=function(A,X,ge,ie){A.isVector4?Ge.set(A.x,A.y,A.z,A.w):Ge.set(A,X,ge,ie),b.viewport(U.copy(Ge).multiplyScalar(ye).round())},this.getScissor=function(A){return A.copy(mt)},this.setScissor=function(A,X,ge,ie){A.isVector4?mt.set(A.x,A.y,A.z,A.w):mt.set(A,X,ge,ie),b.scissor(re.copy(mt).multiplyScalar(ye).round())},this.getScissorTest=function(){return un},this.setScissorTest=function(A){b.setScissorTest(un=A)},this.setOpaqueSort=function(A){we=A},this.setTransparentSort=function(A){at=A},this.getClearColor=function(A){return A.copy(dt.getClearColor())},this.setClearColor=function(){dt.setClearColor(...arguments)},this.getClearAlpha=function(){return dt.getClearAlpha()},this.setClearAlpha=function(){dt.setClearAlpha(...arguments)},this.clear=function(A=!0,X=!0,ge=!0){let ie=0;if(A){let ae=!1;if(ee!==null){const ze=ee.texture.format;ae=M.has(ze)}if(ae){const ze=ee.texture.type,We=y.has(ze),Be=dt.getClearColor(),qe=dt.getClearAlpha(),Ye=Be.r,gt=Be.g,Tt=Be.b;We?(F[0]=Ye,F[1]=gt,F[2]=Tt,F[3]=qe,Z.clearBufferuiv(Z.COLOR,0,F)):(V[0]=Ye,V[1]=gt,V[2]=Tt,V[3]=qe,Z.clearBufferiv(Z.COLOR,0,V))}else ie|=Z.COLOR_BUFFER_BIT}X&&(ie|=Z.DEPTH_BUFFER_BIT,this.state.buffers.depth.setMask(!0)),ge&&(ie|=Z.STENCIL_BUFFER_BIT,this.state.buffers.stencil.setMask(4294967295)),ie!==0&&Z.clear(ie)},this.clearColor=function(){this.clear(!0,!1,!1)},this.clearDepth=function(){this.clear(!1,!0,!1)},this.clearStencil=function(){this.clear(!1,!1,!0)},this.setNodesHandler=function(A){A.setRenderer(this),J=A},this.dispose=function(){i.removeEventListener("webglcontextlost",Qt,!1),i.removeEventListener("webglcontextrestored",Nt,!1),i.removeEventListener("webglcontextcreationerror",ei,!1),dt.dispose(),He.dispose(),Fe.dispose(),ce.dispose(),ne.dispose(),Se.dispose(),Ve.dispose(),Re.dispose(),Ne.dispose(),Je.dispose(),Je.removeEventListener("sessionstart",yn),Je.removeEventListener("sessionend",Bn),Kn.stop()};function Qt(A){A.preventDefault(),$v("WebGLRenderer: Context Lost."),k=!0}function Nt(){$v("WebGLRenderer: Context Restored."),k=!1;const A=K.autoReset,X=lt.enabled,ge=lt.autoUpdate,ie=lt.needsUpdate,ae=lt.type;et(),K.autoReset=A,lt.enabled=X,lt.autoUpdate=ge,lt.needsUpdate=ie,lt.type=ae}function ei(A){Zt("WebGLRenderer: A WebGL context could not be created. Reason: ",A.statusMessage)}function ti(A){const X=A.target;X.removeEventListener("dispose",ti),Qi(X)}function Qi(A){os(A),ce.remove(A)}function os(A){const X=ce.get(A).programs;X!==void 0&&(X.forEach(function(ge){Ne.releaseProgram(ge)}),A.isShaderMaterial&&Ne.releaseShaderCache(A))}this.renderBufferDirect=function(A,X,ge,ie,ae,ze){X===null&&(X=_n);const We=ae.isMesh&&ae.matrixWorld.determinantAffine()<0,Be=ga(A,X,ge,ie,ae);b.setMaterial(ie,We);let qe=ge.index,Ye=1;if(ie.wireframe===!0){if(qe=pe.getWireframeAttribute(ge),qe===void 0)return;Ye=2}const gt=ge.drawRange,Tt=ge.attributes.position;let $e=gt.start*Ye,zt=(gt.start+gt.count)*Ye;ze!==null&&($e=Math.max($e,ze.start*Ye),zt=Math.min(zt,(ze.start+ze.count)*Ye)),qe!==null?($e=Math.max($e,0),zt=Math.min(zt,qe.count)):Tt!=null&&($e=Math.max($e,0),zt=Math.min(zt,Tt.count));const dn=zt-$e;if(dn<0||dn===1/0)return;Ve.setup(ae,ie,Be,ge,qe);let rn,bt=Oe;if(qe!==null&&(rn=Ae.get(qe),bt=Me,bt.setIndex(rn)),ae.isMesh)ie.wireframe===!0?(b.setLineWidth(ie.wireframeLinewidth*fn()),bt.setMode(Z.LINES)):bt.setMode(Z.TRIANGLES);else if(ae.isLine){let Tn=ie.linewidth;Tn===void 0&&(Tn=1),b.setLineWidth(Tn*fn()),ae.isLineSegments?bt.setMode(Z.LINES):ae.isLineLoop?bt.setMode(Z.LINE_LOOP):bt.setMode(Z.LINE_STRIP)}else ae.isPoints?bt.setMode(Z.POINTS):ae.isSprite&&bt.setMode(Z.TRIANGLES);if(ae.isBatchedMesh)if(Dt.get("WEBGL_multi_draw"))bt.renderMultiDraw(ae._multiDrawStarts,ae._multiDrawCounts,ae._multiDrawCount);else{const Tn=ae._multiDrawStarts,Ke=ae._multiDrawCounts,wn=ae._multiDrawCount,Et=qe?Ae.get(qe).bytesPerElement:1,Qn=ce.get(ie).currentProgram.getUniforms();for(let ci=0;ci<wn;ci++)Qn.setValue(Z,"_gl_DrawID",ci),bt.render(Tn[ci]/Et,Ke[ci])}else if(ae.isInstancedMesh)bt.renderInstances($e,dn,ae.count);else if(ge.isInstancedBufferGeometry){const Tn=ge._maxInstanceCount!==void 0?ge._maxInstanceCount:1/0,Ke=Math.min(ge.instanceCount,Tn);bt.renderInstances($e,dn,Ke)}else bt.render($e,dn)};function Da(A,X,ge,ie){J!==null&&A.isNodeMaterial&&J.setObject(ie,A),vt===!0&&rt.setState(A,ge,!1),A.transparent===!0&&A.side===xr&&A.forceSinglePass===!1?(A.side=Oi,A.needsUpdate=!0,Ji(A,X,ie),A.side=Ns,A.needsUpdate=!0,Ji(A,X,ie),A.side=xr):Ji(A,X,ie)}this.compile=function(A,X,ge=null){ge===null&&(ge=A),J!==null&&J.renderStart(A,X,ge),L=Fe.get(ge),L.init(X),T.push(L),ge.traverseVisible(function(ae){ae.isLight&&ae.layers.test(X.layers)&&(L.pushLight(ae),ae.castShadow&&L.pushShadow(ae))}),A!==ge&&A.traverseVisible(function(ae){ae.isLight&&ae.layers.test(X.layers)&&(L.pushLight(ae),ae.castShadow&&L.pushShadow(ae))}),L.setupLights(),J!==null&&J.updateLights(L.state.lightsArray),Mt=this.localClippingEnabled,vt=rt.init(this.clippingPlanes,Mt),vt===!0&&rt.setGlobalState(this.clippingPlanes,X),J!==null&&lt.render(L.state.shadowsArray,ge,X);const ie=new Set;return A.traverse(function(ae){if(!(ae.isMesh||ae.isPoints||ae.isLine||ae.isSprite))return;const ze=ae.material;if(ze)if(Array.isArray(ze))for(let We=0;We<ze.length;We++){const Be=ze[We];Da(Be,ge,X,ae),ie.add(Be)}else Da(ze,ge,X,ae),ie.add(ze)}),L=T.pop(),J!==null&&J.renderEnd(),ie},this.compileAsync=function(A,X,ge=null){const ie=this.compile(A,X,ge);return new Promise(ae=>{function ze(){if(ie.forEach(function(We){const qe=ce.get(We).currentProgram;(qe===void 0||qe.isReady())&&ie.delete(We)}),ie.size===0){ae(A);return}setTimeout(ze,10)}Dt.get("KHR_parallel_shader_compile")!==null?ze():setTimeout(ze,10)})};let pa=null;function _i(A){pa&&pa(A)}function yn(){Kn.stop()}function Bn(){Kn.start()}const Kn=new Gx;Kn.setAnimationLoop(_i),typeof self<"u"&&Kn.setContext(self),this.setAnimationLoop=function(A){pa=A,Je.setAnimationLoop(A),A===null?Kn.stop():Kn.start()},Je.addEventListener("sessionstart",yn),Je.addEventListener("sessionend",Bn),this.render=function(A,X){if(X!==void 0&&X.isCamera!==!0){Zt("WebGLRenderer.render: camera is not an instance of THREE.Camera.");return}if(k===!0)return;J!==null&&J.renderStart(A,X);const ge=Je.enabled===!0&&Je.isPresenting===!0,ie=O!==null&&(ee===null||ge)&&O.begin(B,ee);if(A.matrixWorldAutoUpdate===!0&&A.updateMatrixWorld(),X.parent===null&&X.matrixWorldAutoUpdate===!0&&X.updateMatrixWorld(),Je.enabled===!0&&Je.isPresenting===!0&&(O===null||O.isCompositing()===!1)&&(Je.cameraAutoUpdate===!0&&Je.updateCamera(X),X=Je.getCamera()),A.isScene===!0&&A.onBeforeRender(B,A,X,ee),L=Fe.get(A,T.length),L.init(X),L.state.textureUnits=ve.getTextureUnits(),T.push(L),pt.multiplyMatrices(X.projectionMatrix,X.matrixWorldInverse),ut.setFromProjectionMatrix(pt,ka,X.reversedDepth),Mt=this.localClippingEnabled,vt=rt.init(this.clippingPlanes,Mt),N=He.get(A,P.length),N.init(),P.push(N),Je.enabled===!0&&Je.isPresenting===!0){const We=B.xr.getDepthSensingMesh();We!==null&&Wt(We,X,-1/0,B.sortObjects)}Wt(A,X,0,B.sortObjects),N.finish(),J!==null&&J.updateLights(L.state.lightsArray),B.sortObjects===!0&&N.sort(we,at),Xt=Je.enabled===!1||Je.isPresenting===!1||Je.hasDepthSensing()===!1,Xt&&dt.addToRenderList(N,A),this.info.render.frame++,this.info.autoReset===!0&&this.info.reset(),vt===!0&&rt.beginShadows();const ae=L.state.shadowsArray;if(lt.render(ae,A,X),vt===!0&&rt.endShadows(),(ie&&O.hasRenderPass())===!1){const We=N.opaque,Be=N.transmissive;if(L.setupLights(),X.isArrayCamera){const qe=X.cameras;if(Be.length>0)for(let Ye=0,gt=qe.length;Ye<gt;Ye++){const Tt=qe[Ye];Tr(We,Be,A,Tt)}Xt&&dt.render(A);for(let Ye=0,gt=qe.length;Ye<gt;Ye++){const Tt=qe[Ye];Mn(N,A,Tt,Tt.viewport)}}else Be.length>0&&Tr(We,Be,A,X),Xt&&dt.render(A),Mn(N,A,X)}ee!==null&&H===0&&(ve.updateMultisampleRenderTarget(ee),ve.updateRenderTargetMipmap(ee)),ie&&O.end(B),A.isScene===!0&&A.onAfterRender(B,A,X),Ve.resetDefaultState(),oe=-1,fe=null,T.pop(),T.length>0?(L=T[T.length-1],ve.setTextureUnits(L.state.textureUnits),vt===!0&&rt.setGlobalState(B.clippingPlanes,L.state.camera)):L=null,P.pop(),P.length>0?N=P[P.length-1]:N=null,J!==null&&J.renderEnd()};function Wt(A,X,ge,ie){if(A.visible===!1)return;if(A.layers.test(X.layers)){if(A.isGroup)ge=A.renderOrder;else if(A.isLOD)A.autoUpdate===!0&&A.update(X);else if(A.isLightProbeGrid)L.pushLightProbeGrid(A);else if(A.isLight)L.pushLight(A),A.castShadow&&L.pushShadow(A);else if(A.isSprite){if(!A.frustumCulled||A.intersectsFrustum(ut)){ie&&Gt.setFromMatrixPosition(A.matrixWorld).applyMatrix4(pt);const We=Se.update(A),Be=A.material;Be.visible&&N.push(A,We,Be,ge,Gt.z,null,X)}}else if((A.isMesh||A.isLine||A.isPoints)&&(!A.frustumCulled||A.intersectsFrustum(ut))){const We=Se.update(A),Be=A.material;if(ie&&(A.boundingSphere!==void 0?(A.boundingSphere===null&&A.computeBoundingSphere(),Gt.copy(A.boundingSphere.center)):(We.boundingSphere===null&&We.computeBoundingSphere(),Gt.copy(We.boundingSphere.center)),Gt.applyMatrix4(A.matrixWorld).applyMatrix4(pt)),Array.isArray(Be)){const qe=We.groups;for(let Ye=0,gt=qe.length;Ye<gt;Ye++){const Tt=qe[Ye],$e=Be[Tt.materialIndex];$e&&$e.visible&&N.push(A,We,$e,ge,Gt.z,Tt,X)}}else Be.visible&&N.push(A,We,Be,ge,Gt.z,null,X)}}const ze=A.children;for(let We=0,Be=ze.length;We<Be;We++)Wt(ze[We],X,ge,ie)}function Mn(A,X,ge,ie){const{opaque:ae,transmissive:ze,transparent:We}=A;L.setupLightsView(ge),vt===!0&&rt.setGlobalState(B.clippingPlanes,ge),ie&&b.viewport(U.copy(ie)),ae.length>0&&Ua(ae,X,ge),ze.length>0&&Ua(ze,X,ge),We.length>0&&Ua(We,X,ge),b.buffers.depth.setTest(!0),b.buffers.depth.setMask(!0),b.buffers.color.setMask(!0),b.setPolygonOffset(!1)}function Tr(A,X,ge,ie){if((ge.isScene===!0?ge.overrideMaterial:null)!==null)return;if(L.state.transmissionRenderTarget[ie.id]===void 0){const $e=Dt.has("EXT_color_buffer_half_float")||Dt.has("EXT_color_buffer_float");L.state.transmissionRenderTarget[ie.id]=new wa(1,1,{generateMipmaps:!0,type:$e?qa:ha,minFilter:Cs,samples:Math.max(4,I.samples),stencilBuffer:c,resolveDepthBuffer:!1,resolveStencilBuffer:!1,storeMultisampledDepthBuffer:!1,storeMultisampledStencilBuffer:!1,colorSpace:kt.workingColorSpace})}const ze=L.state.transmissionRenderTarget[ie.id],We=ie.viewport||U;ze.setSize(We.z*B.transmissionResolutionScale,We.w*B.transmissionResolutionScale);const Be=B.getRenderTarget(),qe=B.getActiveCubeFace(),Ye=B.getActiveMipmapLevel();B.setRenderTarget(ze),B.getClearColor(Ue),Ie=B.getClearAlpha(),Ie<1&&B.setClearColor(16777215,.5),B.clear(),Xt&&dt.render(ge);const gt=B.toneMapping;B.toneMapping=Xa;const Tt=ie.viewport;if(ie.viewport!==void 0&&(ie.viewport=void 0),L.setupLightsView(ie),vt===!0&&rt.setGlobalState(B.clippingPlanes,ie),Ua(A,ge,ie),ve.updateMultisampleRenderTarget(ze),ve.updateRenderTargetMipmap(ze),Dt.has("WEBGL_multisampled_render_to_texture")===!1){let $e=!1;for(let zt=0,dn=X.length;zt<dn;zt++){const rn=X[zt],{object:bt,geometry:Tn,material:Ke,group:wn}=rn;if(Ke.side===xr&&bt.layers.test(ie.layers)){const Et=Ke.side;Ke.side=Oi,Ke.needsUpdate=!0,qt(bt,ge,ie,Tn,Ke,wn),Ke.side=Et,Ke.needsUpdate=!0,$e=!0}}$e===!0&&(ve.updateMultisampleRenderTarget(ze),ve.updateRenderTargetMipmap(ze))}B.setRenderTarget(Be,qe,Ye),B.setClearColor(Ue,Ie),Tt!==void 0&&(ie.viewport=Tt),B.toneMapping=gt}function Ua(A,X,ge){const ie=X.isScene===!0?X.overrideMaterial:null;for(let ae=0,ze=A.length;ae<ze;ae++){const We=A[ae],{object:Be,geometry:qe,group:Ye}=We;let gt=We.material;gt.allowOverride===!0&&ie!==null&&(gt=ie),Be.layers.test(ge.layers)&&qt(Be,X,ge,qe,gt,Ye)}}function qt(A,X,ge,ie,ae,ze){J!==null&&ae.isNodeMaterial&&J.setObject(A,ae),A.onBeforeRender(B,X,ge,ie,ae,ze),A.modelViewMatrix.multiplyMatrices(ge.matrixWorldInverse,A.matrixWorld),A.normalMatrix.getNormalMatrix(A.modelViewMatrix),ae.onBeforeRender(B,X,ge,ie,A,ze),ae.transparent===!0&&ae.side===xr&&ae.forceSinglePass===!1?(ae.side=Oi,ae.needsUpdate=!0,B.renderBufferDirect(ge,X,ie,ae,A,ze),ae.side=Ns,ae.needsUpdate=!0,B.renderBufferDirect(ge,X,ie,ae,A,ze),ae.side=xr):B.renderBufferDirect(ge,X,ie,ae,A,ze),A.onAfterRender(B,X,ge,ie,ae,ze)}function Ji(A,X,ge){X.isScene!==!0&&(X=_n);const ie=ce.get(A),ae=L.state.lights,ze=L.state.shadowsArray,We=ae.state.version,Be=Ne.getParameters(A,ae.state,ze,X,ge,L.state.lightProbeGridArray),qe=Ne.getProgramCacheKey(Be);let Ye=ie.programs;ie.environment=A.isMeshStandardMaterial||A.isMeshLambertMaterial||A.isMeshPhongMaterial?X.environment:null,ie.fog=X.fog;const gt=A.isMeshStandardMaterial||A.isMeshLambertMaterial&&!A.envMap||A.isMeshPhongMaterial&&!A.envMap;ie.envMap=ne.get(A.envMap||ie.environment,gt),ie.envMapRotation=ie.environment!==null&&A.envMap===null?X.environmentRotation:A.envMapRotation,Ye===void 0&&(A.addEventListener("dispose",ti),Ye=new Map,ie.programs=Ye);let Tt=Ye.get(qe);if(Tt!==void 0){if(ie.currentProgram===Tt&&ie.lightsStateVersion===We)return Ii(A,Be),Tt}else Be.uniforms=Ne.getUniforms(A),J!==null&&A.isNodeMaterial&&J.build(A,ge,Be),A.onBeforeCompile(Be,B),Tt=Ne.acquireProgram(Be,qe),Ye.set(qe,Tt),ie.uniforms=Be.uniforms;const $e=ie.uniforms;return(!A.isShaderMaterial&&!A.isRawShaderMaterial||A.clipping===!0)&&($e.clippingPlanes=rt.uniform),Ii(A,Be),ie.needsLights=Na(A),ie.lightsStateVersion=We,ie.needsLights&&($e.ambientLightColor.value=ae.state.ambient,$e.lightProbe.value=ae.state.probe,$e.sunLights.value=ae.state.sun,$e.sunLightShadows.value=ae.state.sunShadow,$e.directionalLights.value=ae.state.directional,$e.directionalLightShadows.value=ae.state.directionalShadow,$e.spotLights.value=ae.state.spot,$e.spotLightShadows.value=ae.state.spotShadow,$e.rectAreaLights.value=ae.state.rectArea,$e.ltc_1.value=ae.state.rectAreaLTC1,$e.ltc_2.value=ae.state.rectAreaLTC2,$e.pointLights.value=ae.state.point,$e.pointLightShadows.value=ae.state.pointShadow,$e.hemisphereLights.value=ae.state.hemi,$e.sunShadowMatrix.value=ae.state.sunShadowMatrix,$e.sunShadowCascade.value=ae.state.sunShadowCascade,$e.directionalShadowMatrix.value=ae.state.directionalShadowMatrix,$e.spotLightMatrix.value=ae.state.spotLightMatrix,$e.spotLightMap.value=ae.state.spotLightMap,$e.pointShadowMatrix.value=ae.state.pointShadowMatrix),ie.lightProbeGrid=L.state.lightProbeGridArray.length>0,ie.currentProgram=Tt,ie.uniformsList=null,Tt}function Pi(A){if(A.uniformsList===null){const X=A.currentProgram.getUniforms();A.uniformsList=Iu.seqWithValue(X.seq,A.uniforms)}return A.uniformsList}function Ii(A,X){const ge=ce.get(A);ge.outputColorSpace=X.outputColorSpace,ge.batching=X.batching,ge.batchingColor=X.batchingColor,ge.instancing=X.instancing,ge.instancingColor=X.instancingColor,ge.instancingMorph=X.instancingMorph,ge.skinning=X.skinning,ge.morphTargets=X.morphTargets,ge.morphNormals=X.morphNormals,ge.morphColors=X.morphColors,ge.morphTargetsCount=X.morphTargetsCount,ge.numClippingPlanes=X.numClippingPlanes,ge.numIntersection=X.numClipIntersection,ge.vertexAlphas=X.vertexAlphas,ge.vertexTangents=X.vertexTangents,ge.toneMapping=X.toneMapping}function ma(A,X){if(A.length===0)return null;if(A.length===1)return A[0].texture!==null?A[0]:null;R.setFromMatrixPosition(X.matrixWorld);for(let ge=0,ie=A.length;ge<ie;ge++){const ae=A[ge];if(ae.texture!==null&&ae.boundingBox.containsPoint(R))return ae}return null}function ga(A,X,ge,ie,ae){X.isScene!==!0&&(X=_n),ve.resetTextureUnits();const ze=X.fog,We=ie.isMeshStandardMaterial||ie.isMeshLambertMaterial||ie.isMeshPhongMaterial?X.environment:null,Be=ee===null?B.outputColorSpace:ee.isXRRenderTarget===!0?ee.texture.colorSpace:kt.workingColorSpace,qe=ie.isMeshStandardMaterial||ie.isMeshLambertMaterial&&!ie.envMap||ie.isMeshPhongMaterial&&!ie.envMap,Ye=ne.get(ie.envMap||We,qe),gt=ie.vertexColors===!0&&!!ge.attributes.color&&ge.attributes.color.itemSize===4,Tt=!!ge.attributes.tangent&&(!!ie.normalMap||ie.anisotropy>0),$e=!!ge.morphAttributes.position,zt=!!ge.morphAttributes.normal,dn=!!ge.morphAttributes.color;let rn=Xa;ie.toneMapped&&(ee===null||ee.isXRRenderTarget===!0)&&(rn=B.toneMapping);const bt=ge.morphAttributes.position||ge.morphAttributes.normal||ge.morphAttributes.color,Tn=bt!==void 0?bt.length:0,Ke=ce.get(ie),wn=L.state.lights;if(vt===!0&&(Mt===!0||A!==fe)){const en=A===fe&&ie.id===oe;rt.setState(ie,A,en)}let Et=!1;ie.version===Ke.__version?(Ke.needsLights&&Ke.lightsStateVersion!==wn.state.version||Ke.outputColorSpace!==Be||ae.isBatchedMesh&&Ke.batching===!1||!ae.isBatchedMesh&&Ke.batching===!0||ae.isBatchedMesh&&Ke.batchingColor===!0&&ae._colorsTexture===null||ae.isBatchedMesh&&Ke.batchingColor===!1&&ae._colorsTexture!==null||ae.isInstancedMesh&&Ke.instancing===!1||!ae.isInstancedMesh&&Ke.instancing===!0||ae.isSkinnedMesh&&Ke.skinning===!1||!ae.isSkinnedMesh&&Ke.skinning===!0||ae.isInstancedMesh&&Ke.instancingColor===!0&&ae.instanceColor===null||ae.isInstancedMesh&&Ke.instancingColor===!1&&ae.instanceColor!==null||ae.isInstancedMesh&&Ke.instancingMorph===!0&&ae.morphTexture===null||ae.isInstancedMesh&&Ke.instancingMorph===!1&&ae.morphTexture!==null||Ke.envMap!==Ye||ie.fog===!0&&Ke.fog!==ze||Ke.numClippingPlanes!==void 0&&(Ke.numClippingPlanes!==rt.numPlanes||Ke.numIntersection!==rt.numIntersection)||Ke.vertexAlphas!==gt||Ke.vertexTangents!==Tt||Ke.morphTargets!==$e||Ke.morphNormals!==zt||Ke.morphColors!==dn||Ke.toneMapping!==rn||Ke.morphTargetsCount!==Tn||!!Ke.lightProbeGrid!=L.state.lightProbeGridArray.length>0)&&(Et=!0):(Et=!0,Ke.__version=ie.version);let Qn=Ke.currentProgram;Et===!0&&(Qn=Ji(ie,X,ae),J&&ie.isNodeMaterial&&J.onUpdateProgram(ie,Qn,Ke));let ci=!1,ni=!1,$i=!1;const jt=Qn.getUniforms(),gn=Ke.uniforms;if(b.useProgram(Qn.program)&&(ci=!0,ni=!0,$i=!0),ie.id!==oe&&(oe=ie.id,ni=!0),Ke.needsLights){const en=ma(L.state.lightProbeGridArray,ae);Ke.lightProbeGrid!==en&&(Ke.lightProbeGrid=en,ni=!0)}if(ci||fe!==A){b.buffers.depth.getReversed()&&A.reversedDepth!==!0&&(A._reversedDepth=!0,A.updateProjectionMatrix()),jt.setValue(Z,"projectionMatrix",A.projectionMatrix),jt.setValue(Z,"viewMatrix",A.matrixWorldInverse);const ea=jt.map.cameraPosition;ea!==void 0&&ea.setValue(Z,_t.setFromMatrixPosition(A.matrixWorld)),I.logarithmicDepthBuffer&&jt.setValue(Z,"logDepthBufFC",2/(Math.log(A.far+1)/Math.LN2)),(ie.isMeshPhongMaterial||ie.isMeshToonMaterial||ie.isMeshLambertMaterial||ie.isMeshBasicMaterial||ie.isMeshStandardMaterial||ie.isShaderMaterial)&&jt.setValue(Z,"isOrthographic",A.isOrthographicCamera===!0),fe!==A&&(fe=A,ni=!0,$i=!0)}if(Ke.needsLights&&(wn.state.sunShadowMap.length>0&&jt.setValue(Z,"sunShadowMap",wn.state.sunShadowMap,ve),wn.state.directionalShadowMap.length>0&&jt.setValue(Z,"directionalShadowMap",wn.state.directionalShadowMap,ve),wn.state.spotShadowMap.length>0&&jt.setValue(Z,"spotShadowMap",wn.state.spotShadowMap,ve),wn.state.pointShadowMap.length>0&&jt.setValue(Z,"pointShadowMap",wn.state.pointShadowMap,ve)),ae.isSkinnedMesh){jt.setOptional(Z,ae,"bindMatrix"),jt.setOptional(Z,ae,"bindMatrixInverse");const en=ae.skeleton;en&&(en.boneTexture===null&&en.computeBoneTexture(),jt.setValue(Z,"boneTexture",en.boneTexture,ve))}ae.isBatchedMesh&&(jt.setOptional(Z,ae,"batchingTexture"),jt.setValue(Z,"batchingTexture",ae._matricesTexture,ve),jt.setOptional(Z,ae,"batchingIdTexture"),jt.setValue(Z,"batchingIdTexture",ae._indirectTexture,ve),jt.setOptional(Z,ae,"batchingColorTexture"),ae._colorsTexture!==null&&jt.setValue(Z,"batchingColorTexture",ae._colorsTexture,ve));const Ai=ge.morphAttributes;if((Ai.position!==void 0||Ai.normal!==void 0||Ai.color!==void 0)&&W.update(ae,ge,Qn),(ni||Ke.receiveShadow!==ae.receiveShadow)&&(Ke.receiveShadow=ae.receiveShadow,jt.setValue(Z,"receiveShadow",ae.receiveShadow)),(ie.isMeshStandardMaterial||ie.isMeshLambertMaterial||ie.isMeshPhongMaterial)&&ie.envMap===null&&X.environment!==null&&(gn.envMapIntensity.value=X.environmentIntensity),gn.dfgLUT!==void 0&&(gn.dfgLUT.value=RC()),ni){if(jt.setValue(Z,"toneMappingExposure",B.toneMappingExposure),Ke.needsLights&&sn(gn,$i),ze&&ie.fog===!0&&Ze.refreshFogUniforms(gn,ze),Ze.refreshMaterialUniforms(gn,ie,ye,ue,L.state.transmissionRenderTarget[A.id]),Ke.needsLights&&Ke.lightProbeGrid){const en=Ke.lightProbeGrid;gn.probesSH.value=en.texture,gn.probesMin.value.copy(en.boundingBox.min),gn.probesMax.value.copy(en.boundingBox.max),gn.probesResolution.value.copy(en.resolution)}Iu.upload(Z,Pi(Ke),gn,ve)}if(ie.isShaderMaterial&&ie.uniformsNeedUpdate===!0&&(Iu.upload(Z,Pi(Ke),gn,ve),ie.uniformsNeedUpdate=!1),ie.isSpriteMaterial&&jt.setValue(Z,"center",ae.center),jt.setValue(Z,"modelViewMatrix",ae.modelViewMatrix),jt.setValue(Z,"normalMatrix",ae.normalMatrix),jt.setValue(Z,"modelMatrix",ae.matrixWorld),ie.uniformsGroups!==void 0){const en=ie.uniformsGroups;for(let ea=0,Fi=en.length;ea<Fi;ea++){const Si=en[ea];Re.update(Si,Qn),Re.bind(Si,Qn)}}return Qn}function sn(A,X){A.ambientLightColor.needsUpdate=X,A.lightProbe.needsUpdate=X,A.sunLights.needsUpdate=X,A.sunLightShadows.needsUpdate=X,A.directionalLights.needsUpdate=X,A.directionalLightShadows.needsUpdate=X,A.pointLights.needsUpdate=X,A.pointLightShadows.needsUpdate=X,A.spotLights.needsUpdate=X,A.spotLightShadows.needsUpdate=X,A.rectAreaLights.needsUpdate=X,A.hemisphereLights.needsUpdate=X}function Na(A){return A.isMeshLambertMaterial||A.isMeshToonMaterial||A.isMeshPhongMaterial||A.isMeshStandardMaterial||A.isShadowMaterial||A.isShaderMaterial&&A.lights===!0}this.getActiveCubeFace=function(){return z},this.getActiveMipmapLevel=function(){return H},this.getRenderTarget=function(){return ee},this.setRenderTargetTextures=function(A,X,ge){const ie=ce.get(A);ie.__autoAllocateDepthBuffer=A.resolveDepthBuffer===!1,ie.__autoAllocateDepthBuffer===!1&&(ie.__useRenderToTexture=!1),ce.get(A.texture).__webglTexture=X,ce.get(A.depthTexture).__webglTexture=ie.__autoAllocateDepthBuffer?void 0:ge,ie.__hasExternalTextures=!0},this.setRenderTargetFramebuffer=function(A,X){const ge=ce.get(A);ge.__webglFramebuffer=X,ge.__useDefaultFramebuffer=X===void 0},this.setRenderTarget=function(A,X=0,ge=0){ee=A,z=X,H=ge;let ie=null,ae=!1,ze=!1;if(A){const Be=ce.get(A);if(Be.__useDefaultFramebuffer!==void 0){b.bindFramebuffer(Z.FRAMEBUFFER,Be.__webglFramebuffer),U.copy(A.viewport),re.copy(A.scissor),xe=A.scissorTest,b.viewport(U),b.scissor(re),b.setScissorTest(xe),oe=-1;return}else if(Be.__webglFramebuffer===void 0)ve.setupRenderTarget(A);else if(Be.__hasExternalTextures)ve.rebindTextures(A,ce.get(A.texture).__webglTexture,ce.get(A.depthTexture).__webglTexture);else if(A.depthBuffer){const gt=A.depthTexture;if(Be.__boundDepthTexture!==gt){if(gt!==null&&ce.has(gt)&&(A.width!==gt.image.width||A.height!==gt.image.height))throw new Error("THREE.WebGLRenderer: Attached DepthTexture is initialized to the incorrect size.");ve.setupDepthRenderbuffer(A)}}const qe=A.texture;(qe.isData3DTexture||qe.isDataArrayTexture||qe.isCompressedArrayTexture)&&(ze=!0);const Ye=ce.get(A).__webglFramebuffer;A.isWebGLCubeRenderTarget?(Array.isArray(Ye[X])?ie=Ye[X][ge]:ie=Ye[X],ae=!0):A.samples>0&&ve.useMultisampledRTT(A)===!1?ie=ce.get(A).__webglMultisampledFramebuffer:Array.isArray(Ye)?ie=Ye[ge]:ie=Ye,U.copy(A.viewport),re.copy(A.scissor),xe=A.scissorTest}else U.copy(Ge).multiplyScalar(ye).floor(),re.copy(mt).multiplyScalar(ye).floor(),xe=un;if(ge!==0&&(ie=se),b.bindFramebuffer(Z.FRAMEBUFFER,ie)&&b.drawBuffers(A,ie),b.viewport(U),b.scissor(re),b.setScissorTest(xe),ae){const Be=ce.get(A.texture);Z.framebufferTexture2D(Z.FRAMEBUFFER,Z.COLOR_ATTACHMENT0,Z.TEXTURE_CUBE_MAP_POSITIVE_X+X,Be.__webglTexture,ge)}else if(ze){const Be=X;for(let qe=0;qe<A.textures.length;qe++){const Ye=ce.get(A.textures[qe]);Z.framebufferTextureLayer(Z.FRAMEBUFFER,Z.COLOR_ATTACHMENT0+qe,Ye.__webglTexture,ge,Be)}}else if(A!==null&&ge!==0){const Be=ce.get(A.texture);Z.framebufferTexture2D(Z.FRAMEBUFFER,Z.COLOR_ATTACHMENT0,Z.TEXTURE_2D,Be.__webglTexture,ge)}oe=-1};function xi(A){const X=ce.get(A);return(X.__readFormat!==A.format||X.__readType!==A.type)&&(X.__readFormat=A.format,X.__readType=A.type,X.__formatReadable=I.textureFormatReadable(A.format),X.__typeReadable=I.textureTypeReadable(A.type)),X}this.readRenderTargetPixels=function(A,X,ge,ie,ae,ze,We,Be=0){if(!(A&&A.isWebGLRenderTarget)){Zt("WebGLRenderer.readRenderTargetPixels: renderTarget is not THREE.WebGLRenderTarget.");return}let qe=ce.get(A).__webglFramebuffer;if(A.isWebGLCubeRenderTarget&&We!==void 0&&(qe=qe[We]),qe){b.bindFramebuffer(Z.FRAMEBUFFER,qe);try{const Ye=A.textures[Be],gt=Ye.format,Tt=Ye.type;A.textures.length>1&&Z.readBuffer(Z.COLOR_ATTACHMENT0+Be);const $e=xi(Ye);if($e.__formatReadable===!1){Zt("WebGLRenderer.readRenderTargetPixels: renderTarget is not in RGBA or implementation defined format.");return}if($e.__typeReadable===!1){Zt("WebGLRenderer.readRenderTargetPixels: renderTarget is not in UnsignedByteType or implementation defined type.");return}X>=0&&X<=A.width-ie&&ge>=0&&ge<=A.height-ae&&Z.readPixels(X,ge,ie,ae,Pe.convert(gt),Pe.convert(Tt),ze)}finally{const Ye=ee!==null?ce.get(ee).__webglFramebuffer:null;b.bindFramebuffer(Z.FRAMEBUFFER,Ye)}}},this.readRenderTargetPixelsAsync=async function(A,X,ge,ie,ae,ze,We,Be=0){if(!(A&&A.isWebGLRenderTarget))throw new Error("THREE.WebGLRenderer.readRenderTargetPixels: renderTarget is not THREE.WebGLRenderTarget.");let qe=ce.get(A).__webglFramebuffer;if(A.isWebGLCubeRenderTarget&&We!==void 0&&(qe=qe[We]),qe)if(X>=0&&X<=A.width-ie&&ge>=0&&ge<=A.height-ae){b.bindFramebuffer(Z.FRAMEBUFFER,qe);const Ye=A.textures[Be],gt=Ye.format,Tt=Ye.type;A.textures.length>1&&Z.readBuffer(Z.COLOR_ATTACHMENT0+Be);const $e=xi(Ye);if($e.__formatReadable===!1)throw new Error("THREE.WebGLRenderer.readRenderTargetPixelsAsync: renderTarget is not in RGBA or implementation defined format.");if($e.__typeReadable===!1)throw new Error("THREE.WebGLRenderer.readRenderTargetPixelsAsync: renderTarget is not in UnsignedByteType or implementation defined type.");const zt=Z.createBuffer();Z.bindBuffer(Z.PIXEL_PACK_BUFFER,zt),Z.bufferData(Z.PIXEL_PACK_BUFFER,ze.byteLength,Z.STREAM_READ),Z.readPixels(X,ge,ie,ae,Pe.convert(gt),Pe.convert(Tt),0),Z.bindBuffer(Z.PIXEL_PACK_BUFFER,null);const dn=ee!==null?ce.get(ee).__webglFramebuffer:null;b.bindFramebuffer(Z.FRAMEBUFFER,dn);const rn=Z.fenceSync(Z.SYNC_GPU_COMMANDS_COMPLETE,0);return Z.flush(),await bb(Z,rn,4),Z.bindBuffer(Z.PIXEL_PACK_BUFFER,zt),Z.getBufferSubData(Z.PIXEL_PACK_BUFFER,0,ze),Z.bindBuffer(Z.PIXEL_PACK_BUFFER,null),Z.deleteBuffer(zt),Z.deleteSync(rn),ze}else throw new Error("THREE.WebGLRenderer.readRenderTargetPixelsAsync: requested read bounds are out of range.")},this.copyFramebufferToTexture=function(A,X=null,ge=0){const ie=Math.pow(2,-ge),ae=Math.floor(A.image.width*ie),ze=Math.floor(A.image.height*ie),We=X!==null?X.x:0,Be=X!==null?X.y:0;ve.setTexture2D(A,0),Z.copyTexSubImage2D(Z.TEXTURE_2D,ge,0,0,We,Be,ae,ze),b.unbindTexture()},this.copyTextureToTexture=function(A,X,ge=null,ie=null,ae=0,ze=0){let We,Be,qe,Ye,gt,Tt,$e,zt,dn;const rn=A.isCompressedTexture?A.mipmaps[ze]:A.image;if(ge!==null)We=ge.max.x-ge.min.x,Be=ge.max.y-ge.min.y,qe=ge.isBox3?ge.max.z-ge.min.z:1,Ye=ge.min.x,gt=ge.min.y,Tt=ge.isBox3?ge.min.z:0;else{const gn=Math.pow(2,-ae);We=Math.floor(rn.width*gn),Be=Math.floor(rn.height*gn),A.isDataArrayTexture?qe=rn.depth:A.isData3DTexture?qe=Math.floor(rn.depth*gn):qe=1,Ye=0,gt=0,Tt=0}ie!==null?($e=ie.x,zt=ie.y,dn=ie.z):($e=0,zt=0,dn=0);const bt=Pe.convert(X.format),Tn=Pe.convert(X.type);let Ke;X.isData3DTexture?(ve.setTexture3D(X,0),Ke=Z.TEXTURE_3D):X.isDataArrayTexture||X.isCompressedArrayTexture?(ve.setTexture2DArray(X,0),Ke=Z.TEXTURE_2D_ARRAY):(ve.setTexture2D(X,0),Ke=Z.TEXTURE_2D),b.activeTexture(Z.TEXTURE0),b.pixelStorei(Z.UNPACK_FLIP_Y_WEBGL,X.flipY),b.pixelStorei(Z.UNPACK_PREMULTIPLY_ALPHA_WEBGL,X.premultiplyAlpha),b.pixelStorei(Z.UNPACK_ALIGNMENT,X.unpackAlignment);const wn=b.getParameter(Z.UNPACK_ROW_LENGTH),Et=b.getParameter(Z.UNPACK_IMAGE_HEIGHT),Qn=b.getParameter(Z.UNPACK_SKIP_PIXELS),ci=b.getParameter(Z.UNPACK_SKIP_ROWS),ni=b.getParameter(Z.UNPACK_SKIP_IMAGES);b.pixelStorei(Z.UNPACK_ROW_LENGTH,rn.width),b.pixelStorei(Z.UNPACK_IMAGE_HEIGHT,rn.height),b.pixelStorei(Z.UNPACK_SKIP_PIXELS,Ye),b.pixelStorei(Z.UNPACK_SKIP_ROWS,gt),b.pixelStorei(Z.UNPACK_SKIP_IMAGES,Tt);const $i=A.isDataArrayTexture||A.isData3DTexture,jt=X.isDataArrayTexture||X.isData3DTexture;if(A.isDepthTexture){const gn=ce.get(A),Ai=ce.get(X),en=ce.get(gn.__renderTarget),ea=ce.get(Ai.__renderTarget);b.bindFramebuffer(Z.READ_FRAMEBUFFER,en.__webglFramebuffer),b.bindFramebuffer(Z.DRAW_FRAMEBUFFER,ea.__webglFramebuffer);for(let Fi=0;Fi<qe;Fi++)$i&&(Z.framebufferTextureLayer(Z.READ_FRAMEBUFFER,Z.COLOR_ATTACHMENT0,ce.get(A).__webglTexture,ae,Tt+Fi),Z.framebufferTextureLayer(Z.DRAW_FRAMEBUFFER,Z.COLOR_ATTACHMENT0,ce.get(X).__webglTexture,ze,dn+Fi)),Z.blitFramebuffer(Ye,gt,We,Be,$e,zt,We,Be,Z.DEPTH_BUFFER_BIT,Z.NEAREST);b.bindFramebuffer(Z.READ_FRAMEBUFFER,null),b.bindFramebuffer(Z.DRAW_FRAMEBUFFER,null)}else if(ae!==0||A.isRenderTargetTexture||ce.has(A)){const gn=ce.get(A),Ai=ce.get(X);b.bindFramebuffer(Z.READ_FRAMEBUFFER,Y),b.bindFramebuffer(Z.DRAW_FRAMEBUFFER,j);for(let en=0;en<qe;en++)$i?Z.framebufferTextureLayer(Z.READ_FRAMEBUFFER,Z.COLOR_ATTACHMENT0,gn.__webglTexture,ae,Tt+en):Z.framebufferTexture2D(Z.READ_FRAMEBUFFER,Z.COLOR_ATTACHMENT0,Z.TEXTURE_2D,gn.__webglTexture,ae),jt?Z.framebufferTextureLayer(Z.DRAW_FRAMEBUFFER,Z.COLOR_ATTACHMENT0,Ai.__webglTexture,ze,dn+en):Z.framebufferTexture2D(Z.DRAW_FRAMEBUFFER,Z.COLOR_ATTACHMENT0,Z.TEXTURE_2D,Ai.__webglTexture,ze),ae!==0?Z.blitFramebuffer(Ye,gt,We,Be,$e,zt,We,Be,Z.COLOR_BUFFER_BIT,Z.NEAREST):jt?Z.copyTexSubImage3D(Ke,ze,$e,zt,dn+en,Ye,gt,We,Be):Z.copyTexSubImage2D(Ke,ze,$e,zt,Ye,gt,We,Be);b.bindFramebuffer(Z.READ_FRAMEBUFFER,null),b.bindFramebuffer(Z.DRAW_FRAMEBUFFER,null)}else jt?A.isDataTexture||A.isData3DTexture?Z.texSubImage3D(Ke,ze,$e,zt,dn,We,Be,qe,bt,Tn,rn.data):X.isCompressedArrayTexture?Z.compressedTexSubImage3D(Ke,ze,$e,zt,dn,We,Be,qe,bt,rn.data):Z.texSubImage3D(Ke,ze,$e,zt,dn,We,Be,qe,bt,Tn,rn):A.isDataTexture?Z.texSubImage2D(Z.TEXTURE_2D,ze,$e,zt,We,Be,bt,Tn,rn.data):A.isCompressedTexture?Z.compressedTexSubImage2D(Z.TEXTURE_2D,ze,$e,zt,rn.width,rn.height,bt,rn.data):Z.texSubImage2D(Z.TEXTURE_2D,ze,$e,zt,We,Be,bt,Tn,rn);b.pixelStorei(Z.UNPACK_ROW_LENGTH,wn),b.pixelStorei(Z.UNPACK_IMAGE_HEIGHT,Et),b.pixelStorei(Z.UNPACK_SKIP_PIXELS,Qn),b.pixelStorei(Z.UNPACK_SKIP_ROWS,ci),b.pixelStorei(Z.UNPACK_SKIP_IMAGES,ni),ze===0&&X.generateMipmaps&&Z.generateMipmap(Ke),b.unbindTexture()},this.initRenderTarget=function(A){ce.get(A).__webglFramebuffer===void 0&&ve.setupRenderTarget(A)},this.initTexture=function(A){A.isCubeTexture?ve.setTextureCube(A,0):A.isData3DTexture?ve.setTexture3D(A,0):A.isDataArrayTexture||A.isCompressedArrayTexture?ve.setTexture2DArray(A,0):ve.setTexture2D(A,0),b.unbindTexture()},this.resetState=function(){z=0,H=0,ee=null,b.reset(),Ve.reset()},typeof __THREE_DEVTOOLS__<"u"&&__THREE_DEVTOOLS__.dispatchEvent(new CustomEvent("observe",{detail:this}))}get coordinateSystem(){return ka}get outputColorSpace(){return this._outputColorSpace}set outputColorSpace(e){this._outputColorSpace=e;const i=this.getContext();i.drawingBufferColorSpace=kt._getDrawingBufferColorSpace(e),i.unpackColorSpace=kt._getUnpackColorSpace()}}const $_=[{key:"short",label:"สั้น",timeframe:"M15–H1",ring:"วงใน"},{key:"medium",label:"กลาง",timeframe:"H1–D1",ring:"วงกลาง"},{key:"long",label:"ยาว",timeframe:"D1–W1",ring:"วงนอก"}],ex={AUD:"AUSTRALIAN DOLLAR",CAD:"CANADIAN DOLLAR",CHF:"SWISS FRANC",EUR:"EURO",GBP:"BRITISH POUND",JPY:"JAPANESE YEN",NZD:"NEW ZEALAND DOLLAR",USD:"US DOLLAR"},CC=["AUDCAD","AUDCHF","AUDJPY","AUDNZD","AUDUSD","CADCHF","CADJPY","CHFJPY","EURAUD","EURCAD","EURCHF","EURGBP","EURJPY","EURNZD","EURUSD","GBPAUD","GBPCAD","GBPCHF","GBPJPY","GBPNZD","GBPUSD","NZDCAD","NZDCHF","NZDJPY","NZDUSD","USDCAD","USDCHF","USDJPY"],wC=["EUR","GBP","AUD","NZD","USD","CAD","CHF"],DC=[...CC.map(s=>({symbol:s,name:`${ex[s.slice(0,3)]} / ${ex[s.slice(3)]}`,kind:s.includes("USD")?"MAJOR":"CROSS",assetClass:"forex",clusterId:wC.find(e=>s.slice(0,3)===e||s.slice(3)===e)})),{symbol:"XAUUSD",name:"GOLD",kind:"METALS",assetClass:"metals",clusterId:"METALS"},{symbol:"XAGUSD",name:"SILVER",kind:"METALS",assetClass:"metals",clusterId:"METALS"},{symbol:"WTI",name:"WEST TEXAS INTERMEDIATE",kind:"OIL",assetClass:"oil",clusterId:"OIL"},{symbol:"BRENT",name:"BRENT CRUDE OIL",kind:"OIL",assetClass:"oil",clusterId:"OIL"}],UC=new Set(["AUDNZD:long","CADCHF:short","EURCHF:medium","GBPCHF:long","NZDCAD:medium"]);function Kx(s){let e=2166136261;for(const i of s)e=Math.imul(e^i.charCodeAt(0),16777619);return e>>>0}function NC(s){let e=s>>>0;return()=>{e=e+1831565813>>>0;let i=Math.imul(e^e>>>15,1|e);return i^=i+Math.imul(i^i>>>7,61|i),((i^i>>>14)>>>0)/4294967296}}function LC(s,e,i){if(i==="unknown")return[];const r=NC(Kx(`${s}:${e}:${i}`)),l=r()*Math.PI*2,c=2+Math.floor(r()*3),f=i==="up"?9:i==="down"?-9:0,h=i==="range"?1.25:.9;return Array.from({length:70},(m,p)=>{const g=p/69,_=Math.sin(Math.PI*g),v=Math.sin(g*Math.PI*2*c+l),x=(r()-.5)*.45;return Number((100+f*g+(v*h+x)*_).toFixed(4))})}const yr=DC.map(s=>{const{symbol:e}=s,i=$_.map(({key:r})=>UC.has(`${e}:${r}`)?"unknown":["up","range","down"][Kx(`${e}:${r}`)%3]);return e==="EURUSD"&&i.splice(0,3,"up","range","down"),e==="XAUUSD"&&i.splice(0,3,"up","range","up"),{...s,states:i,series:$_.map(({key:r},l)=>LC(e,r,i[l]))}}),OC=[{id:"EUR",label:"EUR",assetClass:"forex",color:"#56d9ed"},{id:"GBP",label:"GBP",assetClass:"forex",color:"#dc91db"},{id:"AUD",label:"AUD",assetClass:"forex",color:"#e4bd72"},{id:"NZD",label:"NZD",assetClass:"forex",color:"#67d9d2"},{id:"USD",label:"USD",assetClass:"forex",color:"#71abef"},{id:"CAD",label:"CAD",assetClass:"forex",color:"#a89be0"},{id:"CHF",label:"CHF",assetClass:"forex",color:"#bacbd8"},{id:"METALS",label:"METALS",assetClass:"metals",color:"#e4c46f"},{id:"OIL",label:"OIL",assetClass:"oil",color:"#da9b56"}].map(s=>({...s,count:yr.filter(({clusterId:e})=>e===s.id).length})),PC=[.5,1,1.8];function IC(s,e,{playing:i,hidden:r=!1,dragging:l=!1,speed:c=1}){if(!i||r||l)return s;const f=PC.includes(c)?c:1;return s+Math.max(0,Math.min(.05,Number.isFinite(e)?e:0))*f}function tx(s,e,i,r,l,c){const f=e+l*c,h=s*(1+.075*Math.sin(l*.32+r));return[Math.cos(f)*h,Math.sin(f)*h*i,.14+Math.sin(f*2+r)*.18]}function FC(s,e,i,{rate:r=.13,phase:l=0,meteor:c=!1}={}){const f=s.getPoints(180),h=new zn().setFromPoints(f);h.setAttribute("aProgress",new Cn(f.map((p,g)=>g/180),1));const m=new Yn({transparent:!0,depthWrite:!1,blending:Ca,uniforms:{time:i,tint:{value:new Rt(e)},rate:{value:r},phase:{value:l},pixelScale:{value:1},meteor:{value:c?1:0}},vertexShader:`attribute float aProgress; uniform float time; uniform float rate;
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
      }`});return new Ds(h,m)}const zC={unavailable:"#65656b"},Qx=Math.PI*2;function Vh(s,e,i){const r=Math.max(0,Math.min(1,i));return`#${[1,3,5].map(c=>{const f=Number.parseInt(s.slice(c,c+2),16),h=Number.parseInt(e.slice(c,c+2),16);return Math.round(f+(h-f)*r).toString(16).padStart(2,"0")}).join("")}`}const BC=["#8c9bb5","#7fbaa4","#3fc991","#13d976","#05b85c","#009e4c"],HC=["#8c9bb5","#ba8e99","#db6678","#cf1732","#ad1028","#940b20"];function ef(s){const e=(s==null?void 0:s.long)+(s==null?void 0:s.short);if(!((s==null?void 0:s.available)===!0&&Number.isFinite(s.long)&&Number.isFinite(s.short)&&s.long>=0&&s.long<=100&&s.short>=0&&s.short<=100&&e>0&&Math.abs(e-100)<=2))return{available:!1,bias:"unavailable",strength:0,dominance:null,color:zC.unavailable,core:"#74747a",corona:"#65656b",particles:"#77777e",highlight:"#98989f",brightness:.4};const r=s.long/e*100,l=s.long===s.short?"neutral":s.long>s.short?"long":"short",c=Math.abs(r-50)/50,f=Math.min(5,c*5),h=Math.min(4,Math.floor(f)),m=l==="short"?HC:BC,p=Vh(m[h],m[h+1],f-h);return{available:!0,bias:l,strength:c,dominance:Math.max(r,100-r),color:p,core:Vh(p,"#ffffff",.09),corona:p,particles:p,highlight:Vh(p,"#ffffff",.25),brightness:.62+c*.38}}function em(s){return{coreTint:{value:new Rt(s.core)},coronaTint:{value:new Rt(s.corona)},particleTint:{value:new Rt(s.particles)},highlightTint:{value:new Rt(s.highlight)},brightness:{value:s.brightness}}}function Jx(s=""){let e=2166136261;for(const i of String(s).trim().toUpperCase())e=Math.imul(e^i.charCodeAt(0),16777619);return(e>>>0)/4294967296*Qx}function GC(s){let e=s>>>0;return()=>(e=Math.imul(e,1664525)+1013904223>>>0,e/4294967296)}function nx(s,e=!1){const i=GC(e?76183:42851),r=[],l=[],c=[];for(let h=0;h<s;h++){const m=i()*Qx;if(e){const p=.22+i()*.27;r.push(Math.cos(m)*p,Math.sin(m)*p*.56,(i()-.5)*.09+Math.sin(m*3)*.045)}else{const p=.135+Math.pow(i(),2.1)*.42,g=i()*2-1,_=Math.sqrt(1-g*g);r.push(Math.cos(m)*_*p,Math.sin(m)*_*p,g*p)}l.push((e?.005:.007)+i()*(e?.011:.021)),c.push(i())}const f=new zn;return f.setAttribute("position",new Cn(r,3)),f.setAttribute("aSize",new Cn(l,1)),f.setAttribute("aSeed",new Cn(c,1)),f.computeBoundingSphere(),f}function $x(){return{core:new Jl(.148,28,20),bead:new Jl(.012,8,6),particles:nx(480),flow:nx(130,!0),filamentMaterials:new Map,glow:new zn().setAttribute("position",new Cn([0,0,0],3))}}function VC(s){return new Yn({uniforms:{time:{value:0},phase:{value:0},muted:{value:s.available?0:1},...em(s)},vertexShader:`uniform float time; uniform float phase; varying vec3 surface; varying vec3 viewNormal; varying vec3 viewPosition;
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
      }`})}function ix(s,e,i){return new Yn({transparent:!0,depthWrite:!1,blending:Ca,uniforms:{time:{value:0},phase:{value:0},viewportHeight:{value:900},alpha:{value:i},available:{value:s.available?1:0},longFraction:{value:e},...em(s)},vertexShader:`attribute float aSize;attribute float aSeed;uniform float time;uniform float phase;uniform float viewportHeight;varying float seed;varying float radius;
      void main(){seed=aSeed;radius=length(position);vec3 p=position*(1.0+sin(time*.46+aSeed*15.0+phase)*.045);
        p+=vec3(sin(time*.16+aSeed*22.0),cos(time*.19+aSeed*17.0),sin(time*.13+aSeed*31.0))*.009;
        vec4 mv=modelViewMatrix*vec4(p,1.0);float divisor=projectionMatrix[2][3]<-.5?max(.1,-mv.z):1.0;
        gl_PointSize=clamp(aSize*viewportHeight*projectionMatrix[1][1]/divisor,1.0,26.0);gl_Position=projectionMatrix*mv;}`,fragmentShader:`uniform float time;uniform float alpha;uniform float brightness;uniform vec3 particleTint;uniform vec3 highlightTint;varying float seed;varying float radius;
      void main(){float r=length(gl_PointCoord-.5)*2.0;if(r>1.0)discard;
        vec3 stellar=mix(highlightTint,particleTint,smoothstep(.13,.32,radius));
        float envelope=pow(1.0-r,2.0)*(0.66+.34*sin(seed*31.0+time*.7));gl_FragColor=vec4(stellar,envelope*alpha*(.55+brightness*.45));
        #include <tonemapping_fragment>
        #include <colorspace_fragment>
      }`})}function kC(s){return new Yn({transparent:!0,depthWrite:!1,blending:Ca,uniforms:{viewportHeight:{value:900},time:{value:0},available:{value:s.available?1:0},...em(s)},vertexShader:"uniform float viewportHeight;void main(){vec4 mv=modelViewMatrix*vec4(position,1.0);float divisor=projectionMatrix[2][3]<-.5?max(.1,-mv.z):1.0;gl_PointSize=1.26*viewportHeight*projectionMatrix[1][1]/divisor;gl_Position=projectionMatrix*mv;}",fragmentShader:`uniform float time;uniform float brightness;uniform vec3 coronaTint;uniform vec3 coreTint;void main(){vec2 p=(gl_PointCoord-.5)*2.0;float r=length(p);if(r>1.0)discard;
      float angle=atan(p.y,p.x);float wisps=1.0+sin(angle*5.0+time*.12)*.12+sin(angle*9.0-time*.09)*.06;
      float haze=exp(-r*r*12.0)*pow(1.0-r,1.3)*wisps;vec3 color=mix(coronaTint,coreTint,exp(-r*r*36.0));
      gl_FragColor=vec4(color,haze*(.30+brightness*.24));
      #include <tonemapping_fragment>
      #include <colorspace_fragment>
    }`})}function XC(s,e,i){const r=new zn;r.setAttribute("position",new Cn(new Float32Array(147),3));const l=s%3?e.corona:e.highlight,c=`${l}:${s%2}`;i.filamentMaterials.has(c)||i.filamentMaterials.set(c,new Kp({color:l,transparent:!0,opacity:(s%2?.12:.2)*e.brightness,depthWrite:!1,blending:Ca}));const f=i.filamentMaterials.get(c),h=new Qp(r,f);return h.rotation.set(s*.93,s*.71,s*1.13),{mesh:h,index:s}}function eS(s,e,i=0){const r=new da,l=new da;r.add(l);const c=ef(s),f=c.available,h=f?s.long/(s.long+s.short):.5,m=new Ki(e.core,VC(c)),p=new Ds(e.glow,kC(c)),g=new Ds(e.particles,ix(c,h,.72)),_=new Ds(e.flow,ix(c,h,.3));_.rotation.x=.65;const v=Array.from({length:6},(D,M)=>XC(M,c,e)),x=new Ki(e.bead,new Qu({color:c.highlight,transparent:!0,opacity:.65,depthWrite:!1,blending:Ca}));x.visible=f,l.add(p,m,g,_,...v.map(D=>D.mesh),x);const E={group:r,plane:l,core:m,glow:p,particles:g,flow:_,filaments:v,bead:x,phase:i,appearance:c,available:f,ringCount:0,segments:[],composition:f?{long:s.long,short:s.short}:null};return tm(E,0),E}function tS(s,e){const i=ef(e),r=i.available;s.ownsFilamentMaterials||(s.filaments.forEach(({mesh:c})=>{c.material=c.material.clone()}),s.ownsFilamentMaterials=!0),s.appearance=i,s.available=r,s.composition=r?{long:e.long,short:e.short}:null;const l={coreTint:i.core,coronaTint:i.corona,particleTint:i.particles,highlightTint:i.highlight};for(const c of[s.core,s.glow,s.particles,s.flow]){const f=c.material.uniforms;for(const[h,m]of Object.entries(l))f[h]&&f[h].value.set(m);f.brightness&&(f.brightness.value=i.brightness),f.available&&(f.available.value=r?1:0),f.muted&&(f.muted.value=r?0:1),f.longFraction&&(f.longFraction.value=r?e.long/(e.long+e.short):.5)}s.bead.visible=r,s.bead.material.color.set(i.highlight),s.filaments.forEach(({mesh:c,index:f})=>{c.material.color.set(f%3?i.corona:i.highlight),c.material.opacity=(f%2?.12:.2)*i.brightness})}function tm(s,e){const i=Number.isFinite(e)?e:0,r=Number.isFinite(s.phase)?s.phase:0;s.plane.rotation.set(.16+Math.sin(i*.09+r)*.06,i*.055+r,-.16),s.core.rotation.set(i*.047,i*.09+r,0),s.particles.rotation.set(i*.035,i*-.067,i*.045),s.flow.rotation.z=i*.13+r;for(const f of[s.core,s.glow,s.particles,s.flow])f.material.uniforms.time.value=i,f.material.uniforms.phase&&(f.material.uniforms.phase.value=r);for(const{mesh:f,index:h}of s.filaments){const m=f.geometry.attributes.position,p=.12+h*.021;for(let g=0;g<m.count;g++){const _=g/(m.count-1),v=_*Math.PI,x=Math.sin(v),E=Math.sin(_*17+i*.21+r+h)*.009*x;m.setXYZ(g,Math.cos(v)*(.085+h*.004),.09+x*p+E,Math.sin(_*8+h+i*.13)*.025*x)}m.needsUpdate=!0,f.geometry.boundingSphere||(f.geometry.boundingSphere=new Fs(new Q,.4))}const l=i*.35+r,c=.21+Math.sin(i*.17+r)*.025;s.bead.position.set(Math.cos(l)*c,Math.sin(l)*c*.52,Math.sin(l*1.7)*.06)}function nS(s,e){const i=Number.isFinite(e)&&e>0?e:900;for(const r of[s.glow,s.particles,s.flow])r.material.uniforms.viewportHeight.value=i}function iS(s,e){var l;const i=new Set,r=new Set;s.traverse(c=>{c.geometry&&i.add(c.geometry),c.material&&(Array.isArray(c.material)?c.material:[c.material]).forEach(f=>r.add(f))}),e&&(Object.values(e).forEach(c=>{c!=null&&c.isBufferGeometry&&i.add(c)}),(l=e.filamentMaterials)==null||l.forEach(c=>r.add(c))),i.forEach(c=>c.dispose()),r.forEach(c=>c.dispose())}const Us=new Map(yr.map(s=>[s.symbol,s])),WC=()=>({available:!1,long:null,short:null,avgLong:null,avgShort:null,asOf:null});let ji={schemaVersion:1,mode:"live",generatedAt:null,connection:"loading",revision:0,sentiment:{source:"Myfxbook",status:"loading",items:[]},correlations:{source:"MT5",status:"loading",items:[]},news:{source:"Forex Factory",status:"loading",events:[],calendarEvents:[]}};const Yu=new Set,qC=s=>(Yu.add(s),()=>Yu.delete(s)),YC=()=>ji,nm=s=>typeof s=="number"&&Number.isFinite(s)&&Math.abs(s)<=1,Du=s=>typeof s=="number"&&Number.isFinite(s)?s:null,Lp=s=>{try{const e=new URL(s);return e.protocol==="https:"&&!e.username&&!e.password?e.href:null}catch{return null}};function jC(s,e=Date.now(),i=!1){var c;const r=(c=s==null?void 0:s.mirror)==null?void 0:c.publishedAt;if(!i&&!r)return{connection:"online",heartbeatAt:null};const l=typeof r=="string"&&/(Z|[+-]\d{2}:\d{2})$/.test(r)?Date.parse(r):NaN;return{connection:Number.isFinite(l)&&e-l<=12e4&&l-e<=3e4?"online":"stale",heartbeatAt:Number.isFinite(l)?r:null}}function ZC(s,{requireHeartbeat:e=!1,now:i=Date.now()}={}){var h,m,p;if((s==null?void 0:s.schemaVersion)!==1||(s==null?void 0:s.mode)!=="live"||!Array.isArray((h=s.sentiment)==null?void 0:h.items)||!Array.isArray((m=s.correlations)==null?void 0:m.items)||!Array.isArray((p=s.news)==null?void 0:p.events))throw new Error("invalid_market_snapshot");const r=s.sentiment.items.filter(g=>Us.has(g.symbol)).map(g=>{const _=Du(g.long),v=Du(g.short),x=g.available===!0&&_!==null&&v!==null&&_>=0&&_<=100&&v>=0&&v<=100&&Math.abs(_+v-100)<=2;return{...g,available:x,long:x?_:null,short:x?v:null,avgLong:Du(g.avgLong),avgShort:Du(g.avgShort)}}),l=new Set,c=s.correlations.items.filter(g=>Us.has(g.source)&&Us.has(g.target)&&g.source!==g.target).filter(g=>{const _=[g.source,g.target].sort().join("|");return l.has(_)?!1:(l.add(_),!0)}).map(g=>({...g,value:nm(g.value)?g.value:null})),f=g=>Array.isArray(g)?g.filter(_=>_&&typeof _.id=="string"&&typeof _.title=="string"&&!_.mock).map(_=>({..._,currency:String(_.currency||"").toUpperCase(),sourceUrl:Lp(_.sourceUrl),forecast:_.forecast??"—",previous:_.previous??"—",actual:_.actual??null,mock:!1})):[];ji={...s,...jC(s,i,e),revision:ji.revision+1,sentiment:{...s.sentiment,items:r},correlations:{...s.correlations,items:c},news:{...s.news,events:f(s.news.events),calendarEvents:f(s.news.calendarEvents)}},Yu.forEach(g=>g())}function KC(){ji={...ji,connection:"offline"},Yu.forEach(s=>s())}function as(s){return ji.sentiment.items.find(e=>e.symbol===s)||WC()}function Op(s){return ji.correlations.items.filter(e=>nm(e.value)&&(e.source===s||e.target===s)).map(e=>({...e,symbol:e.source===s?e.target:e.source})).sort((e,i)=>Math.abs(i.value)-Math.abs(e.value)||e.symbol.localeCompare(i.symbol))}function QC(s="all"){return ji.correlations.items.filter(e=>{var i,r;return nm(e.value)&&(s==="all"||((i=Us.get(e.source))==null?void 0:i.assetClass)===s&&((r=Us.get(e.target))==null?void 0:r.assetClass)===s)})}function Zi(s=new Date().toISOString()){const e=new Date(s);return Number.isFinite(e.getTime())?new Intl.DateTimeFormat("en-CA",{timeZone:"Asia/Bangkok",year:"numeric",month:"2-digit",day:"2-digit"}).format(e):""}function JC(s){if(typeof s!="string"||!/(Z|[+-]\d{2}:\d{2})$/.test(s))return"—";const e=new Date(s);return Number.isFinite(e.getTime())?new Intl.DateTimeFormat("en-GB",{timeZone:"Asia/Bangkok",hour:"2-digit",minute:"2-digit",hourCycle:"h23"}).format(e):"—"}function Ya(s){if(!s)return"ยังไม่มี";const e=new Date(s);return Number.isFinite(e.getTime())?new Intl.DateTimeFormat("th-TH",{timeZone:"Asia/Bangkok",day:"numeric",month:"short",hour:"2-digit",minute:"2-digit",hourCycle:"h23"}).format(e):"ยังไม่มี"}function Pp(s){const e=s.timePrecision||s.timeKind;return e==="date"||e==="all_day"?"ทั้งวัน":e==="tentative"?"รอยืนยันเวลา":s.timeLabel||JC(s.time)}function aS(s,e=Zi()){const i=ji.news.calendarEvents.length?ji.news.calendarEvents:ji.news.events,r=Us.get(s),l=(r==null?void 0:r.assetClass)==="forex"?[s.slice(0,3),s.slice(3)]:["USD"];return i.filter(c=>(c.dayThai||Zi(c.time))===e&&(!s||l.includes(c.currency)||c.currency==="ALL")).sort((c,f)=>(c.time||"9999").localeCompare(f.time||"9999")||c.id.localeCompare(f.id))}const $C=new Set(["pending","queued","running","ready","failed","blocked","interrupted","stale","empty"]),e2=new Set(["up","down","mixed","unknown"]),Uo=(s,e)=>typeof s=="string"&&s.trim().length>0&&s.length<=e,rS=s=>typeof s=="string"&&/(Z|[+-]\d{2}:\d{2})$/.test(s)&&Number.isFinite(Date.parse(s));function sS(s=ji.news,e=Zi(),i=Date.now()){const r=s==null?void 0:s.aiAnalysis;let l=$C.has(r==null?void 0:r.status)?r.status:"pending";(e!==Zi(new Date(i).toISOString())||r!=null&&r.dayThai&&r.dayThai!==e)&&(l="stale"),l==="ready"&&(r.dayThai!==e||!/^[a-f0-9]{64}$/.test((r==null?void 0:r.inputDigest)||"")||!rS(r==null?void 0:r.generatedAt)||Zi(r.generatedAt)!==e||Date.parse(r.generatedAt)>i+3e4)&&(l="stale");const c={pending:"รอ AI รายวัน",queued:"AI รายวันอยู่ในคิว",running:"AI กำลังวิเคราะห์ข่าววันนี้",ready:"AI รายวันพร้อม",failed:"AI รายวันไม่สำเร็จ",blocked:"AI รายวันรอความพร้อม",interrupted:"AI รายวันถูกขัดจังหวะ",stale:"ยังไม่มี AI ที่ตรงกับวันที่เลือก",empty:"วันนี้ไม่มีข่าวให้ AI วิเคราะห์"}[l],f={quota_unavailable:"รอข้อมูลโควต้า",quota_below_reserve:"โควต้ายังไม่พร้อม",council_busy:"รอสภา AI ทำงานเสร็จ",council_window:"รอพ้นรอบสภา AI",waiting_calendar:"รอปฏิทินข่าว",calendar_stale:"ปฏิทินยังไม่เป็นปัจจุบัน",calendar_changed:"ปฏิทินเปลี่ยนหลังวิเคราะห์",result_invalid:"ผลวิเคราะห์ยังไม่ผ่านการตรวจ",day_expired:"พ้นวันที่วิเคราะห์แล้ว"}[r==null?void 0:r.reason]||"";return{status:l,label:c,reason:f,generatedAt:l==="ready"?r.generatedAt:null}}function tf(s,e=ji.news,i=Date.now()){const r=s==null?void 0:s.ai,l=(s==null?void 0:s.dayThai)||(rS(s==null?void 0:s.time)?Zi(s.time):""),c=e==null?void 0:e.aiAnalysis;return!s||sS(e,l,i).status!=="ready"||(r==null?void 0:r.status)!=="ready"||r.eventId!==s.id||r.dayThai!==l||r.inputDigest!==(c==null?void 0:c.inputDigest)||r.generatedAt!==(c==null?void 0:c.generatedAt)||!Uo(r.summaryTh,400)||!Array.isArray(r.explanationTh)||r.explanationTh.length<1||r.explanationTh.length>4||!r.explanationTh.every(f=>Uo(f,180))||!Uo(r.caveatTh,240)||!["short","medium","long"].every(f=>{var h;return Uo((h=r.horizonNotesTh)==null?void 0:h[f],160)})||!Array.isArray(r.sourceRefs)||r.sourceRefs.length<1||r.sourceRefs.length>4||!r.sourceRefs.every(f=>Uo(f==null?void 0:f.name,240)&&Lp(f==null?void 0:f.url))||!r.scenarios||!["currency","XAUUSD","XAGUSD"].every(f=>r.scenarios[f]===null||["below","inline","above"].every(h=>{var m,p,g,_;return e2.has((p=(m=r.scenarios[f])==null?void 0:m[h])==null?void 0:p.direction)&&Uo((_=(g=r.scenarios[f])==null?void 0:g[h])==null?void 0:_.textTh,280)}))?null:{...r,explanationTh:[...r.explanationTh],sourceRefs:r.sourceRefs.map(f=>({name:f.name,url:Lp(f.url)}))}}function t2(s,e){var h;const i=Us.get(e);if(!i||!Number.isFinite(s.forecastValue)||!s.numeric)return[];const r=s.currency===e.slice(0,3)?1:s.currency===e.slice(3)?-1:0,l=tf(s),c=(h=l==null?void 0:l.scenarios)==null?void 0:h[i.assetClass==="forex"?"currency":e];if(l)return!c||(i.assetClass==="forex"?!r:i.assetClass!=="metals"||s.currency!=="USD")?[]:[["below","ต่ำกว่าคาด"],["inline","ใกล้เคียงคาด"],["above","สูงกว่าคาด"]].map(([m,p])=>{const g=c[m],_=i.assetClass==="forex"&&r===-1&&{up:"down",down:"up"}[g.direction]||g.direction,v=_==="up"?`อาจหนุน ${e} ↑`:_==="down"?`อาจกดดัน ${e} ↓`:_==="mixed"?"แรงหนุนและแรงกดดันอาจหักล้างกัน":"ยังไม่ระบุทิศทาง";return{key:m,label:p,direction:_,summary:v,detail:g.textTh,note:l.caveatTh,origin:"ai"}});if(i.assetClass!=="forex"||!r||!["activity","employment","unemployment","inflation","confidence","growth","rates","retail"].includes(s.metric))return[];const f=s.metric==="unemployment"?-1:1;return[{key:"below",label:"ต่ำกว่าคาด",delta:-1},{key:"inline",label:"ใกล้เคียงคาด",delta:0},{key:"above",label:"สูงกว่าคาด",delta:1}].map(({delta:m,...p})=>{const g=m*f*r;return{...p,direction:g>0?"up":g<0?"down":"neutral",summary:g>0?`อาจหนุน ${e} ↑`:g<0?`อาจกดดัน ${e} ↓`:"ยังไม่ชี้ทิศ ต้องดูรายละเอียดและข่าวอื่นร่วมด้วย",note:s.metric==="inflation"?"ขึ้นกับการปรับคาดการณ์ดอกเบี้ย ไม่ใช่ผลตายตัว":"ฉากทัศน์พื้นฐานตามเงื่อนไข ไม่ใช่คำแนะนำซื้อขาย",origin:"dictionary"}})}function rs(s){const e=s==null?void 0:s.status;return{loading:"กำลังเชื่อมต่อ",ready:"พร้อม",ok:"พร้อม",fresh:"พร้อม",empty:"ไม่มีข่าววันนี้ในปฏิทิน",partial:"ข้อมูลบางส่วน",stale:"ข้อมูลเก่า",error:"เชื่อมต่อไม่สำเร็จ",needs_configuration:"รอเชื่อมบัญชี",auth_error:"ตรวจบัญชีอีกครั้ง",auth_failed:"ตรวจบัญชีอีกครั้ง",authentication_failed:"ตรวจบัญชีอีกครั้ง",rate_limited:"รอรอบโควต้า",provider_unavailable:"แหล่งข้อมูลยังไม่พร้อม",unavailable:"ยังไม่มีข้อมูล",market_closed:"ตลาดปิด",not_covered:"วันที่อยู่นอกช่วงข้อมูล",cached:"ข้อมูลจากรอบล่าสุด"}[e]||e||"ยังไม่มีข้อมูล"}const Fu=20,n2=.7,zu=.6,im=.3,oS=.1,lS=.8,_r={brightYellow:"#ffe66d",gold:"#dfb64f",positive:"#66dda0",deepPositive:"#18985b",negative:"#ff9292",deepNegative:"#c9384a",unavailable:"#778593"},nf=s=>Number.isFinite(s)&&Math.abs(s)<=1;function kh(s,e,i){const r=Math.max(0,Math.min(1,i)),l=c=>Math.round(parseInt(s.slice(c,c+2),16)*(1-r)+parseInt(e.slice(c,c+2),16)*r).toString(16).padStart(2,"0");return`#${l(1)}${l(3)}${l(5)}`}function kl(s){return nf(s)?Math.abs(s)<=im?"neutral":s>0?"positive":"negative":"unavailable"}function pi(s){if(!nf(s))return _r.unavailable;const e=Math.abs(s);if(e<=oS)return _r.brightYellow;if(e<=im)return kh(_r.brightYellow,_r.gold,(e-.1)/.2);const i=s>0?_r.positive:_r.negative,r=s>0?_r.deepPositive:_r.deepNegative;return e<.4?kh(_r.gold,i,(e-.3)/.1):e<lS?kh(i,r,(e-.4)/.4):r}function ax(s){if(!nf(s))return{strength:null,emphasized:!1,opacity:0};const e=Math.abs(s),i=e>=zu,r=i?.3+.26*(e-zu)/(1-zu):e<=.1?.24:e<=.3?.16+.08*(.3-e)/.2:.16+.03*(e-.3)/.3;return{strength:e,emphasized:i,opacity:r}}function cS(s,e){return!s||!e?null:s.source===e?s.target:s.target===e?s.source:null}function i2(s,e){const i=cS(s,e);return i&&!nf(s.value)?`${i} ไม่มีข้อมูล`:i?`${i} ${s.value>0?"+":""}${Math.round(s.value*100)}%`:""}function Oo(s,e){return[s,e].sort().join("|")}function rx(s,e=()=>[]){const i=[...new Map(s.map(l=>[l.symbol,l])).values()],r=[];for(let l=0;l<i.length;l++){const c=i[l],f=new Map(e(c.symbol).map(h=>[h.symbol,h.value]));for(let h=l+1;h<i.length;h++){const m=i[h],p=f.get(m.symbol);!Number.isFinite(p)||p<-1||p>1||r.push({source:c.symbol,target:m.symbol,value:p,sourceClass:c.assetClass,targetClass:m.assetClass,key:Oo(c.symbol,m.symbol),index:r.length})}}return r}function a2(s,e="all"){return e==="all"?s:s.filter(i=>i.sourceClass===e&&i.targetClass===e)}function r2(s,e){return e?s.filter(i=>i.source===e||i.target===e):[]}function sx(s){return s.filter(e=>Math.abs(e.value)>n2)}function ox(s,e=0){const i=e*.173;return((s*(.12+e%5*.013)+i)%1+1)%1}function s2(s,e,i=0){const r=e.x-s.x,l=e.y-s.y,c=e.z-s.z,f=Math.max(.01,Math.hypot(r,l)),h=Math.min(4.6,Math.hypot(r,l,c)*(.15+i%4*.025)),m=i%2?1:-1;return{x:(s.x+e.x)*.5-l/f*h*m,y:(s.y+e.y)*.5+r/f*h*m,z:(s.z+e.z)*.5+.45+Math.sin(i*1.31)*h*.72}}function lx(s,e,i,r,l={}){const c=Math.max(0,Math.min(1,r)),f=1-c,h=f*f,m=2*f*c,p=c*c;return l.x=h*s.x+m*i.x+p*e.x,l.y=h*s.y+m*i.y+p*e.y,l.z=h*s.z+m*i.z+p*e.z,l}function o2(s,e,i=Fu){return!Number.isInteger(e)||e<0?null:s[Math.floor(e/(i*2))]??null}function uS(s="/",e){return`${String(s).replace(/\/+$/,"")}/assets/${e}`}const l2={CHF:{center:[-9.6,3.7,-.5],radius:1.6,tilt:.95,turn:-.25},EUR:{center:[.6,1.1,.5],radius:3.9,tilt:.92,turn:.18},GBP:{center:[-7.5,-3,.4],radius:2.9,tilt:.98,turn:.08},USD:{center:[-1.1,6.3,-.4],radius:2.9,tilt:.96,turn:-.1},AUD:{center:[11.5,4.8,-.6],radius:3.2,tilt:.93,turn:-.15},CAD:{center:[14.3,-.2,.1],radius:1.8,tilt:.94,turn:.2},NZD:{center:[12.8,-5.2,.3],radius:2.9,tilt:.95,turn:-.15},METALS:{center:[5.2,-10.4,1],radius:2.7,tilt:.98,turn:-.1},OIL:{center:[-1.9,-9.2,.2],radius:2.2,tilt:.98,turn:.04}},cx=new Set(["CHFJPY","EURUSD","EURGBP","GBPUSD","USDJPY","USDCAD","AUDUSD","CADJPY","NZDUSD","XAUUSD","XAGUSD","WTI","BRENT"]),c2={EUR:[-4.8,10.5,.5],GBP:[4.8,10.5,.4],USD:[-4.8,5.2,-.4],AUD:[4.8,5.2,-.6],METALS:[0,0,1],CHF:[-4.1,-4.8,-.5],CAD:[4.8,-5.4,.1],NZD:[-4.8,-10.7,.3],OIL:[4.8,-10.7,.2]},u2={CHF:[-6.2,1,-.5],EUR:[0,6.8,.5],USD:[7.4,6.8,-.4],GBP:[-9.5,-2.7,.4],METALS:[0,0,1],AUD:[7.4,.1,-.6],OIL:[-7.1,-6.8,.2],NZD:[0,-6.8,.3],CAD:[7.4,-6.8,.1]},zl=Math.PI*2;function f2(s){return()=>(s=s*1664525+1013904223>>>0,s/4294967296)}function d2(s,e,i,r=1,l=48,c={value:0},f=0){const h=new zn;h.setAttribute("position",new Cn(s,3)),h.setAttribute("color",new Cn(e,3)),h.setAttribute("aSize",new Cn(i,1));const m=new Yn({transparent:!0,depthWrite:!1,blending:Ca,vertexColors:!0,uniforms:{opacity:{value:r},pixelScale:{value:1},maxSize:{value:l},time:c,shear:{value:f}},vertexShader:`attribute float aSize; varying vec3 vColor; varying float vShimmer;
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
      }`});return new Ds(h,m)}function h2(s,e,i=.2){return new Qp(new zn().setFromPoints(s),new Kp({color:e,transparent:!0,opacity:i,depthWrite:!1}))}function p2({assetBase:s="/",pairs:e,selectedSymbol:i,axis:r="free",playing:l=!0,reducedMotion:c=!1,motionSpeed:f=1,motionClock:h,filter:m="all",correlationsVisible:p=!0,selectedCorrelation:g=null,resetKey:_=0,focusKey:v=0,dataRevision:x=0,onSelect:E,onCorrelationSelect:D,onReady:M,onError:y}){const F=nt.useRef(null),V=nt.useRef(null),R=nt.useRef(null);return R.current={selectedSymbol:i,axis:r,playing:l,reducedMotion:c,motionSpeed:f,filter:m,correlationsVisible:p,selectedCorrelation:g,dataRevision:x,onSelect:E,onCorrelationSelect:D,onReady:M,onError:y},nt.useEffect(()=>{var Bs,ja,Za,Wo;const N=F.current;if(!N)return;let L;try{L=new Zx({antialias:!0,alpha:!0,powerPreference:"high-performance"})}catch{(ja=(Bs=R.current).onError)==null||ja.call(Bs,"เบราว์เซอร์นี้เปิด WebGL ไม่สำเร็จ กรุณาลอง Chrome หรือ Edge");return}L.setClearColor("#020810",1),L.setPixelRatio(Math.min(window.devicePixelRatio||1,1.6)),L.outputColorSpace=Ei;const P=L.domElement;P.className="orbital-webgl",P.tabIndex=0,P.setAttribute("aria-label","จักรวาล 32 สินทรัพย์ ลากซ้ายเพื่อหมุน ลากขวาเพื่อเลื่อนมุมมอง เลื่อนล้อเพื่อซูม"),P.setAttribute("role","application"),N.appendChild(P);const T=document.createElement("canvas");T.className="orbital-leaders",T.setAttribute("aria-hidden","true"),N.appendChild(T);const O=T.getContext("2d"),B=document.createElement("div");B.className="orbital-label-layer",N.appendChild(B);const k=(le,te)=>{le.addEventListener("pointerdown",De=>{De.button===0&&(De.preventDefault(),De.stopPropagation(),le.focus({preventScroll:!0}),te())}),le.addEventListener("click",De=>{De.detail===0&&te()})},J=(le,te)=>k(le,()=>{var Ce,Qe;const De=te();De&&((Qe=(Ce=R.current).onSelect)==null||Qe.call(Ce,De))}),se=new Ux,Y=new da;se.add(Y);const j=new Yi(43,1,.1,220);j.position.set(0,0,37),j.lookAt(0,0,0);const z=[],H=[],ee=[],oe=(h==null?void 0:h.current)||{value:0},fe=f2(20261024),U=(le,te,De,Ce,Qe,Lt,Le=0)=>{const st=d2(te,De,Ce,Qe,Lt,oe,Le);return le.add(st),z.push(st.material),st},re=(le,te,De,Ce)=>{const Qe=FC(te,De,oe,Ce);return le.add(Qe),z.push(Qe.material),Qe},xe=[],Ue=[],Ie=[];for(let le=0;le<16e3;le++){xe.push((fe()-.5)*75,(fe()-.5)*42,-9-fe()*25);const te=.1+Math.pow(fe(),5)*.8;Ue.push(.3*te,.58*te,te),Ie.push(.065+Math.pow(fe(),8)*1.08)}U(se,xe,Ue,Ie,.86);const Xe=[],ue=[],ye=[];for(let le=0;le<2800;le++){const te=fe()*zl,De=le%3;Xe.push(Math.sin(te)*(17+fe()*2),Math.cos(te*1.4+De)*8+(fe()-.5)*2,-8-fe()*8),ue.push(.06,.13,.28),ye.push(.6+fe()*2.8)}U(se,Xe,ue,ye,.15,100);let we=!1;const at=new RE().load(uS(s,"nebula-depth-v1.png"),()=>{we?at.dispose():N.dataset.nebula="ready"},void 0,()=>{N.dataset.nebula="unavailable"});at.colorSpace=Ei;const Ge=[{z:-20,w:84,h:48,x:-2,y:2,angle:-.12,opacity:1},{z:-12,w:66,h:40,x:7,y:-4,angle:.22,opacity:.56},{z:-6,w:42,h:26,x:-11,y:3,angle:-.48,opacity:.225}].map((le,te)=>{const De=new Yn({transparent:!0,depthWrite:!1,blending:Ca,uniforms:{map:{value:at},opacity:{value:le.opacity}},vertexShader:"varying vec2 vUv; void main(){vUv=uv;gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.0);}",fragmentShader:`varying vec2 vUv; uniform sampler2D map; uniform float opacity;
          void main(){vec3 c=texture2D(map,vUv).rgb;float edge=smoothstep(0.0,.15,vUv.x)*smoothstep(0.0,.15,vUv.y)*(1.0-smoothstep(.85,1.0,vUv.x))*(1.0-smoothstep(.85,1.0,vUv.y));gl_FragColor=vec4(c,opacity*edge);
          #include <tonemapping_fragment>
          #include <colorspace_fragment>
          }`}),Ce=new Ki(new ec(le.w,le.h),De);return Ce.position.set(le.x,le.y,le.z),Ce.rotation.z=le.angle,se.add(Ce),{mesh:Ce,spec:le,index:te}}),mt=new Jl(.46,8,6),un=new Qu({visible:!1}),ut=$x();OC.forEach((le,te)=>{const De=l2[le.id],Ce=e.filter(nn=>nn.clusterId===le.id),Qe=new da;Qe.position.fromArray(De.center),Y.add(Qe);const Lt=new da;Lt.rotation.set(De.tilt,0,De.turn),Qe.add(Lt);const Le=new da;Lt.add(Le);const st=.72+te%3*.09,xt=(.036+te%4*.009)*(te%3===1?-1:1),Ot=new Rt(le.color),Yt=new Rt("#d8e7ff"),Wn=new Rt("#8bbaff"),it=[],ke=[],tn=[],An=[],Rn=[],va=[],Dn=Math.round(2700+De.radius*1250);for(let nn=0;nn<Dn;nn++){const ui=Math.pow(fe(),.68)*De.radius,ta=nn%3,_a=ui/De.radius*4.9+ta*zl/3+(fe()-.5)*(.3+ui*.12),xa=1+.13*Math.sin(_a*2+te),na=nn%5===0?.7:.22,Qa=Math.cos(_a)*ui*xa+(fe()-.5)*na,Ar=Math.sin(_a)*ui*st+(fe()-.5)*na,Ci=(fe()-.5)*.22+Math.sin(_a*2+ui)*.12;it.push(Qa,Ar,Ci);const Rr=nn%29===0,Cr=.24+fe()*.67,ii=le.id==="METALS"&&Qa>.3?Yt:le.id==="OIL"&&Qa>.2?Wn:Ot;ke.push((Rr?.85:ii.r)*Cr,(Rr?.94:ii.g)*Cr,(Rr?1:ii.b)*Cr),tn.push(.045+Math.pow(fe(),5)*.32+(nn%181===0?.75:0)),nn%9===0&&(An.push(Qa,Ar,Ci-.1),Rn.push(ii.r,ii.g,ii.b),va.push(.7+fe()*1.1))}U(Le,it,ke,tn,1.04,48,xt*.65),U(Le,An,Rn,va,.07,85,xt*.65);for(let nn=0;nn<3;nn++){const ui=Array.from({length:100},(ta,_a)=>{const xa=(.16+_a/99*.84)*De.radius,na=xa/De.radius*4.9+nn*zl/3;return new Q(Math.cos(na)*xa*(1+.13*Math.sin(na*2+te)),Math.sin(na)*xa*st,Math.sin(na*2+xa)*.12)});Le.add(h2(ui,le.color,.16)),re(Le,new dE(ui),le.color,{rate:.11+nn*.025,phase:nn/3+te*.07})}const On=document.createElement("div");On.className="galaxy-cluster-label",On.style.setProperty("--cluster-color",le.color);const Ri=document.createElement("strong");Ri.textContent=le.label;const La=document.createElement("span");La.textContent=` · ${Ce.length}`,On.append(Ri,La),B.appendChild(On);const Oa=new Q(De.radius*-.15,le.id==="METALS"?1:De.radius*.62+.35,.1),Ka={meta:le,layout:De,group:Qe,layoutTarget:Qe.position.clone(),plane:Lt,spin:Le,spinRate:xt,phase:te*.8,caption:On,labelPoint:Oa,members:Ce,visible:!0};H.push(Ka),Ce.forEach((nn,ui)=>{const ta=new da,_a=ui/Math.max(1,Ce.length)*zl+.38+te*.3,xa=De.radius*(Ce.length===1?.3:Ce.length===2?.65:.62+ui%2*.23),na=ui*1.7+te,Qa=(.019+ui%3*.009)*(xt<0?-1:1);ta.position.fromArray(tx(xa,_a,st,na,0,Qa)),Le.add(ta);const Ar=new Ki(mt,un);Ar.userData.symbol=nn.symbol,ta.add(Ar);const Ci=as(nn.symbol),Rr=eS(Ci,ut,Jx(nn.symbol)),Cr=Rr.group;ta.add(Cr);const ii=document.createElement("button");ii.className="orbital-node-label",ii.textContent=nn.symbol,ii.setAttribute("aria-label",`เลือกสินทรัพย์ ${nn.symbol} ${Ci.available?`Short ${Ci.short}% Long ${Ci.long}%`:"ไม่มีข้อมูล Sentiment"}`),ii.dataset.symbol=nn.symbol,ii.title=Ci.available?`${nn.symbol} · Short ${Ci.short}% / Long ${Ci.long}% · Myfxbook`:`${nn.symbol} · ยังไม่มีข้อมูล Myfxbook`,J(ii,()=>nn.symbol),B.appendChild(ii),ee.push({pair:nn,cluster:Ka,group:ta,rings:Cr,nucleus:Rr,sentiment:Ci,hit:Ar,label:ii,radius:xa,angle:_a,eccentricity:st,phase:na,rate:Qa,depthOffset:Math.sin(ui*2.4)*.4,point:new Q})})});let vt=rx(e,Op);const Mt=e.length*(e.length-1)/2,pt=new Map(ee.map(le=>[le.pair.symbol,le])),_t=Fu*2,Gt=new zn,_n=new Fn(new Float32Array(Mt*_t*3),3).setUsage(ch),Xt=new Fn(new Float32Array(Mt*_t),1),fn=new Fn(new Float32Array(Mt*_t),1),Z=new Fn(new Float32Array(Mt*_t),1),Ft=new Fn(new Float32Array(Mt*_t),1),Dt=new Fn(new Float32Array(Mt*_t*3),3);Gt.setAttribute("position",_n),Gt.setAttribute("aValue",Xt),Gt.setAttribute("aEdge",fn),Gt.setAttribute("aIncident",Z),Gt.setAttribute("aOverviewOpacity",Ft),Gt.setAttribute("aCorrelationColor",Dt),Gt.boundingSphere=new Fs(new Q,180);const I=new Yn({transparent:!0,depthWrite:!1,blending:Io,uniforms:{selectedEdge:{value:-1},hasSelection:{value:0}},vertexShader:`attribute float aValue;attribute float aEdge;attribute float aIncident;attribute float aOverviewOpacity;attribute vec3 aCorrelationColor;uniform float selectedEdge;varying float vValue;varying float vSelected;varying float vIncident;varying float vOverviewOpacity;varying vec3 vCorrelationColor;
        void main(){vValue=aValue;vIncident=aIncident;vOverviewOpacity=aOverviewOpacity;vCorrelationColor=aCorrelationColor;vSelected=1.-step(.5,abs(aEdge-selectedEdge));gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.0);}`,fragmentShader:`varying float vValue;varying float vSelected;varying float vIncident;varying float vOverviewOpacity;varying vec3 vCorrelationColor;uniform float hasSelection;
        void main(){float strength=abs(vValue);vec3 tint=vCorrelationColor;
          float alpha=vOverviewOpacity*mix(1.,.13,hasSelection);
          alpha=mix(alpha,.24+pow(strength,1.4)*.52,vIncident);
          gl_FragColor=vec4(tint,mix(alpha,.94,vSelected));
          #include <tonemapping_fragment>
          #include <colorspace_fragment>
        }`}),b=new cE(Gt,I);b.frustumCulled=!1,se.add(b);let K=[],ce=[],ve=[],ne={neutral:0,positive:0,negative:0,minOpacity:0,maxOpacity:0};const Ae=new Map,pe=new Map,Se=Array.from({length:Math.max(0,e.length-1)},()=>{const le=document.createElement("button");return le.className="orbital-correlation-label",le.hidden=!0,B.appendChild(le),le.type="button",{label:le,edge:null,progress:null,offset:null,width:104}});let Ne=null,Ze=0;const He=le=>{var De,Ce;const te=(Ce=(De=le.target).closest)==null?void 0:Ce.call(De,".orbital-correlation-label");return te&&B.contains(te)&&!te.hidden?te:null},Fe=(le,te)=>{var Qe,Lt;const De=Oo(le.dataset.source,le.dataset.target),Ce=K.find(Le=>Le.key===De);N.dataset.correlationLabelEvent=te.type,N.dataset.correlationLabelCallback=String(typeof R.current.onCorrelationSelect=="function"),Ce&&(N.dataset.lastPickedCorrelation=Ce.key,N.dataset.correlationActivationCount=String(++Ze),(Lt=(Qe=R.current).onCorrelationSelect)==null||Lt.call(Qe,{source:Ce.source,target:Ce.target,value:Ce.value}))},rt=le=>{const te=He(le);!te||le.button!==0||(le.preventDefault(),le.stopPropagation(),te.focus({preventScroll:!0}),Ne=te,Fe(te,le))},lt=le=>{const te=He(le);if(!te)return;le.preventDefault(),le.stopPropagation();const De=le.detail>0&&Ne===te;Ne=null,De||Fe(te,le)},dt=le=>{const te=He(le);!te||!["Enter"," "].includes(le.key)||le.repeat||(le.preventDefault(),le.stopPropagation(),Ne=null,Fe(te,le))};B.addEventListener("pointerdown",rt,!0),B.addEventListener("click",lt,!0),B.addEventListener("keydown",dt,!0);const W=new zn,Oe=new Fn(new Float32Array(Mt*3),3).setUsage(ch),Me=new Fn(new Float32Array(Mt),1),Pe=new Fn(new Float32Array(Mt),1),Ve=new Fn(new Float32Array(Mt*3),3);W.setAttribute("position",Oe),W.setAttribute("aValue",Me),W.setAttribute("aEmphasis",Pe),W.setAttribute("aCorrelationColor",Ve);const Re=new Yn({transparent:!0,depthWrite:!1,blending:Ca,uniforms:{pixelScale:{value:1}},vertexShader:`attribute float aEmphasis;attribute vec3 aCorrelationColor;uniform float pixelScale;varying float vEmphasis;varying vec3 vCorrelationColor;
        void main(){vCorrelationColor=aCorrelationColor;vEmphasis=aEmphasis;vec4 p=modelViewMatrix*vec4(position,1.);gl_Position=projectionMatrix*p;gl_PointSize=clamp((4.+aEmphasis*4.)*pixelScale,3.,18.);}`,fragmentShader:`varying vec3 vCorrelationColor;varying float vEmphasis;void main(){float r=length(gl_PointCoord-.5)*2.;if(r>1.)discard;
        vec3 tint=vCorrelationColor;float core=pow(1.-r,2.);
        gl_FragColor=vec4(mix(tint,vec3(1.,.97,.8),pow(1.-r,5.)*.25),core*vEmphasis);
        #include <tonemapping_fragment>
        #include <colorspace_fragment>
      }`}),et=new Ds(W,Re);et.frustumCulled=!1,se.add(et),z.push(Re);const Je=new zn,Qt=new Fn(new Float32Array(ee.length*3),3).setUsage(ch),Nt=new Fn(new Float32Array(ee.length),1);Je.setAttribute("position",Qt),Je.setAttribute("aStrength",Nt);const ei=new Yn({transparent:!0,depthWrite:!1,blending:Ca,uniforms:{pixelScale:{value:1}},vertexShader:"attribute float aStrength;uniform float pixelScale;varying float vStrength;void main(){vStrength=aStrength;gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.);gl_PointSize=(7.+aStrength*4.)*pixelScale;}",fragmentShader:`varying float vStrength;void main(){float r=length(gl_PointCoord-.5)*2.;if(r>1.||vStrength<.01)discard;gl_FragColor=vec4(1.,.75,.27,pow(1.-r,2.7)*vStrength*.7);
        #include <tonemapping_fragment>
        #include <colorspace_fragment>
      }`}),ti=new Ds(Je,ei);ti.frustumCulled=!1,se.add(ti),z.push(ei);const Qi=new da;Y.add(Qi);const os=Array.from({length:5},(le,te)=>{const De=new gE(new Q(-19+te*1.8,7-te*3,-4-te),new Q(-2+te*2,5-te*2,-2-te),new Q(18-te,3-te*2,-4-te));return re(Qi,De,te%2?"#8facf9":"#62c9f2",{rate:.06+te*.008,phase:.07+te*.19,meteor:!0})}),Da=new DE,pa=new Kt,_i={x:new Q(1,0,0),y:new Q(0,1,0),z:new Q(0,0,1)},yn=new ss,Bn=new ss,Kn=new Q;let Wt=1,Mn=1,Tr=0,Ua=!1,qt=null,Ji=null,Pi=!1;const Ii=new Q(1,1,1);let ma=performance.now(),ga=0,sn=1,Na=null,xi=null,A=!1,X="",ge=null;const ie=new Q,ae=new Q,ze=new Q;let We=37,Be=!0;const qe=(le,te)=>{const De=R.current.axis;De==="free"?(Y.quaternion.premultiply(yn.setFromAxisAngle(_i.y,le*.004)),Y.quaternion.premultiply(yn.setFromAxisAngle(_i.x,te*.004))):Y.quaternion.premultiply(yn.setFromAxisAngle(_i[De]||_i.z,(le+te*.65)*.005)),Y.quaternion.normalize()},Ye=(le,te)=>{const De=2*Math.tan(go.degToRad(j.fov*.5))*j.position.distanceTo(ie)/Mn;ze.x-=le*De,ze.y+=te*De},gt=le=>{const te=P.getBoundingClientRect();pa.set((le.clientX-te.left)/te.width*2-1,-((le.clientY-te.top)/te.height)*2+1),Da.setFromCamera(pa,j)},Tt=le=>{var te;return gt(le),((te=Da.intersectObjects(ee.filter(De=>De.cluster.visible).map(De=>De.hit),!1)[0])==null?void 0:te.object.userData.symbol)||null},$e=le=>{if(!b.visible||!K.length)return null;gt(le);const te=2*Math.tan(go.degToRad(j.fov*.5))*j.position.distanceTo(ie)/Mn;Da.params.Line.threshold=te*4;const De=Da.intersectObject(b,!1);let Ce=null,Qe=5;for(const Lt of De){Kn.copy(Lt.point).project(j);const Le=Math.hypot((Kn.x-pa.x)*Wt*.5,(Kn.y-pa.y)*Mn*.5);Le<Qe&&(Qe=Le,Ce=o2(K,Lt.index))}return Ce},zt=le=>{var De,Ce;if(le.button!==0&&le.button!==2&&le.pointerType!=="touch"||le.button===0&&((Ce=(De=le.target).closest)!=null&&Ce.call(De,"button")))return;le.preventDefault(),P.focus({preventScroll:!0});const te=le.button===0?Tt(le):null;qt={id:le.pointerId,x:le.clientX,y:le.clientY,button:le.button,travel:0,symbol:te,correlation:le.button===0&&!te?$e(le):null},P.setPointerCapture(le.pointerId),P.classList.add("is-dragging")},dn=le=>{if(qt&&le.pointerId===qt.id){const te=le.clientX-qt.x,De=le.clientY-qt.y;qt.travel+=Math.abs(te)+Math.abs(De),qt.button===2?Ye(te,De):qe(te,De),qt.x=le.clientX,qt.y=le.clientY}else Ji=Tt(le),P.style.cursor=Ji?"pointer":R.current.correlationsVisible?"crosshair":"grab"},rn=le=>{var te,De,Ce,Qe;if(!(!qt||le.pointerId!==qt.id)){if(qt.button===0&&qt.travel<6){if(qt.symbol)(De=(te=R.current).onSelect)==null||De.call(te,qt.symbol);else if(qt.correlation){const{source:Lt,target:Le,value:st}=qt.correlation;N.dataset.lastPickedCorrelation=Oo(Lt,Le),(Qe=(Ce=R.current).onCorrelationSelect)==null||Qe.call(Ce,{source:Lt,target:Le,value:st})}}P.hasPointerCapture(le.pointerId)&&P.releasePointerCapture(le.pointerId),qt=null,P.classList.remove("is-dragging")}},bt=()=>{qt=null,P.classList.remove("is-dragging")},Tn=le=>le.preventDefault(),Ke=le=>{le.preventDefault(),sn=go.clamp(sn*Math.exp(le.deltaY*7e-4),.42,1.7)},wn=le=>{const te={ArrowLeft:[-14,0],ArrowRight:[14,0],ArrowUp:[0,-14],ArrowDown:[0,14]};te[le.key]?(le.preventDefault(),le.shiftKey?Ye(...te[le.key]):qe(...te[le.key])):["+","=","-"].includes(le.key)&&(le.preventDefault(),sn=go.clamp(sn*(le.key==="-"?1.08:.92),.42,1.7))},Et=le=>{var te,De;le.preventDefault(),(De=(te=R.current).onError)==null||De.call(te,"ฉากสามมิติหยุดชั่วคราว กรุณาโหลดหน้าใหม่เพื่อเชื่อมต่อกราฟิกอีกครั้ง")};N.addEventListener("pointerdown",zt),N.addEventListener("pointermove",dn),N.addEventListener("pointerup",rn),N.addEventListener("pointercancel",bt),N.addEventListener("contextmenu",Tn),N.addEventListener("wheel",Ke,{passive:!1}),P.addEventListener("keydown",wn),P.addEventListener("webglcontextlost",Et);const Qn=()=>{const le=N.getBoundingClientRect();Wt=Math.max(1,le.width),Mn=Math.max(1,le.height);const te=Wt>=640&&Wt/Mn<1.24;N.dataset.framing=Wt<640?"portrait":te?"compact":"wide",H.forEach(Ce=>{Ce.layoutTarget.fromArray(Wt<640?c2[Ce.meta.id]:te?u2[Ce.meta.id]:Ce.layout.center),(!Pi||R.current.reducedMotion)&&Ce.group.position.copy(Ce.layoutTarget)}),Ii.set(Wt<640?.5:1,Wt<640?1.7:1,1),(!Pi||R.current.reducedMotion)&&Qi.scale.copy(Ii),Pi=!0,L.setSize(Wt,Mn,!1),j.aspect=Wt/Mn,j.updateProjectionMatrix();const De=Math.min(window.devicePixelRatio||1,1.6);T.width=Wt*De,T.height=Mn*De,T.style.width=`${Wt}px`,T.style.height=`${Mn}px`,O==null||O.setTransform(De,0,0,De,0,0),z.forEach(Ce=>{Ce.uniforms.pixelScale.value=Mn/720*De}),ee.forEach(Ce=>nS(Ce.nucleus,Mn*De))},ci=new ResizeObserver(Qn);ci.observe(N),Qn();const ni=()=>{const le=new Vo,te=new Q;if(H.filter(st=>st.visible&&(!xi||st.meta.id===xi)).forEach(st=>{const xt=st.layout.radius;for(const Ot of[-xt*1.12,xt*1.12])for(const Yt of[-xt*.7,xt*.74+.35])for(const Wn of[-xt*.65,xt*.65])te.set(Ot,Yt,Wn),st.group.localToWorld(te),le.expandByPoint(te)}),le.isEmpty())return;const De=le.getSize(new Q);le.getCenter(ae),Wt>=640&&R.current.filter==="all"&&!xi&&(ae.y+=1.05),ae.add(ze);const Ce=Math.tan(go.degToRad(j.fov*.5)),Qe=Mn/Math.max(240,Mn-160),Lt=Wt/Math.max(240,Wt-40);We=(Math.max(De.y/(2*Ce)*Qe,De.x/(2*Ce*j.aspect)*Lt)*(Wt<640?1.08:1.025)+De.z*.5)*sn,Be&&(ie.copy(ae),j.position.set(ae.x,ae.y,ae.z+We),Be=!1)},$i=le=>({x:(le.x*.5+.5)*Wt,y:(-le.y*.5+.5)*Mn});function jt(){O==null||O.clearRect(0,0,Wt,Mn);const le=[],te=new Q,De=(Le,st,xt,Ot)=>Le>=8&&Le+xt<=Wt-8&&st>=65&&st+Ot<=Mn-124&&!le.some(Yt=>Le<Yt.x+Yt.w+4&&Le+xt>Yt.x-4&&st<Yt.y+Yt.h+3&&st+Ot>Yt.y-3),Ce=(Le,st,xt)=>{if(!O)return;const Ot=Math.max(st.x,Math.min(st.x+st.w,Le.x)),Yt=Math.max(st.y,Math.min(st.y+st.h,Le.y));Math.hypot(Ot-Le.x,Yt-Le.y)<12||(O.beginPath(),O.strokeStyle=xt,O.lineWidth=.7,O.moveTo(Le.x,Le.y),O.lineTo(Ot,Yt),O.stroke())};H.forEach(Le=>{te.copy(Le.labelPoint),Le.group.localToWorld(te),te.project(j);const st=$i(te),xt=Wt<640?72:108,Ot=Le.visible&&te.z<1&&st.x>12&&st.x<Wt-12&&st.y>70&&st.y<Mn-120;if(Le.caption.hidden=!Ot,Ot){const Yt=Math.min(st.x,Wt-xt-8);Le.caption.style.transform=`translate3d(${Yt.toFixed(1)}px,${(st.y-20).toFixed(1)}px,0)`,le.push({x:Yt,y:st.y-20,w:xt,h:30})}});const Qe=R.current.selectedSymbol;[...ee].sort((Le,st)=>Le.pair.symbol===Qe?-1:st.pair.symbol===Qe?1:0).forEach(Le=>{Le.group.getWorldPosition(Le.point),te.copy(Le.point).project(j);const st=$i(te),xt=Le.pair.symbol===Qe,Ot=R.current.selectedCorrelation,Yt=pe.has(Le.pair.symbol),Wn=xt||Yt||Le.pair.symbol===Ji||(Ot==null?void 0:Ot.source)===Le.pair.symbol||(Ot==null?void 0:Ot.target)===Le.pair.symbol||Wt>=640&&cx.has(Le.pair.symbol)||xi||R.current.filter!=="all",it=Le.cluster.visible&&Wn&&te.z<1&&st.x>6&&st.x<Wt-8&&st.y>65&&st.y<Mn-110;if(Le.label.hidden=!it,!it)return;const ke=xt?82:Wt<640?58:66,tn=xt?27:24,An=[...Le.labelOffset?[Le.labelOffset]:[],{x:17,y:-29},{x:-ke-17,y:-29},{x:17,y:13},{x:-ke-17,y:13}];for(const Dn of[36,58,84,112,144])for(let On=0;On<8;On++){const Ri=On*zl/8;An.push({x:Math.cos(Ri)*Dn-ke*.5,y:Math.sin(Ri)*Dn-tn*.5})}const Rn=An.find(Dn=>De(st.x+Dn.x,st.y+Dn.y,ke,tn));if(Le.label.hidden=!Rn,!Rn)return;Le.labelOffset=Rn;const va={x:st.x+Rn.x,y:st.y+Rn.y,w:ke,h:tn};le.push(va),Ce(st,va,Yt?"#d7b77366":"#93b3c74d"),Le.label.style.transform=`translate3d(${va.x.toFixed(1)}px,${va.y.toFixed(1)}px,0)`,Le.label.classList.toggle("is-selected",xt),Le.label.classList.toggle("is-connected",Yt&&!xt),Le.label.setAttribute("aria-pressed",String(xt))}),Se.forEach((Le,st)=>{const{label:xt,edge:Ot}=Le;if(!Ot){xt.hidden=!0;return}const Yt=pt.get(Ot.source).point,Wn=pt.get(Ot.target).point,it=Ae.get(Ot.key);if(!it){xt.hidden=!0;return}const tn=.5+(Ot.source===Qe?1:-1)*(.08+st%5*.055),An=Le.width,Rn=22,va=[...Le.offset?[Le.offset]:[],{x:0,y:0},{x:0,y:-24},{x:0,y:24},{x:-An*.45,y:-24},{x:An*.45,y:24},{x:-An*.45,y:24},{x:An*.45,y:-24}];let Dn=null;for(let On=0;On<16;On++){const Ri=On-1,La=On===0&&Le.progress!==null?Le.progress:go.clamp(tn+(Ri%2?1:-1)*Math.ceil(Math.max(0,Ri)/2)*.045,.14,.86);lx(Yt,Wn,it,La,te),te.project(j);const Oa=$i(te);if(te.z>=1)continue;const Ka=va.find(nn=>De(Oa.x-An*.5+nn.x,Oa.y-Rn*.5+nn.y,An,Rn));if(Ka){Dn={x:Oa.x-An*.5+Ka.x,y:Oa.y-Rn*.5+Ka.y,progress:La,offset:Ka,anchor:Oa};break}}if(xt.hidden=!Dn,Dn){Le.progress=Dn.progress,Le.offset=Dn.offset,xt.style.transform=`translate3d(${Dn.x.toFixed(1)}px,${Dn.y.toFixed(1)}px,0)`;const On={x:Dn.x,y:Dn.y,w:An,h:Rn};le.push(On),Ce(Dn.anchor,On,`${pi(Ot.value)}66`)}xt.classList.toggle("is-selected",R.current.selectedCorrelation&&Ot.key===Oo(R.current.selectedCorrelation.source,R.current.selectedCorrelation.target))})}function gn(){K=R.current.correlationsVisible?a2(vt,R.current.filter):[],ce=r2(K,R.current.selectedSymbol);const le=new Set(ce.map(te=>te.key));ve=sx(K),I.uniforms.hasSelection.value=ce.length?1:0,pe.clear(),ce.forEach(te=>pe.set(te.source===R.current.selectedSymbol?te.target:te.source,Math.abs(te.value))),b.visible=K.length>0,Gt.setDrawRange(0,K.length*_t),ne={neutral:0,positive:0,negative:0,minOpacity:K.length?1/0:0,maxOpacity:0},K.forEach((te,De)=>{const Ce=De*_t,Qe=ax(te.value),Lt=new Rt(pi(te.value));ne[kl(te.value)]++,ne.minOpacity=Math.min(ne.minOpacity,Qe.opacity),ne.maxOpacity=Math.max(ne.maxOpacity,Qe.opacity),Xt.array.fill(te.value,Ce,Ce+_t),fn.array.fill(te.index,Ce,Ce+_t),Z.array.fill(le.has(te.key)?1:0,Ce,Ce+_t),Ft.array.fill(Qe.opacity,Ce,Ce+_t);for(let Le=Ce;Le<Ce+_t;Le++)Dt.setXYZ(Le,Lt.r,Lt.g,Lt.b)}),Xt.needsUpdate=!0,fn.needsUpdate=!0,Z.needsUpdate=!0,Ft.needsUpdate=!0,Dt.needsUpdate=!0,Se.forEach((te,De)=>{var Qe;const Ce=ce[De];((Qe=te.edge)==null?void 0:Qe.key)!==(Ce==null?void 0:Ce.key)&&(te.progress=null,te.offset=null),te.edge=Ce||null,te.label.hidden=!Ce,Ce&&(te.label.textContent=i2(Ce,R.current.selectedSymbol),O&&(O.font="600 12px Rajdhani, sans-serif"),te.width=Math.max(94,Math.ceil((O==null?void 0:O.measureText(te.label.textContent).width)||te.label.textContent.length*6.2)+14),te.label.style.setProperty("--correlation-color",pi(Ce.value)),te.label.dataset.tone=kl(Ce.value),te.label.title=`${Ce.source} ↔ ${Ce.target} · ${Math.round(Ce.value*100)}% · คำนวณจากราคาปิด MT5`,te.label.setAttribute("aria-label",te.label.title),te.label.dataset.source=Ce.source,te.label.dataset.target=Ce.target,te.label.dataset.correlation=String(Ce.value),te.label.dataset.counterpart=cS(Ce,R.current.selectedSymbol))}),et.visible=ve.length>0,W.setDrawRange(0,ve.length),ve.forEach((te,De)=>{const Ce=new Rt(pi(te.value));Ve.setXYZ(De,Ce.r,Ce.g,Ce.b),Me.setX(De,te.value),Pe.setX(De,ce.length?le.has(te.key)?1:.14:.75)}),Me.needsUpdate=!0,Pe.needsUpdate=!0,Ve.needsUpdate=!0,ee.forEach((te,De)=>{const Ce=pe.get(te.pair.symbol),Qe=te.pair.symbol===R.current.selectedSymbol&&ce.length>0;Nt.setX(De,te.cluster.visible?Qe?.95:Ce===void 0?0:.45+Ce*.5:0)}),Nt.needsUpdate=!0,ti.visible=ce.length>0}function Ai(le){if(!K.length)return;ee.forEach(Qe=>Qe.group.getWorldPosition(Qe.point));const te=_n.array;K.forEach((Qe,Lt)=>{const Le=pt.get(Qe.source).point,st=pt.get(Qe.target).point,xt=s2(Le,st,Qe.index);Ae.set(Qe.key,xt);let Ot=Lt*_t*3;for(let Yt=0;Yt<Fu;Yt++)for(let Wn=0;Wn<2;Wn++){const it=(Yt+Wn)/Fu,ke=1-it,tn=ke*ke,An=2*ke*it,Rn=it*it;te[Ot++]=tn*Le.x+An*xt.x+Rn*st.x,te[Ot++]=tn*Le.y+An*xt.y+Rn*st.y,te[Ot++]=tn*Le.z+An*xt.z+Rn*st.z}}),_n.needsUpdate=!0;const De=new Q;ve.forEach((Qe,Lt)=>{lx(pt.get(Qe.source).point,pt.get(Qe.target).point,Ae.get(Qe.key),ox(le,Qe.index),De),Oe.setXYZ(Lt,De.x,De.y,De.z)}),Oe.needsUpdate=!0;const Ce=new Q(.4,.32,.04).applyQuaternion(j.quaternion);ee.forEach((Qe,Lt)=>Qt.setXYZ(Lt,Qe.point.x+Ce.x,Qe.point.y+Ce.y,Qe.point.z+Ce.z)),Qt.needsUpdate=!0}function en(){ee.forEach(le=>{const te=as(le.pair.symbol);le.sentiment=te,tS(le.nucleus,te),le.label.setAttribute("aria-label",`เลือกสินทรัพย์ ${le.pair.symbol} ${te.available?`Short ${te.short}% Long ${te.long}%`:"ยังไม่มีข้อมูล Myfxbook"}`),le.label.title=te.available?`${le.pair.symbol} · Short ${te.short}% / Long ${te.long}% · Myfxbook${te.asOf?` · รับข้อมูล ${te.asOf}`:""}`:`${le.pair.symbol} · ยังไม่มีข้อมูล Myfxbook`,le.label.dataset.sentimentAvailable=String(te.available),le.label.dataset.sentimentColor=le.nucleus.appearance.color}),vt=rx(e,Op),Ae.clear(),qt!=null&&qt.correlation&&(qt.correlation=vt.find(le=>le.key===qt.correlation.key)||null),gn(),X="",ge=R.current.dataRevision,N.dataset.dataRevision=String(ge)}const ea=()=>{Y.quaternion.identity(),ze.set(0,0,0),xi=null,A=!1,sn=1},Fi=()=>{A=!0};V.current={reset:ea,focus:Fi,refreshData:en};const Si=()=>{ma=performance.now()};document.addEventListener("visibilitychange",Si);function zs(le){var st,xt,Ot,Yt,Wn;if(Ua)return;Tr=requestAnimationFrame(zs);const te=Math.max(0,Math.min(.05,(le-ma)/1e3));if(ma=le,document.hidden||Wt<2||Mn<2)return;Na!==R.current.filter&&(Na=R.current.filter,xi=null,sn=1,H.forEach(it=>{it.visible=Na==="all"||it.meta.assetClass===Na,it.group.visible=it.visible}),Qi.visible=Na==="all"),ge!==R.current.dataRevision&&en();const De=`${R.current.filter}:${R.current.correlationsVisible}:${R.current.selectedSymbol}`;De!==X&&(gn(),X=De);const Ce=R.current.selectedCorrelation;I.uniforms.selectedEdge.value=Ce?((st=vt.find(it=>it.key===Oo(Ce.source,Ce.target)))==null?void 0:st.index)??-1:-1,A&&(xi=((xt=ee.find(it=>it.pair.symbol===R.current.selectedSymbol))==null?void 0:xt.pair.clusterId)||null,sn=1,A=!1),R.current.selectedSymbol||(xi=null),oe.value=IC(oe.value,te,{playing:R.current.playing&&!R.current.reducedMotion,dragging:!!qt,speed:R.current.motionSpeed});const Qe=oe.value,Lt=R.current.reducedMotion?1:1-Math.exp(-te*9);Qi.scale.lerp(Ii,Lt),Ge.forEach(({mesh:it,spec:ke,index:tn})=>{it.position.x=ke.x+Math.sin(Qe*.018+tn)*1.2+Y.quaternion.y*(tn+1)*1.3,it.position.y=ke.y+Math.sin(Qe*.012+tn)*.65-Y.quaternion.x*(tn+1)*.9,it.rotation.z=ke.angle+Math.sin(Qe*.009+tn)*.025}),H.forEach(it=>{it.group.position.lerp(it.layoutTarget,Lt),it.group.position.distanceToSquared(it.layoutTarget)<1e-6&&it.group.position.copy(it.layoutTarget),it.spin.rotation.z=Qe*it.spinRate,it.plane.rotation.x=it.layout.tilt+Math.sin(Qe*.17+it.phase)*.055,it.plane.rotation.z=it.layout.turn+Math.sin(Qe*.12+it.phase)*.035}),ee.forEach(it=>{it.group.position.fromArray(tx(it.radius,it.angle,it.eccentricity,it.phase,Qe,it.rate)),it.group.position.z+=it.depthOffset}),Y.updateMatrixWorld(!0),ni();const Le=R.current.reducedMotion?1:1-Math.exp(-te*6);if(ie.lerp(ae,Le),j.position.x+=(ie.x-j.position.x)*Le,j.position.y+=(ie.y-j.position.y)*Le,j.position.z+=(ie.z+We-j.position.z)*Le,j.lookAt(ie),j.updateMatrixWorld(),ee.forEach(it=>{const ke=it.pair.symbol===R.current.selectedSymbol,tn=cx.has(it.pair.symbol);it.rings.scale.setScalar(ke?1.22:tn?1.08:.92),it.hit.scale.setScalar(ke?1.2:1),it.group.getWorldQuaternion(Bn),it.rings.quaternion.copy(Bn.invert()).multiply(j.quaternion),tm(it.nucleus,Qe)}),se.updateMatrixWorld(!0),Ai(Qe),L.render(se,j),jt(),le-ga>160){const it=new Set(ee.filter(ke=>!ke.label.hidden&&pe.has(ke.pair.symbol)).map(ke=>ke.pair.symbol));Se.filter(ke=>!ke.label.hidden).forEach(ke=>it.add(ke.label.dataset.counterpart)),Object.assign(N.dataset,{rotation:Y.quaternion.toArray().map(ke=>ke.toFixed(5)).join(","),orbit:H[1].spin.rotation.z.toFixed(6),motionTime:Qe.toFixed(6),motionSpeed:String(R.current.motionSpeed),distance:j.position.z.toFixed(3),selected:R.current.selectedSymbol||"",selectionMode:R.current.selectedSymbol?"selected":"overview",axis:R.current.axis,playing:String(R.current.playing),visibleCount:String(ee.filter(ke=>ke.cluster.visible).length),clusterCount:String(H.filter(ke=>ke.visible).length),focus:xi||"overview",reducedMotion:String(R.current.reducedMotion),layoutMoving:String(H.some(ke=>ke.group.position.distanceToSquared(ke.layoutTarget)>1e-6)),layoutDistance:H.reduce((ke,tn)=>ke+tn.group.position.distanceTo(tn.layoutTarget),0).toFixed(4),chfCenter:H.find(ke=>ke.meta.id==="CHF").group.position.toArray().map(ke=>ke.toFixed(4)).join(","),connectionCount:String(K.length),correlationCount:String(K.length),correlationTotal:String(vt.length),correlationDrawCalls:String(b.visible?1:0),selectedCorrelation:Ce?Oo(Ce.source,Ce.target):"",cometCount:String(Qi.visible?os.length:0),starPosition:ee[0].group.position.toArray().map(ke=>ke.toFixed(5)).join(","),selectedEdgeCount:String(ce.length),correlationLabelCount:String(Se.filter(ke=>!ke.label.hidden).length),correlationLabelTotal:String(ce.length),highlightedEndpointCount:String(pe.size),flowCount:String(ve.length),selectedFlowCount:String(sx(ce).length),flowProgress:ve.length?ox(Qe,ve[0].index).toFixed(6):"",flowDrawCalls:String(et.visible?1:0),pan:ze.toArray().map(ke=>ke.toFixed(4)).join(","),panX:ze.x.toFixed(4),panY:ze.y.toFixed(4),cameraControls:"left-rotate,right-pan",overviewThreshold:String(zu),overviewStrongCount:String(K.filter(ke=>ax(ke.value).emphasized).length),visibleNameCount:String(ee.filter(ke=>!ke.label.hidden).length),connectedNameCount:String(it.size),neutralThreshold:String(im),correlationNeutralCount:String(ne.neutral),correlationPositiveCount:String(ne.positive),correlationNegativeCount:String(ne.negative),correlationOpacityMin:ne.minOpacity.toFixed(4),correlationOpacityMax:ne.maxOpacity.toFixed(4),correlationBrightYellowCount:String(K.filter(ke=>Math.abs(ke.value)<=oS).length),correlationDeepCount:String(K.filter(ke=>Math.abs(ke.value)>=lS).length),correlationBlending:"normal",nucleusOrbits:String(((Ot=ee[0])==null?void 0:Ot.nucleus.ringCount)??0),sentimentRings:String(((Yt=ee[0])==null?void 0:Yt.nucleus.ringCount)??0),selectedLong:String(as(R.current.selectedSymbol).long??""),selectedShort:String(as(R.current.selectedSymbol).short??""),beadPosition:((Wn=ee.find(ke=>ke.pair.symbol===R.current.selectedSymbol))==null?void 0:Wn.nucleus.bead.position.toArray().map(ke=>ke.toFixed(5)).join(","))||"",nebulaLayers:String(Ge.length)}),ga=le}}return Tr=requestAnimationFrame(zs),N.dataset.ready="true",N.dataset.nodeCount=String(ee.length),(Wo=(Za=R.current).onReady)==null||Wo.call(Za),()=>{Ua=!0,cancelAnimationFrame(Tr),ci.disconnect(),document.removeEventListener("visibilitychange",Si),N.removeEventListener("pointerdown",zt),N.removeEventListener("pointermove",dn),N.removeEventListener("pointerup",rn),N.removeEventListener("pointercancel",bt),N.removeEventListener("wheel",Ke),N.removeEventListener("contextmenu",Tn),P.removeEventListener("keydown",wn),P.removeEventListener("webglcontextlost",Et),B.removeEventListener("pointerdown",rt,!0),B.removeEventListener("click",lt,!0),B.removeEventListener("keydown",dt,!0),we=!0,at.dispose(),iS(se,ut),L.dispose(),L.forceContextLoss(),P.remove(),T.remove(),B.remove(),V.current=null,delete N.dataset.ready}},[e]),nt.useEffect(()=>{var N;_&&((N=V.current)==null||N.reset())},[_]),nt.useEffect(()=>{var N;v&&((N=V.current)==null||N.focus())},[v]),w.jsx("div",{ref:F,className:"orbital-canvas-wrap","data-testid":"orbital-scene"})}function m2({symbol:s,playing:e,motionClock:i,motionSpeed:r=1,dataRevision:l=0,className:c=""}){const f=nt.useRef(null),h=nt.useRef(null),m=nt.useRef({playing:e,motionSpeed:r});m.current={playing:e,motionSpeed:r},nt.useEffect(()=>{var J;const g=f.current;if(!g)return;let _;try{_=new Zx({antialias:!0,alpha:!0,powerPreference:"low-power"})}catch{g.dataset.ready="false";return}const v=Math.min(window.devicePixelRatio||1,1.75);_.setPixelRatio(v),_.setClearColor(0,0),_.outputColorSpace=Ei,_.domElement.setAttribute("aria-hidden","true"),g.prepend(_.domElement);const x=new Ux,E=new Yi(32,1,.1,20);E.position.set(0,.05,2.65),E.lookAt(0,0,0);const D=$x(),M=eS(as(s),D,Jx(s));x.add(M.group);let y=0,F=0,V=0,R=!0,N=null,L=Number.isFinite((J=i==null?void 0:i.current)==null?void 0:J.value)?i.current.value:0;const P=()=>{tS(M,as(s)),R=!0,g.dataset.sentimentColor=M.appearance.color,g.dataset.sentimentBias=M.appearance.bias,g.dataset.sentimentDominance=String(M.appearance.dominance??""),g.dataset.sentimentAvailable=String(M.available)};h.current=P;const T=()=>{const se=g.getBoundingClientRect();F=se.width,V=se.height,!(F<1||V<1)&&(_.setSize(F,V,!1),E.aspect=F/V,E.updateProjectionMatrix(),nS(M,V*v),R=!0)},O=new ResizeObserver(T);O.observe(g),T();function B(){var Y;if(y=requestAnimationFrame(B),document.hidden||F<1||V<1)return;const se=(Y=i==null?void 0:i.current)==null?void 0:Y.value;m.current.playing&&Number.isFinite(se)&&(L=se),!(!R&&L===N)&&(N=L,R=!1,tm(M,L),_.render(x,E),g.dataset.motionTime=L.toFixed(6),g.dataset.beadPosition=M.bead.position.toArray().map(j=>j.toFixed(5)).join(","))}y=requestAnimationFrame(B),g.dataset.ready="true",g.dataset.orbits="0",g.dataset.sentimentColor=M.appearance.color,g.dataset.sentimentBias=M.appearance.bias,g.dataset.sentimentDominance=String(M.appearance.dominance??"");const k=se=>{se.preventDefault(),g.dataset.ready="false"};return _.domElement.addEventListener("webglcontextlost",k),()=>{h.current=null,cancelAnimationFrame(y),O.disconnect(),_.domElement.removeEventListener("webglcontextlost",k),iS(x,D),_.dispose(),_.forceContextLoss(),_.domElement.remove(),delete g.dataset.ready}},[s,i]),nt.useEffect(()=>{var g;(g=h.current)==null||g.call(h)},[l]);const p=as(s);return w.jsx("div",{ref:f,className:`sentiment-preview ${c}`,"data-symbol":s,"data-data-revision":l,role:"img","aria-label":`ดาวพลาสมาสามมิติ ${s} ${p.available?`Myfxbook Short ${p.short}% Long ${p.long}%`:"ยังไม่มีข้อมูล Myfxbook"}`,children:w.jsx("span",{className:"sentiment-preview-fallback",children:"เปิดภาพดาว 3D ไม่สำเร็จ"})})}function g2({url:s,onData:e,onFailure:i,fetchImpl:r=globalThis.fetch,intervalMs:l=3e4,timeoutMs:c=1e4,schedule:f=setTimeout,cancel:h=clearTimeout}){let m=!1,p,g,_;const v=async()=>{g=new AbortController,_=f(()=>g.abort(),c);try{const x=await r(s,{cache:"no-store",credentials:"omit",signal:g.signal});if(!x.ok)throw new Error("market_unavailable");const E=await x.json();m||e(E)}catch{m||i()}finally{h(_),m||(p=f(v,l))}};return v(),()=>{m=!0,h(p),h(_),g==null||g.abort()}}function v2({marketUrl:s="/api/market",requireHeartbeat:e=!1}={}){const i=nt.useSyncExternalStore(qC,YC);return nt.useEffect(()=>g2({url:s,onData:r=>ZC(r,{requireHeartbeat:e}),onFailure:KC}),[s,e]),i}function _2(s){return[...s.querySelectorAll('button:not(:disabled),a[href],input:not(:disabled),select:not(:disabled),textarea:not(:disabled),[tabindex="0"]')].filter(e=>!e.closest("[inert]")&&e.getClientRects().length)}function x2(s,e){var i,r,l;if(s.key==="Escape"){const c=e.explainerOpen?e.closeExplainer:e.eventOpen?e.closeNews:e.settingsOpen?e.closeSettings:e.inspectorOpen?e.closeInspector:null;return c?(c(),s.preventDefault(),s.stopPropagation(),!0):!1}if(e.embedded&&s.key==="Tab"){const c=_2(e.root),f=e.root.getRootNode().activeElement;return s.shiftKey&&f===c[0]?(s.preventDefault(),(i=c.at(-1))==null||i.focus()):!s.shiftKey&&f===c.at(-1)&&(s.preventDefault(),(r=c[0])==null||r.focus()),s.stopPropagation(),!0}return e.explainerOpen||/INPUT|SELECT|TEXTAREA|BUTTON|A/.test((l=s.target)==null?void 0:l.tagName)?!1:s.key===" "?(s.preventDefault(),s.stopPropagation(),e.toggleMotion(),!0):!1}const S2={pmi:{title:"PMI · ดัชนีผู้จัดการฝ่ายจัดซื้อ",lines:["สำรวจภาวะธุรกิจ เป็นค่าดัชนี ไม่ใช่ % การเติบโต","50 = คงเดิม; สูงกว่า = ขยาย; ต่ำกว่า = หดจากเดือนก่อน","ดีขึ้นแต่ยังต่ำกว่า 50 = ยังหดตัว; เทียบค่าคาดด้วย","ค่าเงินอาจตอบสนองผ่านมุมมองเศรษฐกิจและดอกเบี้ย"],sourceName:"S&P Global · PMI FAQ",sourceUrl:"https://www.spglobal.com/market-intelligence/en/solutions/products/resources/pmi-faq"},consumerConfidence:{title:"ความเชื่อมั่นผู้บริโภค",lines:["สำรวจมุมมองต่อการเงิน เศรษฐกิจ และการใช้จ่าย","เป็นดุลคำตอบเชิงบวก–ลบ ไม่ใช่อัตราโตของยอดขาย","สูงขึ้นคือมุมมองดีขึ้น; เทียบคาดการณ์และครั้งก่อน","อาจหนุนมุมมองเศรษฐกิจ แต่ไม่ยืนยันทิศค่าเงิน"],sourceName:"European Commission · วิธีอ่านแบบสำรวจ",sourceUrl:"https://economy-finance.ec.europa.eu/economic-forecast-and-surveys/business-and-consumer-surveys/methodology-business-and-consumer-surveys/methodological-concepts_en"},businessConfidence:{title:"ANZ · ความเชื่อมั่นธุรกิจ",lines:["สำรวจมุมมองธุรกิจนิวซีแลนด์ต่อเศรษฐกิจข้างหน้า","ดุลสุทธิคือฝั่งมองดีหักฝั่งมองแย่ ไม่ใช่ GDP","แยกความมั่นใจรวมจากแนวโน้มกิจการของผู้ตอบ","เทียบคาดและครั้งก่อน; ค่าเงินยังขึ้นกับปัจจัยอื่น"],sourceName:"ANZ · Business Outlook",sourceUrl:"https://www.anz.co.nz/about-us/economic-markets-research/business-outlook/"},cpi:{title:"CPI · เงินเฟ้อผู้บริโภค",lines:["วัดการเปลี่ยนราคาสินค้าและบริการของผู้บริโภค","m/m เทียบเดือนก่อน; y/y เทียบเดือนเดียวกันปีก่อน","เงินเฟ้อลดลง อาจแค่ราคาเพิ่มช้าลง ไม่ใช่ราคาลด","เกินคาดอาจดันมุมมองดอกเบี้ยขึ้น ค่าเงินไม่แน่นอน"],sourceName:"BLS · CPI FAQ",sourceUrl:"https://www.bls.gov/cpi/questions-and-answers.htm"},coreCpi:{title:"Core CPI · เงินเฟ้อพื้นฐานสหรัฐฯ",lines:["CPI สหรัฐฯ ที่ไม่นับอาหารและพลังงาน","ช่วยดูแรงกดดันราคาพื้นฐาน โดยยังต้องอ่าน CPI รวม","เทียบคาดและครั้งก่อนในช่วงเวลาเดียวกัน เช่น m/m","เกินคาดอาจหนุนดอกเบี้ยสูงนาน แต่ไม่ยืนยันทิศกราฟ"],sourceName:"BLS · Headline และ Core CPI",sourceUrl:"https://www.bls.gov/cpi/factsheets/common-misconceptions-about-cpi.htm"},canadaCpi:{title:"CPI · เงินเฟ้อแคนาดา",lines:["วัดการเปลี่ยนราคาตะกร้าสินค้าและบริการผู้บริโภค","m/m เทียบเดือนก่อน; y/y เทียบเดือนเดียวกันปีก่อน","อ่านผลเทียบคาด ไม่สรุปจากตัวเลขสูงขึ้นอย่างเดียว","CAD อาจตอบสนองผ่านมุมมองดอกเบี้ยและปัจจัยอื่น"],sourceName:"Statistics Canada · CPI FAQ",sourceUrl:"https://www.statcan.gc.ca/en/subjects-start/prices_and_price_indexes/consumer_price_indexes/faq"},japanCpi:{title:"CPI · เงินเฟ้อญี่ปุ่นรายปี",lines:["วัดการเปลี่ยนราคาสินค้าและบริการที่ครัวเรือนซื้อ","รายปีเทียบเดือนเดียวกันปีก่อน ไม่ใช่เดือนก่อน","เทียบคาดการณ์ และแยกเงินเฟ้อรวมจากดัชนีพื้นฐาน","JPY อาจตอบสนองผ่านมุมมอง BOJ ไม่ใช่ตัวเลขเดียว"],sourceName:"Statistics Bureau Japan · CPI Q&A",sourceUrl:"https://www.stat.go.jp/english/data/cpi/1585.htm"},unemployment:{title:"อัตราว่างงาน",lines:["ผู้ว่างงานหารกำลังแรงงาน ไม่ใช่ประชากรทั้งหมด","สูงขึ้นอาจสะท้อนแรงงานอ่อนลง ไม่ใช่ข่าวดีเสมอ","เทียบคาด พร้อมดูค่าจ้างและการมีส่วนร่วมแรงงาน","ค่าเงินอาจอ่อนหากตลาดคาดลดดอกเบี้ย แต่ไม่เสมอ"],sourceName:"ONS · คู่มือสถิติตลาดแรงงาน",sourceUrl:"https://www.ons.gov.uk/employmentandlabourmarket/peopleinwork/employmentandemployeetypes/methodologies/aguidetolabourmarketstatistics/"},employment:{title:"การเปลี่ยนแปลงการจ้างงาน",lines:["จำนวนผู้มีงานทำที่เปลี่ยนจากเดือนก่อน","ครอบคลุมงานเต็มเวลาและพาร์ตไทม์ ไม่ใช่ค่าจ้าง","เทียบคาด พร้อมดูชั่วโมงทำงานและอัตราว่างงาน","เกินคาดอาจหนุน AUD หากมุมมองเศรษฐกิจดีขึ้น"],sourceName:"ABS · Labour force framework",sourceUrl:"https://www.abs.gov.au/statistics/detailed-methodology-information/concepts-sources-methods/labour-statistics-concepts-sources-and-methods/2023/concepts-and-sources/labour-force-framework"},ecbSpeech:{title:"ถ้อยแถลง ECB",lines:["ติดตามมุมมองเงินเฟ้อและแนวทางดอกเบี้ยของ ECB","เข้มขึ้นเน้นคุมเงินเฟ้อ; ผ่อนคลายเน้นหนุนเศรษฐกิจ","ดูว่าต่างจากตลาดคาดอย่างไร ไม่มีค่าคาดแบบตัวเลข","อาจเปลี่ยนมุมมองต่อ EUR แต่ยังไม่ใช่มติขึ้นดอกเบี้ย"],sourceName:"ECB · นโยบายการเงินคืออะไร",sourceUrl:"https://www.ecb.europa.eu/ecb-and-you/explainers/tell-me/html/what-is-monetary-policy.en.html"},fedSpeech:{title:"ถ้อยแถลง Fed",lines:["ติดตามมุมมองเศรษฐกิจ เงินเฟ้อ และดอกเบี้ยสหรัฐฯ","เข้มขึ้นอาจชี้ดอกเบี้ยสูงนาน; ผ่อนคลายอาจตรงข้าม","ดูสิ่งที่ต่างจากตลาดคาด ไม่ใช่ทุกคำพูดคือมติ Fed","USD อาจขยับผ่านคาดการณ์ดอกเบี้ยและปัจจัยอื่น"],sourceName:"Federal Reserve · ดอกเบี้ยคาดการณ์กับค่าเงิน",sourceUrl:"https://www.federalreserve.gov/econres/notes/ifdp-notes/the-sensitivity-of-the-us-dollar-exchange-rate-to-changes-in-monetary-policy-expectations-20170922.htm"},snbSpeech:{title:"ถ้อยแถลง SNB",lines:["ติดตามนโยบายเงินเฟ้อและดอกเบี้ยสวิตเซอร์แลนด์","มองหาท่าทีที่เปลี่ยนจากเดิมและจากตลาดคาด","ไม่มีผลตัวเลขเทียบคาด และไม่ใช่มตินโยบายเสมอไป","CHF อาจตอบสนอง แต่ยังขึ้นกับเศรษฐกิจและความเสี่ยง"],sourceName:"SNB · นโยบายการเงิน",sourceUrl:"https://www.snb.ch/en/the-snb/mandates-goals/monetary-policy"},generic:{title:"อ่านข่าวเศรษฐกิจอย่างไร",lines:["เริ่มจากชื่อ หน่วย และช่วงเวลาที่ตัวเลขครอบคลุม","แยกการเทียบคาดการณ์ออกจากการเทียบครั้งก่อน","ยังไม่มีผลจริง ให้อ่านเพียงฉากทัศน์ตามเงื่อนไข","ข่าวเดียวไม่ยืนยันทิศกราฟหรือแนวโน้มระยะยาว"],sourceName:"Federal Reserve · ความคาดหวังกับค่าเงิน",sourceUrl:"https://www.federalreserve.gov/econres/notes/ifdp-notes/the-sensitivity-of-the-us-dollar-exchange-rate-to-changes-in-monetary-policy-expectations-20170922.htm"}};function y2(s){if(!s||typeof s!="object")return"generic";const e=typeof s.title=="string"?s.title:"";if(/\bPMI\b/i.test(e))return"pmi";if(s.metric==="inflation"){if(s.currency==="JPY")return"japanCpi";if(s.currency==="CAD")return"canadaCpi";if(s.currency==="USD")return/\bcore\b/i.test(e)?"coreCpi":"cpi"}if(s.metric==="confidence"){if(s.currency==="EUR")return"consumerConfidence";if(s.currency==="NZD")return"businessConfidence"}if(s.metric==="unemployment")return"unemployment";if(s.metric==="employment"&&s.currency==="AUD")return"employment";if(s.kind==="speech"){if(s.currency==="EUR")return"ecbSpeech";if(s.currency==="USD")return"fedSpeech";if(s.currency==="CHF")return"snbSpeech"}return"generic"}function M2(s){const e=tf(s);if(e)return{title:s.title,lines:[...e.explanationTh],origin:"ai",generatedAt:e.generatedAt,sourceRefs:e.sourceRefs,sourceName:e.sourceRefs[0].name,sourceUrl:e.sourceRefs[0].url};const i=S2[y2(s)];return{...i,lines:[...i.lines],origin:"dictionary",sourceRefs:[{name:i.sourceName,url:i.sourceUrl}]}}const b2=460;function E2(s,e,i){const[r,l]=nt.useState(null),[c,f]=nt.useState(!1);return nt.useEffect(()=>{let h,m,p;return s&&e?(l(e),i?f(!0):h=requestAnimationFrame(()=>{m=requestAnimationFrame(()=>f(!0))})):(f(!1),i?l(null):p=setTimeout(()=>l(null),b2)),()=>{cancelAnimationFrame(h),cancelAnimationFrame(m),clearTimeout(p)}},[s,e,i]),{displayPair:r,expanded:c}}const T2=[["all","ทั้งหมด",32],["forex","Forex",28],["metals","Metals",2],["oil","Oil",2]],A2=`linear-gradient(90deg,${[0,10,20,35,50,65,80,90,100].map(s=>`${ef({available:!0,long:s,short:100-s}).color} ${s}%`).join(",")})`;function fS({source:s,day:e,event:i}){const r=i?tf(i):null,l=sS(s,e),c=i?!!r:l.status==="ready";return w.jsxs("div",{className:`news-ai-status ${c?"ready":"fallback"}`,role:"status",children:[w.jsx("strong",{children:i&&l.status==="ready"&&!r?"ยังไม่มี AI ที่ตรงกับข่าวนี้":l.label}),w.jsx("small",{children:c?`วิเคราะห์ ${Ya((r==null?void 0:r.generatedAt)||l.generatedAt)} · เวลาไทย`:`${l.reason?`${l.reason} · `:""}แสดงคำอธิบายพื้นฐานจากพจนานุกรมข่าว`})]})}function R2({symbol:s,onSelect:e}){const[i,r]=nt.useState(""),[l,c]=nt.useState(!1),[f,h]=nt.useState(0),m=nt.useRef(null),p=nt.useRef(null),g=yr.filter(v=>`${v.symbol} ${v.name}`.toLowerCase().includes(i.trim().toLowerCase()));nt.useEffect(()=>{const v=x=>{x.composedPath().includes(m.current)||c(!1)};return document.addEventListener("pointerdown",v),()=>document.removeEventListener("pointerdown",v)},[]);const _=v=>{var x;e(v),c(!1),r(""),(x=p.current)==null||x.focus()};return w.jsxs("div",{className:"asset-search",ref:m,children:[w.jsx(IM,{size:18}),w.jsx("input",{ref:p,value:i,role:"combobox","aria-label":"ค้นหาสินทรัพย์ 32 รายการ","aria-expanded":l,"aria-controls":l?"asset-options":void 0,"aria-autocomplete":"list","aria-activedescendant":l&&g[f]?`asset-${g[f].symbol}`:void 0,placeholder:"ค้นหาสินทรัพย์ เช่น EURUSD",onFocus:()=>c(!0),onChange:v=>{r(v.target.value),h(0),c(!0)},onKeyDown:v=>{v.key==="Escape"&&(v.stopPropagation(),c(!1)),(v.key==="ArrowDown"||v.key==="ArrowUp")&&(v.preventDefault(),c(!0),h(x=>Math.max(0,Math.min(g.length-1,x+(v.key==="ArrowDown"?1:-1))))),v.key==="Enter"&&l&&g[f]&&(v.preventDefault(),_(g[f].symbol))}}),l&&w.jsxs("div",{className:"asset-results",id:"asset-options",role:"listbox","aria-label":"ผลค้นหาสินทรัพย์",children:[w.jsxs("div",{className:"result-heading",children:[g.length," สินทรัพย์"]}),g.map((v,x)=>w.jsxs("button",{id:`asset-${v.symbol}`,role:"option","aria-selected":v.symbol===s,className:x===f?"active":"",onPointerMove:()=>h(x),onClick:()=>_(v.symbol),children:[w.jsx("strong",{children:v.symbol}),w.jsx("small",{children:v.assetClass.toUpperCase()})]},v.symbol)),!g.length&&w.jsx("p",{className:"empty-search",children:"ไม่พบสินทรัพย์ ลองค้นหาด้วยชื่อคู่เงิน"})]})]})}function C2({symbol:s,news:e,eventId:i,onEvent:r,highOnly:l,setHighOnly:c,inactive:f,day:h,onDay:m,source:p}){var N,L,P,T,O;const g=l?e.filter(B=>B.impact==="high"):e,_=Object.values(g.reduce((B,k)=>{const J=`${k.dayThai||Zi(k.time)}|${k.timeKind||k.timePrecision||"timed"}|${Pp(k)}`;return B[J]??(B[J]={key:J,event:k,events:[]}),B[J].events.push(k),B},{})),v=(N=p.availableDays)==null?void 0:N.find(B=>B.dayThai===h),x=!!p.lastSuccessAt,E=!["ready","ok","fresh","empty","cached","partial"].includes(p.status),D=(v==null?void 0:v.fullyCovered)===!0,M=(v==null?void 0:v.count)??aS(null,h).length,y=((L=p.coverage)==null?void 0:L.cachedSourceCount)??((P=p.coverage)==null?void 0:P.sourceCount)??((T=p.calendarEvents)==null?void 0:T.length)??0,F=x?v?D?"ครอบคลุมวันที่เลือก":"ครอบคลุมวันบางส่วน":"อยู่นอกช่วงข้อมูล":rs(p),V=x?v?E?"ยังยืนยันข่าวรอบล่าสุดไม่ได้":D?l&&e.length?"ไม่มีข่าวสำคัญในตัวกรองนี้":s&&M?"ไม่มีข่าวตรงกับสินทรัพย์ที่เลือก":"ไม่มีเหตุการณ์ในวันที่เลือก":"ยังยืนยันข่าวครบวันไม่ได้":"วันที่นี้อยู่นอกช่วงข้อมูล":"ยังโหลดปฏิทินไม่สำเร็จ",R=x?v?E?"แสดงเฉพาะข้อมูลรอบที่เก็บไว้ ตรวจสถานะแหล่งข่าวด้านบน":D?l&&e.length?"ปิดตัวกรองเพื่อดูทุกระดับความสำคัญ":s&&M?"เลือกภาพรวมเพื่อดูข่าวทั้งหมดของวันนี้":"แหล่งข่าวส่งปฏิทินมาแล้ว และไม่มีรายการสำหรับวันนี้":"แหล่งข้อมูลครอบคลุมวันนี้เพียงบางช่วง จึงไม่ถือว่าไม่มีข่าวทั้งวัน":"เลือกวันอื่นจากปฏิทิน โดยข้อมูลที่ดึงไว้ยังคงเปิดอ่านได้":"รอการเชื่อมต่อแหล่งข่าว";return w.jsxs("aside",{className:"news-rail","aria-label":"ข่าวที่เกี่ยวข้อง",inert:f,children:[w.jsxs("header",{className:"news-heading",children:[w.jsx("p",{className:"eyebrow",children:"YOUR DAILY BRIEFING"}),w.jsxs("h1",{children:[s?"ข่าวที่เกี่ยวข้อง":"ข่าวภาพรวม"," ",w.jsxs("span",{children:[g.length," เหตุการณ์"]})]}),w.jsxs("h2",{children:[s||"MARKET BRIEF",w.jsx("small",{children:s?((O=yr.find(B=>B.symbol===s))==null?void 0:O.assetClass)==="forex"?`${s.slice(0,3)} + ${s.slice(3)}`:"ข่าว USD ที่เกี่ยวข้อง":"เลือกดาวเพื่อกรองข่าว"})]}),w.jsxs("p",{className:"time-zone",children:[w.jsx(Wv,{size:15}),"เวลาไทย · Asia/Bangkok"]}),w.jsxs("div",{className:"news-date-controls",children:[w.jsx("label",{htmlFor:"calendar-day",className:"sr-only",children:"วันที่ปฏิทินข่าว เวลาไทย"}),w.jsx("input",{id:"calendar-day",type:"date",value:h,onChange:B=>B.target.value&&m(B.target.value)}),w.jsx("button",{onClick:()=>m(Zi()),children:"วันนี้"})]}),w.jsxs("div",{className:"news-filter",children:[w.jsx("span",{className:"sample-mini",children:l?"ข่าวสำคัญ":"ทุกระดับความสำคัญ"}),w.jsx("button",{"aria-pressed":l,onClick:()=>c(B=>!B),children:"เฉพาะข่าวสำคัญ"})]}),w.jsxs("div",{className:"news-source-status",role:"status",children:[w.jsxs("a",{href:p.sourceUrl||"https://www.forexfactory.com/calendar",target:"_blank",rel:"noopener noreferrer",children:[p.source||"Forex Factory",w.jsx(Xl,{size:11})]}),w.jsxs("span",{children:[F,E&&x?` · ${rs(p)}`:""]}),w.jsxs("small",{children:["วันที่เลือก ",M," · ในช่วงที่ดึงไว้ ",y," รายการ",w.jsx("br",{}),"เป็นรายการจากแหล่งนี้ อาจไม่ครอบคลุมทุกข่าวตลาด"]})]}),p.error==="http_429"&&w.jsxs("p",{className:"news-retry-notice",children:["ต้นทางจำกัดการเรียก · ใช้ปฏิทินรอบที่เก็บไว้",w.jsx("br",{}),"ลองใหม่ ",Ya(p.nextAttemptAt)," เวลาไทย"]}),w.jsx(fS,{source:p,day:h})]}),w.jsxs("div",{className:"news-list",children:[_.map(B=>w.jsxs("section",{className:"news-time-group",children:[w.jsxs("div",{className:"time-heading",children:[w.jsx(qv,{size:10}),w.jsx("time",{dateTime:B.event.time||void 0,children:Pp(B.event)}),w.jsx("span",{children:B.events.length>1?`${B.events.length} เหตุการณ์`:B.events[0].currency})]}),w.jsx("div",{className:"events-at-time",children:B.events.map(k=>w.jsxs("button",{id:`news-${k.id}`,className:`news-event ${k.id===i?"selected":""}`,"aria-expanded":k.id===i,"aria-controls":k.id===i?"news-popover":void 0,onClick:()=>r(k.id),children:[w.jsx("span",{className:"event-currency",children:k.currency}),w.jsx("span",{className:"event-title",children:k.title}),w.jsxs("span",{className:`impact ${k.impact}`,title:`ความสำคัญ ${k.impactLabel||"ไม่ระบุ"}`,children:[w.jsx(qv,{size:8}),w.jsx("span",{className:"sr-only",children:k.impactLabel||"ไม่ระบุ"})]})]},k.id))})]},B.key)),!g.length&&w.jsxs("div",{className:"empty-news",children:[w.jsx(CM,{size:28}),w.jsx("h3",{children:V}),w.jsx("p",{children:R})]})]}),w.jsxs("footer",{className:"news-round",children:[w.jsx(Wv,{size:19}),w.jsxs("div",{children:["ปฏิทินอัปเดตวันละครั้ง",w.jsxs("small",{children:["ดึงสำเร็จ ",Ya(p.lastSuccessAt),w.jsx("br",{}),"กำหนดการที่เก็บไว้ อาจมีการเปลี่ยนภายหลัง"]})]})]})]})}function w2({event:s,symbol:e,onClose:i,onLearnMore:r,explainerOpen:l}){const c=nt.useRef(null);nt.useEffect(()=>{var g;(g=c.current)==null||g.focus({preventScroll:!0})},[s.id]);const f=e?t2(s,e):[],h=s.numeric||[s.forecast,s.previous].some(g=>g!=null&&g!=="—"),m=tf(s),p=(m==null?void 0:m.summaryTh)||s.summary;return w.jsxs("section",{className:"news-popover",id:"news-popover",role:l?"region":"dialog","aria-modal":l?void 0:!1,"aria-labelledby":"news-title",children:[w.jsxs("header",{children:[w.jsxs("div",{className:"popup-meta",children:[w.jsx("span",{className:"currency-tag",children:s.currency}),w.jsxs("time",{dateTime:s.time||void 0,children:[s.dayThai||Zi(s.time)," · ",Pp(s)," · ไทย"]})]}),w.jsx("button",{ref:c,className:"icon-button","aria-label":"ปิดบทวิเคราะห์ข่าว",onClick:i,children:w.jsx(Wl,{size:20})})]}),w.jsxs("div",{className:"popup-scroll",children:[w.jsx("h2",{id:"news-title",children:s.title}),w.jsx(fS,{event:s,day:s.dayThai||Zi(s.time)}),p&&w.jsx("p",{className:"news-summary",children:p}),w.jsxs("button",{id:"news-learn-more",className:"news-learn-more","aria-expanded":l,"aria-controls":l?"news-explainer":void 0,onClick:r,children:[w.jsx(Fp,{size:16}),"อ่านเพิ่มเติม · ข่าวนี้หมายถึงอะไร"]}),h&&w.jsxs("div",{className:"event-figures",children:[w.jsxs("div",{children:[w.jsx("small",{children:"คาดการณ์"}),w.jsx("strong",{children:s.forecast??"—"})]}),w.jsxs("div",{children:[w.jsx("small",{children:"ครั้งก่อน"}),w.jsx("strong",{children:s.previous??"—"})]})]}),w.jsxs("p",{className:"actual-status",children:["ผลจริง: ",s.actual===null||s.actual===void 0?"แหล่งนี้ไม่ส่งผลจริง":String(s.actual)]}),f.length>0?w.jsxs(w.Fragment,{children:[w.jsxs("div",{className:"scenario-heading",children:["ฉากทัศน์ต่อ ",w.jsx("strong",{children:e}),w.jsx("span",{children:m?"AI รายวัน · หากผลออกมา…":"หลักการพื้นฐาน · หากผลออกมา…"})]}),w.jsx("div",{className:"scenario-list",children:f.map(g=>w.jsxs("div",{className:`scenario ${g.direction} ${g.detail?"has-analysis":""}`,children:[w.jsxs("div",{children:[w.jsx("span",{className:"scenario-icon",children:g.direction==="up"?w.jsx(SM,{size:18}):g.direction==="down"?w.jsx(_M,{size:18}):w.jsx(AM,{size:18})}),w.jsx("strong",{children:g.label})]}),w.jsxs("p",{children:[g.summary,g.detail&&w.jsx("small",{children:g.detail})]})]},g.key))}),w.jsxs("p",{className:"scenario-note",children:[f[0].note,w.jsx("br",{}),"ข่าวเดียวไม่พอสรุปทิศทางระยะยาว"]})]}):w.jsx("p",{className:"overview-news-hint",children:e?"ยังไม่มีฉากทัศน์ทิศทางที่รองรับสำหรับข่าวและสินทรัพย์นี้":"เลือกสินทรัพย์เพื่อดูฉากทัศน์ เมื่อข่าวมีตัวเลขคาดการณ์ที่รองรับ"}),m&&w.jsxs("details",{className:"news-horizons",children:[w.jsx("summary",{children:"ผลที่อาจเกิดขึ้นตามระยะเวลา"}),w.jsx("dl",{children:[["short","ระยะสั้น"],["medium","ระยะกลาง"],["long","ระยะยาว"]].map(([g,_])=>w.jsxs("div",{children:[w.jsx("dt",{children:_}),w.jsx("dd",{children:m.horizonNotesTh[g]})]},g))}),!f.length&&w.jsx("p",{children:m.caveatTh})]}),s.datePrecisionNote&&w.jsx("p",{className:"scenario-note",children:s.datePrecisionNote})]}),w.jsxs("footer",{children:[s.sourceUrl?w.jsxs("a",{href:s.sourceUrl,target:"_blank",rel:"noopener noreferrer",children:[s.sourceName,w.jsx(Xl,{size:14})]}):w.jsx("span",{children:s.sourceName||"ไม่ระบุแหล่งข่าว"}),w.jsx("span",{children:m?"AI วิเคราะห์รายวัน":"คำอธิบายพื้นฐาน"})]})]})}function D2({event:s,onClose:e}){const i=nt.useRef(null),r=M2(s);return nt.useEffect(()=>{var l,c,f;(l=i.current)==null||l.focus({preventScroll:!0}),matchMedia("(max-width:740px)").matches&&((f=(c=i.current)==null?void 0:c.closest(".news-explainer"))==null||f.scrollIntoView({block:"nearest"}))},[s.id]),w.jsxs("aside",{className:"news-explainer",id:"news-explainer",role:"region","aria-labelledby":"explainer-title",children:[w.jsxs("header",{children:[w.jsxs("div",{children:[w.jsx("p",{className:"eyebrow",children:r.origin==="ai"?"DAILY AI BRIEF":"UNDERSTAND THE EVENT"}),w.jsx("h2",{id:"explainer-title",children:r.title})]}),w.jsx("button",{ref:i,className:"icon-button","aria-label":"ปิดคำอธิบายข่าว",onClick:e,children:w.jsx(Wl,{size:19})})]}),w.jsx("div",{className:"explainer-points",children:r.lines.map((l,c)=>w.jsxs("p",{children:[w.jsx("span",{children:String(c+1).padStart(2,"0")}),l]},c))}),w.jsxs("footer",{children:[r.sourceRefs.map(l=>w.jsxs("a",{href:l.url,target:"_blank",rel:"noopener noreferrer",children:[l.name,w.jsx(Xl,{size:14})]},l.url)),w.jsxs("small",{children:[r.origin==="ai"?`AI รายวัน · วิเคราะห์ ${Ya(r.generatedAt)} เวลาไทย`:"คำอธิบายพื้นฐานจากพจนานุกรมข่าว · ไม่ใช่ผลวิเคราะห์ AI",w.jsx("br",{}),"ตรวจผลจริงจากแหล่งประกาศ · ไม่ใช่สัญญาณซื้อขาย"]})]})]})}function U2({event:s,symbol:e,explainerOpen:i,onClose:r,onLearnMore:l,onCloseExplainer:c,embedded:f=!1}){const h=nt.useRef(null);nt.useEffect(()=>{if(!i||f)return;const p=document.body.style.overflow;return document.body.style.overflow="hidden",()=>{document.body.style.overflow=p}},[i,f]);const m=p=>{if(!i||p.key!=="Tab")return;const g=[...h.current.querySelectorAll('button:not(:disabled),a[href],[tabindex="0"]')].filter(x=>x.getClientRects().length),_=g[0],v=g.at(-1);p.shiftKey&&h.current.getRootNode().activeElement===_?(p.preventDefault(),v==null||v.focus()):!p.shiftKey&&h.current.getRootNode().activeElement===v&&(p.preventDefault(),_==null||_.focus())};return w.jsxs("div",{className:`news-reading-layer ${i?"is-expanded":""}`,children:[i&&w.jsx("button",{className:"news-reading-backdrop","aria-label":"ปิดอ่านเพิ่มเติมและกลับสู่ข่าว",tabIndex:-1,onClick:c}),w.jsxs("div",{ref:h,className:"news-reading-panels",role:i?"dialog":void 0,"aria-modal":i||void 0,"aria-label":i?"อ่านข่าวและคำอธิบายเพิ่มเติม":void 0,onKeyDown:m,children:[w.jsx(w2,{event:s,symbol:e,onClose:r,explainerOpen:i,onLearnMore:l}),i&&w.jsx(D2,{event:s,onClose:c})]})]})}function N2({pair:s,source:e}){const i=as(s.symbol),r=ef(i),l=i.long+i.short,c=i.available?i.long/l*100:null,f=h=>typeof h=="number"&&Number.isFinite(h)?h.toFixed(s.assetClass==="metals"||s.assetClass==="oil"?2:s.symbol.endsWith("JPY")?3:5):"—";return w.jsxs("section",{className:"sentiment-card","aria-label":`Sentiment ${s.symbol}`,children:[w.jsxs("header",{children:[w.jsx(zM,{size:19}),w.jsxs("div",{children:[w.jsx("h2",{children:"COMMUNITY SENTIMENT"}),w.jsxs("small",{children:["Myfxbook · ",rs(e)]})]})]}),i.available?w.jsxs(w.Fragment,{children:[w.jsxs("div",{className:"sentiment-ratio",children:[w.jsxs("div",{className:"short",children:[w.jsx("small",{children:"SHORT"}),w.jsxs("strong",{children:[i.short,w.jsx("span",{children:"%"})]})]}),w.jsxs("div",{className:"ratio-caption",children:["สัดส่วนสถานะ",w.jsx("br",{}),"ของชุมชน"]}),w.jsxs("div",{className:"long",children:[w.jsx("small",{children:"LONG"}),w.jsxs("strong",{children:[i.long,w.jsx("span",{children:"%"})]})]})]}),w.jsxs("div",{className:"average-prices",children:[w.jsxs("div",{children:[w.jsx("small",{children:"ราคา Short เฉลี่ย"}),w.jsx("strong",{className:"short",children:f(i.avgShort)})]}),w.jsxs("div",{children:[w.jsx("small",{children:"ราคา Long เฉลี่ย"}),w.jsx("strong",{className:"long",children:f(i.avgLong)})]})]})]}):w.jsxs("div",{className:"no-sentiment",children:[w.jsx(Fp,{size:22}),w.jsx("strong",{children:"ยังไม่มีข้อมูล Sentiment"}),w.jsx("span",{children:"ไม่แทนค่าที่ขาดหายด้วย Short/Long 50/50"})]}),i.available&&w.jsxs("div",{className:"stellar-color-key","aria-label":"ระดับสีดาวตามสัดส่วน Sentiment",children:[w.jsx("div",{className:"stellar-color-scale",style:{background:A2},children:w.jsx("i",{style:{left:`${c}%`,background:r.color}})}),w.jsxs("div",{children:[w.jsx("span",{children:"SHORT 100%"}),w.jsx("span",{children:"50 / 50"}),w.jsx("span",{children:"LONG 100%"})]})]}),i.available&&Math.abs(l-100)>1e-6&&w.jsxs("p",{className:"rounding-note",children:["ตัวเลขจากแหล่งข้อมูลรวม ",l,"% จากการปัดเศษ · ปรับเฉพาะตำแหน่งสีให้ครบ 100%"]}),w.jsxs("div",{className:"sentiment-source-meta",children:[w.jsxs("span",{children:["ดึงสำเร็จ ",Ya(e.lastSuccessAt)]}),i.available&&w.jsxs("span",{children:["ข้อมูลรายการนี้ ",Ya(i.asOf)]}),i.available&&i.avgLong===null&&i.avgShort===null&&w.jsx("span",{children:"แหล่งข้อมูลไม่มีราคาเฉลี่ยของรายการนี้"})]}),w.jsx("p",{children:"สีดาว = สัดส่วนสถานะของชุมชน ไม่ใช่แนวโน้มราคา"})]})}function L2({pair:s,motionClock:e,playing:i,speed:r,connection:l,onClose:c,onClearConnection:f,onSelect:h,relatedCount:m,correlationsVisible:p,filter:g,onConnectionSelect:_,dataRevision:v,market:x}){const E=nt.useRef(null);nt.useEffect(()=>{E.current&&(E.current.scrollTop=0)},[s.symbol]);const D=Op(s.symbol).filter(y=>{var F;return g==="all"||((F=yr.find(V=>V.symbol===y.symbol))==null?void 0:F.assetClass)===g}),M=l&&(l.source===s.symbol?l.target:l.source);return w.jsxs("aside",{className:"stellar-inspector","aria-label":`รายละเอียด ${s.symbol}`,children:[w.jsxs("header",{className:"inspector-heading",children:[w.jsxs("div",{children:[w.jsx("p",{className:"eyebrow",children:"STELLAR OBSERVATORY"}),w.jsxs("h2",{children:[s.symbol,w.jsx("span",{children:s.assetClass.toUpperCase()})]})]}),w.jsx("button",{className:"icon-button","aria-label":"ปิดรายละเอียดดาว",onClick:c,children:w.jsx(Wl,{size:19})})]}),w.jsxs("div",{className:"inspector-scroll",ref:E,children:[w.jsxs("div",{className:"stellar-hero",children:[w.jsx(m2,{symbol:s.symbol,motionClock:e,playing:i,motionSpeed:r,dataRevision:v}),w.jsx("span",{className:"stellar-caption",children:s.name})]}),w.jsx(N2,{pair:s,source:x.sentiment}),w.jsxs("section",{className:"connection-detail","aria-label":"รายละเอียดเส้น Correlation",children:[w.jsxs("div",{className:"connection-title",children:[w.jsx(Bu,{size:16}),w.jsx("h3",{children:"CORRELATION"}),l&&w.jsx("button",{className:"icon-button","aria-label":"ล้างเส้นที่เลือก",onClick:f,children:w.jsx(Wl,{size:15})})]}),l?w.jsxs(w.Fragment,{children:[w.jsxs("div",{className:"connection-pair",children:[w.jsx("button",{onClick:()=>h(l.source),children:l.source}),w.jsx(Bu,{size:15}),w.jsx("button",{onClick:()=>h(l.target),children:l.target})]}),w.jsxs("div",{className:`connection-value ${kl(l.value)}`,style:{color:pi(l.value)},children:[w.jsxs("strong",{children:[l.value>=0?"+":"",Math.round(l.value*100),w.jsx("small",{children:"%"})]}),w.jsx("span",{children:kl(l.value)==="neutral"?"สัมพันธ์อ่อน / ใกล้ศูนย์":l.value>0?"สัมพันธ์ในทิศทางเดียวกัน":"สัมพันธ์ในทิศทางตรงข้าม"})]}),w.jsxs("p",{children:["MT5 · Pearson จากผลตอบแทน H1 ที่ปิดแล้ว",w.jsx("br",{}),l.samples," ช่วงตรงกัน · สิ้นสุด ",Ya(l.endAt)]})]}):w.jsx("p",{className:"connection-empty",children:p?w.jsxs(w.Fragment,{children:["เน้น ",m," เส้นที่มีข้อมูลของ ",s.symbol,w.jsx("br",{}),m?"กดชื่อบนเส้น หรือเลือกจากรายการด้านล่าง":"ยังไม่มีราคาที่เพียงพอและตรงช่วงเวลา"]}):w.jsxs(w.Fragment,{children:["ซ่อนเส้นอยู่ · เปิด Correlation",w.jsx("br",{}),"เพื่อดูความสัมพันธ์กับดาวอื่น"]})}),w.jsxs("p",{className:"correlation-source-meta",children:["MT5 · ",rs(x.correlations),x.correlations.marketStatus==="market_closed"?" · ตลาดปิด":"",w.jsx("br",{}),"แท่งข้อมูลล่าสุด ",Ya(x.correlations.asOf)]}),w.jsxs("div",{className:"correlation-list-heading",children:[w.jsxs("strong",{children:["คู่ที่สัมพันธ์ ",w.jsx("span",{children:D.length})]}),w.jsx("small",{children:"เรียงตามความสัมพันธ์มาก → น้อย"})]}),w.jsx("div",{className:"correlation-list",role:"region","aria-label":`รายการ Correlation ของ ${s.symbol}`,tabIndex:0,children:D.map(y=>w.jsxs("button",{className:`correlation-row ${kl(y.value)}`,style:{"--correlation-color":pi(y.value)},"aria-label":`${s.symbol} กับ ${y.symbol} ${y.value>=0?"+":""}${Math.round(y.value*100)}%`,"aria-pressed":M===y.symbol,onClick:()=>_({source:s.symbol,target:y.symbol,value:y.value}),children:[w.jsx("span",{className:"correlation-symbol",children:y.symbol}),w.jsx("span",{className:"correlation-meter",children:w.jsx("i",{style:{width:`${Math.abs(y.value)*100}%`}})}),w.jsxs("strong",{children:[y.value>=0?"+":"",Math.round(y.value*100),"%"]})]},y.symbol))},`${s.symbol}:${g}`),w.jsx("p",{className:"list-scroll-hint",children:D.length?"กดคู่ที่มีข้อมูลเพื่อเน้นเส้นบนกาแล็กซี่":"ไม่มีเส้นที่คำนวณได้สำหรับสินทรัพย์นี้"})]}),w.jsxs("p",{className:"inspector-note",children:[w.jsx("span",{className:"gold-key",children:"จุดสีทอง"})," = ดาวที่เชื่อมกับดาวที่เลือก",w.jsx("br",{}),"แสงวิ่งบนเส้นเมื่อ Correlation > +70% หรือ < −70%",w.jsx("br",{}),"ความสัมพันธ์ย้อนหลัง ไม่ใช่การคาดการณ์ราคา",w.jsx("br",{}),"โมชั่นใช้ประกอบภาพ ไม่ใช่คำสั่งซื้อขาย"]})]})]})}function O2({assetBase:s="/",marketUrl:e="/api/market",setupUrl:i="/connect",embedded:r=!1,requireHeartbeat:l=!1}={}){var ve;const c=nt.useRef(null),f=v2({marketUrl:e,requireHeartbeat:l}),[h,m]=nt.useState(null),[p,g]=nt.useState("all"),[_,v]=nt.useState(null),[x,E]=nt.useState(!1),[D,M]=nt.useState(()=>Zi()),y=nt.useRef(Zi()),[F,V]=nt.useState(!0),[R,N]=nt.useState(1),[L,P]=nt.useState(()=>matchMedia("(prefers-reduced-motion: reduce)").matches),[T,O]=nt.useState(!0),[B,k]=nt.useState(0),[J,se]=nt.useState("loading"),[Y,j]=nt.useState(!1),[z,H]=nt.useState(!1),[ee,oe]=nt.useState(null),[fe,U]=nt.useState(!1),re=nt.useRef({value:0}),xe=yr.find(ne=>ne.symbol===h)||null,Ue=nt.useMemo(()=>aS(h,D),[h,D,f.revision]),Ie=nt.useMemo(()=>QC(p),[p,f.revision]),Xe=ee&&Ie.find(ne=>ne.source===ee.source&&ne.target===ee.target||ne.source===ee.target&&ne.target===ee.source)||null,{displayPair:ue,expanded:ye}=E2(z,xe,L),we=Ue.find(ne=>ne.id===_),at=!!(we&&fe),Ge=yr.filter(ne=>p==="all"||ne.assetClass===p).length,mt=Ge*(Ge-1)/2,un=Ie.length,ut=Ie.filter(ne=>ne.source===h||ne.target===h).length,vt=(f.correlations.instruments||[]).filter(ne=>ne.status==="missing").map(ne=>ne.symbol),Mt=ne=>{M(ne),v(null),U(!1)},pt=nt.useCallback(ne=>{m(ne),H(!0),oe(null),v(null),U(!1),g(Ae=>{var pe;return Ae!=="all"&&((pe=yr.find(Se=>Se.symbol===ne))==null?void 0:pe.assetClass)!==Ae?"all":Ae})},[]),_t=nt.useCallback(ne=>{m(Ae=>Ae===ne.source||Ae===ne.target?Ae:ne.source),oe(ne),H(!0),O(!0),v(null),U(!1)},[]),Gt=nt.useCallback(()=>{const ne=we==null?void 0:we.id;v(null),U(!1),requestAnimationFrame(()=>{var Ae,pe;return(pe=(Ae=c.current)==null?void 0:Ae.getRootNode().getElementById(`news-${ne}`))==null?void 0:pe.focus({preventScroll:!0})})},[we==null?void 0:we.id]),_n=nt.useCallback(()=>{U(!1),requestAnimationFrame(()=>{var ne,Ae;return(Ae=(ne=c.current)==null?void 0:ne.getRootNode().getElementById("news-learn-more"))==null?void 0:Ae.focus({preventScroll:!0})})},[]),Xt=nt.useCallback(()=>{H(!1),requestAnimationFrame(()=>{var ne,Ae;return(Ae=(ne=c.current)==null?void 0:ne.getRootNode().getElementById("open-stellar-inspector"))==null?void 0:Ae.focus({preventScroll:!0})})},[]),fn=nt.useCallback(()=>se("ready"),[]),Z=nt.useCallback(()=>se("error"),[]),Ft=ne=>{g(ne),oe(null),xe&&ne!=="all"&&xe.assetClass!==ne&&(m(null),H(!1),v(null),U(!1))},Dt=()=>{g("all"),m(null),H(!1),oe(null),v(null),U(!1),j(!1),O(!0),k(ne=>ne+1),V(!0)};nt.useEffect(()=>{const ne=Zi(),Ae=y.current;ne!==Ae&&(M(pe=>pe===Ae?ne:pe),y.current=ne)},[f.revision]),nt.useEffect(()=>{const ne=matchMedia("(prefers-reduced-motion: reduce)"),Ae=pe=>P(pe.matches);return ne.addEventListener("change",Ae),()=>ne.removeEventListener("change",Ae)},[]),nt.useEffect(()=>{r||(document.title="Metafxclub · Sentiment Universe")},[r]);const I=ne=>x2(ne,{embedded:r,root:c.current,explainerOpen:fe,eventOpen:!!we,settingsOpen:Y,inspectorOpen:z,closeExplainer:_n,closeNews:Gt,closeSettings:()=>j(!1),closeInspector:Xt,toggleMotion:()=>V(Ae=>!Ae)}),b=["offline","stale"].includes(f.connection),K=[f.sentiment,f.correlations].some(ne=>["needs_configuration","auth_error","auth_failed","authentication_failed"].includes(ne.status)),ce=f.connection==="stale"?"บริการข้อมูลหยุดอัปเดต · แสดงข้อมูลรอบที่เก็บไว้":f.connection==="offline"?"ยังเชื่อมบริการข้อมูลไม่ได้ · แสดงข้อมูลรอบที่เก็บไว้":"เชื่อมบัญชี Myfxbook และเลือก MT5 ของเครื่องนี้ครั้งแรก";return w.jsxs("div",{ref:c,onKeyDown:I,className:`app-shell ${L?"reduce-motion":""}`,children:[w.jsxs("header",{className:"app-header",inert:at,children:[w.jsxs("a",{className:"brand",href:"#universe","aria-label":"Metafxclub กลับภาพรวม",onClick:ne=>{ne.preventDefault(),Dt()},children:[w.jsx("img",{src:uS(s,"metafx-mark.png"),alt:""}),w.jsx("span",{children:"METAFXCLUB"})]}),w.jsx("div",{className:"product-title",children:"SENTIMENT UNIVERSE"}),w.jsx("div",{className:"asset-filters",role:"group","aria-label":"กรองกลุ่มสินทรัพย์",children:T2.map(([ne,Ae,pe])=>w.jsxs("button",{className:p===ne?"current":"","aria-pressed":p===ne,onClick:()=>Ft(ne),children:[Ae," ",w.jsx("span",{children:pe})]},ne))}),w.jsx(R2,{symbol:h,onSelect:pt}),w.jsxs("a",{className:"demo-badge live-connect",href:i,target:"_blank",rel:"noopener noreferrer",title:`Myfxbook · ${rs(f.sentiment)}`,children:["ตั้งค่า Myfxbook / MT5 ",w.jsx(Xl,{size:12})]})]}),w.jsxs("main",{className:`app-main ${ye?"has-inspector":""}`,id:"universe",children:[w.jsx(C2,{inactive:at,symbol:h,news:Ue,eventId:we==null?void 0:we.id,onEvent:ne=>{v(ne===(we==null?void 0:we.id)?null:ne),U(!1)},highOnly:x,setHighOnly:E,day:D,onDay:Mt,source:f.news}),w.jsxs("div",{className:"galaxy-stage",inert:at,children:[w.jsx("div",{className:"scene-host",tabIndex:-1,children:w.jsx(p2,{assetBase:s,pairs:yr,selectedSymbol:h,filter:p,axis:"free",reducedMotion:L,playing:F&&!L,motionSpeed:R,motionClock:re,resetKey:B,correlationsVisible:T,selectedCorrelation:Xe,dataRevision:f.revision,onCorrelationSelect:_t,onSelect:pt,onReady:fn,onError:Z})}),(b||K)&&w.jsxs("section",{className:"connection-notice","aria-label":"สถานะแหล่งข้อมูล",children:[w.jsxs("div",{role:"status",children:[w.jsx("strong",{children:ce}),b&&w.jsxs("small",{children:["ตรวจบริการในเครื่อง · ข้อมูลต้นทางสำเร็จล่าสุด Myfxbook ",Ya(f.sentiment.lastSuccessAt)]})]}),w.jsxs("a",{href:i,target:"_blank",rel:"noopener noreferrer",children:["เปิดการตั้งค่า ",w.jsx(Xl,{size:13})]})]}),J!=="ready"&&w.jsx("div",{className:"scene-status",role:"status",children:J==="error"?"เปิดมุมมอง 3D ไม่สำเร็จ ยังเลือกสินทรัพย์จากช่องค้นหาได้":"กำลังเตรียมกาแล็กซี่…"}),w.jsxs("div",{className:"scene-topbar",children:[xe?w.jsxs("button",{id:"open-stellar-inspector",className:"view-label","aria-label":`เปิดรายละเอียด ${h}`,"aria-expanded":z,onClick:()=>H(!0),children:[xe.clusterId," / ",w.jsx("strong",{children:h})]}):w.jsxs("div",{className:"view-label overview-label",children:["ภาพรวม ",w.jsxs("strong",{children:[Ge," สินทรัพย์"]})]}),w.jsxs("div",{className:"view-tools",children:[w.jsxs("button",{className:"tool-button","aria-pressed":T,onClick:()=>{O(ne=>!ne),oe(null)},children:[w.jsx(Bu,{size:16}),"Correlation ",w.jsx("span",{children:T?un:0})]}),w.jsx("button",{className:"icon-button","aria-label":F&&!L?"หยุดโมชั่นทั้งหมด":"เริ่มโมชั่น",disabled:L,onClick:()=>V(ne=>!ne),children:F&&!L?w.jsx(DM,{size:19}):w.jsx(NM,{size:19})}),w.jsx("button",{className:"icon-button","aria-label":"ตั้งค่าการเคลื่อนไหว","aria-expanded":Y,onClick:()=>j(ne=>!ne),children:w.jsx(gM,{size:19})})]})]}),Y&&w.jsxs("section",{className:"view-settings","aria-label":"ตั้งค่าการเคลื่อนไหว",children:[w.jsxs("header",{children:[w.jsx("strong",{children:"การเคลื่อนไหว"}),w.jsx("button",{className:"icon-button","aria-label":"ปิดการตั้งค่า",onClick:()=>j(!1),children:w.jsx(Wl,{size:18})})]}),w.jsxs("label",{children:["ความเร็ว",w.jsxs("select",{"aria-label":"ความเร็วโมชั่น",value:R,onChange:ne=>N(Number(ne.target.value)),children:[w.jsx("option",{value:"0.5",children:"0.5×"}),w.jsx("option",{value:"1",children:"1×"}),w.jsx("option",{value:"1.8",children:"1.8×"})]})]}),w.jsxs("label",{children:["ลดการเคลื่อนไหว",w.jsx("input",{type:"checkbox",checked:L,onChange:ne=>P(ne.target.checked)})]}),w.jsx("p",{children:"โมชั่นเป็นภาพประกอบ ไม่ใช่การส่งคำสั่งเทรด"})]}),w.jsxs("div",{className:"scene-bottom",children:[w.jsx("div",{className:"camera-controls",role:"group","aria-label":"ควบคุมมุมมอง",children:w.jsxs("button",{className:"reset-overview","aria-label":"รีเซต กลับภาพรวมไม่เลือกสินทรัพย์",onClick:Dt,children:[w.jsx(OM,{size:17}),w.jsx("span",{children:"รีเซต"})]})}),w.jsx("span",{className:"scene-hint",children:"ลากซ้ายหมุน · ลากขวาเลื่อน · ล้อเมาส์ซูม"})]}),T&&w.jsxs("div",{className:"correlation-legend","aria-label":"คำอธิบายสีเส้น Correlation",children:[w.jsxs("span",{children:[w.jsx(Bu,{size:14}),h?`${h} · เน้น ${ut} / ${un} เส้น`:`คำนวณได้ ${un} / ${mt} เส้น`]}),w.jsxs("div",{className:"correlation-color-bands",children:[w.jsxs("b",{style:{color:pi(0)},children:[w.jsx("i",{style:{background:pi(0)}}),"เหลือง −30% ถึง +30%"]}),w.jsx("small",{children:"ใกล้ 0% ช่วง ±10% สว่างขึ้น"}),w.jsxs("b",{style:{color:pi(.6)},children:[w.jsx("i",{style:{background:pi(.6)}}),"เขียว +40 ถึง <80%"]}),w.jsxs("b",{style:{color:pi(.9)},children:[w.jsx("i",{style:{background:pi(.9)}}),"เข้ม +80 ถึง +100%"]}),w.jsxs("b",{style:{color:pi(-.6)},children:[w.jsx("i",{style:{background:pi(-.6)}}),"แดง −40 ถึง >−80%"]}),w.jsxs("b",{style:{color:pi(-.9)},children:[w.jsx("i",{style:{background:pi(-.9)}}),"เข้ม −80 ถึง −100%"]})]}),w.jsx("small",{children:"ช่วง ±30–40% ไล่สีต่อเนื่อง"}),w.jsx("small",{children:h?"จุดทอง = ดาวที่เชื่อมกับดาวที่เลือก":"เน้นเส้นที่ความสัมพันธ์ตั้งแต่ ±60%"}),w.jsx("small",{children:"แสงวิ่งเฉพาะ > +70% หรือ < −70%"}),w.jsxs("small",{className:"live-correlation-status",children:["MT5 · ",rs(f.correlations),f.correlations.marketStatus==="market_closed"?" · ตลาดปิด":"",w.jsx("br",{}),"H1 ล่าสุด ",Ya(f.correlations.asOf),vt.length>0&&w.jsxs(w.Fragment,{children:[w.jsx("br",{}),vt.join(", ")," ยังไม่มีข้อมูล H1 ที่ใช้คำนวณจาก MT5"]})]})]})]}),w.jsx("div",{className:`inspector-dock ${ye?"is-open":""}`,"aria-hidden":!z||at,inert:!z||at,"data-state":ye?"open":ue?"closing":"closed",children:ue&&w.jsx(L2,{pair:ue,motionClock:re,playing:F&&!L&&z,speed:R,connection:Xe,dataRevision:f.revision,market:f,onClose:Xt,onClearConnection:()=>oe(null),onSelect:pt,relatedCount:ut,correlationsVisible:T,filter:p,onConnectionSelect:_t})}),we&&w.jsx(U2,{embedded:r,event:we,symbol:h,explainerOpen:fe,onClose:Gt,onLearnMore:()=>U(ne=>!ne),onCloseExplainer:_n})]}),w.jsxs("footer",{className:"app-footer",inert:at,children:[w.jsxs("span",{children:[w.jsx(Fp,{size:15}),"คลิกดาวดูเส้นเชื่อม · ลากซ้ายหมุน · ลากขวาเลื่อน · ล้อเมาส์ซูม"]}),w.jsxs("span",{className:"live-flow-status",role:"status",children:[b?ce:f.connection==="loading"?"กำลังเชื่อมบริการข้อมูล":`Myfxbook ${rs(f.sentiment)} · MT5 ${((ve=f.correlations.coverage)==null?void 0:ve.available)??0}/32 · ปฏิทิน ${f.news.status==="empty"?"พร้อม":rs(f.news)}`," · ไม่มีการส่งคำสั่งเทรด"]})]}),w.jsxs("div",{className:"sr-only","aria-live":"polite",children:[h?`เลือก ${h}`:"ภาพรวม ยังไม่เลือกสินทรัพย์"," มีข่าว ",Ue.length," เหตุการณ์"]})]})}hM.createRoot(document.getElementById("root")).render(w.jsx(sM.StrictMode,{children:w.jsx(O2,{})}));
