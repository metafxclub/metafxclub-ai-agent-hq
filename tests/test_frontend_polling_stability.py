import json
import shutil
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MAIN_PATH = ROOT / "frontend" / "src" / "app" / "main.js"


def function_block(source: str, name: str) -> str:
    start = source.index(f"function {name}(")
    next_function = source.find("\nfunction ", start + 10)
    next_async_function = source.find("\nasync function ", start + 10)
    candidates = [index for index in (next_function, next_async_function) if index >= 0]
    end = min(candidates) if candidates else len(source)
    return source[start:end]


class FrontendPollingStabilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.main = MAIN_PATH.read_text(encoding="utf-8")

    def node_binary(self) -> str:
        candidates = [
            shutil.which("node"),
            str(
                Path.home()
                / ".cache"
                / "codex-runtimes"
                / "codex-primary-runtime"
                / "dependencies"
                / "node"
                / "bin"
                / "node.exe"
            ),
        ]
        for candidate in candidates:
            if candidate and Path(candidate).exists():
                return candidate
        self.fail("Node.js runtime is required")

    def test_mission_poll_uses_bounded_runtime_endpoint_and_dedicated_timeout(self) -> None:
        self.assertIn("const MISSION_POLL_MS = 30000;", self.main)
        self.assertIn("const MISSION_FETCH_TIMEOUT_MS = 25000;", self.main)
        load_block = function_block(self.main, "loadBridgeMissions")
        self.assertIn('"/api/missions?scope=runtime&limit=100"', load_block)
        self.assertIn("{ timeoutMs: MISSION_FETCH_TIMEOUT_MS, signal }", load_block)

    def test_cross_tab_polling_uses_single_expiring_local_storage_lease(self) -> None:
        self.assertIn('const POLLING_LEADER_STORAGE_KEY = "metafx-hq-polling-leader-v1";', self.main)
        self.assertIn("const POLLING_LEADER_LEASE_MS = 45000;", self.main)
        self.assertIn("const POLLING_LEADER_RENEW_MS = 10000;", self.main)
        claim = function_block(self.main, "claimPollingLeadership")
        self.assertIn("state.pollingLeadership.storageAvailable === false", claim)
        self.assertIn("current.expiresAt > now", claim)
        self.assertIn("writePollingLeaderLease(now + POLLING_LEADER_LEASE_MS)", claim)
        self.assertNotIn("force", claim)
        lifecycle = function_block(self.main, "initializePollingLeadership")
        self.assertIn('document.addEventListener("visibilitychange"', lifecycle)
        self.assertIn('window.addEventListener("pagehide"', lifecycle)
        self.assertIn('window.addEventListener("pageshow"', lifecycle)
        self.assertIn('window.addEventListener("storage"', lifecycle)
        self.assertIn("releasePollingLeadership();", lifecycle)
        self.assertIn("stopAutomaticPolling();", lifecycle)
        self.assertNotIn("force: true", lifecycle)

    def test_periodic_pollers_are_leader_gated_but_manual_rate_refresh_remains_available(self) -> None:
        for name in (
            "startCodexRateLimitPolling",
            "startOperatorModePolling",
            "startAgentCollaborationPolling",
            "startMissionPolling",
        ):
            self.assertIn("runAutomaticPollingTask", function_block(self.main, name), name)
        automatic_task = function_block(self.main, "runAutomaticPollingTask")
        self.assertIn("isAutomaticPollingLeader()", automatic_task)
        self.assertIn("AbortController", automatic_task)
        self.assertIn("controller.signal.aborted", automatic_task)
        self.assertIn("void refreshCodexRateLimits({ manual: true });", self.main)
        rate_refresh = self.main[
            self.main.index("async function refreshCodexRateLimits("):
            self.main.index("\nfunction startCodexRateLimitPolling", self.main.index("async function refreshCodexRateLimits("))
        ]
        self.assertIn("if (!manual && document.visibilityState", rate_refresh)
        self.assertNotIn("!isAutomaticPollingLeader()", rate_refresh)

    def test_fresh_follower_resolves_initial_read_model_without_stealing_the_lease(self) -> None:
        self.assertIn("initialReadStarted: false", self.main)
        initial_read = function_block(self.main, "runInitialPollingRead")
        self.assertIn("state.pollingLeadership.initialReadStarted", initial_read)
        self.assertIn("void refreshCodexRateLimits();", initial_read)
        self.assertIn("void refreshOperatorMode();", initial_read)
        self.assertIn("void refreshAgentCollaboration();", initial_read)
        self.assertIn("void pollMissionReadModel({ manual: true });", initial_read)
        self.assertNotIn("claimPollingLeadership", initial_read)
        self.assertNotIn("runAutomaticPollingTask", initial_read)

        start = function_block(self.main, "startAutomaticPolling")
        self.assertIn("runInitialPollingRead();", start)
        self.assertIn("claimPollingLeadership();", start)
        self.assertLess(start.index("runInitialPollingRead();"), start.index("claimPollingLeadership();"))

    def test_open_prop_report_reload_is_change_or_ttl_driven(self) -> None:
        self.assertIn("const PROP_REPORT_POLL_TTL_MS = 60000;", self.main)
        load_report = function_block(self.main, "loadPropReport")
        self.assertIn("state.propReportLoadedAt[key] = Date.now();", load_report)
        self.assertIn("propReportInFlight.get(key)", load_report)
        self.assertIn("propReportInFlight.set(key, request)", load_report)
        self.assertIn("propReportInFlight.delete(key)", load_report)
        poll = self.main[
            self.main.index("async function pollMissionReadModel("):
            self.main.index("\nfunction startMissionPolling", self.main.index("async function pollMissionReadModel("))
        ]
        self.assertIn("data?.missionReadModelChanged === true || reportTtlExpired", poll)
        self.assertIn("Date.now() - lastLoadedAt >= PROP_REPORT_POLL_TTL_MS", poll)
        self.assertEqual(poll.count("await loadPropReport(state.modal.id, { signal })"), 1)

    def test_hidden_or_pagehide_clears_and_aborts_every_automatic_poller(self) -> None:
        stop = function_block(self.main, "stopAutomaticPolling")
        for timer in (
            "state.codexRate.timer",
            "state.operatorMode.timer",
            "state.agentCollaboration.timer",
            "state.missionSync.timer",
            "state.pollingLeadership.renewalTimer",
        ):
            self.assertIn(f"window.clearInterval({timer})", stop)
            self.assertIn(f"{timer} = null", stop)
        self.assertIn("abortAutomaticPollingRequests();", stop)
        abort = function_block(self.main, "abortAutomaticPollingRequests")
        self.assertIn("controller.abort()", abort)
        self.assertIn("abortControllers.clear()", abort)
        lifecycle = function_block(self.main, "initializePollingLeadership")
        hidden_branch = lifecycle[lifecycle.index('document.addEventListener("visibilitychange"'):]
        self.assertGreaterEqual(hidden_branch.count("stopAutomaticPolling();"), 2)

    def test_concurrent_prop_report_loads_share_one_request(self) -> None:
        load_report = function_block(self.main, "loadPropReport")
        load_report = f"async {load_report}"
        script = "\n".join([
            "const propReportInFlight = new Map();",
            "let fetchCount = 0;",
            "let resolveFetch = null;",
            "let renderCount = 0;",
            "const PROP_REPORT_FETCH_TIMEOUT_MS = 20000;",
            "const state = { propReports: {}, propReportLoadedAt: {}, propReportLoadState: {}, panelObject: null };",
            "const fetchJson = async () => { fetchCount += 1; return await new Promise((resolve) => { resolveFetch = resolve; }); };",
            "const renderOperationalSidebars = () => { renderCount += 1; };",
            "const selectObject = () => {};",
            load_report,
            "(async () => {",
            "  const first = loadPropReport('left_signal_cube');",
            "  const second = loadPropReport('left_signal_cube');",
            "  if (fetchCount !== 1) throw new Error(`expected one fetch, got ${fetchCount}`);",
            "  resolveFetch({ ok: true, propId: 'left_signal_cube' });",
            "  const values = await Promise.all([first, second]);",
            "  process.stdout.write(JSON.stringify({ fetchCount, renderCount, pending: propReportInFlight.size, loadState: state.propReportLoadState.left_signal_cube?.status, values }));",
            "})().catch((error) => { console.error(error); process.exit(1); });",
        ])
        result = subprocess.run(
            [self.node_binary(), "-e", script],
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        payload = json.loads(result.stdout)
        self.assertEqual(payload["fetchCount"], 1)
        self.assertEqual(payload["renderCount"], 1)
        self.assertEqual(payload["pending"], 0)
        self.assertEqual(payload["loadState"], "ready")
        self.assertEqual(len(payload["values"]), 2)

    def test_failed_prop_report_load_records_safe_retry_state(self) -> None:
        load_report = function_block(self.main, "loadPropReport")
        load_report = f"async {load_report}"
        script = "\n".join([
            "const propReportInFlight = new Map();",
            "const PROP_REPORT_FETCH_TIMEOUT_MS = 20000;",
            "const state = { propReports: {}, propReportLoadedAt: {}, propReportLoadState: {}, panelObject: null };",
            "const fetchJson = async () => { throw new Error('transport details must not reach the UI'); };",
            "const renderOperationalSidebars = () => {};",
            "const selectObject = () => {};",
            load_report,
            "(async () => {",
            "  const value = await loadPropReport('left_signal_cube');",
            "  process.stdout.write(JSON.stringify({ value, pending: propReportInFlight.size, loadState: state.propReportLoadState.left_signal_cube }));",
            "})().catch((error) => { console.error(error); process.exit(1); });",
        ])
        result = subprocess.run(
            [self.node_binary(), "-e", script],
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        payload = json.loads(result.stdout)
        self.assertIsNone(payload["value"])
        self.assertEqual(payload["pending"], 0)
        self.assertEqual(payload["loadState"]["status"], "error")
        self.assertEqual(payload["loadState"]["errorMessage"], "โหลดข้อมูลจาก Local Runner ไม่สำเร็จ")
        self.assertNotIn("transport details", payload["loadState"]["errorMessage"])
        self.assertTrue(payload["loadState"]["lastAttemptAt"])

    def test_collaboration_refresh_marks_request_in_flight_to_coalesce_bursts(self) -> None:
        refresh = self.main[
            self.main.index("async function refreshAgentCollaboration("):
            self.main.index("\nfunction collaborationFormPayload", self.main.index("async function refreshAgentCollaboration("))
        ]
        self.assertIn("if (state.agentCollaboration.inFlight) return null;", refresh)
        self.assertIn("state.agentCollaboration.inFlight = true;", refresh)
        self.assertIn("finally", refresh)
        self.assertIn("state.agentCollaboration.inFlight = false;", refresh)


if __name__ == "__main__":
    unittest.main()
