from pathlib import Path
import json
import re
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
INDEX_PATH = ROOT / "frontend" / "index.html"
MAIN_PATH = ROOT / "frontend" / "src" / "app" / "main.js"
STYLES_PATH = ROOT / "frontend" / "src" / "app" / "styles.css"


class MissionAiRoomFrontendTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.html = INDEX_PATH.read_text(encoding="utf-8")
        cls.main = MAIN_PATH.read_text(encoding="utf-8")
        cls.styles = STYLES_PATH.read_text(encoding="utf-8")

    def function_source(self, name: str) -> str:
        match = re.search(rf"(?:async\s+)?function\s+{re.escape(name)}\s*\(", self.main)
        self.assertIsNotNone(match, f"missing frontend function {name}")
        next_match = re.search(r"\n(?:async\s+)?function\s+[A-Za-z0-9_$]+\s*\(", self.main[match.start() + 1 :])
        if not next_match:
            return self.main[match.start() :]
        return self.main[match.start() : match.start() + 1 + next_match.start()]

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
            if candidate and Path(candidate).is_file():
                return candidate
        self.skipTest("Node.js is required for frontend behavior regressions")

    def run_node(self, script: str) -> dict:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "mission-ai-room-regression.js"
            path.write_text(script, encoding="utf-8")
            result = subprocess.run(
                [self.node_binary(), str(path)],
                check=True,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
        return json.loads(result.stdout)

    def panel_source(self) -> str:
        start = self.html.index('id="modalMissionChatPanel"')
        end = self.html.index('id="modalKanbanPanel"', start)
        return self.html[start:end]

    def test_ai_room_is_first_mission_surface_and_mission_tab_is_unchanged(self) -> None:
        chat_tab = self.html.index('id="missionGroupChatTab"')
        mission_tab = self.html.index('id="missionAllTab"')
        chat_panel = self.html.index('id="modalMissionChatPanel"')
        mission_panel = self.html.index('id="modalKanbanPanel"')
        self.assertLess(chat_tab, mission_tab)
        self.assertLess(chat_panel, mission_panel)
        self.assertIn('data-tab="mission-chat"', self.html[chat_tab:mission_tab])
        self.assertIn('data-tab="kanban"', self.html[mission_tab:chat_panel])
        self.assertIn('aria-controls="modalMissionChatPanel"', self.html[chat_tab:mission_tab])
        self.assertIn('aria-controls="modalKanbanPanel"', self.html[mission_tab:chat_panel])
        self.assertIn('id="modalKanbanSearch"', self.html[mission_panel:])
        self.assertIn('id="modalKanbanBoard"', self.html[mission_panel:])

    def test_real_meeting_controls_replace_all_prototype_content(self) -> None:
        panel = self.panel_source()
        for control_id in (
            "missionMeetingStartForm",
            "missionMeetingAgenda",
            "missionMeetingDevelopmentGoal",
            "missionMeetingAiTurnsPerRound",
            "missionMeetingParticipantOptions",
            "missionMeetingStartButton",
            "missionMeetingSessionSelect",
            "missionMeetingRefreshButton",
            "missionMeetingMessageForm",
            "missionMeetingMessage",
            "missionMeetingSendButton",
            "missionMeetingProposalButton",
            "missionMeetingApproveButton",
            "missionMeetingRejectButton",
            "missionMeetingOpenMissionButton",
        ):
            self.assertIn(f'id="{control_id}"', panel)
        for obsolete in (
            "ต้นแบบ UI",
            "ตัวอย่างการประชุม",
            "ข้อความตัวอย่างของห้องประชุม",
            "ยังไม่เชื่อมระบบสนทนา",
            "ตอนนี้ยังพิมพ์หรือส่งข้อความไม่ได้",
            "MISSION_CHAT_PREVIEW",
        ):
            self.assertNotIn(obsolete, panel)
            self.assertNotIn(obsolete, self.main)
        self.assertNotIn("renderMissionChatPreview", self.main)

    def test_chat_layout_removes_duplicate_headings_and_gives_transcript_the_full_height(self) -> None:
        panel = self.panel_source()
        tab_start = self.html.index('id="missionGroupChatTab"')
        tab_end = self.html.index('id="missionAllTab"', tab_start)
        tab = self.html[tab_start:tab_end]
        self.assertEqual(tab.count("ห้องแชท AI รวม"), 1)
        for duplicate in ("AI MEETING ROOM", 'id="missionChatHeading"', 'class="mission-chat-heading"'):
            self.assertNotIn(duplicate, panel)
        self.assertIn('class="mission-chat-shell" aria-labelledby="missionGroupChatTab"', panel)
        self.assertIn('id="missionMeetingStatus"', panel)
        self.assertIn('class="mission-meeting-status-live"', panel)
        self.assertRegex(
            self.styles,
            r"\.game-modal\.kanban-modal \.dialogue-box\s*\{[^}]*display:\s*none;",
        )
        self.assertRegex(
            self.styles,
            r"\.game-modal\.kanban-modal \.modal-content-panel\s*\{[^}]*grid-template-rows:\s*auto minmax\(0, 1fr\);",
        )
        self.assertRegex(
            self.styles,
            r"\.mission-chat-shell\s*\{[^}]*grid-template-rows:\s*minmax\(0, 1fr\);",
        )
        self.assertRegex(
            self.styles,
            r"\.mission-chat-layout\s*\{[^}]*height:\s*100%;",
        )
        self.assertRegex(
            self.styles,
            r"\.mission-chat-message-list\s*\{[^}]*flex:\s*1 0 clamp\(340px, 45vh, 440px\);[^}]*min-height:\s*clamp\(340px, 45vh, 440px\);[^}]*overflow-y:\s*auto;",
        )
        self.assertRegex(
            self.styles,
            r"\.mission-chat-conversation\s*\{[^}]*overflow-y:\s*auto;",
        )

    def test_exact_meeting_endpoints_are_wired_through_shared_helpers(self) -> None:
        self.assertIn('const MEETING_SESSIONS_ENDPOINT = "/api/meetings/sessions";', self.main)
        load_list = self.function_source("loadMeetingSessions")
        load_detail = self.function_source("fetchMeetingSessionDetail")
        start = self.function_source("startMeetingSession")
        message = self.function_source("sendMeetingMessage")
        proposal = self.function_source("requestMeetingProposal")
        approve = self.function_source("approveMeetingProposal")
        reject = self.function_source("rejectMeetingProposal")
        self.assertIn("fetchJson(MEETING_SESSIONS_ENDPOINT)", load_list)
        self.assertIn("fetchJson(`${MEETING_SESSIONS_ENDPOINT}/${encodeURIComponent(id)}`)", load_detail)
        self.assertIn("postJson(MEETING_SESSIONS_ENDPOINT", start)
        self.assertIn("/messages`", message)
        self.assertIn("/proposal`", proposal)
        self.assertIn("/approve`", approve)
        self.assertIn("/reject`", reject)
        for source in (start, message, proposal, approve, reject):
            self.assertIn("createMeetingIdempotencyKey()", source)
            self.assertNotIn("fetch(", source)

    def test_backend_read_model_fixture_normalizes_truthfully(self) -> None:
        fixture = {
            "ok": True,
            "session": {
                "id": "meeting-session-123",
                "agenda": "ตรวจปัญหา Mission และเสนอแผนแก้ไข",
                "developmentGoal": "ทำให้ห้องประชุมอ่านง่ายและพร้อมส่งต่อเป็นงานพัฒนา",
                "aiTurnsPerRound": 4,
                "participantAgentIds": ["ea_developer", "risk_guard", "manager"],
                "status": "awaiting_user",
                "roundCount": 1,
                "maxRounds": 3,
                "maxTurnsPerRound": 4,
                "turns": [
                    {
                        "id": "turn-1",
                        "roundNumber": 1,
                        "role": "agent",
                        "speakerAgentId": "ea_developer",
                        "speakerName": "EA Developer",
                        "message": "พบสาเหตุจาก state เดิม",
                        "intent": "proposal",
                        "createdAt": "2026-08-22T10:00:00+07:00",
                    },
                    {
                        "id": "turn-2",
                        "roundNumber": 1,
                        "role": "agent",
                        "speakerAgentId": "manager",
                        "speakerName": "Manager Agent",
                        "message": "ให้แก้เฉพาะ Frontend และเพิ่ม regression test",
                        "intent": "decision",
                        "createdAt": "2026-08-22T10:01:00+07:00",
                    },
                ],
                "managerDecision": {
                    "turnId": "turn-2",
                    "message": "ให้แก้เฉพาะ Frontend และเพิ่ม regression test",
                    "proposal": "แก้เฉพาะจุด render โดยไม่แตะ Backend",
                    "risks": ["API ส่ง decision เป็น object ซ้อน"],
                    "acceptanceChecks": ["UI ไม่แสดง [object Object]"],
                    "decision": {
                        "status": "accepted",
                        "summary": "ยอมรับข้อเสนอสำหรับดำเนินการต่อ",
                    },
                    "createdAt": "2026-08-22T10:01:00+07:00",
                },
                "proposal": {
                    "text": "ให้แก้เฉพาะ Frontend และเพิ่ม regression test",
                    "digest": "a" * 64,
                    "digestVersion": "interactive-meeting-proposal-v2",
                    "managerTurnId": "turn-2",
                    "proposal": "แก้เฉพาะจุด render โดยไม่แตะ Backend",
                    "risks": ["API ส่ง decision เป็น object ซ้อน"],
                    "acceptanceChecks": ["UI ไม่แสดง [object Object]"],
                    "managerDecision": {
                        "status": "accepted",
                        "summary": "ยอมรับข้อเสนอสำหรับดำเนินการต่อ",
                    },
                    "frozenAt": "2026-08-22T10:02:00+07:00",
                },
                "implementationMissionId": None,
                "createdAt": "2026-08-22T09:59:00+07:00",
                "updatedAt": "2026-08-22T10:02:00+07:00",
            },
        }
        functions = "\n".join(
            self.function_source(name)
            for name in (
                "normalizeMeetingText",
                "normalizeMeetingTextList",
                "normalizeMeetingParticipant",
                "normalizeMeetingMessage",
                "normalizeMeetingProposal",
                "normalizeMeetingSession",
                "normalizeMeetingSessionPayload",
                "meetingSessionIsPollingActive",
                "meetingSessionCanInterject",
                "meetingSessionCanFreezeProposal",
            )
        )
        script = "\n".join(
            [
                "const getOfficeAgent = (id) => ({",
                "  ea_developer:{id,name:'EA Developer',role:'Developer'},",
                "  risk_guard:{id,name:'Risk Guard',role:'Risk'},",
                "  manager:{id,name:'Manager Agent',role:'Manager'},",
                "}[id] || null);",
                functions,
                f"const normalized=normalizeMeetingSessionPayload({json.dumps(fixture)});",
                "process.stdout.write(JSON.stringify({",
                " id:normalized.id,status:normalized.status,round:normalized.currentRound,maxRounds:normalized.totalRounds,",
                " developmentGoal:normalized.developmentGoal,aiTurnsPerRound:normalized.aiTurnsPerRound,",
                " currentTurn:normalized.currentTurn,maxTurns:normalized.totalTurns,decision:normalized.managerDecision,",
                " proposalText:normalized.proposal.summary,digest:normalized.proposal.digest,missionId:normalized.proposal.implementationMissionId,",
                " structuredProposal:normalized.proposal.structuredProposal,risks:normalized.proposal.risks,acceptanceChecks:normalized.proposal.acceptanceChecks,",
                " decisionStatus:normalized.proposal.managerDecision.status,decisionSummary:normalized.proposal.managerDecision.summary,",
                " digestVersion:normalized.proposal.digestVersion,managerTurnId:normalized.proposal.managerTurnId,visibleComplete:normalized.proposal.visibleConsentPacketComplete,approvalNote:normalized.approvalNote,",
                " contextComplete:normalized.visibleMeetingContextComplete,polling:meetingSessionIsPollingActive(normalized),interject:meetingSessionCanInterject(normalized),freeze:meetingSessionCanFreezeProposal(normalized)",
                "}));",
            ]
        )
        payload = self.run_node(script)
        self.assertEqual(payload["id"], "meeting-session-123")
        self.assertEqual(payload["status"], "awaiting_user")
        self.assertEqual(payload["developmentGoal"], "ทำให้ห้องประชุมอ่านง่ายและพร้อมส่งต่อเป็นงานพัฒนา")
        self.assertEqual(payload["aiTurnsPerRound"], 4)
        self.assertEqual(payload["round"], 1)
        self.assertEqual(payload["maxRounds"], 3)
        self.assertEqual(payload["currentTurn"], 2)
        self.assertEqual(payload["maxTurns"], 4)
        self.assertEqual(payload["decision"], "ให้แก้เฉพาะ Frontend และเพิ่ม regression test")
        self.assertNotEqual(payload["decision"], "[object Object]")
        self.assertEqual(payload["proposalText"], "ให้แก้เฉพาะ Frontend และเพิ่ม regression test")
        self.assertEqual(payload["structuredProposal"], "แก้เฉพาะจุด render โดยไม่แตะ Backend")
        self.assertEqual(payload["risks"], ["API ส่ง decision เป็น object ซ้อน"])
        self.assertEqual(payload["acceptanceChecks"], ["UI ไม่แสดง [object Object]"])
        self.assertEqual(payload["decisionStatus"], "accepted")
        self.assertEqual(payload["decisionSummary"], "ยอมรับข้อเสนอสำหรับดำเนินการต่อ")
        self.assertEqual(payload["digest"], "a" * 64)
        self.assertEqual(payload["digestVersion"], "interactive-meeting-proposal-v2")
        self.assertEqual(payload["managerTurnId"], "turn-2")
        self.assertTrue(payload["visibleComplete"])
        self.assertTrue(payload["contextComplete"])
        self.assertEqual(payload["approvalNote"], "")
        self.assertEqual(payload["missionId"], "")
        self.assertFalse(payload["polling"])
        self.assertTrue(payload["interject"])
        self.assertTrue(payload["freeze"])

    def test_approve_response_envelope_preserves_real_mission_and_ready_state(self) -> None:
        fixture = {
            "ok": True,
            "readyToExecute": True,
            "implementationMissionId": "mission-implementation-9",
            "mission": {"id": "mission-implementation-9", "status": "waiting_approval", "readyToExecute": True},
            "session": {
                "id": "meeting-session-9",
                "agenda": "อนุมัติแผนแก้ไข",
                "participantAgentIds": ["ea_developer", "manager"],
                "status": "approved",
                "roundCount": 1,
                "maxRounds": 3,
                "maxTurnsPerRound": 2,
                "turns": [],
                "proposal": {"text": "แผนที่ถูกแช่แข็ง", "digest": "b" * 64},
                "approvalNote": "อนุมัติเฉพาะไฟล์ Agent Office ที่ระบุ",
            },
        }
        functions = "\n".join(
            self.function_source(name)
            for name in (
                "normalizeMeetingText",
                "normalizeMeetingTextList",
                "normalizeMeetingParticipant",
                "normalizeMeetingMessage",
                "normalizeMeetingProposal",
                "normalizeMeetingSession",
                "normalizeMeetingSessionPayload",
            )
        )
        script = "\n".join(
            [
                "const getOfficeAgent = () => null;",
                functions,
                f"const normalized=normalizeMeetingSessionPayload({json.dumps(fixture)});",
                "process.stdout.write(JSON.stringify({status:normalized.proposal.status,missionId:normalized.proposal.implementationMissionId,ready:normalized.proposal.readyToExecute,approvalNote:normalized.approvalNote}));",
            ]
        )
        self.assertEqual(
            self.run_node(script),
            {
                "status": "approved",
                "missionId": "mission-implementation-9",
                "ready": True,
                "approvalNote": "อนุมัติเฉพาะไฟล์ Agent Office ที่ระบุ",
            },
        )

    def test_digest_bound_proposal_fields_render_as_text_only(self) -> None:
        panel = self.panel_source()
        renderer = self.function_source("renderMeetingDecisionAndProposal")
        for element_id, element_ref in (
            ("missionMeetingProposalMeetingId", "missionMeetingProposalMeetingId"),
            ("missionMeetingStructuredProposal", "missionMeetingStructuredProposal"),
            ("missionMeetingProposalRisks", "missionMeetingProposalRisks"),
            ("missionMeetingProposalAcceptanceChecks", "missionMeetingProposalAcceptanceChecks"),
            ("missionMeetingProposalManagerDecisionStatus", "missionMeetingProposalManagerDecisionStatus"),
            ("missionMeetingProposalManagerDecisionSummary", "missionMeetingProposalManagerDecisionSummary"),
            ("missionMeetingProposalDigestVersion", "missionMeetingProposalDigestVersion"),
            ("missionMeetingProposalManagerTurnId", "missionMeetingProposalManagerTurnId"),
        ):
            self.assertIn(f'id="{element_id}"', panel)
            self.assertIn(f"els.{element_ref}.textContent", renderer)
            self.assertNotIn(f"els.{element_ref}.innerHTML", renderer)
        normalizer = self.function_source("normalizeMeetingProposal")
        for field in (
            "structuredProposal",
            "risks",
            "acceptanceChecks",
            "managerDecision",
            "digestVersion",
            "managerTurnId",
            "visibleConsentPacketComplete",
        ):
            self.assertIn(field, normalizer)

    def test_digest_only_or_partial_packet_cannot_be_approved(self) -> None:
        functions = "\n".join(
            self.function_source(name)
            for name in (
                "normalizeMeetingText",
                "normalizeMeetingTextList",
                "normalizeMeetingProposal",
                "meetingProposalDigestIsValid",
                "meetingProposalVisibleConsentIsComplete",
            )
        )
        complete = {
            "proposal": {
                "text": "ข้อสรุปที่ผู้ใช้เห็น",
                "digest": "c" * 64,
                "digestVersion": "interactive-meeting-proposal-v2",
                "managerTurnId": "turn-manager-1",
                "proposal": "แก้เฉพาะไฟล์ที่แสดงในแผน",
                "risks": [],
                "acceptanceChecks": ["ชุดทดสอบผ่าน"],
                "managerDecision": {"status": "accepted", "summary": "พร้อมขออนุมัติ"},
            }
        }
        partial = {"proposal": {"text": "ข้อความไม่ครบ", "digest": "d" * 64}}
        mismatched_alias = {
            "proposal": {
                **complete["proposal"],
                "structuredProposal": "แผน A ที่ไม่ได้ผูกกับ digest",
            }
        }
        overlong_visible = {
            "proposal": {
                **complete["proposal"],
                "risks": ["ย" * 241],
            }
        }
        script = "\n".join(
            [
                functions,
                f"const complete=normalizeMeetingProposal({json.dumps(complete)});",
                f"const partial=normalizeMeetingProposal({json.dumps(partial)});",
                f"const mismatched=normalizeMeetingProposal({json.dumps(mismatched_alias)});",
                f"const overlong=normalizeMeetingProposal({json.dumps(overlong_visible)});",
                "process.stdout.write(JSON.stringify({",
                " complete:meetingProposalVisibleConsentIsComplete({id:'session-complete',visibleMeetingContextComplete:true,proposal:complete}),",
                " partial:meetingProposalVisibleConsentIsComplete({id:'session-partial',visibleMeetingContextComplete:true,proposal:partial}),",
                " mismatched:meetingProposalVisibleConsentIsComplete({id:'session-mismatched',visibleMeetingContextComplete:true,proposal:mismatched}),",
                " mismatchedShown:mismatched.structuredProposal,",
                " overlong:meetingProposalVisibleConsentIsComplete({id:'session-overlong',visibleMeetingContextComplete:true,proposal:overlong}),",
                " missingContext:meetingProposalVisibleConsentIsComplete({id:'session-no-context',proposal:complete})",
                "}));",
            ]
        )
        self.assertEqual(
            self.run_node(script),
            {
                "complete": True,
                "partial": False,
                "mismatched": False,
                "mismatchedShown": "แก้เฉพาะไฟล์ที่แสดงในแผน",
                "overlong": False,
                "missingContext": False,
            },
        )

        renderer = self.function_source("renderMeetingDecisionAndProposal")
        request = self.function_source("requestMeetingProposal")
        approve = self.function_source("approveMeetingProposal")
        self.assertIn("meetingProposalVisibleConsentIsComplete(session)", renderer)
        self.assertIn("!consentPacketComplete", renderer)
        self.assertIn("meetingProposalVisibleConsentIsComplete(updated)", request)
        self.assertIn("!meetingProposalVisibleConsentIsComplete(session)", approve)

    def test_message_and_approval_drafts_are_session_scoped_and_approved_note_is_read_only(self) -> None:
        functions = "\n".join(
            self.function_source(name)
            for name in (
                "normalizeMeetingText",
                "meetingSessionApprovalNoteIsImmutable",
                "meetingSessionDraftKey",
                "saveMeetingSessionDrafts",
                "restoreMeetingSessionDrafts",
            )
        )
        script = "\n".join(
            [
                "const state={meetingRoom:{activeSessionId:'session-a',session:{id:'session-a',status:'awaiting_user',proposal:{status:'proposed'}},draftsBySession:Object.create(null)}};",
                "const field=()=>({value:'',readOnly:false,disabled:false,attributes:{},setAttribute(name,value){this.attributes[name]=value;}});",
                "const els={missionMeetingMessage:field(),missionMeetingApprovalNote:field(),missionMeetingApprovalNoteHelp:{textContent:''}};",
                functions,
                "els.missionMeetingMessage.value='ข้อความ A';els.missionMeetingApprovalNote.value='หมายเหตุ A';saveMeetingSessionDrafts();",
                "state.meetingRoom.activeSessionId='session-b';state.meetingRoom.session={id:'session-b',status:'awaiting_user',proposal:{status:'proposed'}};restoreMeetingSessionDrafts();",
                "const bInitially={message:els.missionMeetingMessage.value,note:els.missionMeetingApprovalNote.value};",
                "els.missionMeetingMessage.value='ข้อความ B';els.missionMeetingApprovalNote.value='หมายเหตุ B';saveMeetingSessionDrafts();",
                "state.meetingRoom.activeSessionId='session-a';state.meetingRoom.session={id:'session-a',status:'awaiting_user',proposal:{status:'proposed'}};restoreMeetingSessionDrafts();",
                "const aRestored={message:els.missionMeetingMessage.value,note:els.missionMeetingApprovalNote.value};",
                "state.meetingRoom.session={id:'session-a',status:'approved',approvalNote:'หมายเหตุที่ Backend บันทึก',proposal:{status:'approved'}};restoreMeetingSessionDrafts();",
                "const approved={note:els.missionMeetingApprovalNote.value,readOnly:els.missionMeetingApprovalNote.readOnly,aria:els.missionMeetingApprovalNote.attributes['aria-readonly']};",
                "state.meetingRoom.activeSessionId='session-b';state.meetingRoom.session={id:'session-b',status:'awaiting_user',proposal:{status:'proposed'}};restoreMeetingSessionDrafts();",
                "const bRestored={message:els.missionMeetingMessage.value,note:els.missionMeetingApprovalNote.value};",
                "process.stdout.write(JSON.stringify({bInitially,aRestored,approved,bRestored}));",
            ]
        )
        self.assertEqual(
            self.run_node(script),
            {
                "bInitially": {"message": "", "note": ""},
                "aRestored": {"message": "ข้อความ A", "note": "หมายเหตุ A"},
                "approved": {"note": "หมายเหตุที่ Backend บันทึก", "readOnly": True, "aria": "true"},
                "bRestored": {"message": "ข้อความ B", "note": "หมายเหตุ B"},
            },
        )

    def test_session_switch_and_poll_cannot_bleed_drafts_or_stale_session(self) -> None:
        event_start = self.main.index('els.missionMeetingSessionSelect?.addEventListener("change"')
        event_end = self.main.index('els.missionMeetingMessageForm?.addEventListener("submit"', event_start)
        switch = self.main[event_start:event_end]
        self.assertLess(
            switch.index("saveMeetingSessionDrafts(state.meetingRoom.activeSessionId)"),
            switch.index("state.meetingRoom.activeSessionId = sessionId"),
        )
        self.assertIn("restoreMeetingSessionDrafts(state.meetingRoom.session)", switch)
        poll = self.function_source("pollMeetingSession")
        self.assertIn("requestedSessionId", poll)
        self.assertIn("{ activate: false }", poll)
        self.assertIn("state.meetingRoom.activeSessionId !== requestedSessionId", poll)
        self.assertIn("state.meetingRoom.session = session", poll)

    def test_transcript_escapes_backend_content_and_shows_real_identity_fields(self) -> None:
        script = "\n".join(
            [
                self.function_source("escapeHtml"),
                "process.stdout.write(JSON.stringify({value:escapeHtml('<img src=x onerror=alert(1)> & \\\"quoted\\\"')}));",
            ]
        )
        escaped = self.run_node(script)["value"]
        self.assertNotIn("<img", escaped)
        self.assertIn("&lt;img", escaped)
        self.assertIn("&amp;", escaped)
        renderer = self.function_source("renderMeetingTranscript")
        for marker in (
            "speaker.innerHTML = escapeHtml(message.speakerName)",
            "role.innerHTML = escapeHtml(",
            "text.innerHTML = escapeHtml(message.text)",
            "formatThaiDateTime(message.createdAt",
            "message.speakerStatus",
        ):
            self.assertIn(marker, renderer)

    def test_polling_runs_only_while_backend_round_is_running_and_cleans_up(self) -> None:
        poll_state = self.function_source("meetingSessionIsPollingActive")
        active_state = self.function_source("meetingSessionIsActive")
        interject_state = self.function_source("meetingSessionCanInterject")
        sync = self.function_source("syncMeetingRoomPolling")
        poll = self.function_source("pollMeetingSession")
        tab = self.function_source("setModalTab")
        close = self.function_source("closeGameModal")
        self.assertIn('=== "running"', poll_state)
        self.assertIn("meetingSessionIsPollingActive(session)", active_state)
        self.assertNotIn("awaiting_user", active_state)
        self.assertIn('!== "awaiting_user"', interject_state)
        self.assertIn("session.currentRound", interject_state)
        self.assertIn("window.setInterval", sync)
        self.assertIn("meetingSessionIsPollingActive()", sync)
        self.assertIn("meetingRoomIsVisible()", poll)
        self.assertIn("ensureMeetingRoomLoaded()", tab)
        self.assertIn("stopMeetingRoomPolling()", tab)
        self.assertIn("stopMeetingRoomPolling()", close)
        self.assertIn('document.addEventListener("visibilitychange"', self.main)

    def test_duplicate_actions_are_disabled_and_guarded(self) -> None:
        for name in (
            "loadMeetingSessions",
            "startMeetingSession",
            "sendMeetingMessage",
            "requestMeetingProposal",
            "approveMeetingProposal",
            "rejectMeetingProposal",
        ):
            self.assertIn("state.meetingRoom.inFlight", self.function_source(name))
        renderer = self.function_source("renderMissionMeetingRoom")
        proposal_renderer = self.function_source("renderMeetingDecisionAndProposal")
        for marker in (
            "els.missionMeetingStartButton.disabled",
            "els.missionMeetingRefreshButton.disabled",
            "els.missionMeetingSendButton.disabled",
        ):
            self.assertIn(marker, renderer)
        self.assertIn("els.missionMeetingApproveButton.disabled", proposal_renderer)
        self.assertIn("els.missionMeetingRejectButton.disabled", proposal_renderer)

    def test_participant_defaults_and_validation_match_backend_contract(self) -> None:
        options = self.function_source("renderMeetingParticipantOptions")
        start = self.function_source("startMeetingSession")
        self.assertIn('agent.id !== "manager"', options)
        self.assertIn("slice(0, 2)", options)
        self.assertIn('const managerRequired = agent.id === "manager"', options)
        self.assertIn("input.disabled = managerRequired", options)
        self.assertIn("เข้าร่วมและสรุปทุกครั้ง", options)
        self.assertIn('participantAgentIds.filter((agentId) => agentId !== "manager")', start)
        self.assertIn("Specialist Agent อย่างน้อย 1 ตัว", start)
        self.assertIn("specialistAgentIds.length > 3", start)

    def test_user_controls_topic_goal_and_ai_chat_batch(self) -> None:
        panel = self.panel_source()
        start = self.function_source("startMeetingSession")
        normalizer = self.function_source("normalizeMeetingSession")
        for copy in (
            "หัวข้อที่ให้ AI ประชุม",
            "สิ่งที่ต้องการพัฒนา",
            "จำนวนข้อความ AI ก่อนรอคุณ",
            "2 ข้อความ",
            "8 ข้อความ",
        ):
            self.assertIn(copy, panel)
        self.assertIn("const developmentGoal = normalizeMeetingText(els.missionMeetingDevelopmentGoal?.value, 2400)", start)
        self.assertIn("const aiTurnsPerRound = Number(els.missionMeetingAiTurnsPerRound?.value)", start)
        self.assertIn("developmentGoal,", start)
        self.assertIn("aiTurnsPerRound,", start)
        self.assertIn("aiTurnsPerRound < 2 || aiTurnsPerRound > 8", start)
        self.assertIn("aiTurnsPerRound < distinctParticipantCount", start)
        self.assertIn("เพื่อให้ทุก Agent ได้พูดในรอบนี้", start)
        self.assertGreaterEqual(panel.count('maxlength="2400"'), 2)
        self.assertIn('id="missionMeetingMessage" rows="2" maxlength="1600"', panel)
        self.assertIn("value.developmentGoal", normalizer)
        self.assertIn("value.aiTurnsPerRound", normalizer)

    def test_chat_feed_and_composer_are_primary_while_approval_is_collapsed(self) -> None:
        panel = self.panel_source()
        transcript = panel.index('id="missionChatMessages"')
        composer = panel.index('id="missionMeetingMessageForm"')
        proposal = panel.index('id="missionMeetingProposal"')
        self.assertLess(transcript, composer)
        self.assertLess(composer, proposal)
        self.assertIn('<details class="mission-meeting-proposal"', panel)
        self.assertIn("ช่องนี้จะเปิดเมื่อ AI คุยครบจำนวนข้อความ", panel)
        helper = self.function_source("meetingComposerHelpCopy")
        self.assertIn("meetingSessionCanInterject(session)", helper)
        self.assertIn("ช่องนี้จะเปิดทันทีเมื่อจบรอบ", helper)

    def test_proposal_is_digest_bound_and_never_claims_automatic_execution(self) -> None:
        panel = self.panel_source()
        for copy in (
            "Proposal digest",
            "Backend จะสร้าง Mission แยกหลังอนุมัติ",
            "อนุมัติแผนโค้ด",
            "เปิด Mission เพื่อยืนยันรันหนึ่งครั้ง",
            "ระบบจะไม่รันโค้ด ไม่ Deploy และไม่ส่งคำสั่ง Live Trade อัตโนมัติ",
            "ระบบส่งหมายเหตุตามที่คุณพิมพ์โดยไม่เติมข้อความต่อท้าย",
        ):
            self.assertIn(copy, panel)
        approve = self.function_source("approveMeetingProposal")
        reject = self.function_source("rejectMeetingProposal")
        digest_validator = self.function_source("meetingProposalDigestIsValid")
        open_mission = self.function_source("openMeetingImplementationMission")
        for source in (approve, reject):
            self.assertIn("confirmMeetingId", source)
            self.assertIn("confirmProposalDigest", source)
            self.assertIn("note:", source)
        self.assertIn("if (proposal.implementationMissionId)", approve)
        self.assertIn("/^[0-9a-f]{64}$/", digest_validator)
        self.assertIn("meetingProposalVisibleConsentIsComplete(session)", approve)
        self.assertIn("meetingProposalDigestIsValid(proposal)", reject)
        self.assertIn("note: userNote", approve)
        self.assertNotIn("ขอบเขตการอนุมัติ:", approve)
        self.assertIn("payload.confirmMissionId", approve)
        self.assertNotIn("confirmMissionId: \"\"", approve)
        self.assertIn('setModalTab("kanban")', open_mission)
        self.assertIn("loadBridgeMissions", open_mission)
        self.assertIn("openTaskDetail", open_mission)
        self.assertNotIn("postJson", open_mission)
        self.assertNotIn("/execute", open_mission)

    def test_empty_loading_offline_rate_and_blocked_states_are_truthful(self) -> None:
        panel = self.panel_source()
        status_renderer = self.function_source("renderMeetingRuntimeStatus")
        transcript_renderer = self.function_source("renderMeetingTranscript")
        for state_name in ("idle", "loading", "ready", "empty", "offline", "rate_limited", "blocked", "error"):
            self.assertIn(f"{state_name}:", status_renderer)
        for copy in ("Backend ออฟไลน์", "ติด Rate Limit", "คำขอถูกบล็อก", "ยังไม่มี Session"):
            self.assertIn(copy, status_renderer + transcript_renderer + panel)
        classifier = self.function_source("meetingRoomFailureState")
        self.assertIn("status === 429", classifier)
        self.assertIn("401, 403, 409, 423", classifier)
        self.assertIn("502, 503, 504", classifier)

    def test_accessibility_keyboard_and_mobile_contract(self) -> None:
        panel = self.panel_source()
        for marker in (
            'role="status"',
            'aria-live="polite"',
            'role="log"',
            'aria-relevant="additions text"',
            'aria-labelledby="missionGroupChatTab"',
            'aria-label="รายชื่อ Agent ที่เลือกเข้าประชุม"',
            'aria-describedby="missionMeetingMessageHelp"',
        ):
            self.assertIn(marker, panel)
        event_source = self.main[self.main.index('els.missionMeetingMessage?.addEventListener("keydown"') :]
        self.assertIn('event.key !== "Enter"', event_source)
        self.assertIn("event.ctrlKey", event_source)
        self.assertIn("event.metaKey", event_source)
        for selector in (
            ".mission-chat-shell",
            ".mission-chat-layout",
            ".mission-chat-sidebar",
            ".mission-meeting-message-form",
            ".mission-meeting-proposal",
            ".mission-meeting-proposal > summary",
            ".mission-meeting-proposal-body",
            ".mission-meeting-proposal > summary:focus-visible",
            ".mission-chat-shell button:focus-visible",
            "@media (max-width: 900px)",
            "@media (max-width: 640px)",
        ):
            self.assertIn(selector, self.styles)
        mobile = self.styles[self.styles.index("@media (max-width: 640px)") :]
        self.assertIn(".mission-meeting-message-form", mobile)
        self.assertIn("grid-template-columns: minmax(0, 1fr);", mobile)

    def test_ai_room_default_and_tabs_keep_keyboard_navigation(self) -> None:
        tab_logic = self.function_source("setModalTab")
        self.assertIn('kanban: ["mission-chat", "kanban"]', tab_logic)
        self.assertIn('tab.setAttribute("aria-selected", String(selected))', tab_logic)
        self.assertIn("tab.tabIndex = selected ? 0 : -1", tab_logic)
        open_modal = self.function_source("openGameModal")
        self.assertIn('(tab || "mission-chat")', open_modal)
        event_start = self.main.index('els.modalTabs?.addEventListener("keydown"')
        event_end = self.main.index('els.missionMeetingStartForm?.addEventListener("submit"', event_start)
        keyboard = self.main[event_start:event_end]
        for key in ("ArrowRight", "ArrowLeft", "Home", "End"):
            self.assertIn(key, keyboard)

    def test_queued_missions_still_fold_into_running_without_backend_mutation(self) -> None:
        script = "\n".join(
            [
                "const getMissionPresentationStatus = (mission) => mission.status;",
                self.function_source("getMissionCenterColumnStatus"),
                "process.stdout.write(JSON.stringify({queued:getMissionCenterColumnStatus({status:'queued'}),running:getMissionCenterColumnStatus({status:'running'}),blocked:getMissionCenterColumnStatus({status:'blocked'}),completed:getMissionCenterColumnStatus({status:'completed'}),failed:getMissionCenterColumnStatus({status:'failed'})}));",
            ]
        )
        self.assertEqual(
            self.run_node(script),
            {"queued": "running", "running": "running", "blocked": "blocked", "completed": "completed", "failed": "failed"},
        )
        columns_start = self.main.index("const MISSION_KANBAN_COLUMNS")
        columns_end = self.main.index("function escapeHtml", columns_start)
        columns = self.main[columns_start:columns_end]
        self.assertNotIn('id: "queued"', columns)
        for status in ("running", "blocked", "completed", "failed"):
            self.assertIn(f'id: "{status}"', columns)

    def test_cache_version_keeps_expanded_meeting_room_in_latest_build(self) -> None:
        self.assertGreaterEqual(self.html.count("20260827-google-auth-v074"), 2)
        self.assertNotIn("20260824-ea-optimization-lab-v072", self.html)
        self.assertNotIn("20260823-radar-run-truth-v069", self.html)
        self.assertNotIn("20260822-ai-meeting-chat-first-v067", self.html)
        self.assertNotIn("20260822-ai-meeting-room-v066", self.html)
        self.assertNotIn("20260822-trading-system-gate-v065", self.html)
        self.assertNotIn("20260814-ai-meeting-preview-v063", self.html)

    def test_user_facing_waiting_to_start_copy_remains_removed(self) -> None:
        for source in (self.html, self.main):
            self.assertNotIn("รอเริ่มงาน", source)
            self.assertNotIn("งานที่รอเริ่ม", source)
        self.assertIn("กดโต๊ะเพื่อเปิดห้องแชท AI รวมที่เชื่อม Session จาก Backend", self.main)


if __name__ == "__main__":
    unittest.main()
