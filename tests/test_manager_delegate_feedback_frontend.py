"""Manager delegation failures stay visible without inventing a created Task."""

import json
import re
import shutil
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class ManagerDelegateFeedbackFrontendTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.main = (ROOT / "frontend/src/app/main.js").read_text(encoding="utf-8")
        bundled = Path.home() / ".cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe"
        cls.node = shutil.which("node") or (str(bundled) if bundled.exists() else None)
        if not cls.node:
            raise RuntimeError("Node.js is required for Manager feedback tests")
        functions = []
        for name in ["safeDashboardDisplayText", "postJson", "handleBridgeRequestError", "setAgentChatStatus", "handleModalDelegate", "submitManagerCommand"]:
            match = re.search(r"^(?:async )?function " + name + r"\(", cls.main, re.M)
            end = re.search(r"^(?:async )?function ", cls.main[match.end():], re.M)
            functions.append(cls.main[match.start():match.end() + end.start()])
        cls.source = "\n".join(functions)

    def run_case(self, scenario):
        script = r"""
const vm = require('node:vm');
const requests = [], merged = [], events = [];
let renderCount = 0, secretBlocked = false;
const input = {value: 'Read-only text-only goal with exact source IDs', focus() {this.focused = true;}};
const state = {modal: {open: true, type: 'agent', id: 'manager', activeTab: 'chat'},
  agentChat: {agentId: null, message: '', tone: 'neutral'}, bridge: {}, managerCommandInFlight: false};
const els = {modalCommandInput: input, modalDelegateButton: {disabled: false}, modalChatStatus: {textContent: '', dataset: {}}, runCommandButton: {disabled: false}};
const context = {state, els, Date, Math,
  getModalSubject: () => ({id: state.modal.id}), isManagerWorkspace: subject => ['manager', 'ceo'].includes(subject?.id),
  getPromptFromModal: () => input.value, renderGameModal: () => {renderCount++;},
  blockSecretIntent: () => secretBlocked, isMetatraderDiscoveryIntent: () => false,
  updateBridgeLabel: () => {}, updateDecisionLog: text => events.push(text), addBridgeEvent: (...args) => events.push(args),
  setAgentSpeech: () => {}, routeAgentToTargetId: () => {},
  mergeBackendMission: row => merged.push(row.id), isBackendAutoEligibleMission: () => false,
  callMeeting: () => {}, getOfficeAgent: () => null, getTargetPoint: () => null,
  loadBridgeMissions: async () => {}, loadPropReport: async () => {}, selectObject: () => {},
  fetch: (path, options) => new Promise((resolve, reject) => requests.push({path, options, resolve, reject})),
};
vm.createContext(context); vm.runInContext(SOURCE, context);
const respond = (status, body) => requests[requests.length - 1].resolve({ok: status >= 200 && status < 300, status, json: async () => body});
const snapshot = () => ({tab: state.modal.activeTab, visible: els.modalChatStatus.textContent, tone: els.modalChatStatus.dataset.tone,
  draft: input.value, buttonDisabled: els.modalDelegateButton.disabled, inFlight: state.managerCommandInFlight,
  fetchCount: requests.length, merged, renderCount, agentChat: state.agentChat});
(async () => {SCENARIO})().catch(error => {console.error(error); process.exitCode = 1;});
""".replace("SOURCE", json.dumps(self.source)).replace("SCENARIO", scenario)
        result = subprocess.run([self.node, "-e", script], cwd=ROOT, capture_output=True, text=True, encoding="utf-8", timeout=15)
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def test_http_422_exact_backend_reason_is_visible_and_draft_chat_tab_remain(self):
        result = self.run_case("""
const pending = context.handleModalDelegate();
respond(422, {kind: 'manager_source_invalid', messageTh: 'Source record ไม่ตรงกับหลักฐาน Mission ที่ยืนยันแล้ว'});
await pending; process.stdout.write(JSON.stringify(snapshot()));
""")
        self.assertEqual(result["visible"], "Source record ไม่ตรงกับหลักฐาน Mission ที่ยืนยันแล้ว")
        self.assertEqual((result["tab"], result["tone"]), ("chat", "error"))
        self.assertEqual(result["draft"], "Read-only text-only goal with exact source IDs")
        self.assertEqual((result["fetchCount"], result["renderCount"], result["merged"]), (1, 0, []))
        self.assertFalse(result["buttonDisabled"])
        self.assertFalse(result["inFlight"])

    def test_success_moves_to_tasks_only_after_backend_parent_and_posts_once(self):
        result = self.run_case("""
const pending = context.handleModalDelegate();
await context.handleModalDelegate();
const before = snapshot();
respond(201, {ok: true, parent: {id: 'mission-parent', result: 'Backend queued two children'}, subtasks: [{id:'child-1'}, {id:'child-2'}]});
await pending; process.stdout.write(JSON.stringify({before, after: snapshot(), path: requests[0].path, body: JSON.parse(requests[0].options.body)}));
""")
        self.assertEqual(result["before"]["tab"], "chat")
        self.assertTrue(result["before"]["buttonDisabled"])
        self.assertEqual(result["after"]["tab"], "tasks")
        self.assertEqual(result["after"]["tone"], "ready")
        self.assertEqual(result["after"]["merged"], ["mission-parent", "child-1", "child-2"])
        self.assertEqual(result["after"]["fetchCount"], 1)
        self.assertEqual(result["path"], "/api/manager/delegate")
        self.assertEqual(set(result["body"]), {"agentId", "goal", "idempotencyKey"})

    def test_nonthrowing_rejection_does_not_apply_success_side_effects(self):
        result = self.run_case("""
const pending = context.handleModalDelegate();
respond(200, {ok: false, kind: 'scope_invalid', message: 'Exact selected scope is unavailable'});
await pending; process.stdout.write(JSON.stringify(snapshot()));
""")
        self.assertEqual(result["visible"], "Exact selected scope is unavailable")
        self.assertEqual((result["tab"], result["renderCount"], result["merged"]), ("chat", 0, []))

    def test_late_failure_does_not_overwrite_another_agents_status_or_switch_tab(self):
        result = self.run_case("""
const pending = context.handleModalDelegate();
state.modal.id = 'risk_guard'; state.modal.activeTab = 'chat';
context.setAgentChatStatus('risk_guard', 'Risk Guard current message', 'ready');
respond(422, {message: 'Old Manager rejection'});
await pending; process.stdout.write(JSON.stringify(snapshot()));
""")
        self.assertEqual(result["visible"], "Risk Guard current message")
        self.assertEqual(result["agentChat"]["agentId"], "risk_guard")
        self.assertEqual((result["tab"], result["tone"], result["renderCount"]), ("chat", "ready", 0))

    def test_error_is_text_only_and_keeps_existing_secret_redaction(self):
        result = self.run_case("""
const pending = context.handleModalDelegate();
respond(422, {message: '<img src=x onerror=alert(1)> api_key=never-show-this'});
await pending; process.stdout.write(JSON.stringify(snapshot()));
""")
        self.assertIn("<img src=x onerror=alert(1)>", result["visible"])
        self.assertNotIn("never-show-this", result["visible"])
        self.assertEqual(result["tone"], "error")

    def test_local_secret_guard_and_missing_goal_never_post_or_navigate(self):
        result = self.run_case("""
secretBlocked = true; await context.handleModalDelegate(); const secret = snapshot();
input.value = ''; await context.handleModalDelegate();
process.stdout.write(JSON.stringify({secret, empty: snapshot(), focused: input.focused}));
""")
        self.assertIn("Risk Guard", result["secret"]["visible"])
        self.assertEqual(result["secret"]["fetchCount"], 0)
        self.assertEqual(result["empty"]["fetchCount"], 0)
        self.assertEqual(result["empty"]["tab"], "chat")
        self.assertTrue(result["focused"])

    def test_modal_button_is_bound_to_guarded_handler(self):
        self.assertIn('els.modalDelegateButton?.addEventListener("click", handleModalDelegate);', self.main)


if __name__ == "__main__":
    unittest.main()
