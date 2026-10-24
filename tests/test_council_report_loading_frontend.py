import json
import re
import shutil
import subprocess
import unittest
from pathlib import Path

from test_frontend_polling_stability import function_block


ROOT = Path(__file__).resolve().parents[1]


class CouncilReportLoadingFrontendTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.main = (ROOT / "frontend/src/app/main.js").read_text(encoding="utf-8")
        cls.node = shutil.which("node") or str(
            Path.home() / ".cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe"
        )

    def run_js(self, body):
        constants = "\n".join(
            re.search(rf"^const {name} = .*?;", self.main, re.M).group(0)
            for name in (
                "DEFAULT_FETCH_TIMEOUT_MS", "PROP_REPORT_FETCH_TIMEOUT_MS",
                "AI_TRADE_COUNCIL_REPORT_FETCH_TIMEOUT_MS", "OPEN_PROP_REPORT_POLL_TTL_MS",
                "AI_TRADE_COUNCIL_PROP_ID", "AI_TRADE_HEARTBEAT_FRESH_SECONDS",
            )
        )
        fetch_start = self.main.index("class FetchTimeoutError ")
        fetch_end = self.main.index("\nfunction renderCodexRateReserve", fetch_start)
        script = constants + "\n" + r"""
const assert = require('node:assert/strict');
let clock = 100000;
Date.now = () => clock;
const timers = new Map(); let timerId = 0;
const window = {
  setTimeout: (callback, delay) => { const id = ++timerId; timers.set(id, {callback, due: clock + delay}); return id; },
  clearTimeout: (id) => timers.delete(id),
};
async function advance(milliseconds) {
  clock += milliseconds;
  for (const [id, timer] of [...timers]) {
    if (timer.due <= clock) { timers.delete(id); timer.callback(); }
  }
  for (let turn = 0; turn < 12; turn += 1) await Promise.resolve();
}
let fetches = [];
const fetch = (path, {signal}) => new Promise((resolve, reject) => {
  const request = {path, signal, resolve: (body) => resolve({ok: true, json: async () => body})};
  fetches.push(request);
  if (signal.aborted) reject(signal.reason);
  else signal.addEventListener('abort', () => reject(signal.reason), {once: true});
});
const propReportInFlight = new Map();
const state = {propReports: {}, propReportLoadedAt: {}, propReportLoadState: {}, panelObject: null, globalMetatraderHub: {}};
const renderOperationalSidebars = () => {};
const selectObject = () => {};
const safeDashboardDisplayText = (value, fallback = '') => value == null ? fallback : String(value);
const signalCouncilModel = (report = {}) => report.aiTradeCouncil || {};
const report = { aiTradeCouncil: {platformConnections: {
  active: {platform: 'mt5', candidateId: 'selected-mt5'},
  items: [{platform: 'mt5', candidateId: 'selected-mt5', selected: true,
    connectionState: 'connected', observedAt: new Date(clock).toISOString(), ageSeconds: 0, freshForSeconds: 20}],
}}};
""" + self.main[fetch_start:fetch_end] + "\nasync " + function_block(self.main, "loadPropReport")
        script += "\n" + function_block(self.main, "signalSelectedPlatformConnectionHealth")
        script += "\n(async () => {\n" + body + "\nprocess.stdout.write(JSON.stringify({ok:true}));\n})().catch(error => {console.error(error);process.exit(1);});"
        result = subprocess.run([self.node, "-e", script], capture_output=True, text=True, encoding="utf-8", check=True)
        self.assertEqual(json.loads(result.stdout), {"ok": True})

    def test_slow_council_read_completes_once_with_loading_state(self):
        self.run_js(r"""
const first = loadPropReport('left_analytics_console');
const duplicate = loadPropReport('left_analytics_console');
assert.equal(fetches.length, 1);
assert.equal(state.propReportLoadState.left_analytics_console.status, 'loading');
await advance(32000);
assert.equal(fetches[0].signal.aborted, false);
assert.equal(state.propReportLoadedAt.left_analytics_console, undefined);
report.aiTradeCouncil.platformConnections.items[0].observedAt = new Date(clock).toISOString();
fetches[0].resolve(report);
assert.deepEqual(await Promise.all([first, duplicate]), [report, report]);
assert.equal(state.propReportLoadState.left_analytics_console.status, 'ready');
assert.equal(signalSelectedPlatformConnectionHealth(report).connected, true);
assert.equal(propReportInFlight.size, 0);
""")

    def test_other_equipment_still_times_out_at_twenty_seconds(self):
        self.run_js(r"""
// The old FX cube now uses Sentiment's independent read model; exercise an
// equipment report that still goes through this shared loader.
const pending = loadPropReport('right_server_racks');
await advance(19999);
assert.equal(fetches[0].signal.aborted, false);
await advance(1);
assert.equal(await pending, null);
assert.equal(fetches[0].signal.reason.timeoutMs, 20000);
assert.equal(state.propReportLoadState.right_server_racks.status, 'error');
assert.equal(state.propReportLoadedAt.right_server_racks, undefined);
""")

    def test_council_timeout_is_bounded_and_old_report_stays_fail_closed(self):
        self.run_js(r"""
state.propReports.left_analytics_console = report;
state.propReportLoadedAt.left_analytics_console = clock;
const pending = loadPropReport('left_analytics_console');
await advance(30001);
assert.equal(signalSelectedPlatformConnectionHealth(report).connected, false);
assert.equal(signalSelectedPlatformConnectionHealth(report).reasonCode, 'council_report_expired');
await advance(29999);
assert.equal(await pending, null);
assert.equal(fetches[0].signal.reason.timeoutMs, 60000);
assert.equal(state.propReportLoadState.left_analytics_console.status, 'error');
assert.equal(state.propReports.left_analytics_console, report);
assert.equal(state.propReportLoadedAt.left_analytics_console, 100000);
assert.equal(signalSelectedPlatformConnectionHealth(report).reasonCode, 'council_report_refresh_failed');
assert.equal(propReportInFlight.size, 0);
""")

    def test_parent_abort_cancels_read_without_claiming_fresh_connection(self):
        self.run_js(r"""
state.propReports.left_analytics_console = report;
state.propReportLoadedAt.left_analytics_console = clock - 31000;
const controller = new AbortController();
const pending = loadPropReport('left_analytics_console', {signal: controller.signal});
controller.abort();
assert.equal(await pending, null);
assert.equal(fetches[0].signal.aborted, true);
assert.equal(state.propReportLoadedAt.left_analytics_console, 69000);
assert.equal(signalSelectedPlatformConnectionHealth(report).connected, false);
assert.equal(signalSelectedPlatformConnectionHealth(report).reasonCode, 'council_report_expired');
assert.equal(propReportInFlight.size, 0);
""")


if __name__ == "__main__":
    unittest.main()
