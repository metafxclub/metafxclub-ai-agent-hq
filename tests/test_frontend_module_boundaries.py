"""Exercise shipped module imports without a browser, bridge, or real requests."""

import json
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "frontend" / "src" / "app"
FEATURE_MODELS = {
    "research-sheet": APP.parent / "features" / "research" / "research-sheet.js",
    "meeting-session": APP.parent / "features" / "chat" / "meeting-session.js",
    "codex-rate": APP.parent / "features" / "quota" / "codex-rate.js",
}


class FrontendModuleBoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        bundled = Path.home() / ".cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe"
        cls.node = shutil.which("node") or (str(bundled) if bundled.exists() else None)
        if not cls.node:
            raise RuntimeError("Node.js is required for frontend module boundary tests")

    def run_node(self, script):
        result = subprocess.run(
            [self.node, "--input-type=module", "-e", script],
            cwd=ROOT, capture_output=True, text=True, encoding="utf-8", timeout=20,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def test_real_app_import_registers_public_entrypoints_before_contract_reads(self):
        # Hold initial contract reads pending: no polling, runtime actions, or network.
        result = self.run_node("""
const events = [];
const reads = [];
const nodes = new Map();
const node = (id) => {
  if (!nodes.has(id)) nodes.set(id, {
    dataset: {}, style: {}, value: '', hidden: true,
    addEventListener(type) { events.push([id, type]); },
    querySelectorAll() { return []; },
  });
  return nodes.get(id);
};
globalThis.document = {
  getElementById: node,
  querySelectorAll() { return []; },
  addEventListener(type) { events.push(['document', type]); },
};
globalThis.window = {
  addEventListener(type) { events.push(['window', type]); },
  setTimeout() { return 1; }, clearTimeout() {},
};
globalThis.fetch = (path, options = {}) => {
  reads.push({path, method: options.method || 'GET'});
  return new Promise(() => {});
};
await import(MAIN_URI);
const entrypoints = ['selectAgent', 'moveAgentTo', 'assignTask', 'callMeeting',
  'agentTalk', 'openPropReport', 'runBridgeTask', 'loadMemoryStatus'];
console.log(JSON.stringify({
  entrypoints: entrypoints.filter(name => typeof window[name] === 'function'),
  reads, eventCount: events.length,
  leakedModels: Object.keys(window).filter(name => /^(create|normalize)/.test(name)),
}));
""".replace("MAIN_URI", json.dumps((APP / "main.js").as_uri())))
        self.assertEqual(len(result["entrypoints"]), 8)
        self.assertGreater(result["eventCount"], 20)
        self.assertEqual(result["leakedModels"], [])
        self.assertEqual([row["method"] for row in result["reads"]], ["GET", "GET"])
        self.assertEqual(
            [row["path"].split("?")[0] for row in result["reads"]],
            ["/contracts/rooms/command-room.json", "/contracts/agents/agents.json"],
        )

    def test_missing_model_rejects_app_graph_before_any_dom_or_network_access(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            (target / "app").mkdir()
            temporary_main = target / "app" / "main.js"
            shutil.copy2(APP / "main.js", temporary_main)
            for name, model_path in FEATURE_MODELS.items():
                if name != "meeting-session":
                    destination = target / model_path.relative_to(APP.parent)
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(model_path, destination)
            result = self.run_node("""
let reads = 0;
Object.defineProperty(globalThis, 'document', {get() { reads += 1; throw Error('DOM accessed'); }});
globalThis.fetch = () => { reads += 1; throw Error('Network accessed'); };
let failure = '';
try { await import(MAIN_URI); } catch (error) { failure = error.code; }
console.log(JSON.stringify({failure, reads}));
""".replace("MAIN_URI", json.dumps(temporary_main.as_uri())))
        self.assertEqual(result, {"failure": "ERR_MODULE_NOT_FOUND", "reads": 0})

    def test_boot_loader_reports_module_load_and_execution_failures(self):
        html = (ROOT / "frontend" / "index.html").read_text(encoding="utf-8")
        boot = re.findall(r"<script>([\s\S]*?)</script>", html)[-1]
        result = self.run_node("""
import vm from 'node:vm';
const elements = new Map();
const handlers = {};
let script;
const element = id => {
  if (!elements.has(id)) elements.set(id, {dataset: {}, addEventListener() {}});
  return elements.get(id);
};
const context = {
  document: {getElementById: element, querySelectorAll: () => [],
    createElement: () => ({dataset: {}}), body: {appendChild(value) { script = value; }}},
  window: {addEventListener(type, handler) { handlers[type] = handler; },
    clearTimeout() {}, setTimeout() { return 1; }},
};
vm.runInNewContext(BOOT_SOURCE, context);
script.onerror();
const loadFailure = elements.get('bootDiagnostic').dataset.level;
handlers.error({filename: 'http://127.0.0.1/frontend/src/features/chat/meeting-session.js', message: 'module failed'});
const executionFailure = elements.get('bootDiagnostic').dataset.level;
console.log(JSON.stringify({type: script.type, loadFailure, executionFailure,
  resource: elements.get('bootDiagnosticResource').textContent}));
""".replace("BOOT_SOURCE", json.dumps(boot)))
        self.assertEqual(result["type"], "module")
        self.assertEqual(result["loadFailure"], "error")
        self.assertEqual(result["executionFailure"], "error")
        self.assertIn("features/chat/meeting-session.js", result["resource"])

    def test_research_model_keeps_identity_oauth_and_verified_probe_guards(self):
        result = self.run_node("""
const {createResearchSheetModel} = await import(MODEL_URI);
const model = createResearchSheetModel({
  safeDashboardDisplayText: (value, fallback = '') => String(value ?? fallback),
  consumers: [{propId: 'research', tabKey: 'research', requiresWrite: true}],
  linkedSystems: [], queryMaxMatches: 2, queryMaxColumnsPerTab: 2,
});
const sheetId = '1AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA';
const hub = model.normalizeResearchSheetHub({researchSheet: {
  configured: true, sheetId, rawSheetIdExposed: false,
  consumers: [{propId: 'research', readReady: 'true', writeReady: 1}],
}});
const probe = {sheetId, verificationToken: 'a'.repeat(64), readyForConfirmation: true,
  verifiedConsumerCount: 1, consumers: [{propId: 'research', readReady: true, probeEvidence: {confirmed: false}}]};
const unverified = model.normalizeResearchSheetInspection({verificationPreview: probe});
probe.consumers[0].probeEvidence.confirmed = true;
const verified = model.normalizeResearchSheetInspection({verificationPreview: probe});
const query = model.normalizeResearchSheetQueryResult({matches: [{value: 'a'}, {value: 'b'}, {value: 'c'}]});
console.log(JSON.stringify({
  hiddenId: hub.sheetId, credentialsAccepted: hub.credentialsAcceptedByFrontend,
  readReady: hub.consumers[0].readReady, writeReady: hub.consumers[0].writeReady,
  unverified: unverified.readyForConfirmation, verified: verified.readyForConfirmation,
  wrongHost: model.normalizeResearchSheetAuthorizationUrl('https://accounts.google.com.evil.example/auth'),
  wrongProtocol: model.normalizeResearchSheetAuthorizationUrl('http://accounts.google.com/auth'),
  credentialsInUrl: model.normalizeResearchSheetAuthorizationUrl('https://user:password@accounts.google.com/auth'),
  validUrl: model.normalizeResearchSheetAuthorizationUrl('https://accounts.google.com/o/oauth2/v2/auth'),
  matches: query.matches.length,
}));
""".replace("MODEL_URI", json.dumps(FEATURE_MODELS["research-sheet"].as_uri())))
        self.assertEqual(result["hiddenId"], "")
        for field in ("credentialsAccepted", "readReady", "writeReady", "unverified"):
            self.assertFalse(result[field], field)
        self.assertTrue(result["verified"])
        for field in ("wrongHost", "wrongProtocol", "credentialsInUrl"):
            self.assertEqual(result[field], "", field)
        self.assertTrue(result["validUrl"].startswith("https://accounts.google.com/"))
        self.assertEqual(result["matches"], 2)

    def test_meeting_model_reads_current_roster_and_keeps_context_fail_closed(self):
        result = self.run_node("""
const {createMeetingSessionModel} = await import(MODEL_URI);
let roster = {manager: {name: 'Before', role: 'Manager'}};
const model = createMeetingSessionModel({getOfficeAgent: id => roster[id]});
const first = model.normalizeMeetingParticipant('manager').name;
roster = {manager: {name: 'After', role: 'Manager'}};
const second = model.normalizeMeetingParticipant('manager').name;
const incomplete = model.normalizeMeetingSession({id: 'meeting', agenda: 'Task', developmentGoal: 'Goal', aiTurnsPerRound: '2'});
const complete = model.normalizeMeetingSession({id: 'meeting', agenda: 'Task', developmentGoal: 'Goal', aiTurnsPerRound: 2});
console.log(JSON.stringify({first, second, incomplete: incomplete.visibleMeetingContextComplete,
  complete: complete.visibleMeetingContextComplete, proposal: complete.proposal.visibleConsentPacketComplete}));
""".replace("MODEL_URI", json.dumps(FEATURE_MODELS["meeting-session"].as_uri())))
        self.assertEqual(result, {"first": "Before", "second": "After", "incomplete": False, "complete": True, "proposal": False})

    def test_room_props_characters_and_fallback_resolve_to_existing_assets(self):
        source = (APP / "main.js").read_text(encoding="utf-8")

        def function_source(name):
            start = source.index(f"function {name}(")
            end = source.index("\n}\n", start) + 2
            return source[start:end]

        def asset_references(value):
            if isinstance(value, dict):
                for child in value.values():
                    yield from asset_references(child)
            elif isinstance(value, list):
                for child in value:
                    yield from asset_references(child)
            elif isinstance(value, str) and value.split("?", 1)[0].endswith(".png"):
                yield value

        room = json.loads((ROOT / "contracts/rooms/command-room.json").read_text(encoding="utf-8"))
        agents = json.loads((ROOT / "contracts/agents/agents.json").read_text(encoding="utf-8"))
        references = list(asset_references(room)) + list(asset_references(agents))
        references.append(room["room"]["propSet"])
        # Keep legacy room/overlay references and the new canonical shortcut usable.
        references.extend([
            "./assets/exact-scene-layers-v002/metafx-aihq-exact-layer-codex_mcp_portal-v002.png",
            "./assets/images/characters/male-roster-set-a-core-command-operators-v001/characters/01-ceo-male-static-v001.png",
        ])
        asset_root = re.search(r'^const PROJECT_ASSET_ROOT = .+;$', source, re.MULTILINE)
        self.assertIsNotNone(asset_root)
        result = self.run_node("\n".join([
            asset_root.group(0),
            function_source("resolveProjectAssetPath"),
            function_source("createFallbackRoomData"),
            f"const references = {json.dumps(references)};",
            "references.push(createFallbackRoomData().room.image);",
            "console.log(JSON.stringify(references.map(resolveProjectAssetPath)));",
        ]))
        self.assertGreaterEqual(len(result), 25)
        for url in result:
            with self.subTest(url=url):
                relative = url.removeprefix("./").split("?", 1)[0]
                self.assertTrue(relative.startswith("frontend/public/assets/images/"))
                self.assertTrue((ROOT / relative).is_file(), relative)


if __name__ == "__main__":
    unittest.main()
