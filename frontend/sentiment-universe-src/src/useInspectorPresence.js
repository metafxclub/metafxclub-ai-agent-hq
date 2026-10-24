import { useEffect, useState } from 'react';

export const INSPECTOR_TRANSITION_MS = 460;

// Retain the outgoing panel until the width/slide transition has finished.
// Cleanup cancels stale close timers and entrance frames on rapid re-selection.
export function useInspectorPresence(open, pair, reducedMotion) {
  const [displayPair, setDisplayPair] = useState(null);
  const [expanded, setExpanded] = useState(false);
  useEffect(() => {
    let firstFrame, secondFrame, closeTimer;
    if (open && pair) {
      setDisplayPair(pair);
      if (reducedMotion) setExpanded(true);
      else firstFrame = requestAnimationFrame(() => {
        secondFrame = requestAnimationFrame(() => setExpanded(true));
      });
    } else {
      setExpanded(false);
      if (reducedMotion) setDisplayPair(null);
      else closeTimer = setTimeout(() => setDisplayPair(null), INSPECTOR_TRANSITION_MS);
    }
    return () => {
      cancelAnimationFrame(firstFrame);
      cancelAnimationFrame(secondFrame);
      clearTimeout(closeTimer);
    };
  }, [open, pair, reducedMotion]);
  return { displayPair, expanded };
}
