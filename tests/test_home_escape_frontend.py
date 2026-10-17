"""Exercise shipped home navigation handlers without a browser or runtime requests."""

import json
import shutil
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class HomeEscapeFrontendTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        source = (ROOT / "frontend/src/app/main.js").read_text(encoding="utf-8")
        start = source.rindex('document.addEventListener("keydown", (event) => {')
        end = source.index('els.stage.addEventListener("click"', start)
        cls.handler_source = source[start:end]
        trap_start = source.index("function trapGameModalFocus(event) {")
        trap_end = source.index("\nfunction openGameModal(", trap_start)
        cls.trap_source = source[trap_start:trap_end]
        toggle_start = source.index('els.homeStatusMenu?.addEventListener("toggle", () => {')
        toggle_end = source.index('\ndocument.addEventListener("click",', toggle_start)
        cls.toggle_source = source[toggle_start:toggle_end]
        bundled = Path.home() / ".cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe"
        cls.node = shutil.which("node") or (str(bundled) if bundled.exists() else None)
        if not cls.node:
            raise RuntimeError("Node.js is required for Escape navigation tests")

    def dispatch(
        self, *, panels=None, modal_open=True, key="Escape", sheet_open=False,
        drawer_open=False, through_game_modal=False,
    ):
        settings = json.dumps({
            "panels": panels or {},
            "modalOpen": modal_open,
            "key": key,
            "sheetOpen": sheet_open,
            "drawerOpen": drawer_open,
            "throughGameModal": through_game_modal,
        })
        script = """
const vm = require('node:vm');
const settings = SETTINGS;
const calls = [];
let handler;
let drawerOpen = settings.drawerOpen;
let propagationStopped = false;
const state = {modal: {open: settings.modalOpen}};
const els = {
  globalMetatraderPanel: {hidden: true},
  agentCollabPanel: null,
  operatorModePanel: {hidden: true},
  globalMetatraderButton: {focus: () => calls.push(['focus', 'metatrader'])},
  agentCollabButton: {focus: () => calls.push(['focus', 'collaboration'])},
  operatorModeButton: {focus: () => calls.push(['focus', 'operator'])},
  newsEventDialog: {open: false},
  dashboardResultDialog: {open: false},
  taskDetailDialog: {open: false},
  gameModal: {classList: {contains: () => true}},
  homeStatusMenu: {
    get open() { return drawerOpen; },
    set open(value) { drawerOpen = value; calls.push(['drawer', value]); },
  },
  homeStatusToggle: {focus: () => calls.push(['focus', 'status'])},
  ...settings.panels,
};
const context = {
  els,
  state,
  document: {addEventListener(type, callback) {
    if (type !== 'keydown' || handler) throw new Error('Unexpected listener');
    handler = callback;
  }},
  researchSheetHubPopoverIsOpen: () => settings.sheetOpen,
  closeResearchSheetHubPopover: () => calls.push(['close', 'sheet']),
  closeFxNewsEventDetail: () => calls.push(['close', 'news']),
  setGlobalMetatraderPanelOpen: (open) => calls.push(['metatrader', open]),
  setAgentCollaborationPanelOpen: (open) => calls.push(['collaboration', open]),
  setOperatorModePanelOpen: (open) => calls.push(['operator', open]),
  closeDashboardResultDetail: () => calls.push(['close', 'result']),
  closeTaskDetail: () => calls.push(['close', 'task']),
  closeGameModal: () => {state.modal.open = false; calls.push(['close', 'game']);},
};
vm.runInNewContext(TRAP, context, {timeout: 1000});
vm.runInNewContext(HANDLER, context, {timeout: 1000});
if (!handler) throw new Error('Escape listener was not registered');
const event = {
  key: settings.key,
  defaultPrevented: false,
  preventDefault() {this.defaultPrevented = true; calls.push(['preventDefault']);},
  stopPropagation: () => {propagationStopped = true; calls.push(['stopPropagation']);},
};
if (settings.throughGameModal) context.trapGameModalFocus(event);
if (!propagationStopped) handler(event);
process.stdout.write(JSON.stringify(calls));
""".replace("SETTINGS", settings).replace("TRAP", json.dumps(self.trap_source)).replace("HANDLER", json.dumps(self.handler_source))
        result = subprocess.run(
            [self.node, "-e", script], cwd=ROOT, capture_output=True,
            text=True, encoding="utf-8", timeout=10,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def test_absent_collaboration_panel_does_not_intercept_operator_escape(self):
        calls = self.dispatch(panels={"operatorModePanel": {"hidden": False}})
        self.assertEqual(calls, [["operator", False], ["focus", "operator"]])

    def test_absent_optional_panels_do_not_intercept_game_modal_escape(self):
        for panels in (
            {},
            {"globalMetatraderPanel": None},
            {"operatorModePanel": None},
            {"globalMetatraderPanel": None, "operatorModePanel": None},
        ):
            with self.subTest(panels=panels):
                self.assertEqual(self.dispatch(panels=panels), [["close", "game"]])

    def test_visible_collaboration_panel_closes_before_operator_and_game_modal(self):
        calls = self.dispatch(panels={
            "agentCollabPanel": {"hidden": False},
            "operatorModePanel": {"hidden": False},
        })
        self.assertEqual(calls, [["collaboration", False], ["focus", "collaboration"]])

    def test_non_escape_key_does_not_close_or_focus_any_surface(self):
        calls = self.dispatch(
            key="Enter", sheet_open=True, drawer_open=True,
            panels={
                "globalMetatraderPanel": {"hidden": False},
                "agentCollabPanel": {"hidden": False},
                "operatorModePanel": {"hidden": False},
            },
        )
        self.assertEqual(calls, [])

    def test_escape_closes_status_drawer_and_returns_to_its_toggle(self):
        calls = self.dispatch(modal_open=False, drawer_open=True)
        self.assertEqual(calls, [
            ["preventDefault"], ["drawer", False], ["focus", "status"],
        ])

    def test_game_modal_escape_does_not_also_close_the_status_drawer(self):
        calls = self.dispatch(drawer_open=True, through_game_modal=True)
        self.assertIn(["close", "game"], calls)
        self.assertNotIn(["drawer", False], calls)
        self.assertNotIn(["focus", "status"], calls)

    def test_task_detail_escape_leaves_the_underlying_status_drawer_open(self):
        calls = self.dispatch(
            modal_open=False, drawer_open=True,
            panels={"taskDetailDialog": {"open": True}},
        )
        self.assertEqual(calls, [
            ["preventDefault"], ["stopPropagation"], ["close", "task"],
        ])

    def toggle_status(self, **sheet_state):
        settings = {
            "sheetOpen": True, "preview": None, "inFlight": False,
            "authBusy": False, "queryBusy": False, **sheet_state,
        }
        script = """
const vm = require('node:vm');
const settings = SETTINGS;
const calls = [];
let handler;
const menu = {open: true, addEventListener(type, callback) {
  if (type !== 'toggle' || handler) throw new Error('Unexpected listener');
  handler = callback;
}};
const hub = {preview: settings.preview, inFlight: settings.inFlight};
const context = {
  els: {homeStatusMenu: menu},
  state: {researchSheetHub: hub},
  researchSheetHubPopoverIsOpen: () => settings.sheetOpen,
  researchSheetGoogleAuthIsBusy: () => settings.authBusy,
  researchSheetHubQueryIsBusy: () => settings.queryBusy,
  closeResearchSheetHubPopover: (options) => calls.push(['sheet', options]),
  setGlobalMetatraderPanelOpen: (open) => calls.push(['metatrader', open]),
  setOperatorModePanelOpen: (open) => calls.push(['operator', open]),
};
vm.runInNewContext(HANDLER, context, {timeout: 1000});
if (!handler) throw new Error('Status toggle listener was not registered');
handler();
process.stdout.write(JSON.stringify({open: menu.open, hub, calls}));
""".replace("SETTINGS", json.dumps(settings)).replace("HANDLER", json.dumps(self.toggle_source))
        result = subprocess.run(
            [self.node, "-e", script], cwd=ROOT, capture_output=True,
            text=True, encoding="utf-8", timeout=10,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def test_status_drawer_preserves_unfinished_sheet_inspection_and_requests(self):
        for sheet_state in (
            {"preview": {"candidate": "pending-inspection"}},
            {"inFlight": True}, {"authBusy": True}, {"queryBusy": True},
        ):
            with self.subTest(sheet_state=sheet_state):
                result = self.toggle_status(**sheet_state)
                self.assertFalse(result["open"])
                self.assertEqual(result["calls"], [])
                self.assertEqual(result["hub"]["preview"], sheet_state.get("preview"))

    def test_status_drawer_closes_idle_sheet_without_discarding_or_stealing_focus(self):
        result = self.toggle_status()
        self.assertTrue(result["open"])
        self.assertEqual(result["calls"], [
            ["sheet", {"discardPreview": False, "focusToggle": False}],
            ["metatrader", False], ["operator", False],
        ])


if __name__ == "__main__":
    unittest.main()
