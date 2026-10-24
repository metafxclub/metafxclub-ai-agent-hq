import json
import re
import shutil
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class EaFactoryFrontendTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.main = (ROOT / "frontend" / "src" / "app" / "main.js").read_text(encoding="utf-8")
        cls.styles = (ROOT / "frontend" / "src" / "styles" / "main.css").read_text(encoding="utf-8")

    def block(self, start, end):
        start_index = self.main.index(start)
        return self.main[start_index:self.main.index(end, start_index)]

    def node_binary(self):
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

    def test_factory_has_three_operator_pages_and_keeps_seven_internal_stages(self):
        constants = self.block("const EA_FACTORY_STAGE_IDS", "const TRADING_RESEARCH_MAX_OHLC_ROWS")
        stage_start = constants.index("const EA_FACTORY_STAGE_IDS")
        stage_end = constants.index("]);", stage_start)
        ui_ids = re.findall(r'^\s+"([a-z_]+)",?$', constants[stage_start:stage_end], re.M)
        self.assertEqual(
            ui_ids,
            [
                "source",
                "spec",
                "generate",
                "review",
                "compile_validate",
                "backtest_recheck",
                "artifacts_report",
            ],
        )
        for ui_id, backend_id in {
            "spec": "strategy_spec",
            "generate": "generate_source",
            "review": "source_review",
            "compile_validate": "compile_validate",
            "backtest_recheck": "backtest_recheck",
            "artifacts_report": "final_report",
        }.items():
            self.assertIn(f'{ui_id}: "{backend_id}"', constants)
        page_line = re.search(r"const EA_FACTORY_PAGE_IDS = Object\.freeze\(\[([^\]]+)\]\);", constants)
        self.assertIsNotNone(page_line)
        self.assertEqual(re.findall(r'"([a-z_]+)"', page_line.group(1)), ["source", "progress", "result"])
        for label in (
            "1 เลือกระบบและเริ่มเขียน",
            "2 สถานะการทำงาน",
            "3 ตรวจโค้ดและเสร็จสิ้น",
        ):
            self.assertIn(label, constants)
        fallback = self.block("const WORKFLOW_DASHBOARD_FALLBACKS", "  right_tool_console: {")
        self.assertIn("tabs: EA_FACTORY_PAGE_IDS.map", fallback)
        self.assertNotIn("tabs: EA_FACTORY_STAGE_IDS.map", fallback)
        dashboard = self.block("function normalizeWorkflowDashboard", "function getWorkflowSelectedTab")
        self.assertIn("presentationTabs = EA_FACTORY_PAGE_IDS.map", dashboard)
        self.assertNotIn("presentationTabs = EA_FACTORY_STAGE_IDS.map", dashboard)

    def test_three_operator_pages_are_navigable_and_route_to_the_correct_content(self):
        selected = self.block("function getWorkflowSelectedTab", "function renderWorkflowTabs")
        self.assertIn("eaFactoryPreferredPageId", selected)
        tabs = self.block("function renderWorkflowTabs", "function workflowAvailabilityCopy")
        self.assertIn('dataset.eaFactoryPages = factoryPages ? "true" : "false"', tabs)
        self.assertIn("const factoryLocked = false", tabs)
        self.assertIn("button.disabled = Boolean(factoryLocked)", tabs)
        panel = self.block("function renderEaFactoryPanel", "function validateEaFactoryBusyModel")
        self.assertIn('tabId === "source"', panel)
        self.assertIn('tabId === "progress"', panel)
        self.assertIn('tabId === "result"', panel)
        self.assertNotIn('tabId === "generate"', panel)
        page_status = self.block("function eaFactoryPageStatus", "function eaFactoryPreferredPageId")
        self.assertIn("if (!domain.authoritative)", page_status)
        self.assertIn('pageId === "source" ? "blocked" : "unknown"', page_status)
        self.assertIn('["progress", "result"].includes(pageId) && !domain.activeBuild', page_status)
        self.assertLess(
            page_status.index('["progress", "result"].includes(pageId) && !domain.activeBuild'),
            page_status.index('if (pageId === "result")'),
        )
        preferred = self.block("function eaFactoryPreferredPageId", "function createEaFactoryPageHeader")
        self.assertIn('if (domain.backendBusy) return "progress"', preferred)
        self.assertIn("eaFactoryCertifiedDeliveryCompleted(domain)", preferred)
        self.assertIn("eaFactoryRunNeedsProgressPage(domain)", preferred)
        self.assertIn('finalStatus === "completed"', preferred)
        self.assertIn('return "source"', preferred)
        self.assertIn('.workflow-tabs[data-ea-factory-pages="true"]', self.styles)
        self.assertIn("grid-template-columns: repeat(3, minmax(0, 1fr))", self.styles)
        tab_switch = self.block("function setWorkflowDashboardTab", "function workflowActionFormPayload")
        self.assertIn(
            "[EA_OPTIMIZATION_LAB_PROP_ID, EA_FACTORY_PROP_ID].includes(propId)",
            tab_switch,
        )
        self.assertIn("scrollArea.scrollTop = 0", tab_switch)

    def test_factory_pages_share_visible_settings_rail_without_duplicate_workflow_controls(self):
        tabs = self.block("function renderWorkflowTabs", "function workflowAvailabilityCopy")
        self.assertIn("els.workflowDashboardTabs.hidden = false", tabs)
        self.assertNotIn('selectedTab?.id === "source"', tabs)
        rail = self.block("function renderWorkflowSettingsRail", "function getWorkflowHandoffReports")
        self.assertIn("els.workflowSettingsRail.hidden = false", rail)
        self.assertNotIn("els.workflowSettingsRail.hidden = true", rail)
        self.assertIn("createEaFactoryRailSettings()", rail)
        self.assertIn("createEaFactoryRailTaskStatus(dashboard?.domainData?.eaFactory || {})", rail)
        self.assertNotIn("renderEaFactoryTerminalPicker", rail)
        self.assertNotIn("factorySelectedPageId", rail)
        self.assertNotIn("createWorkflowUseGuideCard", rail)
        self.assertNotIn('.workflow-settings-rail[data-ea-factory-intake="true"]', self.styles)

    def test_factory_sidebar_is_read_only_and_navigable_on_each_page(self):
        script = "\n".join([
            "const assert = require('node:assert/strict');",
            "class Element {",
            "  constructor(tag) { this.tagName=tag; this.children=[]; this.dataset={}; this.listeners={}; this.textContent=''; }",
            "  append(...nodes) { this.children.push(...nodes); }",
            "  appendChild(node) { this.children.push(node); return node; }",
            "  addEventListener(type, callback) { this.listeners[type]=callback; }",
            "  set innerHTML(value) { assert.equal(value,''); this.children=[]; }",
            "}",
            "const document = {createElement: tag => new Element(tag)};",
            "const EA_FACTORY_PROP_ID='right_server_racks', FX_NEWS_BIAS_PROP_ID='news', INDICATOR_SCOUT_PROP_ID='scout';",
            "const TRADING_RESEARCH_LAB_PROP_ID='left_server_racks', HQ_CONNECTION_HUB_PROP_ID='hub';",
            "const RESEARCH_SHEET_CONSUMER_PROP_IDS=new Set();",
            "const els={workflowSettingsRail:new Element('section'), workflowSettingsRailContent:new Element('div'), workflowSettingsRailTitle:new Element('strong')};",
            "const state={modal:{eaFactory:{}}};",
            "const navigations=[];",
            "const setWorkflowDashboardTab=(...args)=>navigations.push(args);",
            "const workflowRailActions=()=>[];",
            "const createResearchSheetConsumerCard=()=>new Element('section');",
            "const createEaFactoryRailTaskStatus=()=>new Element('section');",
            "const descendants=node=>[node,...node.children.flatMap(descendants)];",
            "const fetch=()=>{throw new Error('Sidebar must not make a request');};",
            self.block("function normalizeEaFactoryPlatform", "const EA_FACTORY_READINESS_ISSUE_LABELS"),
            self.block("function eaFactoryPlatformLabel", "function eaFactorySourceIsBuildSelectable"),
            self.block("function createWorkflowConnectionLink", "function createEaFactoryRailTaskStatus"),
            self.block("function renderWorkflowSettingsRail", "function getWorkflowHandoffReports"),
            "const cases=[",
            "  [{},['ยังไม่เลือก','ยังไม่เลือก','ยังไม่เลือก']],",
            "  [{selectedPlatform:'mt5',selectedArtifactKind:'custom_indicator',sourceMode:'google_sheet'},['MT5 / MQL5','Custom Indicator','Google Sheet']],",
            "  [{selectedPlatform:'tradingview',selectedArtifactKind:'expert_advisor',sourceMode:'custom'},['TradingView / Pine Script','Pine Strategy','เงื่อนไขของคุณ']],",
            "  [{selectedPlatform:'unknown',selectedArtifactKind:'unknown',sourceMode:'unknown'},['ยังไม่เลือก','ยังไม่เลือก','ยังไม่เลือก']],",
            "];",
            "let checked=0;",
            "for (const page of ['source','progress','result']) {",
            "  for (const [selection,expected] of cases) {",
            "    state.modal.eaFactory=Object.freeze({...selection,selectedPageId:page});",
            "    const before=JSON.stringify(state);",
            "    renderWorkflowSettingsRail({id:EA_FACTORY_PROP_ID},{domainData:{eaFactory:{}}},{id:'ea-factory'});",
            "    assert.equal(els.workflowSettingsRail.hidden,false);",
            "    assert.notEqual(els.workflowSettingsRail.dataset.eaFactoryIntake,'true');",
            "    const nodes=descendants(els.workflowSettingsRailContent);",
            "    assert.deepEqual(nodes.filter(node=>node.tagName==='dd').map(node=>node.textContent),expected);",
            "    assert.equal(nodes.filter(node=>['input','select','textarea','form','ol'].includes(node.tagName)).length,0);",
            "    const links=nodes.filter(node=>node.dataset.openConnectionHub==='true');",
            "    assert.equal(links.length,1); assert.equal(links[0].type,'button');",
            "    const sourceButton=nodes.find(node=>node.textContent==='เปิดการตั้งค่างาน');",
            "    assert.equal(sourceButton.type,'button'); sourceButton.listeners.click();",
            "    assert.deepEqual(navigations.at(-1),[EA_FACTORY_PROP_ID,'source',{focus:true}]);",
            "    assert.equal(JSON.stringify(state),before); checked++;",
            "  }",
            "}",
            "process.stdout.write(JSON.stringify({checked,navigations:navigations.length}));",
        ])
        completed = subprocess.run(
            [self.node_binary(), "-e", script],
            cwd=ROOT,
            capture_output=True,
            check=True,
            text=True,
            encoding="utf-8",
        )
        self.assertEqual(json.loads(completed.stdout), {"checked": 12, "navigations": 12})

    def test_phase_gate_progress_and_backend_cancel_are_visible_without_model_polling(self):
        progress = self.block("function eaFactoryPhaseGateProgress", "function eaFactoryOneClickStepCopy")
        self.assertIn("const phaseIds = EA_FACTORY_VISUAL_STAGE_IDS", progress)
        self.assertIn("progressPercent", progress)
        self.assertNotIn("optimizationProgressPercent", progress)
        self.assertNotIn('"optimization"', progress)
        self.assertIn("progress.shouldPoll", progress)
        self.assertIn("EA_FACTORY_ACTIVE_POLL_MS", progress)
        self.assertIn("loadEaFactoryReadModel({ forceFresh: true })", progress)
        self.assertIn("ไม่เรียก AI และไม่หักโควตาโมเดล", progress)
        self.assertIn('"aria-valuetext"', progress)
        self.assertIn("canAbortSubmission", progress)
        self.assertIn("cancelEaFactorySubmittingRequest", progress)
        cancel = self.block("async function cancelEaFactoryOneClick", "async function createAndRunEaFactoryBuild")
        self.assertIn("run.canCancel === true", cancel)
        self.assertIn("{ runId, idempotencyKey }", cancel)
        self.assertIn("/cancel`", cancel)
        self.assertNotIn("AbortController", cancel)
        submitting = self.block("function cancelEaFactorySubmittingRequest", "async function cancelEaFactoryOneClick")
        self.assertIn("controller.abort(error)", submitting)
        self.assertIn('error.kind = "ea_factory_operator_cancelled_request"', submitting)
        request_runner = self.block("async function runEaFactoryRequest", "async function syncEaFactoryGoogleSheet")
        self.assertIn("eaFactoryActiveActionAbortController = actionController", request_runner)
        self.assertIn("loadEaFactoryReadModel({ forceFresh: true })", request_runner)
        self.assertIn("cancelEaFactoryOneClick(buildId, run)", request_runner)
        self.assertIn("operator_cancelled_request", request_runner)

    def test_preferred_page_keeps_exact_recovery_and_final_report_completion(self):
        helper = self.block("function eaFactoryCertifiedDeliveryCompleted", "function createEaFactoryPageHeader")
        script = "\n".join([
            helper,
            "const page = ({status='idle',busy=null,finalStatus='locked',platform='mt5',runId='run-1',canResume=false}) => eaFactoryPreferredPageId({backendBusy:busy,activeBuild:{platform},oneClick:{run:{status,runId,canResume}},stages:[{id:'artifacts_report',status:finalStatus}]});",
            "process.stdout.write(JSON.stringify({",
            "  busy:page({status:'running',busy:{buildId:'live'}}),",
            "  failed:page({status:'failed'}), awaiting:page({status:'awaiting_visible_terminal',canResume:true}),",
            "  queued:page({status:'queued'}), running:page({status:'running'}),",
            "  completed:page({status:'completed',finalStatus:'completed'}),",
            "  manualCompleted:page({status:'idle',runId:'',platform:'mt5',finalStatus:'completed'}),",
            "  idle:page({status:'idle',runId:'',platform:'mt5',finalStatus:'locked'}),",
            "}));",
        ])
        completed = subprocess.run(
            [self.node_binary(), "-e", script],
            cwd=ROOT,
            capture_output=True,
            check=True,
            text=True,
            encoding="utf-8",
        )
        self.assertEqual(
            json.loads(completed.stdout),
            {
                "busy": "progress",
                "failed": "progress",
                "awaiting": "progress",
                "queued": "progress",
                "running": "progress",
                "completed": "result",
                "manualCompleted": "result",
                "idle": "source",
            },
        )

    def test_one_click_success_ends_at_final_report_for_mt4_and_mt5(self):
        helpers = self.block("function eaFactoryCertifiedDeliveryCompleted", "function eaFactoryPageStatus")
        script = "\n".join([
            helpers,
            "const domain = (platform,status,runId='run-1',finalStatus='completed') => ({activeBuild:{platform},oneClick:{run:{runId,status}},stages:[{id:'artifacts_report',status:finalStatus}]});",
            "process.stdout.write(JSON.stringify({",
            "  runningMt5:eaFactoryCertifiedDeliveryCompleted(domain('mt5','running')),",
            "  completedMt5:eaFactoryCertifiedDeliveryCompleted(domain('mt5','completed')),",
            "  completedMt4:eaFactoryCertifiedDeliveryCompleted(domain('mt4','completed')),",
            "  manualFinalReport:eaFactoryCertifiedDeliveryCompleted(domain('mt5','idle','','completed')),",
            "  manualLocked:eaFactoryCertifiedDeliveryCompleted(domain('mt5','idle','','locked')),",
            "}));",
        ])
        completed = subprocess.run(
            [self.node_binary(), "-e", script],
            cwd=ROOT,
            capture_output=True,
            check=True,
            text=True,
            encoding="utf-8",
        )
        self.assertEqual(
            json.loads(completed.stdout),
            {
                "runningMt5": False,
                "completedMt5": True,
                "completedMt4": True,
                "manualFinalReport": True,
                "manualLocked": False,
            },
        )
        self.assertNotIn("optimization", helpers.lower())

    def test_persisted_page_one_cannot_hide_exact_resumable_build_after_reload(self):
        helpers = self.block("function eaFactoryCertifiedDeliveryCompleted", "function createEaFactoryPageHeader")
        selection = self.block("function getWorkflowSelectedTab", "function renderWorkflowTabs")
        script = "\n".join([
            "const EA_FACTORY_PROP_ID='right_server_racks';",
            "const state={modal:{workflowTabs:{right_server_racks:'source'}}};",
            helpers,
            selection,
            "const tabs=[{id:'source'},{id:'progress'},{id:'result'}];",
            "const dashboard=(run)=>({tabs,domainData:{eaFactory:{activeBuild:{platform:'mt5'},backendBusy:null,oneClick:{run},stages:[{id:'artifacts_report',status:'completed'}]}}});",
            "const awaiting=getWorkflowSelectedTab(EA_FACTORY_PROP_ID,dashboard({runId:'run-1',status:'awaiting_visible_terminal',canResume:true}));",
            "const retryable=getWorkflowSelectedTab(EA_FACTORY_PROP_ID,dashboard({runId:'run-2',status:'failed',canRetry:true}));",
            "const completed=getWorkflowSelectedTab(EA_FACTORY_PROP_ID,dashboard({runId:'run-3',status:'completed'}));",
            "process.stdout.write(JSON.stringify({awaiting:awaiting.id,retryable:retryable.id,completed:completed.id}));",
        ])
        completed = subprocess.run(
            [self.node_binary(), "-e", script],
            cwd=ROOT,
            capture_output=True,
            check=True,
            text=True,
            encoding="utf-8",
        )
        self.assertEqual(
            json.loads(completed.stdout),
            {"awaiting": "progress", "retryable": "progress", "completed": "source"},
        )

    def test_explicit_factory_tabs_survive_polling_and_modal_reopen_restores_default(self):
        script = "\n".join([
            "const assert=require('node:assert/strict');",
            "const EA_FACTORY_PROP_ID='right_server_racks',EA_OPTIMIZATION_LAB_PROP_ID='right_tool_console',AI_TRADE_COUNCIL_PROP_ID='left_analytics_console';",
            "const heartbeatController=new AbortController(),cancelledTimers=[];",
            "const state={modal:{open:true,id:EA_FACTORY_PROP_ID,type:'prop',workflowTabs:{},workflowVoice:{},eaFactory:{explicitPageId:''}},propReports:{},aiTradeCouncilHeartbeat:{timer:7,controller:heartbeatController,data:{stale:true},status:'ready',nextPollAt:100}};",
            "const tabs=[{id:'source'},{id:'progress'},{id:'result'}];",
            "const domain={activeBuild:{id:'ea-build-elder'},backendBusy:null,oneClick:{run:{runId:'run-existing',status:'awaiting_visible_terminal',canResume:false}},stages:[]};",
            "const dashboard={tabs,domainData:{eaFactory:domain}};let renders=[],saves=0,gameModalReturnFocus;",
            "const els={};const document={activeElement:null,body:{classList:{add(){}}},createElement:()=>({events:{},addEventListener(name,handler){this.events[name]=handler;}})};",
            "const window={requestAnimationFrame(){},clearInterval(timer){cancelledTimers.push(timer);}};const focusGameModalInitialControl=()=>{};",
            "const isWorkflowDashboardPropId=()=>true,getModalSubject=()=>({id:EA_FACTORY_PROP_ID}),getPropertyRole=()=>({}),normalizeWorkflowDashboard=()=>dashboard,getModalSurface=()=> 'dashboard';",
            "const saveSessionSnapshot=()=>{saves++;};",
            self.block("function eaFactoryCertifiedDeliveryCompleted", "function createEaFactoryPageHeader"),
            self.block("function getWorkflowSelectedTab", "function renderWorkflowTabs"),
            "const renderWorkflowDashboard=()=>{const tab=getWorkflowSelectedTab(EA_FACTORY_PROP_ID,dashboard);state.modal.workflowTabs[EA_FACTORY_PROP_ID]=tab.id;renders.push(tab.id);};",
            "const renderGameModal=()=>renderWorkflowDashboard();",
            self.block("function setWorkflowDashboardTab", "function workflowActionFormPayload"),
            self.block("function createEaFactoryPageNavigation", "function renderEaFactoryExistingBuildPicker"),
            self.block("function stopAiTradeHeartbeatPolling", "function startAiTradeHeartbeatPolling"),
            self.block("function openGameModal", "function closeGameModal"),
            "for(const status of ['queued','running','waiting_ai','cancelling','failed','blocked','awaiting_visible_terminal']){",
            "  domain.oneClick.run.status=status;state.modal.eaFactory.explicitPageId='';state.modal.workflowTabs[EA_FACTORY_PROP_ID]='source';",
            "  assert.equal(getWorkflowSelectedTab(EA_FACTORY_PROP_ID,dashboard).id,'progress');",
            "  for(const page of ['result','source','progress']){setWorkflowDashboardTab(EA_FACTORY_PROP_ID,page);assert.equal(renders.at(-1),page);renderWorkflowDashboard();assert.equal(renders.at(-1),page);}",
            "}",
            "const before=JSON.stringify(domain);const back=createEaFactoryPageNavigation('กลับไปตั้งค่างานหน้า 1','source');back.events.click();",
            "assert.equal(renders.at(-1),'source');renderWorkflowDashboard();assert.equal(renders.at(-1),'source');assert.equal(JSON.stringify(domain),before);",
            "openGameModal('prop',EA_FACTORY_PROP_ID);assert.equal(state.modal.eaFactory.explicitPageId,'');assert.equal(renders.at(-1),'progress');",
            "assert.equal(heartbeatController.signal.aborted,true);assert.deepEqual(cancelledTimers,[7]);assert.equal(state.aiTradeCouncilHeartbeat.timer,null);assert.equal(state.aiTradeCouncilHeartbeat.data,null);assert.equal(state.aiTradeCouncilHeartbeat.status,'idle');assert.equal(state.aiTradeCouncilHeartbeat.nextPollAt,0);",
            "state.modal.eaFactory.explicitPageId='not-a-page';assert.equal(getWorkflowSelectedTab(EA_FACTORY_PROP_ID,dashboard).id,'progress');",
            "process.stdout.write(JSON.stringify({passed:true,historyUnchanged:JSON.stringify(domain)===before,saves}));",
        ])
        completed = subprocess.run([self.node_binary(), "-"], input=script, cwd=ROOT,
                                   capture_output=True, check=False, text=True, encoding="utf-8")
        self.assertEqual(completed.returncode, 0, completed.stderr)
        result = json.loads(completed.stdout)
        self.assertTrue(result["passed"])
        self.assertTrue(result["historyUnchanged"])
        self.assertEqual(result["saves"], 23)

    def test_selected_build_retains_sanitized_system_name_without_changing_identity(self):
        start = self.main.index("  const activeBuild = ", self.main.index("function normalizeEaFactoryDomain"))
        mapping = self.main[start:self.main.index("  const oneClickOwnsBuild =", start)]
        script = "\n".join([
            "const assert=require('node:assert/strict');",
            self.block("function safeDashboardDisplayText", "function safeAgentChatReplyText"),
            "const normalizeEaFactoryArtifactKind=v=>v,normalizeEaFactoryPlatform=v=>v,normalizeEaFactoryTextList=()=>[],normalizeEaFactoryArtifact=v=>v,normalizeEaFactoryAudit=()=>[],normalizeEaFactoryOneClickRun=v=>v;",
            "const workflowDomainObject=v=>v||{},eaFactoryFirstArray=(...values)=>values.find(Array.isArray)||[];",
            "function normalize(activeBuildRaw){const buildId=activeBuildRaw.id,latestBuildVersion=0,root={};",
            mapping,
            "return activeBuild;}",
            "const raw={id:'ea-build-existing-ema',sourceDisplayName:'EMA 10/60 Closed-Bar Smoke EA',oneClickRun:{runId:'ea-run-original',status:'completed'}};const before=JSON.stringify(raw);",
            "const result=normalize(raw);assert.equal(result.sourceDisplayName,'EMA 10/60 Closed-Bar Smoke EA');assert.equal(result.id,raw.id);assert.equal(result.raw,raw);assert.equal(JSON.stringify(raw),before);",
            "assert.equal(normalize({id:raw.id}).sourceDisplayName,'Strategy Build');",
            "assert.ok(!normalize({id:raw.id,sourceDisplayName:'token=private-value'}).sourceDisplayName.includes('private-value'));",
            "assert.equal(normalize({id:raw.id,sourceDisplayName:'x'.repeat(500)}).sourceDisplayName.length,180);",
        ])
        subprocess.run([self.node_binary(), "-"], input=script, cwd=ROOT,
                       capture_output=True, check=True, text=True, encoding="utf-8")

    def test_factory_run_normalization_rejects_optimization_resume_and_bounds_progress(self):
        normalizers = self.block(
            "function normalizeEaFactoryOneClickRun",
            "function normalizeEaFactoryAudit",
        )
        script = "\n".join([
            "const safeDashboardDisplayText=(value,fallback='')=>String(value || fallback);",
            "const EA_FACTORY_UI_STAGE_BY_BACKEND={};",
            "const EA_FACTORY_STAGE_IDS=['source','spec','generate','review','compile_validate','backtest_recheck','artifacts_report'];",
            "const normalizeEaFactoryStageStatus=(value)=>String(value || 'unknown');",
            "const eaFactoryFirstArray=(...values)=>values.find(Array.isArray)||[];",
            normalizers,
            "const rejected=normalizeEaFactoryOneClickRun({runId:'run-1',status:'failed',canResume:true,canRetry:true,resumeKind:'optimization_handoff',progressPercent:137.4,optimizationProgressPercent:91,optimizationHandoff:{state:'running'}});",
            "const visible=normalizeEaFactoryOneClickRun({runId:'run-2',status:'awaiting_visible_terminal',canResume:true,canRetry:true,resumeKind:'visible_terminal',progressPercent:-20});",
            "process.stdout.write(JSON.stringify({rejected,visible}));",
        ])
        completed = subprocess.run(
            [self.node_binary(), "-e", script],
            cwd=ROOT,
            capture_output=True,
            check=True,
            text=True,
            encoding="utf-8",
        )
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["rejected"]["progressPercent"], 100)
        self.assertEqual(payload["rejected"]["resumeKind"], "")
        self.assertFalse(payload["rejected"]["canResume"])
        self.assertFalse(payload["rejected"]["canRetry"])
        self.assertNotIn("optimizationProgressPercent", payload["rejected"])
        self.assertNotIn("optimizationHandoff", payload["rejected"])
        self.assertEqual(payload["visible"]["progressPercent"], 0)
        self.assertEqual(payload["visible"]["resumeKind"], "visible_terminal")
        self.assertTrue(payload["visible"]["canResume"])
        self.assertTrue(payload["visible"]["canRetry"])

    def test_waiting_factory_states_poll_without_claiming_active_or_aria_busy(self):
        helpers = self.block("function eaFactoryCertifiedDeliveryCompleted", "function eaFactoryPageStatus")
        stage_status = self.block("function eaFactoryOneClickStageStatus", "function eaFactoryExistingOneClickAdmission")
        progress = self.block("function eaFactoryPhaseGateProgress", "function stopEaFactoryActiveProgressPolling")
        renderer = self.block("function renderEaFactoryGameProgressPanel", "function renderEaFactoryOneClickSetup")
        script = "\n".join([
            "const EA_FACTORY_VISUAL_STAGE_IDS=['generate','review','compile_validate','backtest_recheck','artifacts_report'];",
            "const EA_FACTORY_UI_STAGE_BY_BACKEND={};",
            "const EA_FACTORY_STAGE_COPY={artifacts_report:{titleTh:'Final Report'}};",
            "const state={modal:{eaFactory:{inFlight:false}}};",
            helpers,
            stage_status,
            progress,
            "const stages=['generate','review','compile_validate','backtest_recheck','artifacts_report'].map((id)=>({id,status:'completed'}));",
            "const domain=(status)=>({activeBuild:{platform:'mt5'},backendBusy:null,currentStageId:'artifacts_report',oneClick:{run:{runId:'run-1',status,progressPercent:80}},stages});",
            "const queued=eaFactoryPhaseGateProgress(domain('queued'));",
            "const awaiting=eaFactoryPhaseGateProgress(domain('awaiting_visible_terminal'));",
            "const running=eaFactoryPhaseGateProgress(domain('running'));",
            "const failed=eaFactoryPhaseGateProgress(domain('failed'));",
            "process.stdout.write(JSON.stringify({queued,awaiting,running,failed}));",
        ])
        completed = subprocess.run(
            [self.node_binary(), "-e", script],
            cwd=ROOT,
            capture_output=True,
            check=True,
            text=True,
            encoding="utf-8",
        )
        payload = json.loads(completed.stdout)
        for key in ("queued", "awaiting"):
            self.assertFalse(payload[key]["active"], key)
            self.assertTrue(payload[key]["waiting"], key)
            self.assertTrue(payload[key]["shouldPoll"], key)
        self.assertTrue(payload["running"]["active"])
        self.assertFalse(payload["running"]["waiting"])
        self.assertFalse(payload["failed"]["active"])
        self.assertFalse(payload["failed"]["waiting"])
        self.assertFalse(payload["failed"]["shouldPoll"])
        self.assertIn('panel.setAttribute("aria-busy", progressState.active && live ? "true" : "false")', renderer)
        self.assertIn("ตรวจสถานะล่าสุด", renderer)

    def test_sheet_source_uses_exact_a_j_strategy_brief_and_posts_opaque_source_record_id(self):
        constants = self.block("const EA_FACTORY_SHEET_COLUMNS", "const EA_FACTORY_LEGACY_SHEET_COLUMNS")
        columns = re.findall(r'\["([A-J])", "([a-z_]+)"\]', constants)
        self.assertEqual(len(columns), 10)
        self.assertEqual("".join(letter for letter, _ in columns), "ABCDEFGHIJ")
        self.assertEqual(
            [name for _, name in columns],
            [
                "record_id",
                "system_name",
                "system_overview",
                "entry_rules",
                "recovery_rules",
                "exit_rules",
                "money_management",
                "order_execution",
                "display_requirements",
                "additional_notes",
            ],
        )

        normalizer = self.block("function normalizeEaFactorySourceRecord", "function normalizeEaFactoryStageStatus")
        self.assertIn("item?.sourceRecordId", normalizer)
        self.assertIn("item?.columnValues", normalizer)
        self.assertIn("item?.core", normalizer)
        self.assertIn("item?.downstream", normalizer)
        self.assertIn("const eaResearch = normalizeEaFactoryResearchReadModel({", normalizer)
        self.assertIn("strategyBrief: item?.strategyBrief", normalizer)
        self.assertIn("buildReady: item?.buildReady === true && eaResearch.ready", normalizer)
        self.assertIn("sourceReportId:", normalizer)
        self.assertIn("blueprintDigest: eaResearch.blueprintDigest", normalizer)
        self.assertIn("...eaResearch.readinessIssues", normalizer)
        self.assertIn("...missingCoreFields.map", normalizer)
        self.assertIn("compatiblePlatforms", normalizer)
        self.assertIn("factoryCompatibility", normalizer)
        self.assertIn("&& compatibilityReady", normalizer)
        self.assertIn("eaResearch,", normalizer)
        self.assertIn("backtestReport:", normalizer)
        self.assertIn("optimizationReport:", normalizer)
        self.assertIn("sourceUrls.slice(0, 10)", normalizer)
        list_normalizer = self.block("function normalizeEaFactoryTextList", "function eaFactoryFirstArray")
        self.assertIn("safeAgentChatReplyText", list_normalizer)
        self.assertIn("limit = 80", list_normalizer)
        self.assertIn(r"split(/\r?\n|\s*;\s*/)", list_normalizer)
        create = self.block("async function createEaFactoryBuild", "async function advanceEaFactoryStage")
        self.assertIn("sourceRecordId,", create)
        self.assertIn("artifactKind: normalizedArtifactKind", create)
        self.assertIn("platform: normalizedPlatform", create)
        self.assertIn(".slice(0, 900)", create)
        self.assertIn("source.compatiblePlatforms.includes(normalizedPlatform)", create)
        spec = self.block("function renderEaFactorySpecStage", "function renderEaFactoryTerminalPicker")
        self.assertIn("brief.maxLength = 900", spec)
        self.assertIn("compatiblePlatformSet.has(value)", spec)
        self.assertIn("compatiblePlatformSet.has(platform.value)", spec)

    def test_clean_intake_requires_explicit_platform_artifact_and_source_mode_choices(self):
        factory_state = self.block("    eaFactory: {", "    eaOptimizationLab: {")
        for field in (
            "sourceMode",
            "sheetRecordId",
            "importedSourceId",
            "customConditions",
            "discoveryTargetProfitPercent",
            "discoveryMaxDrawdownPercent",
            "discoveryBacktestYears",
        ):
            self.assertIn(f"{field}:", factory_state)
        self.assertIn('selectedPlatform: ""', factory_state)
        self.assertIn('selectedArtifactKind: ""', factory_state)

        intake = self.block("function renderEaFactorySourceStage", "function renderEaFactorySpecStage")
        for value in ("mt4", "mt5", "tradingview"):
            self.assertIn(f'"{value}"', intake)
        for label in ("MT4", "MT5", "TradingView"):
            self.assertIn(label, intake)
        for value in ("expert_advisor", "custom_indicator"):
            self.assertIn(f'"{value}"', intake)
        for label in ("EA", "Indicator"):
            self.assertIn(label, intake)
        for label in ("Google Sheet", "EA Discovery", "เขียนเงื่อนไขเอง"):
            self.assertIn(label, intake)

    def test_sheet_record_import_is_trimmed_case_insensitive_exact_and_never_fuzzy(self):
        helper = self.block(
            "function eaFactoryFindSourceByExactRecordId",
            "function createEaFactoryNotice",
        )
        self.assertIn(".trim()", helper)
        self.assertIn(".toLowerCase()", helper)
        self.assertIn("===", helper)
        self.assertNotIn(".includes(", helper)
        self.assertNotIn(".startsWith(", helper)

        script = "\n".join([
            helper,
            "const records = [",
            "  {recordId:'EA-007',sourceRecordId:'source-exact'},",
            "  {recordId:'EA-007-SCALPER',sourceRecordId:'source-longer'},",
            "  {recordId:'EA-008',sourceRecordId:'source-other'},",
            "];",
            "const exact = eaFactoryFindSourceByExactRecordId(records, '  ea-007  ');",
            "const partial = eaFactoryFindSourceByExactRecordId(records, 'EA-00');",
            "const prefix = eaFactoryFindSourceByExactRecordId(records, 'EA-007-');",
            "const blank = eaFactoryFindSourceByExactRecordId(records, '   ');",
            "const duplicate = eaFactoryFindSourceByExactRecordId([",
            "  {recordId:'EA-DUP',sourceRecordId:'source-dup-a'},",
            "  {recordId:'ea-dup',sourceRecordId:'source-dup-b'},",
            "], 'EA-DUP');",
            "process.stdout.write(JSON.stringify({exact:exact?.sourceRecordId || null,partial,prefix,blank,duplicate}));",
        ])
        completed = subprocess.run(
            [self.node_binary(), "-e", script],
            cwd=ROOT,
            capture_output=True,
            check=True,
            text=True,
            encoding="utf-8",
        )
        self.assertEqual(
            json.loads(completed.stdout),
            {
                "exact": "source-exact",
                "partial": None,
                "prefix": None,
                "blank": None,
                "duplicate": None,
            },
        )

    def test_clean_intake_requires_import_and_fails_closed_for_unimplemented_sources(self):
        intake = self.block("function renderEaFactorySourceStage", "function renderEaFactorySpecStage")
        record_import = self.block(
            "function renderEaFactoryRecordImport",
            "function renderEaFactoryStartControls",
        )
        start_controls = self.block(
            "function renderEaFactoryStartControls",
            "function renderEaFactoryDiscoveryPreview",
        )
        import_action = self.block(
            "function eaFactoryGoogleSheetSyncReceipt",
            "async function createEaFactoryBuild",
        )
        self.assertIn("sheetRecordId", intake)
        self.assertIn('sourceMode === "google_sheet"', intake)
        self.assertIn("importedSourceId", record_import)
        self.assertIn("Import ข้อมูล", record_import)
        self.assertIn("if (imported)", record_import)
        self.assertIn("renderEaFactoryStartControls", record_import)
        self.assertIn("renderEaFactoryImportedSummary", record_import)
        self.assertIn("selectedRecord: catalog.selectedRecord", record_import)
        self.assertIn("importBindingReady", start_controls)
        self.assertIn("submit.disabled = !canStart", start_controls)
        self.assertIn("importedRecordStillMatches", start_controls)
        self.assertIn("ข้อมูล Google Sheet เปลี่ยนหลัง Import", start_controls)
        self.assertIn("eaFactoryFindSourceByExactRecordId", import_action)
        self.assertIn("state.modal.eaFactory.importedSourceId = source.sourceRecordId", import_action)
        self.assertIn("discoveryTargetProfitPercent", intake)
        self.assertIn("discoveryMaxDrawdownPercent", intake)
        self.assertIn("discoveryBacktestYears", intake)
        self.assertIn("customConditions", intake)
        self.assertIn("EA Discovery Runner จริง", intake)
        self.assertIn("Source Contract", intake)
        self.assertNotIn("prepare_ea_discovery_plan", intake)
        self.assertIn('state.modal.eaFactory.sourceMode === "discovery"', intake)
        self.assertIn('state.modal.eaFactory.sourceMode = ""', intake)

    def test_discovery_form_uses_annual_profit_and_valid_backtest_years_but_runner_stays_disabled(self):
        discovery = self.block(
            "function renderEaFactoryDiscoveryPreview",
            "function renderEaFactoryCustomSourcePreview",
        )
        self.assertIn(
            '["กำไรเป้าหมายต่อปี (%)", "discoveryTargetProfitPercent", "เช่น 20"]',
            discovery,
        )
        self.assertIn(
            '["จำนวนปี Backtest", "discoveryBacktestYears", "เช่น 5"]',
            discovery,
        )
        self.assertIn(
            'input.min = stateKey === "discoveryBacktestYears" ? "1" : "0.1";',
            discovery,
        )
        self.assertIn('start.disabled = true;', discovery)
        self.assertIn('start.textContent = "EA Discovery Runner ยังไม่เปิดใช้งาน";', discovery)
        self.assertNotIn("prepare_ea_discovery_plan", discovery)

    def test_custom_source_is_live_and_reuses_the_normal_build_and_one_click_flow(self):
        custom = self.block(
            "function eaFactoryEmaSmokeCustomSourcePayload",
            "function renderEaFactorySpecStage",
        )
        constants = self.main[:10000]
        self.assertIn(
            'EA_FACTORY_CUSTOM_SOURCE_ENDPOINT = "/api/props/right_server_racks/ea-factory/sources/custom"',
            constants,
        )
        self.assertIn("async function createEaFactoryCustomSourceAndStart", custom)
        self.assertIn("EA_FACTORY_CUSTOM_SOURCE_ENDPOINT", custom)
        self.assertIn("runEaFactoryRequest(\"custom_source\"", custom)
        self.assertIn("await waitForEaFactoryAuthoritativeReceipt", custom)
        self.assertIn("{ refreshReadModel: false, isCurrent }", custom)
        self.assertIn("createAndRunEaFactoryBuild(sourceRecordId, artifactKind, platform", custom)
        self.assertIn("createEaFactoryBuild(sourceRecordId, artifactKind, platform", custom)
        self.assertIn("const updateStartAvailability = () =>", custom)
        self.assertIn("start.disabled = !Boolean(", custom)
        self.assertIn("ใช้ชุดทดสอบ EMA 10/60", custom)
        self.assertNotIn("ต้องสร้าง Strategy Source ก่อนเริ่มเขียน", custom)

    def test_custom_ema_smoke_payload_is_exact_closed_bar_buy_sell_and_tester_only(self):
        helper = self.block(
            "function eaFactoryEmaSmokeCustomSourcePayload",
            "function eaFactoryCustomSourcePayload",
        )
        self.assertIn('platform: "mt5"', helper)
        self.assertIn('artifactKind: "expert_advisor"', helper)
        self.assertIn("EMA(10) at closed bar 2", helper)
        self.assertIn("closed bar 1", helper)
        self.assertIn("SELL on the exact inverse", helper)
        self.assertIn("StopLossPips", helper)
        self.assertIn("TakeProfitPips", helper)
        self.assertIn("fixed lot of 0.01", helper)
        self.assertIn("Strategy Tester only", helper)
        self.assertIn("verify entry markers against the crossover", helper)

    def test_discovery_market_watch_uses_mt4_endpoint_and_exact_terminal_revision_binding(self):
        binding = self.block(
            "function eaFactoryDiscoveryTerminalBinding",
            "function normalizeEaFactoryDiscoveryMarketWatch",
        )
        loader = self.block(
            "async function loadEaFactoryDiscoveryMarketWatch",
            "function normalizeEaFactoryArtifact",
        )
        discovery = self.block(
            "function renderEaFactoryDiscoveryPreview",
            "function renderEaFactoryCustomSourcePreview",
        )

        self.assertIn('if (normalizedPlatform !== "mt4") return null;', binding)
        self.assertIn("candidateId: candidate.candidateId", binding)
        self.assertIn("selectionRevision,", binding)
        self.assertIn(
            "`${binding.platform}:${binding.candidateId}:${binding.selectionRevision}`",
            binding,
        )
        self.assertIn(
            '"/api/props/right_server_racks/ea-factory/market-watch"',
            loader,
        )
        self.assertIn("currentBindingKey === bindingKey", loader)
        self.assertIn("responseBindingKey !== bindingKey", loader)
        self.assertIn('reasonCode: "market_watch_binding_mismatch"', loader)
        self.assertIn('document.createElement("select")', discovery)
        self.assertIn('symbolSelect.dataset.eaFactoryDiscoverySymbol = "true";', discovery)

    def test_discovery_symbol_dropdown_never_auto_selects_and_mt5_is_fail_closed(self):
        binding = self.block(
            "function eaFactoryDiscoveryTerminalBinding",
            "function normalizeEaFactoryDiscoveryMarketWatch",
        )
        discovery = self.block(
            "function renderEaFactoryDiscoveryPreview",
            "function renderEaFactoryCustomSourcePreview",
        )
        script = "\n".join([
            "const EA_FACTORY_PROP_ID = 'right_server_racks';",
            "function normalizeEaFactoryPlatform(value) { const result = String(value || '').toLowerCase(); return ['mt4','mt5','tradingview'].includes(result) ? result : ''; }",
            "function normalizeMetatraderCandidate(value) { return value && typeof value === 'object' ? value : null; }",
            "const digest = 'a'.repeat(64);",
            "const state = {",
            "  globalMetatraderHub:{readModel:{platforms:{mt4:{targets:[{propId:EA_FACTORY_PROP_ID,status:'configured',selectionRevision:7,selectedCandidate:{candidateId:'mtc-terminal-one',platform:'MT4'}}]}}}},",
            "  modal:{eaFactory:{discoverySymbol:'',discoverySymbolBinding:'',discoveryMarketWatch:{status:'ready',candidateId:'mtc-terminal-one',selectionRevision:7,symbols:['EURUSD','XAUUSD.a'],symbolCount:2,catalogDigest:digest,inFlight:false,message:'ready'}}},",
            "};",
            "function makeElement(tag) { return {tag,children:[],dataset:{},listeners:{},textContent:'',value:'',disabled:false,appendChild(node){this.children.push(node);return node;},append(...nodes){this.children.push(...nodes);},addEventListener(type,handler){this.listeners[type]=handler;}}; }",
            "const created = [];",
            "const document = {createElement(tag){const node=makeElement(tag);created.push(node);return node;}};",
            "function createEaFactoryNotice(){return makeElement('notice');}",
            binding,
            discovery,
            "const mt4Binding = eaFactoryDiscoveryTerminalBinding('mt4');",
            "const mt4BindingKey = eaFactoryDiscoveryTerminalBindingKey(mt4Binding);",
            "const mt5Binding = eaFactoryDiscoveryTerminalBinding('mt5');",
            "renderEaFactoryDiscoveryPreview(makeElement('container'), {platform:'mt4'});",
            "const mt4Select = created.filter((node) => node.tag === 'select')[0];",
            "const mt4Start = created.filter((node) => node.tag === 'button' && node.textContent.includes('Discovery Runner'))[0];",
            "const mt4InitialValue = mt4Select.value;",
            "const mt4Options = mt4Select.children.map((node) => node.value);",
            "mt4Select.value = 'XAUUSD.a';",
            "mt4Select.listeners.change();",
            "const selectedAfterExplicitChange = {symbol:state.modal.eaFactory.discoverySymbol,binding:state.modal.eaFactory.discoverySymbolBinding};",
            "renderEaFactoryDiscoveryPreview(makeElement('container'), {platform:'mt5'});",
            "const selects = created.filter((node) => node.tag === 'select');",
            "const mt5Select = selects[1];",
            "const starts = created.filter((node) => node.tag === 'button' && node.textContent.includes('Discovery Runner'));",
            "process.stdout.write(JSON.stringify({mt4Binding,mt4BindingKey,mt5Binding,mt4InitialValue,mt4Options,mt4Disabled:mt4Select.disabled,mt4StartDisabled:mt4Start.disabled,selectedAfterExplicitChange,mt5Value:mt5Select.value,mt5Options:mt5Select.children.map((node) => node.value),mt5Disabled:mt5Select.disabled,mt5StartDisabled:starts[1].disabled,selectionAfterMt5:{symbol:state.modal.eaFactory.discoverySymbol,binding:state.modal.eaFactory.discoverySymbolBinding}}));",
        ])
        completed = subprocess.run(
            [self.node_binary(), "-e", script],
            cwd=ROOT,
            capture_output=True,
            check=True,
            text=True,
            encoding="utf-8",
        )
        payload = json.loads(completed.stdout)
        self.assertEqual(
            payload["mt4Binding"],
            {"platform": "mt4", "candidateId": "mtc-terminal-one", "selectionRevision": 7},
        )
        self.assertEqual(payload["mt4BindingKey"], "mt4:mtc-terminal-one:7")
        self.assertIsNone(payload["mt5Binding"])
        self.assertEqual(payload["mt4InitialValue"], "")
        self.assertEqual(payload["mt4Options"], ["", "EURUSD", "XAUUSD.a"])
        self.assertFalse(payload["mt4Disabled"])
        self.assertTrue(payload["mt4StartDisabled"])
        self.assertEqual(
            payload["selectedAfterExplicitChange"],
            {"symbol": "XAUUSD.a", "binding": "a" * 64},
        )
        self.assertEqual(payload["mt5Value"], "")
        self.assertEqual(payload["mt5Options"], [""])
        self.assertTrue(payload["mt5Disabled"])
        self.assertTrue(payload["mt5StartDisabled"])
        self.assertEqual(payload["selectionAfterMt5"], {"symbol": "", "binding": ""})

    def test_clean_intake_routes_only_supported_ea_one_click_and_never_coerces_indicator(self):
        intake = self.block("function renderEaFactorySourceStage", "function renderEaFactorySpecStage")
        self.assertIn('artifactKind === "expert_advisor"', intake)
        self.assertRegex(intake, r'\[\s*"mt4"\s*,\s*"mt5"\s*\]\.includes\(platform\)')
        self.assertIn("createAndRunEaFactoryBuild(", intake)
        direct_create = re.search(
            r"createEaFactoryBuild\([\s\S]{0,400}?artifactKind[\s\S]{0,200}?platform[\s\S]{0,200}?\)",
            intake,
        )
        self.assertIsNotNone(direct_create)
        self.assertNotIn('createEaFactoryBuild(source.sourceRecordId, "expert_advisor"', intake)

        create = self.block("async function createEaFactoryBuild", "function eaFactoryOneClickRequestKey")
        self.assertIn(
            'normalizedArtifactKind === "custom_indicator" && normalizedPlatform === "tradingview"',
            create,
        )

    def test_custom_indicator_picker_and_truthful_no_backtest_ui(self):
        normalizer = self.block(
            "function normalizeEaFactoryArtifactKind",
            "const EA_FACTORY_READINESS_ISSUE_LABELS",
        )
        self.assertIn('return "custom_indicator"', normalizer)
        self.assertIn('return "expert_advisor"', normalizer)
        domain = self.block("function normalizeEaFactoryDomain", "function normalizeWorkflowDomainData")
        self.assertIn("artifactKind: normalizeEaFactoryArtifactKind", domain)
        spec = self.block("function renderEaFactorySpecStage", "function renderEaFactoryTerminalPicker")
        self.assertIn('artifactKind.dataset.eaFactoryArtifactKind = "true"', spec)
        self.assertIn('["custom_indicator", "Custom Indicator"]', spec)
        self.assertIn("tradingViewOption.disabled = indicatorSelected", spec)
        self.assertIn('platform.value === "tradingview"', spec)
        operational = self.block("function renderEaFactoryOperationalStage", "function renderEaFactoryPanel")
        self.assertIn('domain.activeBuild.artifactKind === "custom_indicator"', operational)
        self.assertIn("Not Applicable สำหรับ Custom Indicator", operational)
        self.assertIn("ไม่มีการ attach หรือเทรด", self.main)
        self.assertIn("เริ่มตรวจ Indicator และ No-Trade Guard", operational)

    def test_requests_use_dedicated_endpoints_and_tradingview_is_canonical(self):
        actions = self.block("async function syncEaFactoryGoogleSheet", "function connectionHubStatusGroup")
        self.assertIn('"/api/props/right_server_racks/ea-factory/sources/google-sheet/sync"', actions)
        self.assertIn('"/api/props/right_server_racks/ea-factory/builds"', actions)
        self.assertIn("/ea-factory/builds/${encodeURIComponent(buildId)}/advance", actions)
        self.assertNotIn("/api/integrations/metatrader/", actions)
        self.assertIn('postJson("/api/integrations/metatrader/global/select"', self.main)
        self.assertNotIn('postJson("/api/integrations/metatrader/select"', self.main)
        self.assertIn('["tradingview", "TradingView / Pine Script"]', self.main)
        self.assertNotIn('["pine", "TradingView / Pine Script"]', self.main)
        self.assertIn('return "tradingview";', self.block("function normalizeEaFactoryPlatform", "function normalizeEaFactorySourceRecord"))

    def test_authoritative_read_model_and_stage_gates_fail_closed(self):
        supported_modes = self.block("const EA_FACTORY_SUPPORTED_MODES", "const POLLING_LEADER_STORAGE_KEY")
        self.assertEqual(
            re.findall(r'^\s+"([a-z_]+)",?$', supported_modes, re.M),
            ["one_click_with_manual_stage_recovery", "manual_stage_by_stage"],
        )
        normalizer = self.block("function normalizeEaFactoryDomain", "function normalizeWorkflowDomainData")
        self.assertIn('root.schemaVersion === "ea-factory-v1"', normalizer)
        self.assertIn("EA_FACTORY_SUPPORTED_MODES.has(root.mode)", normalizer)
        self.assertIn('"one_click_with_manual_stage_recovery"', self.main)
        self.assertIn('"manual_stage_by_stage"', self.main)
        self.assertIn("root.scheduled === false", normalizer)
        self.assertIn("dedicatedReadModelFresh", normalizer)
        self.assertIn("state.eaFactoryReadModel.stale !== true", normalizer)
        self.assertIn("root.snapshotStale !== true", normalizer)
        self.assertNotIn("report.eaFactory", normalizer)
        self.assertNotIn("latestReportMetrics", normalizer)
        self.assertIn("const canRun = raw?.canAdvance === true", self.main)
        stage_normalizer = self.block("function normalizeEaFactoryStage", "function normalizeEaFactoryTerminal")
        self.assertNotIn("raw?.canRun", stage_normalizer)
        self.assertNotIn("raw?.actionEnabled", stage_normalizer)
        self.assertIn('canRun && normalizedStatus === "locked" ? "ready"', self.main)
        self.assertIn("terminalSelection.selectedCandidate", normalizer)
        self.assertIn('status: "locked"', normalizer)

        tabs = self.block("function renderWorkflowTabs", "function workflowAvailabilityCopy")
        self.assertIn("eaFactoryPageStatus", tabs)
        self.assertIn("const factoryLocked = false", tabs)
        self.assertIn("button.disabled = Boolean(factoryLocked)", tabs)
        operational = self.block("function renderEaFactoryOperationalStage", "function renderEaFactoryPanel")
        self.assertIn("stage?.canRun === true", operational)
        self.assertIn("domain.currentStageId === stageId", operational)
        self.assertIn("domain.selectedTerminalReady === true", operational)
        self.assertIn('["compile_validate", "backtest_recheck"].includes(stageId)', operational)
        self.assertIn("ยังไม่มีผล Visual Backtest จริง", operational)
        self.assertNotIn("domain.activeBuild.raw?.backtest", operational)
        self.assertIn("ระบบไม่อ่าน metric นอกสัญญา", operational)

    def test_pine_skips_terminal_and_backtest_without_fake_result(self):
        picker = self.block("function renderEaFactoryTerminalPicker", "function renderEaFactoryOperationalStage")
        self.assertIn('platform === "tradingview"', picker)
        self.assertIn("Pine Script ใช้ Code Validation เท่านั้น", picker)
        operational = self.block("function renderEaFactoryOperationalStage", "function renderEaFactoryPanel")
        self.assertIn('domain.activeBuild.platform === "tradingview"', operational)
        self.assertIn("Not Applicable สำหรับ Pine Script", operational)
        self.assertIn("ระบบไม่สร้างผล Backtest ทดแทน", operational)

    def test_only_authoritative_backend_busy_locks_new_factory_work(self):
        normalizer = self.block("function normalizeEaFactoryDomain", "function normalizeWorkflowDomainData")
        self.assertIn("const backendBusyActive = Object.keys(backendBusy).length > 0", normalizer)
        self.assertIn("const busyBuild = backendBusyActive ? builds.find", normalizer)
        self.assertIn('const oneClickOwnsBuild = ["queued", "running", "waiting_ai", "awaiting_visible_terminal", "cancelling"]', normalizer)
        self.assertIn("const canStartNewBuild = !backendBusyActive", normalizer)
        self.assertIn("historicalRunLooksActive: !backendBusyActive && oneClickOwnsBuild", normalizer)
        self.assertNotIn("const canStartNewBuild = !backendBusyActive && !oneClickOwnsBuild", normalizer)
        self.assertIn("backendBusyActive ? matchingBusyRootBuild : requestedBuild", normalizer)
        self.assertIn("backendBusyActive || requestedBuildId ? null : rootActiveBuild", normalizer)
        self.assertIn("backendBusyActive || requestedBuildId ? null : builds[0]", normalizer)
        source = self.block("function renderEaFactoryLegacySourceStage", "function renderEaFactoryChoiceSection")
        spec = self.block("function renderEaFactorySpecStage", "function renderEaFactoryTerminalPicker")
        self.assertIn("if (domain.canStartNewBuild)", source)
        self.assertIn("if (domain.canStartNewBuild)", spec)
        self.assertIn("ไม่เขียนทับ Version เดิม", spec)

    def test_running_build_keeps_its_exact_source_record_bound(self):
        selector = self.block("function eaFactorySelectedSource", "function createEaFactoryNotice")
        self.assertIn("domain.backendBusy && domain.activeBuild?.sourceRecordId", selector)
        self.assertIn("if (domain.backendBusy && requestedRecord) return requestedRecord", selector)
        source = self.block("function renderEaFactoryLegacySourceStage", "function renderEaFactoryChoiceSection")
        self.assertIn("select.disabled = !domain.authoritative || !domain.canStartNewBuild", source)

    def test_legacy_and_non_ready_sources_are_read_only_and_never_selected_for_new_build(self):
        selector = self.block("function eaFactorySelectedSource", "function createEaFactoryNotice")
        self.assertIn("records.filter(eaFactorySourceIsBuildSelectable)", selector)
        self.assertNotIn("selectableRecords[0]", selector)
        self.assertNotIn("records[0]", selector)
        self.assertIn("eaFactoryFindSourceByExactRecordId", selector)

        selectable = self.block(
            "function eaFactorySourceIsBuildSelectable",
            "function eaFactorySelectedSource",
        )
        self.assertIn("record?.buildReady === true", selectable)
        self.assertIn("research.ready === true", selectable)
        self.assertIn("research.validated === true", selectable)
        self.assertIn("research.digestMatched === true", selectable)
        self.assertIn("research.legacy !== true", selectable)
        self.assertIn("TRADING_RESEARCH_STRATEGY_BRIEF_SCHEMA_VERSION", selectable)

        source = self.block("function renderEaFactoryLegacySourceStage", "function renderEaFactoryChoiceSection")
        self.assertIn("option.disabled = !selectable", source)
        self.assertIn('" • อ่านอย่างเดียว"', source)
        self.assertIn("if (!eaFactorySourceIsBuildSelectable(next))", source)
        self.assertIn("ยังไม่มี Strategy Brief A-J ที่พร้อมสร้าง", source)
        self.assertIn("กรุณากลับไปวิเคราะห์ Revision ใหม่ก่อน", source)

    def test_strategy_spec_confirmation_uses_canonical_strategy_brief_not_legacy_blueprint(self):
        spec = self.block("function renderEaFactorySpecStage", "function renderEaFactoryTerminalPicker")
        self.assertIn("renderEaFactoryResearchGate(section, source, { showBrief: true })", spec)
        self.assertIn("if (!source.buildReady || !source.eaResearch.ready) return", spec)
        self.assertIn('"Brief SHA-256"', spec)
        self.assertNotIn("appendEaFactoryRuleList", spec)
        for column in "ABCDEFGHIJKLM":
            self.assertNotIn(f'"{column} •', spec)

        normalizer = self.block("function normalizeEaFactoryResearchReadModel", "function normalizeEaFactorySourceRecord")
        self.assertIn("item?.eaResearch", normalizer)
        self.assertIn("raw.strategyBrief", normalizer)
        self.assertIn("raw.briefDigest", normalizer)
        self.assertIn("raw.validated === true", normalizer)
        self.assertIn("raw.digestMatched === true", normalizer)
        self.assertIn("tradingResearchStrategyBriefReadModel(briefReport)", normalizer)
        self.assertIn("/^[0-9a-f]{64}$/", normalizer)
        self.assertIn("raw.readinessIssues", normalizer)
        self.assertIn("raw.blockingIssues", normalizer)
        self.assertNotIn("eaImplementationBlueprint", normalizer)
        self.assertNotIn("eaBlueprint", normalizer)

    def test_all_strategy_brief_fields_and_full_bounded_catalog_are_visible(self):
        normalizer = self.block("function normalizeEaFactoryDomain", "function normalizeWorkflowDomainData")
        source = self.block("function renderEaFactoryLegacySourceStage", "function renderEaFactoryChoiceSection")
        self.assertIn(").slice(0, 200).map(normalizeEaFactorySourceRecord)", normalizer)
        self.assertIn("eaFactoryFirstArray(root.builds).slice(0, 100)", normalizer)
        self.assertIn("eaFactoryFirstArray(activeBuildRaw?.files).slice(0, 200)", normalizer)
        self.assertIn("createTradingResearchStrategyBrief", source)
        self.assertNotIn("N • Source URLs", source)
        self.assertNotIn("W • Updated At", source)
        gate = self.block("function renderEaFactoryResearchGate", "function renderEaFactorySourceStage")
        self.assertIn("source?.readinessIssues", gate)
        self.assertIn("createTradingResearchStrategyBrief", gate)
        self.assertIn("Strategy Brief", gate)
        self.assertIn("legacy", gate)
        self.assertNotIn("innerHTML", gate)

    def test_selected_build_normalization_stays_backend_and_terminal_bound(self):
        self.assertIn('selectedBuildId: ""', self.main)
        normalizer = self.block("function normalizeEaFactoryDomain", "function normalizeWorkflowDomainData")
        self.assertIn("state.modal.eaFactory.selectedBuildId", normalizer)
        self.assertIn("requestedBuild,", normalizer)
        self.assertIn("selectedTerminalMatch", normalizer)
        self.assertIn("buildTerminalGate.ready === true", normalizer)
        self.assertIn("buildTerminalGate.adapterReady === true", normalizer)
        self.assertIn("buildTerminalGate.platform === activeBuild?.platform", normalizer)
        self.assertIn("buildTerminalGate.candidateId === selectedTerminalId", normalizer)

    def test_result_page_uses_safe_manifest_artifacts_without_operational_clutter(self):
        result = self.block("function renderEaFactoryResultPage", "function renderEaFactoryPanel")
        self.assertIn("EA_FACTORY_VISUAL_STAGE_IDS.forEach", result)
        self.assertIn("attentionRequired === true", result)
        self.assertIn(
            "appendDashboardArtifactLinks(artifacts, domain.activeBuild.artifacts, { limit: 200 })",
            result,
        )
        self.assertIn("ยังไม่มีไฟล์ที่ Backend อนุญาตให้ดาวน์โหลด", result)
        self.assertNotIn("reports.flatMap", result)
        for forbidden in (
            "renderEaFactoryOperationalStage",
            "renderEaFactoryTerminalPicker",
            "normalizeEaFactoryAudit",
            "buildHistory",
            "historyBuildId",
            "selectedBuildId",
            'document.createElement("form")',
            'document.createElement("details")',
            "createEaFactoryActionButton",
            "advanceEaFactoryStage",
            "retryEaFactoryStage",
        ):
            self.assertNotIn(forbidden, result)

        url_guard = self.block(
            "function getSafeReportArtifactUrl",
            "function appendDashboardArtifactLinks",
        )
        self.assertIn("parsed.origin !== window.location.origin", url_guard)
        self.assertIn("parsed.username || parsed.password", url_guard)
        self.assertIn("parsed.search || parsed.hash", url_guard)
        self.assertIn("/ea-factory\\/builds\\/ea-build-", url_guard)
        artifact_links = self.block(
            "function appendDashboardArtifactLinks",
            "function appendDashboardVisualEvidence",
        )
        self.assertIn("item.available !== true", artifact_links)
        self.assertIn("getSafeReportArtifactUrl(item.url)", artifact_links)
        self.assertIn('link.rel = "noopener noreferrer"', artifact_links)

    def test_factory_authority_and_downloads_only_use_dedicated_read_model(self):
        domain_router = self.block("function normalizeWorkflowDomainData", "function createWorkflowExternalSource")
        self.assertIn("state.eaFactoryReadModel.payload || {}", domain_router)
        merge = self.block("function mergeEaFactoryReadModel", "async function loadEaFactoryReadModel")
        self.assertIn("state.eaFactoryReadModel.payload = model", merge)
        self.assertIn("state.eaFactoryReadModel.lastLoadedAt = Date.now()", merge)
        self.assertIn("state.eaFactoryReadModel.stale = backendSnapshotStale", merge)
        normalizer = self.block("function normalizeEaFactoryDomain", "function normalizeWorkflowDomainData")
        self.assertIn("eaFactoryFirstArray(activeBuildRaw?.files)", normalizer)
        self.assertNotIn("root.downloads", normalizer)
        self.assertNotIn("root.artifacts", normalizer)
        self.assertNotIn("root.files", normalizer)

    def test_successful_fresh_read_clears_stale_error_but_preserves_working_action(self):
        validator = self.block("function validateEaFactoryBusyModel", "function eaFactoryBusyContext")
        merge = self.block("function mergeEaFactoryReadModel", "function mergeEaFactoryResponseReport")
        self.assertIn("const staleActionError = !actionState.inFlight", merge)
        self.assertIn('["error", "warning"].includes(state.modal.eaFactory.tone)', merge)
        self.assertIn('actionState.tone = "neutral"', merge)

        script = "\n".join([
            "const EA_FACTORY_STAGE_IDS = Object.freeze(['source','spec','generate','review','compile_validate','backtest_recheck','artifacts_report']);",
            "const EA_FACTORY_BACKEND_STAGE_BY_UI = Object.freeze({ spec:'strategy_spec', generate:'generate_source', review:'source_review', compile_validate:'compile_validate', backtest_recheck:'backtest_recheck', artifacts_report:'final_report' });",
            "const EA_FACTORY_PROP_ID = 'right_server_racks';",
            "const safeDashboardDisplayText = (value, fallback='') => String(value || fallback).slice(0, 240);",
            "const workflowDomainObject = (...values) => values.find((value) => value && typeof value === 'object' && !Array.isArray(value)) || {};",
            "const state = { eaFactoryReadModel:{payload:null,lastLoadedAt:0,stale:false,lastError:null,busy:null}, modal:{eaFactory:{inFlight:false,stageId:'generate',message:'error เก่า',tone:'error'}}, propReports:{} };",
            validator,
            merge,
            "mergeEaFactoryReadModel({eaFactory:{schemaVersion:'ea-factory-v1',busy:null}});",
            "const cleared = {...state.modal.eaFactory};",
            "state.modal.eaFactory = {inFlight:true,stageId:'one_click_run',message:'กำลังทำงาน',tone:'working'};",
            "mergeEaFactoryReadModel({eaFactory:{schemaVersion:'ea-factory-v1',busy:null}});",
            "const preserved = {...state.modal.eaFactory};",
            "process.stdout.write(JSON.stringify({cleared,preserved}));",
        ])
        completed = subprocess.run(
            [self.node_binary(), "-e", script],
            cwd=ROOT,
            capture_output=True,
            check=True,
            text=True,
            encoding="utf-8",
        )
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["cleared"]["stageId"], "")
        self.assertEqual(payload["cleared"]["message"], "")
        self.assertEqual(payload["cleared"]["tone"], "neutral")
        self.assertTrue(payload["preserved"]["inFlight"])
        self.assertEqual(payload["preserved"]["stageId"], "one_click_run")
        self.assertEqual(payload["preserved"]["message"], "กำลังทำงาน")
        self.assertEqual(payload["preserved"]["tone"], "working")

    def test_backend_stale_snapshot_disables_factory_authority_and_surfaces_refresh(self):
        validator = self.block("function validateEaFactoryBusyModel", "function eaFactoryBusyContext")
        merge = self.block("function mergeEaFactoryReadModel", "function mergeEaFactoryResponseReport")
        normalizer = self.block("function normalizeEaFactoryDomain", "function normalizeWorkflowDomainData")
        self.assertIn("const backendSnapshotStale = model.snapshotStale === true", merge)
        self.assertIn("state.eaFactoryReadModel.stale = backendSnapshotStale", merge)
        self.assertIn("กำลังรีเฟรชสถานะ EA Factory", merge)
        self.assertIn("state.eaFactoryReadModel.stale !== true", normalizer)
        self.assertIn("root.snapshotStale !== true", normalizer)

        script = "\n".join([
            "const EA_FACTORY_STAGE_IDS = Object.freeze(['source','spec','generate','review','compile_validate','backtest_recheck','artifacts_report']);",
            "const EA_FACTORY_BACKEND_STAGE_BY_UI = Object.freeze({ spec:'strategy_spec', generate:'generate_source', review:'source_review', compile_validate:'compile_validate', backtest_recheck:'backtest_recheck', artifacts_report:'final_report' });",
            "const EA_FACTORY_PROP_ID = 'right_server_racks';",
            "const safeDashboardDisplayText = (value, fallback='') => String(value || fallback).slice(0, 240);",
            "const workflowDomainObject = (...values) => values.find((value) => value && typeof value === 'object' && !Array.isArray(value)) || {};",
            "const state = { eaFactoryReadModel:{payload:null,lastLoadedAt:0,stale:false,lastError:null,busy:null}, modal:{eaFactory:{inFlight:false,stageId:'',message:'',tone:'neutral'}}, propReports:{} };",
            validator,
            merge,
            "const merged = mergeEaFactoryReadModel({eaFactory:{schemaVersion:'ea-factory-v1',snapshotStale:true,busy:null}});",
            "process.stdout.write(JSON.stringify({merged,stale:state.eaFactoryReadModel.stale,lastError:state.eaFactoryReadModel.lastError}));",
        ])
        completed = subprocess.run(
            [self.node_binary(), "-e", script],
            cwd=ROOT,
            capture_output=True,
            check=True,
            text=True,
            encoding="utf-8",
        )
        payload = json.loads(completed.stdout)
        self.assertTrue(payload["merged"])
        self.assertTrue(payload["stale"])
        self.assertEqual(payload["lastError"]["kind"], "refreshing")

    def test_dedicated_read_model_is_polled_without_overlapping_requests(self):
        loader = self.block("async function loadEaFactoryReadModel", "function setEaFactoryActionState")
        self.assertIn("state.eaFactoryReadModel.inFlight", loader)
        self.assertIn("signal?.aborted", loader)
        self.assertIn('error?.kind === "parent_abort"', loader)
        self.assertIn("const hasLastGood = Boolean(state.eaFactoryReadModel.payload)", loader)
        self.assertIn("state.eaFactoryReadModel.stale = hasLastGood", loader)
        self.assertIn('if (presentation.kind === "schema")', loader)
        self.assertEqual(loader.count("state.eaFactoryReadModel.payload = null"), 1)
        self.assertIn("eaFactoryReadModelFailurePresentation", loader)
        self.assertIn("setEaFactoryActionState", loader)
        poller = self.block("async function pollOpenPropReport", "function startMissionPolling")
        self.assertIn("factoryStageActive", poller)
        self.assertIn("factoryTtlExpired", poller)
        self.assertIn("await loadEaFactoryReadModel({ signal })", poller)
        self.assertIn("propId !== EA_FACTORY_PROP_ID && (force || reportTtlExpired)", poller)

    def test_factory_open_starts_dedicated_read_immediately_and_skips_generic_report(self):
        open_dialog = self.block("async function openPropDialog", "function setConnectionActionState")
        self.assertIn("? loadEaFactoryReadModel()", open_dialog)
        self.assertIn("? Promise.resolve(null)\n    : loadPropReport(propId)", open_dialog)
        self.assertNotIn("reportRequest.then(() => loadEaFactoryReadModel())", open_dialog)
        self.assertLess(open_dialog.index("loadEaFactoryReadModel()"), open_dialog.index("loadPropReport(propId)"))
        self.assertLess(open_dialog.index("loadEaFactoryReadModel()"), open_dialog.index("openGameModal("))

        request = self.block("async function runEaFactoryRequest", "async function syncEaFactoryGoogleSheet")
        self.assertNotIn("loadPropReport(EA_FACTORY_PROP_ID)", request)
        self.assertIn("mergeEaFactoryResponseReport(response)", request)
        self.assertIn("if (!mergeEaFactoryReadModel(response) && refreshReadModel)", request)

        global_apply = self.block("async function applyGlobalMetatraderTarget", "function renderAiTradeTerminalSummary")
        self.assertIn(".filter((target) => target.propId !== EA_FACTORY_PROP_ID)", global_apply)

    def test_fetch_timeout_and_parent_abort_are_typed_separately(self):
        fetch = self.block("class FetchTimeoutError", "function renderCodexRateReserve")
        self.assertIn('this.kind = "fetch_timeout"', fetch)
        self.assertIn('this.kind = "parent_abort"', fetch)
        self.assertIn("controller.abort(new FetchParentAbortError(path))", fetch)
        self.assertIn("controller.abort(new FetchTimeoutError(path, timeoutMs))", fetch)
        self.assertNotIn("setTimeout(() => controller.abort(), timeoutMs)", fetch)
        self.assertIn("controller.signal.reason instanceof FetchTimeoutError", fetch)
        self.assertIn("controller.signal.reason instanceof FetchParentAbortError", fetch)

        script = "\n".join([
            "const window = { setTimeout, clearTimeout };",
            "const DEFAULT_FETCH_TIMEOUT_MS = 50;",
            fetch,
            "const abortingFetch = (_path, options) => new Promise((_resolve, reject) => {",
            "  options.signal.addEventListener('abort', () => reject(options.signal.reason), { once: true });",
            "});",
            "(async () => {",
            "  globalThis.fetch = abortingFetch;",
            "  let timeoutError = null;",
            "  try { await fetchJson('/slow', { timeoutMs: 5 }); } catch (error) { timeoutError = error; }",
            "  const parent = new AbortController();",
            "  const parentRequest = fetchJson('/poll', { timeoutMs: 100, signal: parent.signal }).catch((error) => error);",
            "  parent.abort();",
            "  const parentError = await parentRequest;",
            "  globalThis.fetch = async () => ({ ok: false, status: 409, json: async () => ({",
            "    kind: 'ea_factory_busy', code: 'ea_factory_single_active_build', busy: { buildId: 'build-live' },",
            "  }) });",
            "  const httpError = await fetchJson('/busy').catch((error) => error);",
            "  process.stdout.write(JSON.stringify({",
            "    timeout: { name: timeoutError?.name, kind: timeoutError?.kind, thai: /[ก-๙]/.test(timeoutError?.message || '') },",
            "    parent: { name: parentError?.name, kind: parentError?.kind },",
            "    http: { status: httpError?.status, kind: httpError?.kind, buildId: httpError?.body?.busy?.buildId },",
            "  }));",
            "})().catch((error) => { console.error(error); process.exit(1); });",
        ])
        completed = subprocess.run(
            [self.node_binary(), "-e", script],
            cwd=ROOT,
            capture_output=True,
            check=True,
            text=True,
            encoding="utf-8",
        )
        self.assertEqual(
            json.loads(completed.stdout),
            {
                "timeout": {"name": "TimeoutError", "kind": "fetch_timeout", "thai": True},
                "parent": {"name": "AbortError", "kind": "parent_abort"},
                "http": {"status": 409, "kind": "ea_factory_busy", "buildId": "build-live"},
            },
        )

    def test_factory_posts_have_a_bounded_timeout_and_reconcile_busy_after_failure(self):
        helper = self.block("async function postEaFactoryJson", "async function runEaFactoryRequest")
        self.assertIn("EA_FACTORY_ACTION_TIMEOUT_MS", helper)
        self.assertIn("const controller = new AbortController()", helper)
        self.assertIn("controller.abort(new FetchTimeoutError(path, timeoutMs))", helper)
        self.assertIn("window.clearTimeout(timeoutId)", helper)
        request = self.block("async function runEaFactoryRequest", "async function syncEaFactoryGoogleSheet")
        self.assertIn("const refreshed = await loadEaFactoryReadModel({ forceFresh: true })", request)
        self.assertIn("state.eaFactoryReadModel.busy", request)
        self.assertIn("eaFactoryBusyPresentation(state.eaFactoryReadModel.busy)", request)
        self.assertIn("const busyClearedByFreshRead = refreshedAuthoritative", request)
        self.assertIn('failedRequestPresentation.kind === "busy"', request)
        self.assertIn('kind: "busy_reconciled"', request)
        self.assertIn("Backend ยืนยัน busy=null", request)
        self.assertIn('stageId: busyClearedByFreshRead ? "" : stageId', request)
        self.assertIn("if (refreshedAuthoritative)", request)
        self.assertIn("state.eaFactoryReadModel.lastError = null", request)
        self.assertIn("state.eaFactoryReadModel.stale = false", request)
        self.assertIn("if (state.modal.eaFactory.inFlight", request)
        self.assertIn("คำขอสิ้นสุดแล้ว", request)

        script = "\n".join([
            "const window = { setTimeout, clearTimeout };",
            "const EA_FACTORY_ACTION_TIMEOUT_MS = 20;",
            "class FetchTimeoutError extends Error { constructor(path, timeoutMs) { super(path); this.name='TimeoutError'; this.kind='fetch_timeout'; this.timeoutMs=timeoutMs; } }",
            helper,
            "globalThis.fetch = (_path, options) => new Promise((_resolve, reject) => options.signal.addEventListener('abort', () => reject(options.signal.reason), {once:true}));",
            "postEaFactoryJson('/slow', {}, {timeoutMs:5}).then(() => process.exit(2)).catch((error) => process.stdout.write(JSON.stringify({name:error.name,kind:error.kind,timeoutMs:error.timeoutMs})));",
        ])
        completed = subprocess.run(
            [self.node_binary(), "-e", script],
            cwd=ROOT,
            capture_output=True,
            check=True,
            text=True,
            encoding="utf-8",
        )
        self.assertEqual(
            json.loads(completed.stdout),
            {"name": "TimeoutError", "kind": "fetch_timeout", "timeoutMs": 5},
        )

        abort_script = "\n".join([
            "const window = { setTimeout, clearTimeout };",
            "const EA_FACTORY_ACTION_TIMEOUT_MS = 200;",
            "class FetchTimeoutError extends Error { constructor(path, timeoutMs) { super(path); this.name='TimeoutError'; this.kind='fetch_timeout'; this.timeoutMs=timeoutMs; } }",
            helper,
            "globalThis.fetch = (_path, options) => new Promise((_resolve, reject) => options.signal.addEventListener('abort', () => reject(options.signal.reason), {once:true}));",
            "const parent = new AbortController();",
            "const reason = new Error('operator stop'); reason.name='AbortError'; reason.kind='ea_factory_operator_cancelled_request';",
            "const pending = postEaFactoryJson('/slow', {}, {timeoutMs:100, signal:parent.signal});",
            "parent.abort(reason);",
            "pending.then(() => process.exit(2)).catch((error) => process.stdout.write(JSON.stringify({name:error.name,kind:error.kind})));",
        ])
        aborted = subprocess.run(
            [self.node_binary(), "-e", abort_script],
            cwd=ROOT,
            capture_output=True,
            check=True,
            text=True,
            encoding="utf-8",
        )
        self.assertEqual(
            json.loads(aborted.stdout),
            {"name": "AbortError", "kind": "ea_factory_operator_cancelled_request"},
        )

    def test_structured_factory_rejection_wins_over_generic_404_copy(self):
        presentation = self.block(
            "function eaFactoryReadModelFailurePresentation",
            "function renderEaFactoryReadModelNotice",
        )
        self.assertIn("const structuredFactoryRejection", presentation)
        self.assertIn('kind === "ea_factory_request_rejected"', presentation)
        self.assertIn('String(body.code || "").startsWith("ea_factory_")', presentation)
        self.assertLess(
            presentation.index("if (structuredFactoryRejection)"),
            presentation.index("if (status === 404)"),
        )
        self.assertIn("message: `${messageTh}${staleNote}`", presentation)

    def test_integrity_409_surfaces_backend_thai_instead_of_transport_copy(self):
        presentation = self.block(
            "function eaFactoryReadModelFailurePresentation",
            "function renderEaFactoryReadModelNotice",
        )
        message_th = (
            "Build รุ่นเดิมยังไม่ผ่านการตรวจความเข้ากันได้ของ Source profile "
            "ระบบปิดคำสั่งใหม่ไว้จนกว่าจะตรวจหลักฐานรุ่นเดิมครบ"
        )
        script = "\n".join([
            "const workflowDomainObject = (value) => value && typeof value === 'object' && !Array.isArray(value) ? value : {};",
            "const safeDashboardDisplayText = (value, fallback='') => String(value || fallback).slice(0, 600);",
            "const eaFactoryBusyContext = () => null;",
            "const eaFactoryBusyPresentation = () => ({kind:'busy'});",
            "const PROP_REPORT_FETCH_TIMEOUT_MS = 1000;",
            presentation,
            "const result = eaFactoryReadModelFailurePresentation({",
            "  status: 409,",
            "  kind: 'ea_factory_integrity_blocked',",
            "  body: {",
            "    kind: 'ea_factory_integrity_blocked',",
            "    code: 'ea_factory_artifact_integrity_failed',",
            f"    messageTh: {json.dumps(message_th, ensure_ascii=False)},",
            "  },",
            "});",
            "process.stdout.write(JSON.stringify(result));",
        ])
        completed = subprocess.run(
            [self.node_binary(), "-e", script],
            cwd=ROOT,
            capture_output=True,
            check=True,
            text=True,
            encoding="utf-8",
        )
        result = json.loads(completed.stdout)
        self.assertEqual(result["kind"], "integrity_blocked")
        self.assertEqual(result["tone"], "error")
        self.assertEqual(result["message"], message_th)
        self.assertNotIn("ติดต่อ EA Factory Backend ไม่สำเร็จ", result["message"])

    def test_current_integrity_reason_wins_over_stale_action_and_run_copy(self):
        failure = self.block("function eaFactoryReadModelFailurePresentation", "function renderEaFactoryReadModelNotice")
        action = self.block("function eaFactoryActionPresentation", "function renderEaFactoryOperationalStage")
        script = "\n".join([
            "const assert = require('node:assert/strict');",
            "const workflowDomainObject = value => value && typeof value === 'object' ? value : {};",
            "const safeDashboardDisplayText = (value, fallback='') => String(value || fallback);",
            "const eaFactoryBusyContext = () => null;",
            "const PROP_REPORT_FETCH_TIMEOUT_MS = 1000;",
            "const state = {eaFactoryReadModel:{stale:true,lastError:null}};",
            failure, action,
            "const backendMessage = 'หลักฐาน Build รุ่นเดิมยังไม่ผ่านการตรวจความเข้ากันได้ จึงยังปิดคำสั่งใหม่ไว้';",
            "state.eaFactoryReadModel.lastError = eaFactoryReadModelFailurePresentation({status:409,kind:'ea_factory_integrity_blocked',body:{kind:'ea_factory_integrity_blocked',messageTh:backendMessage}});",
            "const before = JSON.stringify(state);",
            "const result = eaFactoryActionPresentation({authoritative:false,oneClick:{run:{status:'failed',message:'ไฟล์สูญหายหรือเปลี่ยนแปลง'}}},{stageId:'one_click_run',tone:'error',message:'ไฟล์สูญหายหรือเปลี่ยนแปลง'});",
            "assert.equal(result.message, backendMessage);",
            "assert.equal(result.tone, 'error');",
            "assert.equal(JSON.stringify(state), before);",
        ])
        completed = subprocess.run([self.node_binary(), "-e", script], cwd=ROOT,
                                   capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(completed.returncode, 0, completed.stderr)

    def test_busy_post_runtime_reconciles_to_fresh_busy_null(self):
        request = self.block("async function runEaFactoryRequest", "async function syncEaFactoryGoogleSheet")
        script = "\n".join([
            "const state = { modal:{eaFactory:{inFlight:false,stageId:'',message:'',tone:'neutral'}}, eaFactoryReadModel:{payload:{schemaVersion:'ea-factory-v1'},busy:null,lastError:{kind:'busy'},stale:true} };",
            "let refreshCalls = 0;",
            "const EA_FACTORY_SUPPORTED_MODES = new Set(['one_click_with_manual_stage_recovery']);",
            "function setEaFactoryActionState(next) { Object.assign(state.modal.eaFactory, next); }",
            "function eaFactoryReadModelFailurePresentation() { return {kind:'busy',tone:'warning',title:'งานเดิม',message:'งานเดิมกำลังทำ',busy:{buildId:'old-build'}}; }",
            "async function loadEaFactoryReadModel() { refreshCalls += 1; state.eaFactoryReadModel.busy = null; return {eaFactory:{schemaVersion:'ea-factory-v1',busy:null,mode:'one_click_with_manual_stage_recovery',scheduled:false}}; }",
            "function eaFactoryBusyPresentation(busy) { return {kind:'busy',tone:'warning',title:'busy',message:String(busy.buildId),busy}; }",
            request,
            "(async () => {",
            "  const result = await runEaFactoryRequest('one_click_run', async () => { throw new Error('HTTP 409'); }, 'ok');",
            "  process.stdout.write(JSON.stringify({result,refreshCalls,action:state.modal.eaFactory,readModel:state.eaFactoryReadModel}));",
            "})().catch((error) => { console.error(error); process.exit(1); });",
        ])
        completed = subprocess.run(
            [self.node_binary(), "-e", script],
            cwd=ROOT,
            capture_output=True,
            check=True,
            text=True,
            encoding="utf-8",
        )
        payload = json.loads(completed.stdout)
        self.assertIsNone(payload["result"])
        self.assertEqual(payload["refreshCalls"], 1)
        self.assertFalse(payload["action"]["inFlight"])
        self.assertEqual(payload["action"]["stageId"], "")
        self.assertEqual(payload["action"]["tone"], "ready")
        self.assertIn("busy=null", payload["action"]["message"])
        self.assertIsNone(payload["readModel"]["busy"])
        self.assertIsNone(payload["readModel"]["lastError"])
        self.assertFalse(payload["readModel"]["stale"])

    def test_busy_409_is_thai_structured_and_blocks_new_factory_actions(self):
        helpers = self.block("function validateEaFactoryBusyModel", "function mergeEaFactoryReadModel")
        for field in ("buildId", "displayName", "stageId", "status", "activeOperation"):
            self.assertIn(field, helpers)
        self.assertIn("supportedStageIds", helpers)
        self.assertIn('stageId === "" || supportedStageIds.has(stageId)', helpers)
        self.assertIn("supportedStatuses", helpers)
        self.assertIn("supportedOperations", helpers)
        self.assertIn('body.kind === "ea_factory_busy"', helpers)
        self.assertIn('body.code === "ea_factory_single_active_build"', helpers)
        self.assertIn("ตอนนี้ยังไม่รับงานใหม่", helpers)
        self.assertNotIn("error?.message", helpers)

        normalizer = self.block("function normalizeEaFactoryDomain", "function normalizeWorkflowDomainData")
        self.assertIn("const backendBusy = workflowDomainObject(state.eaFactoryReadModel.busy)", normalizer)
        self.assertIn("applyEaFactoryStageAdmission(stage, authoritative, backendBusyActive)", normalizer)
        buttons = self.block("function createEaFactoryActionButton", "function renderEaFactoryStatusStrip")
        self.assertIn("Boolean(state.eaFactoryReadModel.busy)", buttons)
        self.assertIn("disabled || requestBusy || backendBusy", buttons)

    def test_manual_stage_admission_fails_closed_for_stale_and_busy_models(self):
        helper = self.block(
            "function applyEaFactoryStageAdmission",
            "function normalizeEaFactoryDomain",
        )
        script = "\n".join([
            helper,
            "const stage = {id:'generate',canRun:true,canRetry:true};",
            "const pick = (authoritative,busy) => {",
            "  const value = applyEaFactoryStageAdmission(stage,authoritative,busy);",
            "  return {canRun:value.canRun,canRetry:value.canRetry};",
            "};",
            "process.stdout.write(JSON.stringify({",
            "  ready:pick(true,false), stale:pick(false,false), busy:pick(true,true), both:pick(false,true),",
            "}));",
        ])
        completed = subprocess.run(
            [self.node_binary(), "-e", script],
            cwd=ROOT,
            capture_output=True,
            check=True,
            text=True,
            encoding="utf-8",
        )
        self.assertEqual(
            json.loads(completed.stdout),
            {
                "ready": {"canRun": True, "canRetry": True},
                "stale": {"canRun": False, "canRetry": False},
                "busy": {"canRun": False, "canRetry": False},
                "both": {"canRun": False, "canRetry": False},
            },
        )

    def test_successful_poll_retains_validated_backend_busy_until_backend_clears_it(self):
        validator = self.block("function validateEaFactoryBusyModel", "function eaFactoryBusyContext")
        merge = self.block("function mergeEaFactoryReadModel", "function mergeEaFactoryResponseReport")
        self.assertIn("validateEaFactoryBusyModel(model.busy)", merge)
        self.assertIn("if (!busyValidation.valid) return false", merge)
        self.assertIn("state.eaFactoryReadModel.busy = busyValidation.busy", merge)
        self.assertNotIn("state.eaFactoryReadModel.busy = null", merge)

        script = "\n".join([
            "const EA_FACTORY_STAGE_IDS = Object.freeze(['source','spec','generate','review','compile_validate','backtest_recheck','artifacts_report']);",
            "const EA_FACTORY_BACKEND_STAGE_BY_UI = Object.freeze({ spec:'strategy_spec', generate:'generate_source', review:'source_review', compile_validate:'compile_validate', backtest_recheck:'backtest_recheck', artifacts_report:'final_report' });",
            "const EA_FACTORY_PROP_ID = 'right_server_racks';",
            "const safeDashboardDisplayText = (value, fallback='') => String(value || fallback).slice(0, 240);",
            "const workflowDomainObject = (...values) => values.find((value) => value && typeof value === 'object' && !Array.isArray(value)) || {};",
            "const state = { eaFactoryReadModel: { payload:null,lastLoadedAt:0,stale:false,lastError:null,busy:null }, modal:{eaFactory:{stageId:'',message:'',tone:'neutral'}}, propReports:{} };",
            validator,
            merge,
            "const liveBusy = { buildId:'ea-build-live-1', displayName:'งานทดสอบ', stageId:'generate_source', status:'running', activeOperation:'generate_source' };",
            "const first = mergeEaFactoryReadModel({ eaFactory:{ schemaVersion:'ea-factory-v1', busy:liveBusy } });",
            "const kept = state.eaFactoryReadModel.busy;",
            "const edge = validateEaFactoryBusyModel({...liveBusy, stageId:null, activeOperation:'one_click_run'});",
            "const invalid = mergeEaFactoryReadModel({ eaFactory:{ schemaVersion:'ea-factory-v1', busy:{...liveBusy, activeOperation:'unknown_raw_operation'} } });",
            "const afterInvalid = state.eaFactoryReadModel.busy;",
            "const cleared = mergeEaFactoryReadModel({ eaFactory:{ schemaVersion:'ea-factory-v1', busy:null } });",
            "process.stdout.write(JSON.stringify({first,kept,edge,invalid,afterInvalid,cleared,finalBusy:state.eaFactoryReadModel.busy}));",
        ])
        completed = subprocess.run(
            [self.node_binary(), "-e", script],
            cwd=ROOT,
            capture_output=True,
            check=True,
            text=True,
            encoding="utf-8",
        )
        payload = json.loads(completed.stdout)
        self.assertTrue(payload["first"])
        self.assertEqual(payload["kept"]["buildId"], "ea-build-live-1")
        self.assertTrue(payload["edge"]["valid"])
        self.assertEqual(payload["edge"]["busy"]["stageId"], "")
        self.assertFalse(payload["invalid"])
        self.assertEqual(payload["afterInvalid"]["activeOperation"], "generate_source")
        self.assertTrue(payload["cleared"])
        self.assertIsNone(payload["finalBusy"])

    def test_timeout_or_transport_failure_keeps_last_good_payload_as_stale(self):
        state = self.block("eaFactoryReadModel: {", "todayWorkView:")
        self.assertIn("stale: false", state)
        self.assertIn("lastError: null", state)
        self.assertIn("busy: null", state)
        loader = self.block("async function loadEaFactoryReadModel", "function setEaFactoryActionState")
        catch_start = loader.index("} catch (error) {")
        catch_block = loader[catch_start:]
        stale_assignment = catch_block.index("state.eaFactoryReadModel.stale = hasLastGood")
        schema_clear = catch_block.index("state.eaFactoryReadModel.payload = null")
        self.assertGreater(stale_assignment, schema_clear)
        self.assertIn("state.eaFactoryReadModel.lastError = {", catch_block)
        notice = self.block("function renderEaFactoryReadModelNotice", "function mergeEaFactoryReadModel")
        self.assertIn("readModelState.stale", notice)
        self.assertIn("ข้อมูลล่าสุดที่เก็บไว้เมื่อ", notice)

        presentation = self.block(
            "function eaFactoryReadModelFailurePresentation",
            "function renderEaFactoryReadModelNotice",
        )
        script = "\n".join([
            "const PROP_REPORT_FETCH_TIMEOUT_MS = 20000;",
            "const workflowDomainObject = (...values) => values.find((value) => value && typeof value === 'object' && !Array.isArray(value)) || {};",
            "const safeDashboardDisplayText = (value,fallback='') => String(value || fallback);",
            "const eaFactoryBusyContext = () => null;",
            presentation,
            "const result = eaFactoryReadModelFailurePresentation({status:503,kind:'transport',message:'connect ECONNREFUSED 127.0.0.1:8765'},{hasLastGood:true});",
            "process.stdout.write(JSON.stringify(result));",
        ])
        completed = subprocess.run(
            [self.node_binary(), "-e", script],
            cwd=ROOT,
            capture_output=True,
            check=True,
            text=True,
            encoding="utf-8",
        )
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["kind"], "transport")
        self.assertIn("connect ECONNREFUSED 127.0.0.1:8765", payload["message"])
        self.assertIn("ข้อมูลล่าสุด", payload["message"])

    def test_stage_request_is_accepted_before_it_is_truthfully_completed(self):
        stage_normalizer = self.block("function normalizeEaFactoryStageStatus", "function normalizeEaFactoryTerminal")
        self.assertIn("reconcileEaFactoryStageWithMission", stage_normalizer)
        self.assertIn("historical Mission state", stage_normalizer)
        self.assertIn('["completed", "not_applicable", "failed", "blocked", "cancelled", "skipped"]', stage_normalizer)
        self.assertIn("mission.workStatus", stage_normalizer)
        self.assertIn('"invalid_output"', stage_normalizer)
        self.assertIn("failureCode", stage_normalizer)

    def test_visual_progress_keeps_completed_gates_green_and_marks_the_actual_failed_stage(self):
        mission_reconciliation = self.block(
            "function normalizeEaFactoryStageStatus",
            "function normalizeEaFactoryTerminal",
        )
        progress = self.block("function eaFactoryPhaseGateProgress", "function stopEaFactoryActiveProgressPolling")
        stage_status = self.block("function eaFactoryOneClickStageStatus", "function eaFactoryExistingOneClickAdmission")
        visual_state = self.block("function eaFactoryCurrentVisualStageId", "function createEaFactoryGameAction")
        delivery_helpers = self.block("function eaFactoryCertifiedDeliveryCompleted", "function eaFactoryPageStatus")
        script = "\n".join([
            "const EA_FACTORY_STAGE_IDS=['source','spec','generate','review','compile_validate','backtest_recheck','artifacts_report'];",
            "const EA_FACTORY_BACKEND_STAGE_BY_UI={spec:'strategy_spec',generate:'generate_source',review:'source_review',compile_validate:'compile_validate',backtest_recheck:'backtest_recheck',artifacts_report:'final_report'};",
            "const EA_FACTORY_UI_STAGE_BY_BACKEND=Object.fromEntries(Object.entries(EA_FACTORY_BACKEND_STAGE_BY_UI).map(([ui,backend])=>[backend,ui]));",
            "const EA_FACTORY_VISUAL_STAGE_IDS=['generate','review','compile_validate','backtest_recheck','artifacts_report'];",
            "const EA_FACTORY_STAGE_COPY={compile_validate:{titleTh:'Compile'}};",
            "const state={missions:[{id:'mission-generate',status:'failed',workStatus:'invalid_output'}],modal:{eaFactory:{inFlight:false}}};",
            "const safeDashboardDisplayText=(value,fallback='')=>String(value || fallback);",
            "const eaFactoryFirstArray=(...values)=>values.find(Array.isArray)||[];",
            mission_reconciliation,
            delivery_helpers,
            stage_status,
            progress,
            visual_state,
            "const completedGenerate=normalizeEaFactoryStage({id:'generate_source',status:'completed',missionId:'mission-generate'});",
            "const domain={authoritative:true,backendBusy:{stageId:'generate_source'},oneClick:{run:{status:'failed',currentStageId:'compile_validate',progressPercent:0,progressStageIndex:0,progressStageCount:5,stageResults:[{stageId:'generate',status:'completed'},{stageId:'review',status:'completed'},{stageId:'compile_validate',status:'locked'}]}},stages:[completedGenerate,{id:'review',status:'completed'},{id:'compile_validate',status:'locked'},{id:'backtest_recheck',status:'locked'},{id:'artifacts_report',status:'locked'}],currentStageId:'generate'};",
            "const gate=eaFactoryPhaseGateProgress(domain);",
            "const current=eaFactoryCurrentVisualStageId(domain);",
            "process.stdout.write(JSON.stringify({generate:completedGenerate.status,stageIndex:gate.stageIndex,current,generateVisual:eaFactoryVisualStageStatus(domain,'generate',current,gate),reviewVisual:eaFactoryVisualStageStatus(domain,'review',current,gate),compileVisual:eaFactoryVisualStageStatus(domain,'compile_validate',current,gate)}));",
        ])
        completed = subprocess.run(
            [self.node_binary(), "-e", script],
            cwd=ROOT,
            capture_output=True,
            check=True,
            text=True,
            encoding="utf-8",
        )
        self.assertEqual(
            json.loads(completed.stdout),
            {
                "generate": "completed",
                "stageIndex": 2,
                "current": "compile_validate",
                "generateVisual": "completed",
                "reviewVisual": "completed",
                "compileVisual": "failed",
            },
        )

        presentation = self.block("function eaFactoryActionPresentation", "function renderEaFactoryOperationalStage")
        self.assertIn('tone: "working"', presentation)
        self.assertIn("คำขอถูกบันทึกแล้ว แต่ยังไม่ถือว่าสำเร็จ", presentation)
        self.assertIn('tone: "error"', presentation)
        self.assertIn("ขั้นนี้ไม่สำเร็จ", presentation)
        self.assertIn('stage.status === "completed"', presentation)

        request = self.block("async function runEaFactoryRequest", "async function syncEaFactoryGoogleSheet")
        self.assertIn("terminalAware", request)
        self.assertIn("Local Runner รับคำขอแล้ว • กำลังรอผลตรวจจาก Backend", request)
        self.assertIn("eaFactoryActionPresentation", request)

    def test_invalid_generation_output_shows_validator_findings_and_fresh_retry(self):
        diagnostics = self.block("function eaFactoryReportForStage", "function createEaFactoryActionButton")
        self.assertIn("mission?.reportIds", diagnostics)
        self.assertIn("item?.linkedMissionId", diagnostics)
        self.assertIn("workflowOutput.missingFields", diagnostics)
        self.assertIn("workflowOutput.missingEvidenceKinds", diagnostics)
        self.assertIn("semanticRepair.remainingIssues", diagnostics)
        self.assertIn("รายละเอียดที่ Backend Validator ปฏิเสธ", diagnostics)
        self.assertIn('document.createElement("details")', diagnostics)
        self.assertIn('document.createElement("summary")', diagnostics)
        self.assertIn("panel.open = !terminalFailure", diagnostics)
        self.assertIn("ดูรายละเอียด Validator", diagnostics)

        retry_guard = self.block("function eaFactoryRetryableInvalidOutput", "function eaFactoryActionPresentation")
        self.assertIn('stage?.backendId !== "generate_source"', retry_guard)
        self.assertIn("stage?.canRetry !== true", retry_guard)
        self.assertIn('stage.failureCode !== "invalid_output"', retry_guard)
        self.assertIn("versions.length === 0", retry_guard)
        self.assertIn("!hasSourceArtifact", retry_guard)

        operational = self.block("function renderEaFactoryOperationalStage", "function renderEaFactoryPanel")
        self.assertIn("eaFactoryRetryableInvalidOutput(domain, stage)", operational)
        self.assertIn("ลองใหม่ได้อีก ${retriesRemaining} ครั้ง", operational)
        self.assertIn("สร้าง Codex Mission ใหม่และใช้เครดิต Codex เพิ่ม", operational)
        self.assertIn("จะไม่เขียนทับ Version ใด ๆ", operational)
        self.assertIn("สร้าง Codex Mission ใหม่เพื่อลอง Source อีกครั้ง", operational)
        self.assertIn("retryEaFactoryStage(stageId)", operational)
        self.assertIn("stage.retryAttemptCount", operational)
        self.assertIn("stage.retryAttemptLimit", operational)
        self.assertLess(
            operational.index("if (eaFactoryRetryableInvalidOutput(domain, stage))"),
            operational.index("appendEaFactoryBoundReport(section, report, stage)"),
        )

        actions = self.block("async function advanceEaFactoryStage", "function connectionHubStatusGroup")
        self.assertIn("async function retryEaFactoryStage", actions)
        self.assertEqual(actions.count("if (\n    domain.authoritative !== true"), 2)
        self.assertEqual(actions.count("|| Boolean(domain.backendBusy)"), 2)
        self.assertEqual(actions.count("|| state.modal.eaFactory.inFlight"), 2)
        self.assertEqual(actions.count('messageKind: "local_preflight_rejected"'), 2)
        self.assertEqual(actions.count("setEaFactoryActionState({"), 2)
        self.assertIn("/retry`", actions)
        self.assertIn("failedMissionId: stage.missionId", actions)
        self.assertIn("eaFactoryRetryableInvalidOutput(domain, stage)", actions)
        self.assertIn('{ terminalAware: true }', actions)
        self.assertIn("raw?.canRetry === true", self.main)
        self.assertIn('.ea-factory-bound-report[data-tone="error"]', self.styles)
        self.assertIn('.ea-factory-bound-report > summary', self.styles)

    def test_advance_and_retry_preflight_rejections_are_visible_without_posting(self):
        actions = self.block("async function advanceEaFactoryStage", "function connectionHubStatusGroup")
        script = "\n".join([
            "const EA_FACTORY_PROP_ID = 'right_server_racks';",
            "const EA_FACTORY_READ_MODEL_MAX_AGE_MS = 90000;",
            "const EA_FACTORY_SUPPORTED_MODES = new Set(['one_click_with_manual_stage_recovery','manual_stage_by_stage']);",
            "const EA_FACTORY_STAGE_COPY = {};",
            "const state = {eaFactoryReadModel:{payload:{schemaVersion:'ea-factory-v1',mode:'one_click_with_manual_stage_recovery',scheduled:false}},propReports:{right_server_racks:{}},modal:{eaFactory:{inFlight:false}}};",
            "const getModalSubject = () => ({id:EA_FACTORY_PROP_ID});",
            "const getPropertyRole = () => ({});",
            "const workflowDomainObject = (...values) => values.find((value) => value && typeof value === 'object' && !Array.isArray(value)) || {};",
            "const eaFactoryFirstArray = (...values) => values.find(Array.isArray) || [];",
            self.block("function eaFactoryReadModelStateKey", "function mergeEaFactoryReadModel"),
            "let mode = 'advance';",
            "const normalizeWorkflowDashboard = () => mode === 'advance'",
            "  ? {domainData:{eaFactory:{authoritative:false,backendBusy:false,currentStageId:'spec',activeBuild:{id:'build-1'},stages:[{id:'spec',backendId:'strategy_spec',canRun:true}]}}}",
            "  : {domainData:{eaFactory:{authoritative:true,backendBusy:true,currentStageId:'generate',activeBuild:{id:'build-1'},stages:[{id:'generate',backendId:'generate_source',missionId:'mission-1',canRetry:true,failureCode:'invalid_output'}]}}};",
            "const eaFactoryRetryableInvalidOutput = () => true;",
            "const createWorkflowIdempotencyKey = () => 'unused';",
            "let postCount = 0;",
            "const postEaFactoryJson = async () => { postCount += 1; return {}; };",
            "const runEaFactoryRequest = async () => { postCount += 1; return {}; };",
            "function setEaFactoryActionState(next={}) { Object.assign(state.modal.eaFactory,next); }",
            actions,
            "(async () => {",
            "  const advanceResult = await advanceEaFactoryStage('spec');",
            "  const advanceAction = {...state.modal.eaFactory};",
            "  mode = 'retry';",
            "  const retryResult = await retryEaFactoryStage('generate');",
            "  const retryAction = {...state.modal.eaFactory};",
            "  process.stdout.write(JSON.stringify({advanceResult,retryResult,advanceAction,retryAction,postCount}));",
            "})().catch((error) => { console.error(error); process.exit(1); });",
        ])
        completed = subprocess.run(
            [self.node_binary(), "-e", script],
            cwd=ROOT,
            capture_output=True,
            check=True,
            text=True,
            encoding="utf-8",
        )
        payload = json.loads(completed.stdout)
        self.assertIsNone(payload["advanceResult"])
        self.assertIsNone(payload["retryResult"])
        self.assertEqual(payload["postCount"], 0)
        self.assertEqual(payload["advanceAction"]["messageKind"], "local_preflight_rejected")
        self.assertEqual(payload["retryAction"]["messageKind"], "local_preflight_rejected")
        self.assertTrue(payload["advanceAction"]["readModelStateKey"])
        self.assertTrue(payload["retryAction"]["readModelStateKey"])
        self.assertIn("Read Model", payload["advanceAction"]["message"])
        self.assertIn("กำลังทำอยู่", payload["retryAction"]["message"])

    def test_invalid_output_retry_policy_executes_live_read_model_matrix(self):
        node = shutil.which("node")
        if not node:
            self.skipTest("Node.js is required to execute the frontend retry policy")

        first_array = self.block("function eaFactoryFirstArray", "function normalizeEaFactoryPlatform")
        retry_guard = self.block("function eaFactoryRetryableInvalidOutput", "function eaFactoryActionPresentation")
        script = f"""
const assert = require("node:assert/strict");
const vm = require("node:vm");
const sandbox = {{}};
vm.createContext(sandbox);
vm.runInContext({json.dumps(first_array + retry_guard)}, sandbox);
const canRetry = sandbox.eaFactoryRetryableInvalidOutput;

const liveStage = {{
  backendId: "generate_source",
  status: "failed",
  failureCode: "invalid_output",
  canRetry: true,
  retryAttemptCount: 0,
  retryAttemptLimit: 3,
}};
const liveDomain = {{
  activeBuild: {{
    id: "ea-build-1789123053951-6b18ad",
    version: "",
    raw: {{ versions: [] }},
    artifacts: [{{
      fileName: "strategy-spec-v01.json",
      kind: "strategy_spec",
    }}],
  }},
}};

assert.equal(canRetry(liveDomain, liveStage), true, "source-less invalid_output must show Retry");
assert.equal(canRetry(liveDomain, {{ ...liveStage, canRetry: false, retryAttemptCount: 3 }}), false,
  "retry-exhausted backend state must hide Retry");
assert.equal(canRetry({{
  activeBuild: {{
    ...liveDomain.activeBuild,
    artifacts: [{{ fileName: "CAN_SLIM.mq4", kind: "source_code" }}],
  }},
}}, liveStage), false, "an existing Source artifact must hide Retry");
assert.equal(canRetry(liveDomain, {{ ...liveStage, backendId: "source_review" }}), false,
  "Source Review failures must never replay an immutable Source/Version");
assert.equal(canRetry({{
  activeBuild: {{
    id: "ea-build-history-v1",
    version: "v1",
    raw: {{ versions: [{{ version: 1 }}] }},
    artifacts: [],
  }},
}}, liveStage), false, "a history-selected versioned Build must hide Retry");
"""
        completed = subprocess.run(
            [node, "-e", script],
            cwd=ROOT,
            capture_output=True,
            check=False,
            text=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr or completed.stdout)

    def test_one_click_read_model_is_build_bound_and_resumable_after_reload(self):
        constants = self.block("const EA_FACTORY_ONE_CLICK_STAGE_IDS", "const EA_FACTORY_STAGE_COPY")

        def stage_ids(constant_name):
            match = re.search(
                rf"const {constant_name} = Object\.freeze\(\[([\s\S]*?)\]\);",
                constants,
            )
            self.assertIsNotNone(match)
            return re.findall(r'"([a-z_]+)"', match.group(1))

        self.assertEqual(
            stage_ids("EA_FACTORY_ONE_CLICK_STAGE_IDS"),
            ["generate", "review", "compile_validate", "backtest_recheck"],
        )
        self.assertEqual(
            stage_ids("EA_FACTORY_VISUAL_STAGE_IDS"),
            [
                "generate",
                "review",
                "compile_validate",
                "backtest_recheck",
                "artifacts_report",
            ],
        )
        normalizer = self.block("function normalizeEaFactoryOneClickRun", "function normalizeEaFactoryAudit")
        for status in (
            "waiting_ai",
            "awaiting_visible_terminal",
            "blocked",
            "failed",
            "completed",
        ):
            self.assertIn(f'"{status}"', normalizer)
        self.assertIn("raw.idempotencyKey || raw.resumeKey", normalizer)
        self.assertIn('runId: String(raw.runId || "").trim()', normalizer)
        self.assertIn('requestedResumeKind === "visible_terminal"', normalizer)
        self.assertIn('canResume: raw.canResume === true && resumeKind === "visible_terminal"', normalizer)
        self.assertIn("canRetry: raw.canRetry === true && !unsupportedResumeKind", normalizer)
        self.assertNotIn("normalizeEaFactoryOptimizationHandoff", normalizer)
        self.assertNotIn("optimizationProgressPercent", normalizer)
        self.assertNotIn("optimizationHandoff", normalizer)
        self.assertIn("stageResults:", normalizer)

        domain = self.block("function normalizeEaFactoryDomain", "function normalizeWorkflowDomainData")
        self.assertIn("oneClickRun: normalizeEaFactoryOneClickRun(activeBuildRaw?.oneClickRun)", domain)
        self.assertIn("const oneClickCapability = workflowDomainObject(root.oneClick)", domain)
        self.assertIn("oneClickCapability.selectedPlatform || globalSelectedTerminal?.platform", domain)
        self.assertIn("canCreateAndRun: oneClickCapability.canCreateAndRun === true", domain)
        self.assertIn("visibleAdapterConnected: oneClickCapability.visibleAdapterConnected === true", domain)
        self.assertIn("supportedVisiblePlatforms: oneClickVisiblePlatforms", domain)
        self.assertIn("selectedPlatformSupported:", domain)
        self.assertIn("terminalRunning: oneClickCapability.terminalRunning === true", domain)
        self.assertIn("terminalProcessLaunchAllowed: oneClickCapability.terminalProcessLaunchAllowed === true", domain)

    def test_one_click_truth_gate_remains_while_page_two_is_visual_only(self):
        one_click = self.block("function eaFactoryOneClickStatusLabel", "function eaFactoryRetryableInvalidOutput")
        for text in (
            "1 AI เขียน EA",
            "2 ตรวจ Source และเงื่อนไข",
            "3 เปิด MetaEditor และ Compile",
            "4 เปิด ${platformLabel} ทำ Visual Backtest",
            "Strategy Brief 10 ช่อง",
            "6 กลุ่ม",
            "Visual mode",
            "ไม่ใช้ผลหลังบ้านมาอ้างว่าผ่าน",
        ):
            self.assertIn(text, one_click)
        self.assertIn("EA_FACTORY_ONE_CLICK_STAGE_IDS.forEach", one_click)
        self.assertIn("stageResult.missionId", one_click)
        self.assertIn("stageResult.reportId", one_click)
        self.assertIn("หลักฐาน ${stageResult.evidence.length} รายการ", one_click)
        self.assertIn('status === "awaiting_visible_terminal"', one_click)
        self.assertNotIn('resumeKind === "optimization_handoff"', one_click)
        self.assertNotIn("optimizationHandoffResumable", one_click)
        self.assertNotIn("optimizationHandoff", one_click)
        self.assertIn('["failed", "blocked"].includes(status) && capability.canRetry === true', one_click)
        self.assertIn("capability.selectedPlatform === domain.activeBuild?.platform", one_click)
        self.assertIn("Retry จากปุ่มนี้ไม่ได้ • เปิดขั้นละเอียด", one_click)
        self.assertIn('appendEaFactoryFact(facts, "One-click Run", run.runId)', one_click)
        self.assertIn("capability.visibleAdapterConnected", one_click)
        self.assertIn("Array.isArray(capability.supportedVisiblePlatforms)", one_click)
        self.assertIn("capability.supportedVisiblePlatforms.includes(domain.activeBuild?.platform)", one_click)
        self.assertIn('if (!["mt4", "mt5"].includes(platform)) return', one_click)
        self.assertIn("Backend ยังไม่อนุญาต One-click สำหรับ ${platformLabel}", one_click)
        self.assertNotIn("One-click แบบหน้าต่างจริงยังไม่รองรับ MT5", one_click)
        self.assertNotIn('const platformReady = domain.activeBuild?.platform === "mt4"', one_click)
        self.assertIn("capability.terminalReady === true", one_click)
        self.assertIn("capability.terminalRunning === true", one_click)
        self.assertIn("capability.visibleAdapterConnected === true", one_click)
        self.assertIn("capability.terminalProcessLaunchAllowed === false", one_click)
        self.assertIn("function eaFactoryExistingOneClickAdmission", one_click)
        self.assertIn("domain.authoritative === true", one_click)
        self.assertIn("!domain.backendBusy", one_click)
        self.assertIn("!requestInFlight", one_click)
        self.assertIn("Read Model ล่าสุดยังไม่ได้รับการยืนยันจาก Backend", one_click)
        self.assertIn("ปุ่ม One-click ของ Build นี้จะเปิดเมื่อ Backend ยืนยันว่า busy=null", one_click)
        self.assertIn("ปุ่มปิดไว้เพื่อป้องกันการส่งคำขอซ้ำ", one_click)
        self.assertNotIn("สำเร็จอัตโนมัติ", one_click)

        progress = self.block("function renderEaFactoryProgressPage", "function renderEaFactoryResultPage")
        self.assertEqual(
            progress.count("renderEaFactoryGameProgressPanel(section, domain)"),
            1,
        )
        for forbidden in (
            "renderEaFactoryOneClickPanel",
            "renderEaFactoryOperationalStage",
            "renderEaFactoryTerminalPicker",
            'document.createElement("form")',
            'document.createElement("textarea")',
            'document.createElement("input")',
            'document.createElement("select")',
            'document.createElement("details")',
        ):
            self.assertNotIn(forbidden, progress)

        visual_panel = self.block(
            "function renderEaFactoryGameProgressPanel",
            "function renderEaFactoryOneClickSetup",
        )
        self.assertIn("EA_FACTORY_VISUAL_STAGE_IDS.forEach", visual_panel)
        self.assertIn("createEaFactoryStopButton(domain)", visual_panel)
        for forbidden in (
            "renderEaFactoryOneClickPanel",
            "renderEaFactoryOperationalStage",
            "renderEaFactoryTerminalPicker",
            "createEaFactoryActionButton",
            "advanceEaFactoryStage",
            "retryEaFactoryStage",
            'document.createElement("form")',
            'document.createElement("textarea")',
            'document.createElement("input")',
            'document.createElement("select")',
            'document.createElement("details")',
        ):
            self.assertNotIn(forbidden, visual_panel)

        panel = self.block("function renderEaFactoryPanel", "function validateEaFactoryBusyModel")
        self.assertIn(
            'else if (tabId === "progress") renderEaFactoryProgressPage(section, domain, report)',
            panel,
        )
        self.assertNotIn("renderEaFactoryOneClickPanel", panel)
        self.assertNotIn("renderEaFactoryOperationalStage", panel)

    def test_existing_one_click_admission_fails_closed_for_stale_busy_and_inflight_models(self):
        helper = self.block(
            "function eaFactoryExistingOneClickAdmission",
            "function renderEaFactoryOneClickPanel",
        )
        script = "\n".join([
            "const state = {modal:{eaFactory:{inFlight:false}}};",
            helper,
            "const base = {",
            "  authoritative:true, backendBusy:null, currentStageId:'generate',",
            "  activeBuild:{platform:'mt4'}, stages:[{id:'generate',status:'ready'}],",
            "  oneClick:{enabled:true,canRun:true,selectedTerminalId:'mt4-a',selectedPlatform:'mt4',",
            "    supportedVisiblePlatforms:['mt4','mt5'],selectedPlatformSupported:true,terminalReady:true,",
            "    terminalRunning:true,visibleAdapterConnected:true,terminalProcessLaunchAllowed:false,run:{status:'idle'}},",
            "};",
            "const can = (patch={}) => eaFactoryExistingOneClickAdmission({...base,...patch}).canSubmit;",
            "const result = {",
            "  ready:can(),",
            "  stale:can({authoritative:false}),",
            "  busy:can({backendBusy:{buildId:'ea-build-live'}}),",
            "  launchAllowed:can({oneClick:{...base.oneClick,terminalProcessLaunchAllowed:true}}),",
            "  missingCapability:can({oneClick:{...base.oneClick,supportedVisiblePlatforms:undefined}}),",
            "  mt5:can({activeBuild:{platform:'mt5'},oneClick:{...base.oneClick,selectedTerminalId:'mt5-a',selectedPlatform:'mt5'}}),",
            "  resumableMt5:can({activeBuild:{platform:'mt5'},oneClick:{...base.oneClick,canResume:true,selectedTerminalId:'mt5-a',selectedPlatform:'mt5',run:{status:'awaiting_visible_terminal',currentStageId:'compile_validate',resumeKind:'visible_terminal'}}}),",
            "  retryableMt5:can({activeBuild:{platform:'mt5'},oneClick:{...base.oneClick,canRetry:true,selectedTerminalId:'mt5-a',selectedPlatform:'mt5',run:{status:'failed',currentStageId:'compile_validate',failureCode:'visible_terminal_required'}}}),",
            "  unsupportedOptimizationResume:can({activeBuild:{platform:'mt5'},oneClick:{...base.oneClick,canResume:true,selectedTerminalId:'mt5-a',selectedPlatform:'mt5',run:{status:'failed',currentStageId:'',failureCode:'optimization_busy',resumeKind:'optimization_handoff'}}}),",
            "  ordinaryFailed:can({activeBuild:{platform:'mt5'},oneClick:{...base.oneClick,canResume:false,selectedTerminalId:'mt5-a',selectedPlatform:'mt5',run:{status:'failed',currentStageId:'',failureCode:'immutable_source_invalid'}}}),",
            "  resumableMt5Busy:can({activeBuild:{platform:'mt5'},backendBusy:{buildId:'ea-build-live'},oneClick:{...base.oneClick,canResume:true,selectedTerminalId:'mt5-a',selectedPlatform:'mt5',run:{status:'awaiting_visible_terminal',currentStageId:'compile_validate',resumeKind:'visible_terminal'}}}),",
            "  ordinaryQueued:can({oneClick:{...base.oneClick,run:{status:'queued'}}}),",
            "};",
            "state.modal.eaFactory.inFlight = true;",
            "result.inFlight = can();",
            "process.stdout.write(JSON.stringify(result));",
        ])
        completed = subprocess.run(
            [self.node_binary(), "-e", script],
            cwd=ROOT,
            capture_output=True,
            check=True,
            text=True,
            encoding="utf-8",
        )
        self.assertEqual(
            json.loads(completed.stdout),
            {
                "ready": True,
                "stale": False,
                "busy": False,
                "launchAllowed": False,
                "missingCapability": False,
                "mt5": True,
                "resumableMt5": True,
                "retryableMt5": True,
                "unsupportedOptimizationResume": False,
                "ordinaryFailed": False,
                "resumableMt5Busy": False,
                "ordinaryQueued": False,
                "inFlight": False,
            },
        )

    def test_progress_page_is_single_visual_surface_and_create_opens_page_two(self):
        progress = self.block("function renderEaFactoryProgressPage", "function renderEaFactoryResultPage")
        self.assertIn("ยังไม่มีงานที่กำลังสร้าง", progress)
        self.assertIn("กำลังรับข้อมูลงานจาก Local Runner", progress)
        self.assertIn("รายละเอียด Build ยังซิงก์มาไม่ครบ", progress)
        self.assertIn("หน้านี้จะอัปเดตให้อัตโนมัติ", progress)
        self.assertEqual(
            progress.count("renderEaFactoryGameProgressPanel(section, domain)"),
            1,
        )
        self.assertNotIn("renderEaFactoryOneClickPanel", progress)
        self.assertNotIn("renderEaFactoryOperationalStage", progress)

        source = self.block("function renderEaFactorySourceStage", "function renderEaFactorySpecStage")
        result = self.block("function renderEaFactoryResultPage", "function renderEaFactoryPanel")
        self.assertNotIn("renderEaFactoryOneClickPanel", source)
        self.assertNotIn("renderEaFactoryGameProgressPanel", source)
        self.assertNotIn("renderEaFactoryGameProgressPanel", result)

        create = self.block("async function createEaFactoryBuild", "function eaFactoryOneClickRequestKey")
        self.assertIn("!domain.authoritative", create)
        self.assertIn("Boolean(domain.backendBusy)", create)
        self.assertIn("domain.canStartNewBuild !== true", create)
        self.assertIn("state.modal.eaFactory.selectedBuildId = buildId", create)
        self.assertIn('setWorkflowDashboardTab(EA_FACTORY_PROP_ID, "progress")', create)
        self.assertIn("persists the selected page snapshot", create)
        navigation = self.block("function setWorkflowDashboardTab", "function workflowActionFormPayload")
        self.assertIn("renderWorkflowDashboard(subject, propertyRole, report)", navigation)
        self.assertIn("saveSessionSnapshot()", navigation)

    def test_successful_create_immediately_invokes_progress_navigation(self):
        receipt_wait = self.block("async function waitForEaFactoryAuthoritativeReceipt", "async function createEaFactoryCustomSourceAndStart")
        create_identity = self.block(
            "function eaFactoryCreateBuildFormSignature",
            "async function createEaFactoryBuild",
        )
        create = self.block("async function createEaFactoryBuild", "function eaFactoryOneClickRequestKey")
        script = "\n".join([
            "const EA_FACTORY_PROP_ID = 'right_server_racks';",
            "const EA_FACTORY_SUPPORTED_MODES=new Set(['one_click_with_manual_stage_recovery']); let eaFactoryActiveActionAbortController=null; const window={setTimeout,clearTimeout};",
            "const state = {eaFactoryReadModel:{payload:{},stale:false},propReports:{right_server_racks:{}},modal:{open:true,id:EA_FACTORY_PROP_ID,eaFactory:{selectedBuildId:'',selectedArtifactKind:'',selectedPlatform:'',createIdempotencyKey:'',createFormSignature:''}}};",
            "const normalizeEaFactoryArtifactKind = (value) => value;",
            "const normalizeEaFactoryPlatform = (value) => value;",
            "const eaFactoryCreateSourceBinding = () => ({required:false,ready:true,fields:{}});",
            "const getModalSubject = () => ({id:EA_FACTORY_PROP_ID});",
            "const getPropertyRole = () => ({});",
            "const normalizeWorkflowDashboard = () => ({domainData:{eaFactory:{authoritative:true,backendBusy:null,canStartNewBuild:true,sourceCatalog:{records:[{sourceRecordId:'source-1',recordDigest:'a'.repeat(64),buildReady:true,compatiblePlatforms:['mt4']}]}}}});",
            "const createWorkflowIdempotencyKey = () => 'workflow-test-key';",
            "const postEaFactoryJson = async (_path,payload) => ({ok:true,kind:'ea_factory_build_created',requestIdempotencyKey:payload.idempotencyKey,createRequestDigest:'d'.repeat(64),build:{id:'ea-build-new',sourceRecordId:payload.sourceRecordId,sourceRecordDigest:'a'.repeat(64),platform:payload.platform,artifactKind:payload.artifactKind,brief:payload.brief,createRequestDigest:'d'.repeat(64)},eaFactoryReadResult:{status:'deferred',readinessConfirmed:false}});",
            "const runEaFactoryRequest = async (_stage,request) => request();",
            "function setEaFactoryActionState(next) { Object.assign(state.modal.eaFactory,next); }",
            "let navigation = null, refreshStarted = false, finishRefresh;",
            "const refresh = new Promise((resolve) => { finishRefresh = resolve; });",
            "const loadEaFactoryReadModel = async () => { refreshStarted = true; await refresh; const model={schemaVersion:'ea-factory-v1',mode:'one_click_with_manual_stage_recovery',scheduled:false,snapshotStale:false,builds:[{id:'ea-build-new',sourceRecordId:'source-1',sourceRecordDigest:'a'.repeat(64),platform:'mt4',artifactKind:'expert_advisor'}]};state.eaFactoryReadModel.payload=model;state.eaFactoryReadModel.stale=false;return {eaFactory:model}; };",
            "function setWorkflowDashboardTab(propId,pageId) { navigation = {propId,pageId}; }",
            receipt_wait,
            create_identity,
            create,
            "(async () => {",
            "  const pending = createEaFactoryBuild('source-1','expert_advisor','mt4','');",
            "  await new Promise((resolve) => setImmediate(resolve));",
            "  const beforeRefresh = {navigation,selectedBuildId:state.modal.eaFactory.selectedBuildId,stale:state.eaFactoryReadModel.stale,refreshStarted};",
            "  finishRefresh();",
            "  const response = await pending;",
            "  process.stdout.write(JSON.stringify({response,beforeRefresh,selectedBuildId:state.modal.eaFactory.selectedBuildId,navigation,pendingKey:state.modal.eaFactory.createIdempotencyKey}));",
            "})().catch((error) => { console.error(error); process.exit(1); });",
        ])
        completed = subprocess.run(
            [self.node_binary(), "-e", script],
            cwd=ROOT,
            capture_output=True,
            check=True,
            text=True,
            encoding="utf-8",
        )
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["response"]["build"]["id"], "ea-build-new")
        self.assertNotIn("eaFactory", payload["response"])
        self.assertEqual(payload["selectedBuildId"], "ea-build-new")
        self.assertEqual(payload["beforeRefresh"], {
            "navigation": {"propId": "right_server_racks", "pageId": "progress"},
            "selectedBuildId": "ea-build-new", "stale": True, "refreshStarted": True,
        })
        self.assertEqual(payload["pendingKey"], "")
        self.assertEqual(
            payload["navigation"],
            {"propId": "right_server_racks", "pageId": "progress"},
        )

    def test_lost_create_response_retries_with_same_key_then_rotates_after_success(self):
        receipt_wait = self.block("async function waitForEaFactoryAuthoritativeReceipt", "async function createEaFactoryCustomSourceAndStart")
        create_identity = self.block(
            "function eaFactoryCreateBuildFormSignature",
            "async function createEaFactoryBuild",
        )
        create = self.block("async function createEaFactoryBuild", "function eaFactoryOneClickRequestKey")
        script = "\n".join([
            "const EA_FACTORY_PROP_ID = 'right_server_racks';",
            "const EA_FACTORY_SUPPORTED_MODES=new Set(['one_click_with_manual_stage_recovery']); let eaFactoryActiveActionAbortController=null; const window={setTimeout,clearTimeout};",
            "const state = {eaFactoryReadModel:{payload:{},stale:false},propReports:{right_server_racks:{}},modal:{open:true,id:EA_FACTORY_PROP_ID,eaFactory:{selectedBuildId:'',selectedArtifactKind:'',selectedPlatform:'',createIdempotencyKey:'',createFormSignature:'',googleSheetCatalog:{}}}};",
            "const normalizeEaFactoryArtifactKind = (value) => value;",
            "const normalizeEaFactoryPlatform = (value) => value;",
            "const binding = {sourceRecordId:'source-1',recordId:'deep-a',recordDigest:'a'.repeat(64),catalogDigest:'b'.repeat(64),snapshotDigest:'c'.repeat(64),configRevision:7};",
            "const eaFactoryCreateSourceBinding = () => ({required:true,ready:true,fields:binding});",
            "const getModalSubject = () => ({id:EA_FACTORY_PROP_ID});",
            "const getPropertyRole = () => ({});",
            "const normalizeWorkflowDashboard = () => ({domainData:{eaFactory:{authoritative:true,backendBusy:null,canStartNewBuild:true,sourceCatalog:{records:[{sourceRecordId:'source-1',recordDigest:'a'.repeat(64),buildReady:true,compatiblePlatforms:['mt5']}]}}}});",
            "let keyCounter = 0;",
            "const createWorkflowIdempotencyKey = () => `workflow-create-${++keyCounter}`;",
            "const posted = [], builds = new Map();",
            "const postEaFactoryJson = async (_path,payload) => { posted.push({...payload}); const replayed = builds.has(payload.idempotencyKey); if (!replayed) builds.set(payload.idempotencyKey,{id:`ea-build-${builds.size+1}`,sourceRecordId:payload.sourceRecordId,sourceRecordDigest:'a'.repeat(64),platform:payload.platform,artifactKind:payload.artifactKind,brief:payload.brief,createRequestDigest:'d'.repeat(64),createSheetBinding:binding}); return {ok:true,kind:replayed?'ea_factory_build_replayed':'ea_factory_build_created',requestIdempotencyKey:payload.idempotencyKey,createRequestDigest:'d'.repeat(64),build:builds.get(payload.idempotencyKey)}; };",
            "let attempt = 0;",
            "const runEaFactoryRequest = async (_stage,request) => { const response = await request(); attempt += 1; return attempt === 1 ? null : response; };",
            "function setEaFactoryActionState(next) { Object.assign(state.modal.eaFactory,next); }",
            "const loadEaFactoryReadModel = async () => { const model={schemaVersion:'ea-factory-v1',mode:'one_click_with_manual_stage_recovery',scheduled:false,snapshotStale:false,builds:[...builds.values()]};state.eaFactoryReadModel.payload=model;state.eaFactoryReadModel.stale=false;return {eaFactory:model}; };",
            "function setWorkflowDashboardTab() {}",
            receipt_wait,
            create_identity,
            create,
            "(async () => {",
            "  const lost = await createEaFactoryBuild('source-1','expert_advisor','mt5','same   brief');",
            "  const replayed = await createEaFactoryBuild('source-1','expert_advisor','mt5','same brief');",
            "  const fresh = await createEaFactoryBuild('source-1','expert_advisor','mt5','same brief');",
            "  process.stdout.write(JSON.stringify({lost,replayed,fresh,keys:posted.map((item)=>item.idempotencyKey),keyCounter,buildCount:builds.size,pendingKey:state.modal.eaFactory.createIdempotencyKey}));",
            "})().catch((error) => { console.error(error); process.exit(1); });",
        ])
        completed = subprocess.run(
            [self.node_binary(), "-e", script],
            cwd=ROOT,
            capture_output=True,
            check=True,
            text=True,
            encoding="utf-8",
        )
        payload = json.loads(completed.stdout)
        self.assertIsNone(payload["lost"])
        self.assertEqual(payload["replayed"]["build"]["id"], "ea-build-1")
        self.assertEqual(payload["replayed"]["kind"], "ea_factory_build_replayed")
        self.assertEqual(payload["fresh"]["build"]["id"], "ea-build-2")
        self.assertEqual(payload["keys"][0], payload["keys"][1])
        self.assertNotEqual(payload["keys"][1], payload["keys"][2])
        self.assertEqual(payload["keyCounter"], 2)
        self.assertEqual(payload["buildCount"], 2)
        self.assertEqual(payload["pendingKey"], "")

    def test_create_and_run_preflight_never_leaves_phantom_working_status(self):
        create = self.block("async function createEaFactoryBuild", "function eaFactoryOneClickRequestKey")
        create_context = self.block("function eaFactoryCreateContextSignature", "function eaFactoryCreateCommitReceipt")
        flow = self.block("async function createAndRunEaFactoryBuild", "async function advanceEaFactoryStage")
        state_key = self.block("function eaFactoryReadModelStateKey", "function mergeEaFactoryReadModel")
        script = "\n".join([
            "const EA_FACTORY_PROP_ID = 'right_server_racks';",
            "const EA_FACTORY_READ_MODEL_MAX_AGE_MS = 90000;",
            "const EA_FACTORY_SUPPORTED_MODES = new Set(['one_click_with_manual_stage_recovery','manual_stage_by_stage']);",
            "const state = {eaFactoryReadModel:{payload:{schemaVersion:'ea-factory-v1',mode:'one_click_with_manual_stage_recovery',scheduled:false}},propReports:{right_server_racks:{}},modal:{eaFactory:{inFlight:false,message:'',tone:'neutral'}}};",
            "const workflowDomainObject = (...values) => values.find((value) => value && typeof value === 'object' && !Array.isArray(value)) || {};",
            "const eaFactoryFirstArray = (...values) => values.find(Array.isArray) || [];",
            "const normalizeEaFactoryArtifactKind = (value) => value;",
            "const normalizeEaFactoryPlatform = (value) => value;",
            "const getModalSubject = () => ({id:EA_FACTORY_PROP_ID});",
            "const getPropertyRole = () => ({});",
            "const normalizeWorkflowDashboard = () => ({domainData:{eaFactory:{authoritative:false,backendBusy:null,canStartNewBuild:false,sourceCatalog:{records:[{sourceRecordId:'source-1',buildReady:true,compatiblePlatforms:['mt4']}]}}}});",
            "const createWorkflowIdempotencyKey = () => 'workflow-test-key';",
            "let postCount = 0;",
            "const postEaFactoryJson = async () => { postCount += 1; return {}; };",
            "const runEaFactoryRequest = async () => { postCount += 1; return {}; };",
            "const setWorkflowDashboardTab = () => {};",
            "let oneClickCount = 0;",
            "const runEaFactoryOneClick = async () => { oneClickCount += 1; return {}; };",
            "function setEaFactoryActionState(next={}) { Object.assign(state.modal.eaFactory,next); }",
            state_key,
            create_context,
            create,
            flow,
            "(async () => {",
            "  const result = await createAndRunEaFactoryBuild('source-1','expert_advisor','mt4','');",
            "  process.stdout.write(JSON.stringify({result,action:state.modal.eaFactory,postCount,oneClickCount}));",
            "})().catch((error) => { console.error(error); process.exit(1); });",
        ])
        completed = subprocess.run(
            [self.node_binary(), "-e", script],
            cwd=ROOT,
            capture_output=True,
            check=True,
            text=True,
            encoding="utf-8",
        )
        payload = json.loads(completed.stdout)
        self.assertIsNone(payload["result"])
        self.assertEqual(payload["postCount"], 0)
        self.assertEqual(payload["oneClickCount"], 0)
        self.assertFalse(payload["action"]["inFlight"])
        self.assertEqual(payload["action"]["tone"], "warning")
        self.assertEqual(payload["action"]["messageKind"], "local_preflight_rejected")
        self.assertIn("One-click capability", payload["action"]["message"])

    def test_stale_busy_is_not_presented_as_live_on_visual_progress_or_status_helper(self):
        rail = self.block("function createEaFactoryRailTaskStatus", "function createFxNewsRailFact")
        visual_progress = self.block(
            "function renderEaFactoryGameProgressPanel",
            "function renderEaFactoryOneClickSetup",
        )
        read_notice = self.block("function renderEaFactoryReadModelNotice", "function eaFactoryReadModelStateKey")
        panel = self.block("function renderEaFactoryPanel", "function validateEaFactoryBusyModel")
        self.assertIn("const live = domain.authoritative === true", visual_progress)
        self.assertIn('panel.dataset.status = live ? status : "checking"', visual_progress)
        self.assertIn("live && progressState.determinate", visual_progress)
        self.assertIn("ระบบจะไม่เดาความคืบหน้าแทน Backend", visual_progress)
        self.assertIn("กำลังรอสถานะที่ยืนยันจาก Backend", visual_progress)
        self.assertIn("readModelState.lastError", read_notice)
        self.assertIn("if (!domain.authoritative)", panel)

        script = "\n".join([
            "const state = {modal:{eaFactory:{inFlight:false}},eaFactoryReadModel:{lastError:{message:'HTTP 503 exact transport reason'},lastLoadedAt:1700000000000}};",
            "const workflowDomainObject = (value) => value && typeof value === 'object' && !Array.isArray(value) ? value : {};",
            "const eaFactoryBusyStatusLabel = () => 'กำลังทำงาน';",
            "const eaFactoryBusyOperationLabel = () => 'กำลังสร้าง Source Code';",
            "const safeDashboardDisplayText = (value,fallback='') => String(value || fallback);",
            "const formatThaiDateTime = () => '14 พ.ย. 2566 05:13';",
            "const setWorkflowDashboardTab = () => {};",
            "const document = {createElement:(tag) => ({tag,dataset:{},children:[],textContent:'',addEventListener(){},append(...nodes){this.children.push(...nodes);}})};",
            rail,
            "const card = createEaFactoryRailTaskStatus({authoritative:false,backendBusy:{buildId:'ea-build-stale',status:'running',activeOperation:'generate_source'},oneClick:{terminalRunning:true}});",
            "process.stdout.write(JSON.stringify({status:card.dataset.status,title:card.children[0].textContent,detail:card.children[1].textContent,button:card.children[3].textContent}));",
        ])
        completed = subprocess.run(
            [self.node_binary(), "-e", script],
            cwd=ROOT,
            capture_output=True,
            check=True,
            text=True,
            encoding="utf-8",
        )
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["status"], "checking")
        self.assertIn("ยังยืนยันไม่ได้", payload["title"])
        self.assertIn("สถานะครั้งล่าสุด", payload["detail"])
        self.assertIn("HTTP 503 exact transport reason", payload["detail"])
        self.assertIn("14 พ.ย. 2566 05:13", payload["detail"])
        self.assertIn("เหตุผล", payload["button"])

    def test_structured_request_rejection_survives_identical_poll_until_state_transition(self):
        validator = self.block("function validateEaFactoryBusyModel", "function eaFactoryBusyContext")
        state_merge = self.block("function eaFactoryReadModelStateKey", "function mergeEaFactoryResponseReport")
        setter = self.block("function setEaFactoryActionState", "async function postEaFactoryJson")
        self.assertIn('messageKind = ""', setter)
        self.assertIn('readModelStateKey = ""', setter)
        script = "\n".join([
            "const EA_FACTORY_STAGE_IDS = Object.freeze(['source','spec','generate','review','compile_validate','backtest_recheck','artifacts_report']);",
            "const EA_FACTORY_BACKEND_STAGE_BY_UI = Object.freeze({spec:'strategy_spec',generate:'generate_source',review:'source_review',compile_validate:'compile_validate',backtest_recheck:'backtest_recheck',artifacts_report:'final_report'});",
            "const EA_FACTORY_PROP_ID = 'right_server_racks';",
            "const EA_FACTORY_READ_MODEL_MAX_AGE_MS = 90000;",
            "const EA_FACTORY_SUPPORTED_MODES = new Set(['one_click_with_manual_stage_recovery','manual_stage_by_stage']);",
            "const safeDashboardDisplayText = (value,fallback='') => String(value || fallback);",
            "const workflowDomainObject = (...values) => values.find((value) => value && typeof value === 'object' && !Array.isArray(value)) || {};",
            "const eaFactoryFirstArray = (...values) => values.find(Array.isArray) || [];",
            "const state = {eaFactoryReadModel:{payload:null,lastLoadedAt:Date.now(),stale:false,lastError:null,busy:null},modal:{eaFactory:{inFlight:false,stageId:'create_build',message:'Backend rejected exact reason',tone:'warning',messageKind:'local_preflight_rejected',readModelStateKey:''}},propReports:{}};",
            validator,
            state_merge,
            "const initial = {schemaVersion:'ea-factory-v1',mode:'one_click_with_manual_stage_recovery',scheduled:false,busy:null,sourceCatalog:{records:[{sourceRecordId:'source-1',buildReady:false,verificationStatus:'blocked'}]},builds:[],terminalSelection:{},oneClick:{}};",
            "state.modal.eaFactory.readModelStateKey = eaFactoryReadModelStateKey(initial);",
            "mergeEaFactoryReadModel({eaFactory:initial});",
            "const afterSame = {...state.modal.eaFactory};",
            "const changed = {...initial,oneClick:{terminalProcessLaunchAllowed:true}};",
            "mergeEaFactoryReadModel({eaFactory:changed});",
            "const afterChanged = {...state.modal.eaFactory};",
            "process.stdout.write(JSON.stringify({afterSame,afterChanged}));",
        ])
        completed = subprocess.run(
            [self.node_binary(), "-e", script],
            cwd=ROOT,
            capture_output=True,
            check=True,
            text=True,
            encoding="utf-8",
        )
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["afterSame"]["message"], "Backend rejected exact reason")
        self.assertEqual(payload["afterSame"]["messageKind"], "local_preflight_rejected")
        self.assertEqual(payload["afterChanged"]["message"], "")
        self.assertEqual(payload["afterChanged"]["messageKind"], "")

    def test_read_model_key_tracks_backend_failure_reason_and_detail(self):
        state_key = self.block(
            "function eaFactoryReadModelStateKey",
            "function mergeEaFactoryReadModel",
        )
        script = "\n".join([
            "const EA_FACTORY_READ_MODEL_MAX_AGE_MS = 90000;",
            "const EA_FACTORY_SUPPORTED_MODES = new Set(['one_click_with_manual_stage_recovery','manual_stage_by_stage']);",
            "const state = {eaFactoryReadModel:{lastLoadedAt:Date.now(),stale:false}};",
            "const workflowDomainObject = (...values) => values.find((value) => value && typeof value === 'object' && !Array.isArray(value)) || {};",
            "const eaFactoryFirstArray = (...values) => values.find(Array.isArray) || [];",
            state_key,
            "const base = {schemaVersion:'ea-factory-v1',mode:'one_click_with_manual_stage_recovery',scheduled:false,busy:null,sourceCatalog:{records:[]},terminalSelection:{},oneClick:{},builds:[{id:'build-1',status:'attention_required',oneClickRun:{runId:'run-1',status:'failed',currentStageId:'generate_source',failureCode:'model_unavailable',messageTh:'เหตุผลเดิม'},stages:[{id:'generate_source',status:'failed',blockedReasonCode:'model_unavailable',detailTh:'รายละเอียดเดิม'}]}]};",
            "const messageChanged = structuredClone(base); messageChanged.builds[0].oneClickRun.messageTh = 'เหตุผลใหม่';",
            "const detailChanged = structuredClone(base); detailChanged.builds[0].stages[0].detailTh = 'รายละเอียดใหม่';",
            "const reasonChanged = structuredClone(base); reasonChanged.builds[0].stages[0].blockedReasonCode = 'invalid_output';",
            "process.stdout.write(JSON.stringify({base:eaFactoryReadModelStateKey(base),message:eaFactoryReadModelStateKey(messageChanged),detail:eaFactoryReadModelStateKey(detailChanged),reason:eaFactoryReadModelStateKey(reasonChanged)}));",
        ])
        completed = subprocess.run(
            [self.node_binary(), "-e", script],
            cwd=ROOT,
            capture_output=True,
            check=True,
            text=True,
            encoding="utf-8",
        )
        payload = json.loads(completed.stdout)
        self.assertNotEqual(payload["base"], payload["message"])
        self.assertNotEqual(payload["base"], payload["detail"])
        self.assertNotEqual(payload["base"], payload["reason"])

    def test_local_preflight_rejection_clears_when_identical_poll_refreshes_authority(self):
        validator = self.block("function validateEaFactoryBusyModel", "function eaFactoryBusyContext")
        state_merge = self.block("function eaFactoryReadModelStateKey", "function mergeEaFactoryResponseReport")
        script = "\n".join([
            "const EA_FACTORY_STAGE_IDS = Object.freeze(['source','spec','generate','review','compile_validate','backtest_recheck','artifacts_report']);",
            "const EA_FACTORY_BACKEND_STAGE_BY_UI = Object.freeze({spec:'strategy_spec',generate:'generate_source',review:'source_review',compile_validate:'compile_validate',backtest_recheck:'backtest_recheck',artifacts_report:'final_report'});",
            "const EA_FACTORY_PROP_ID = 'right_server_racks';",
            "const EA_FACTORY_READ_MODEL_MAX_AGE_MS = 90000;",
            "const EA_FACTORY_SUPPORTED_MODES = new Set(['one_click_with_manual_stage_recovery','manual_stage_by_stage']);",
            "const safeDashboardDisplayText = (value,fallback='') => String(value || fallback);",
            "const workflowDomainObject = (...values) => values.find((value) => value && typeof value === 'object' && !Array.isArray(value)) || {};",
            "const eaFactoryFirstArray = (...values) => values.find(Array.isArray) || [];",
            "const model = {schemaVersion:'ea-factory-v1',mode:'one_click_with_manual_stage_recovery',scheduled:false,busy:null,sourceCatalog:{records:[]},builds:[],terminalSelection:{},oneClick:{}};",
            "const state = {eaFactoryReadModel:{payload:model,lastLoadedAt:Date.now()-EA_FACTORY_READ_MODEL_MAX_AGE_MS-1,stale:false,lastError:null,busy:null},modal:{eaFactory:{inFlight:false,stageId:'create_build',message:'Read Model หมดอายุ',tone:'warning',messageKind:'local_preflight_rejected',readModelStateKey:''}},propReports:{}};",
            validator,
            state_merge,
            "state.modal.eaFactory.readModelStateKey = eaFactoryReadModelStateKey(model);",
            "mergeEaFactoryReadModel({eaFactory:model});",
            "process.stdout.write(JSON.stringify(state.modal.eaFactory));",
        ])
        completed = subprocess.run(
            [self.node_binary(), "-e", script],
            cwd=ROOT,
            capture_output=True,
            check=True,
            text=True,
            encoding="utf-8",
        )
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["message"], "")
        self.assertEqual(payload["messageKind"], "")

    def test_one_click_uses_global_terminal_and_posts_exact_idempotent_run_contract(self):
        setup = self.block("function renderEaFactoryOneClickSetup", "function eaFactoryRetryableInvalidOutput")
        self.assertIn("const platform = capability.selectedPlatform", setup)
        self.assertIn("capability.selectedTerminalId || domain.selectedTerminalId", setup)
        self.assertIn("capability.supportedVisiblePlatforms.includes(platform)", setup)
        self.assertIn("capability.selectedPlatformSupported === true", setup)
        self.assertIn("capability.terminalReady === true", setup)
        self.assertIn("capability.visibleAdapterConnected === true", setup)
        self.assertIn("source.compatiblePlatforms.includes(platform)", setup)
        self.assertIn("createAndRunEaFactoryBuild(", setup)
        self.assertIn("source.sourceRecordId", setup)
        self.assertIn('"expert_advisor"', setup)
        self.assertIn("platform", setup)
        self.assertIn("brief.value", setup)
        self.assertNotIn('document.createElement("select")', setup)

        request = self.block("function eaFactoryOneClickRequestKey", "async function advanceEaFactoryStage")
        self.assertIn("run?.idempotencyKey", request)
        self.assertIn("state.modal.eaFactory.idempotencyKey = persisted", request)
        self.assertIn("createWorkflowIdempotencyKey()", request)
        self.assertIn("async function createAndRunEaFactoryBuild", request)
        self.assertIn('"expert_advisor"', request)
        self.assertIn("/ea-factory/builds/${encodeURIComponent(buildId)}/run`", request)
        self.assertIn("{ idempotencyKey }", request)
        self.assertIn("capability.selectedPlatform !== platform", request)
        self.assertIn("capability.supportedVisiblePlatforms.includes(platform)", request)
        self.assertNotIn('platform !== "mt4"', request)
        self.assertIn("capability.terminalReady !== true", request)
        self.assertIn("capability.terminalRunning !== true", request)
        self.assertIn("capability.visibleAdapterConnected !== true", request)
        self.assertIn("capability.terminalProcessLaunchAllowed === true", request)
        self.assertIn("state.eaFactoryReadModel.stale === true || model?.snapshotStale === true", request)
        self.assertIn("!current.authoritative || current.activeBuild?.id !== buildId", request)
        self.assertIn("confirmed.sourceRecordDigest !== created.build.sourceRecordDigest", request)
        self.assertIn("return runEaFactoryOneClick(buildId)", request)
        self.assertNotIn("{ allowFreshBuild: true }", request)

        poller = self.block("async function pollOpenPropReport", "function startMissionPolling")
        self.assertIn("factoryOneClickActive", poller)
        self.assertIn('String(factoryDomain?.oneClick?.run?.status || "")', poller)
        self.assertIn('"awaiting_visible_terminal"', poller)
        self.assertIn("const factoryBackendBusy = Boolean(factoryDomain?.backendBusy)", poller)
        self.assertIn("const factoryStageActive = factoryBackendBusy", poller)
        self.assertIn("const factoryOneClickActive = factoryBackendBusy", poller)
        self.assertIn("force || factoryBackendBusy || factoryStageActive || factoryOneClickActive || factoryTtlExpired", poller)

    def test_one_click_request_key_executes_reload_and_fresh_build_matrix(self):
        node = shutil.which("node")
        if not node:
            self.skipTest("Node.js is required to execute the one-click idempotency policy")
        helper = self.block("function eaFactoryOneClickRequestKey", "async function runEaFactoryOneClick")
        script = f"""
const assert = require("node:assert/strict");
const state = {{ modal: {{ eaFactory: {{
  oneClickBuildId: "", idempotencyKey: "", formSignature: "",
}} }} }};
let generated = 0;
function createWorkflowIdempotencyKey() {{ generated += 1; return `wf-generated-${{generated}}`; }}
{helper}
const persisted = eaFactoryOneClickRequestKey("ea-build-a", {{ idempotencyKey: "wf-persisted-1234" }});
assert.equal(persisted, "wf-persisted-1234");
assert.equal(generated, 0);
const replay = eaFactoryOneClickRequestKey("ea-build-a", {{}});
assert.equal(replay, "wf-persisted-1234");
assert.equal(generated, 0);
const fresh = eaFactoryOneClickRequestKey("ea-build-b", {{}});
assert.equal(fresh, "wf-generated-1");
assert.equal(generated, 1);
assert.equal(eaFactoryOneClickRequestKey("ea-build-b", {{}}), fresh);
assert.equal(generated, 1);
"""
        completed = subprocess.run(
            [node, "-e", script],
            cwd=ROOT,
            capture_output=True,
            check=False,
            text=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr or completed.stdout)

    def test_backtest_only_restart_is_visible_idempotent_and_exactly_scoped(self):
        normalizer = self.block(
            "function normalizeEaFactoryOneClickRun",
            "function normalizeEaFactoryAudit",
        )
        self.assertIn("canRestartBacktest: raw.canRestartBacktest === true", normalizer)
        self.assertIn("restartBacktestEndpoint", normalizer)
        progress = self.block(
            "function renderEaFactoryGameProgressPanel",
            "function renderEaFactoryOneClickSetup",
        )
        self.assertIn("เริ่ม Backtest ใหม่ • ใช้ Source/Compile เดิม", progress)
        self.assertIn("restartEaFactoryBacktestOnly", progress)
        self.assertIn("รอบ Backend หยุดแล้ว", progress)
        self.assertIn("จะตรวจว่า Strategy Tester ว่างจริงตอนกดเริ่ม", progress)
        self.assertNotIn("รอบเดิมหยุดแล้ว • เริ่มเฉพาะ Backtest ใหม่ได้", progress)
        self.assertIn("เก็บ Source, Version และ Compile เดิมทั้งหมด", progress)
        request = self.block(
            "async function restartEaFactoryBacktestOnly",
            "async function runEaFactoryOneClick",
        )
        self.assertIn("/restart-backtest", request)
        self.assertIn("{ runId, idempotencyKey }", request)
        self.assertIn('runEaFactoryRequest("restart_backtest"', request)
        self.assertIn("cancelled", request)
        self.assertIn("failed", request)
        self.assertIn("awaiting_visible_terminal", request)
        self.assertNotIn("advanceEaFactoryStage", request)
        self.assertNotIn("createAndRunEaFactoryBuild", request)

        node = shutil.which("node")
        if not node:
            self.skipTest("Node.js is required to execute the restart idempotency policy")
        helper = self.block(
            "function eaFactoryBacktestRestartRequestKey",
            "async function restartEaFactoryBacktestOnly",
        )
        script = f"""
const assert = require("node:assert/strict");
const state = {{ modal: {{ eaFactory: {{
  oneClickBuildId: "", idempotencyKey: "", formSignature: "",
}} }} }};
let generated = 0;
function createWorkflowIdempotencyKey() {{ generated += 1; return `wf-restart-${{generated}}`; }}
{helper}
const first = eaFactoryBacktestRestartRequestKey("ea-build-a", "ea-run-old-a");
assert.equal(first, "wf-restart-1");
assert.equal(eaFactoryBacktestRestartRequestKey("ea-build-a", "ea-run-old-a"), first);
assert.equal(generated, 1);
const nextRun = eaFactoryBacktestRestartRequestKey("ea-build-a", "ea-run-old-b");
assert.equal(nextRun, "wf-restart-2");
assert.notEqual(nextRun, first);
const nextBuild = eaFactoryBacktestRestartRequestKey("ea-build-b", "ea-run-old-b");
assert.equal(nextBuild, "wf-restart-3");
"""
        completed = subprocess.run(
            [node, "-e", script],
            cwd=ROOT,
            capture_output=True,
            check=False,
            text=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr or completed.stdout)

    def test_compile_and_backtest_copy_does_not_hide_visible_user_steps(self):
        picker = self.block("function renderEaFactoryTerminalPicker", "function eaFactoryOneClickStatusLabel")
        self.assertIn("MetaEditor และ Visual Strategy Tester", picker)
        self.assertIn("ขั้น Compile ต้องเปิด MetaEditor ให้เห็นจริง", picker)
        self.assertIn("Visual Strategy Tester ให้เห็นจริง", picker)
        self.assertIn("eaFactoryPlatformLabel(platform)", picker)
        self.assertNotIn("MT5 • ขั้นละเอียดแบบ Manual", picker)
        self.assertNotIn("รุ่นนี้จะไม่เปิด MT5 อัตโนมัติ", picker)
        constants = self.block("const EA_FACTORY_STAGE_COPY", "const EA_FACTORY_BACKEND_STAGE_BY_UI")
        self.assertIn("เปิด MetaEditor ของ Terminal ที่เลือกให้เห็นจริง", constants)
        self.assertIn("ต้องเห็น Strategy Tester", constants)

    def test_backtest_attention_distinguishes_zero_trade_and_history_quality(self):
        attention = self.block(
            "function eaFactoryBacktestAttentionPresentation",
            "function eaFactoryActionPresentation",
        )
        operational = self.block(
            "function renderEaFactoryOperationalStage",
            "function renderEaFactoryPanel",
        )
        self.assertIn("eaFactoryBacktestAttentionPresentation(stage, domain.oneClick?.run", operational)
        self.assertNotIn("เก็บงานเป็นสำเร็จแบบต้องตรวจสอบ", operational)
        self.assertNotIn("ไปเริ่ม Session ใหม่ด้วยตนเองใน Optimization Lab", operational)
        action = self.block("function eaFactoryActionPresentation", "function renderEaFactoryOperationalStage")
        script = "\n".join([
            "const assert = require('node:assert/strict');",
            "const state = {eaFactoryReadModel:{lastError:null}};",
            "const safeDashboardDisplayText = (value, fallback='') => String(value || fallback);",
            "const EA_FACTORY_STAGE_IDS = ['backtest_recheck'];",
            attention, action,
            "for (const code of ['backtest_acceptance_zero_trades','backtest_acceptance_history_quality_issue']) {",
            "  const stage = {id:'backtest_recheck',status:'completed',reportId:'verified-report'};",
            "  const result = eaFactoryActionPresentation({authoritative:true,stages:[stage],oneClick:{run:{status:'failed',failureCode:code}}},{stageId:'backtest_recheck',tone:'success',message:'ขั้นนี้ผ่าน Gate แล้ว'});",
            "  assert.equal(result.tone,'error');",
            "  assert.match(result.message,/หยุดก่อน Final Report/);",
            "  assert.match(result.message,/ยังไม่ถือว่างานสำเร็จ/);",
            "  assert.doesNotMatch(result.message,/Optimization Lab|สำเร็จแบบต้องตรวจสอบ/);",
            "}",
            "const historic = eaFactoryBacktestAttentionPresentation({status:'completed',attentionRequired:true,attentionReasonCode:'backtest_zero_trades_and_history_quality_errors'});",
            "assert.equal(historic.tone,'warning');",
            "assert.match(historic.title,/0 ออเดอร์.*คุณภาพข้อมูล/);",
            "assert.match(historic.message,/Mismatched chart errors/);",
            "assert.doesNotMatch(historic.message,/Backend หยุดก่อน Final Report/);",
            "assert.equal(eaFactoryBacktestAttentionPresentation({status:'completed'}),null);",
        ])
        completed = subprocess.run([self.node_binary(), "-e", script], cwd=ROOT,
                                   capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(completed.returncode, 0, completed.stderr)

    def test_collapsed_tester_has_actionable_guidance_without_admission_changes(self):
        attention = self.block("function eaFactoryBacktestAttentionPresentation", "function eaFactoryActionPresentation")
        action = self.block("function eaFactoryActionPresentation", "function renderEaFactoryOperationalStage")
        script = "\n".join([
            "const assert = require('node:assert/strict');",
            "const state = {eaFactoryReadModel:{lastError:null}};",
            "const safeDashboardDisplayText = (value, fallback='') => String(value || fallback);",
            "const eaFactoryPlatformLabel = () => 'MT5';",
            attention, action,
            "const stage = eaFactoryBacktestAttentionPresentation({failureCode:'mt5_tester_pane_collapsed'});",
            "assert.equal(stage.tone,'warning'); assert.match(stage.message,/ลากขอบบน.*Settings.*ไม่กด Start/);",
            "assert.match(stage.message,/ทำขั้นนี้ต่อ/);",
            "for (const status of ['awaiting_visible_terminal','failed','blocked']) {",
            " const domain = {authoritative:true,oneClick:{run:{status,failureCode:'mt5_tester_pane_collapsed'}}};",
            " const before = JSON.stringify(domain);",
            " const result = eaFactoryActionPresentation(domain,{stageId:'one_click_run'});",
            " assert.equal(result.message,stage.message); assert.equal(JSON.stringify(domain),before);",
            "}",
            "assert.equal(eaFactoryBacktestAttentionPresentation({failureCode:'unknown_native_error'}),null);",
        ])
        completed = subprocess.run([self.node_binary(), "-e", script], cwd=ROOT,
                                   capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(completed.returncode, 0, completed.stderr)

    def test_artifacts_are_backend_downloads_and_factory_layout_is_responsive(self):
        operational = self.block("function renderEaFactoryOperationalStage", "function renderEaFactoryPanel")
        url_guard = self.block("function getSafeReportArtifactUrl", "function appendDashboardArtifactLinks")
        artifact_normalizer = self.block("function normalizeEaFactoryArtifact", "function normalizeEaFactoryDomain")
        self.assertIn("/ea-factory\\/builds\\/ea-build-", url_guard)
        self.assertIn("item.downloadUrl || item.url", artifact_normalizer)
        self.assertIn("item.available === true || isFactoryFile", artifact_normalizer)
        self.assertIn("domain.activeBuild.artifactLineage", operational)
        self.assertIn("appendDashboardArtifactLinks(section, domain.activeBuild.artifacts, { limit: 200 })", operational)
        self.assertNotIn("reports.flatMap", operational)
        artifact_links = self.block("function appendDashboardArtifactLinks", "function appendDashboardVisualEvidence")
        self.assertIn("Math.min(Number(limit) || 20, 200)", artifact_links)
        self.assertIn(".slice(0, boundedLimit)", artifact_links)
        self.assertIn("ยังไม่มีไฟล์ที่ Backend อนุญาตให้ดาวน์โหลด", operational)
        self.assertIn("Audit และประวัติ Version", operational)
        self.assertIn("ประวัติ Build ในโรงงาน", operational)
        self.assertIn(".ea-factory-panel", self.styles)
        self.assertIn(".ea-factory-source-rules", self.styles)
        self.assertIn(".ea-factory-terminal-picker", self.styles)
        self.assertIn(".ea-factory-build-history", self.styles)
        self.assertIn(".ea-factory-one-click-progress", self.styles)
        self.assertIn(".ea-factory-manual-details", self.styles)
        self.assertRegex(self.styles, r"@media \(max-width: 900px\)[\s\S]+?ea-factory")


if __name__ == "__main__":
    unittest.main()
