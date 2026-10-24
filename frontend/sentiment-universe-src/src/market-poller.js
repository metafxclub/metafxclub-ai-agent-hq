// One request at a time, with cancellable timeout and no work after unmount.
export function startMarketPolling({url, onData, onFailure, fetchImpl = globalThis.fetch,
  intervalMs = 30000, timeoutMs = 10000, schedule = setTimeout, cancel = clearTimeout}) {
  let disposed = false, timer, controller, timeout;
  const refresh = async () => {
    controller = new AbortController();
    timeout = schedule(() => controller.abort(), timeoutMs);
    try {
      const response = await fetchImpl(url, {cache:'no-store', credentials:'omit', signal:controller.signal});
      if (!response.ok) throw new Error('market_unavailable');
      const data = await response.json();
      if (!disposed) onData(data);
    } catch {
      if (!disposed) onFailure();
    } finally {
      cancel(timeout);
      if (!disposed) timer = schedule(refresh, intervalMs);
    }
  };
  void refresh();
  return () => {disposed = true; cancel(timer); cancel(timeout); controller?.abort();};
}
