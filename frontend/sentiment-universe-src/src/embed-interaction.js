export function universeFocusable(root) {
  return [...root.querySelectorAll('button:not(:disabled),a[href],input:not(:disabled),select:not(:disabled),textarea:not(:disabled),[tabindex="0"]')]
    .filter(element=>!element.closest('[inert]')&&element.getClientRects().length);
}

// React invokes this after child controls (e.g. the search combobox) handle keys.
export function handleUniverseKey(event, state) {
  if(event.key==='Escape'){
    const close=state.explainerOpen?state.closeExplainer:state.eventOpen?state.closeNews:state.settingsOpen?state.closeSettings:state.inspectorOpen?state.closeInspector:null;
    if(!close)return false;
    close();event.preventDefault();event.stopPropagation();return true;
  }
  if(state.embedded&&event.key==='Tab'){
    const items=universeFocusable(state.root),active=state.root.getRootNode().activeElement;
    if(event.shiftKey&&active===items[0]){event.preventDefault();items.at(-1)?.focus();}
    else if(!event.shiftKey&&active===items.at(-1)){event.preventDefault();items[0]?.focus();}
    // HQ's bubbling focus trap cannot inspect the active element in this shadow.
    event.stopPropagation();return true;
  }
  if(state.explainerOpen||/INPUT|SELECT|TEXTAREA|BUTTON|A/.test(event.target?.tagName))return false;
  if(event.key===' '){event.preventDefault();event.stopPropagation();state.toggleMotion();return true;}
  return false;
}
