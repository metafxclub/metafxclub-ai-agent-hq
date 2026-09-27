from __future__ import annotations

import re
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
INDEX_PATH = PROJECT_ROOT / "frontend" / "index.html"
MAIN_PATH = PROJECT_ROOT / "frontend" / "src" / "app" / "main.js"
STYLES_PATH = PROJECT_ROOT / "frontend" / "src" / "app" / "styles.css"


def function_block(source: str, signature: str) -> str:
    start = source.index(signature)
    next_function = source.find("\nfunction ", start + len(signature))
    next_async = source.find("\nasync function ", start + len(signature))
    candidates = [value for value in (next_function, next_async) if value >= 0]
    return source[start : min(candidates) if candidates else len(source)]


class FullAgentFrontendTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.index = INDEX_PATH.read_text(encoding="utf-8")
        cls.main = MAIN_PATH.read_text(encoding="utf-8")
        cls.styles = STYLES_PATH.read_text(encoding="utf-8")

    def test_modal_exposes_thread_model_reasoning_mode_and_lifecycle_controls(self) -> None:
        for element_id in (
            "modalAgentRuntimeConsole",
            "modalAgentThreadSelect",
            "modalAgentRefreshThread",
            "modalAgentNewThread",
            "modalAgentArchiveThread",
            "modalAgentThreadMeta",
            "modalAgentModelSelect",
            "modalAgentReasoningSelect",
            "modalAgentCapabilityMode",
            "modalAgentActivityTimeline",
            "modalAgentStopButton",
            "modalAgentContinueButton",
        ):
            with self.subTest(element_id=element_id):
                self.assertEqual(self.index.count(f'id="{element_id}"'), 1)

        for mode in ("chat", "workspace", "computer", "full"):
            self.assertRegex(self.index, rf'<option value="{re.escape(mode)}"')

    def test_full_agent_uses_only_the_versioned_runtime_namespace_contract(self) -> None:
        for endpoint in (
            '"/api/agent-runtime/status"',
            '"/api/agent-runtime/models"',
            '"/api/agent-runtime/threads"',
            '"/settings"',
            '"/turn"',
            '"/interrupt"',
            '"/archive"',
        ):
            with self.subTest(endpoint=endpoint):
                self.assertIn(endpoint, self.main)

        self.assertIn('const AGENT_CHAT_ENDPOINT = "/api/agents/chat"', self.main)
        self.assertIn("profile.mode === \"chat\" && isAgentRuntimeEndpointUnavailable(error)", self.main)
        self.assertIn("Turn endpoint ยังไม่มี • สลับเป็น limited_chat", self.main)

    def test_readiness_is_fail_closed_and_never_inferred_from_ui_presence(self) -> None:
        normalizer = function_block(self.main, "function normalizeAgentRuntimeStatus(payload)")
        self.assertIn("payload?.ok === true", normalizer)
        self.assertIn("runtime.available === true", normalizer)
        self.assertIn("runtime.executionEnabled === true", normalizer)
        self.assertIn("runtime?.chatReady !== false", normalizer)
        self.assertIn("runtime?.toolExecutionEnabled === true", normalizer)
        self.assertIn("runtime?.fullAgentReady === true", normalizer)
        self.assertIn("value.ready === true", self.main)
        self.assertNotIn("available: Boolean(runtime", normalizer)

        renderer = function_block(self.main, "function renderAgentRuntimeConsole(subject)")
        truth = function_block(self.main, "function agentRuntimeCapabilityTruth(status)")
        self.assertIn("status?.modeReadiness?.chat === true", truth)
        self.assertIn("status?.fullAgentReady === true", truth)
        self.assertIn("status?.toolExecutionEnabled === true", truth)
        self.assertIn("status?.approvalBrokerReady === true", truth)
        self.assertIn("Chat พร้อม • Workspace/Computer/Full Access ล็อกโดย Backend", renderer)
        self.assertIn('setAgentRuntimeBadge(els.modalAgentRuntimeBadge, "Chat Runtime", chatReady', renderer)
        self.assertNotIn("runtimeReady", renderer)
        self.assertIn("ล็อกโดย Backend", renderer)
        self.assertIn("selectedThread?.canInterrupt !== true", renderer)
        self.assertIn("selectedThread?.canContinue !== true", renderer)

    def test_limited_chat_fallback_does_not_claim_tool_readiness(self) -> None:
        runtime_turn = function_block(self.main, "async function postAgentRuntimeTurn(subject")
        self.assertIn('profile.mode === "chat"', runtime_turn)
        self.assertIn("return { handled: false }", runtime_turn)
        self.assertIn("ไม่อ้างว่า Tool ทำงาน", runtime_turn)

        renderer = function_block(self.main, "function renderAgentRuntimeActivity(profile)")
        self.assertIn("ไม่มี Tool Call, Computer Use, MCP หรือ Plugin", renderer)
        self.assertIn("ไม่สร้าง Tool Call จำลอง", renderer)

    def test_turn_and_settings_payloads_do_not_send_credentials(self) -> None:
        turn = function_block(self.main, "async function postAgentRuntimeTurn(subject")
        settings = function_block(self.main, "async function saveAgentRuntimeThreadSettings(subject")
        create = function_block(self.main, "async function createAgentRuntimeThread(subject)")
        for block in (turn, settings, create):
            lowered = block.lower()
            for forbidden in ("accesstoken", "refreshtoken", "clientsecret", "password"):
                with self.subTest(forbidden=forbidden):
                    self.assertNotIn(forbidden, lowered)
        self.assertIn("message,", turn)
        self.assertIn("idempotencyKey:", turn)
        self.assertIn("model:", settings)
        self.assertIn("reasoning:", settings)
        self.assertIn("mode:", settings)
        self.assertIn("expectedRevision: thread.revision", settings)

    def test_thread_mutations_bind_revision_and_archive_history_is_reversible(self) -> None:
        normalizer = function_block(self.main, "function normalizeAgentRuntimeThread(item")
        loader = function_block(self.main, "async function loadAgentRuntimeWorkspace(agentId")
        archive = function_block(self.main, "async function archiveSelectedAgentRuntimeThread(subject)")
        renderer = function_block(self.main, "function renderAgentRuntimeConsole(subject)")

        self.assertIn("Number.isSafeInteger(item.revision)", normalizer)
        self.assertIn("includeArchived=true", loader)
        self.assertIn(".filter(Boolean)", loader)
        self.assertNotIn("!thread.archived", loader)
        self.assertIn("archived: nextArchived", archive)
        self.assertIn("expectedRevision: thread.revision", archive)
        self.assertIn("applyAgentRuntimeThreadPayload(profile, payload, subject)", archive)
        self.assertNotIn("delete profile.messagesByThread", archive)
        self.assertNotIn("profile.threads.filter", archive)
        self.assertIn('"นำออกจากคลัง"', renderer)
        self.assertIn("selectedThread?.archived === true", renderer)

    def test_model_catalog_drives_model_specific_default_reasoning(self) -> None:
        normalizer = function_block(self.main, "function normalizeAgentRuntimeOptionList(value")
        model_options = function_block(self.main, "function agentRuntimeReasoningOptionsForModel(modelId)")
        model_default = function_block(self.main, "function agentRuntimeDefaultReasoningForModel(modelId)")
        settings = function_block(self.main, "async function saveAgentRuntimeThreadSettings(subject")
        renderer = function_block(self.main, "function renderAgentRuntimeConsole(subject)")

        self.assertIn("defaultReasoningEffort", normalizer)
        self.assertIn("supportedReasoningEfforts", normalizer)
        self.assertIn("model.defaultReasoningEffort", model_options)
        self.assertIn("options.find((item) => item.isDefault)", model_default)
        self.assertIn('changedField === "model"', settings)
        self.assertIn("agentRuntimeDefaultReasoningForModel(profile.model)", settings)
        self.assertIn("agentRuntimeReasoningOptionsForModel(profile.model)", renderer)

    def test_async_turn_is_posted_once_then_polled_with_get_only(self) -> None:
        turn = function_block(self.main, "async function postAgentRuntimeTurn(subject")
        polling = function_block(self.main, "async function pollAgentRuntimeTurn(subject")

        self.assertEqual(turn.count("postJson(path"), 1)
        self.assertIn("pollAgentRuntimeTurn(subject, profile, thread.id", turn)
        self.assertIn("fetchJson(path", polling)
        self.assertNotIn("postJson(", polling)
        self.assertIn("waitForAgentRuntimePollDelay", polling)

    def test_async_turn_polling_is_bounded_and_renders_backend_state(self) -> None:
        timeout = re.search(
            r"const AGENT_RUNTIME_TURN_POLL_TIMEOUT_MS\s*=\s*(\d+)\s*\*\s*60\s*\*\s*1000",
            self.main,
        )
        self.assertIsNotNone(timeout)
        self.assertLessEqual(int(timeout.group(1)), 10)

        polling = function_block(self.main, "async function pollAgentRuntimeTurn(subject")
        self.assertIn("applyAgentRuntimeThreadPayload(profile, payload, subject)", polling)
        self.assertIn("renderGameModal()", polling)
        self.assertIn('"interrupt_requested"', polling)
        self.assertIn("AGENT_RUNTIME_TURN_POLL_TIMEOUT_MS", polling)

    def test_async_turn_returns_only_persisted_reply_and_surfaces_persisted_failure(self) -> None:
        polling = function_block(self.main, "async function pollAgentRuntimeTurn(subject")
        runtime_turn = function_block(self.main, "async function postAgentRuntimeTurn(subject")

        self.assertIn("agentRuntimePersistedReply(events, turnId, knownEventIds)", polling)
        self.assertIn("agentRuntimePersistedFailure(events, turnId, knownEventIds)", polling)
        self.assertIn("agent_runtime_reply_missing", polling)
        self.assertIn("agent_runtime_turn_poll_timeout", polling)
        self.assertIn("validated.persistedReply", runtime_turn)
        self.assertNotRegex(runtime_turn, r"reply:\s*validated\.reply\s*\|\|")

    def test_capability_mode_ids_remain_backend_contract_values(self) -> None:
        mode_block = self.main[
            self.main.index("const AGENT_RUNTIME_CAPABILITY_MODES") :
            self.main.index("const MEMORY_ENDPOINT")
        ]
        self.assertEqual(
            re.findall(r'\{ id: "([^"]+)"', mode_block),
            ["chat", "workspace", "computer", "full"],
        )

    def test_thread_selection_and_preferences_are_restored_without_storing_messages(self) -> None:
        save_block = function_block(self.main, "function saveSessionSnapshot()")
        restore_block = function_block(self.main, "function applySessionSnapshot(snapshot)")
        self.assertIn("agentRuntimePreferences", save_block)
        self.assertIn("selectedThreadId", save_block)
        self.assertIn("model:", save_block)
        self.assertIn("reasoning:", save_block)
        self.assertIn("mode:", save_block)
        self.assertNotIn("messagesByThread", save_block)
        self.assertIn("snapshot.agentRuntimePreferences", restore_block)

    def test_dormant_one_shot_approval_ui_is_bound_and_hidden_by_default(self) -> None:
        self.assertRegex(
            self.index,
            r'<section class="agent-runtime-approval" id="modalAgentApprovalPanel"[^>]*\shidden>',
        )
        normalizer = function_block(
            self.main,
            "function normalizeAgentRuntimeApproval(payload, expectedThreadId",
        )
        for binding in (
            "requestId",
            "threadId",
            "turnId",
            "missionId",
            "gatewayThreadId",
            "gatewayTurnId",
            "gatewayGeneration",
            "itemId",
            "requestDigest",
            "decisionNonce",
            "expiresAtMs",
        ):
            with self.subTest(binding=binding):
                self.assertIn(binding, normalizer)
        self.assertIn('threadId === String(expectedThreadId || "")', normalizer)
        self.assertIn("turnId === String(expectedTurnId)", normalizer)

        resolver = function_block(
            self.main,
            "async function resolveAgentRuntimeApproval(subject, decision)",
        )
        self.assertIn('"X-Metafx-Approval-Version"', resolver)
        self.assertIn('"X-Metafx-Approval-Nonce"', resolver)
        self.assertIn('cache: "no-store"', resolver)
        self.assertIn('result.status === "resolution_pending"', resolver)
        self.assertIn('result.status !== "resolution_committed"', resolver)
        self.assertIn("result.committed !== true", resolver)

        save_block = function_block(self.main, "function saveSessionSnapshot()")
        self.assertNotIn("pendingApproval", save_block)
        self.assertNotIn("decisionNonce", save_block)
        self.assertNotIn("data-nonce", self.index.lower())

    def test_interrupt_disables_approval_but_stop_remains_available_while_decision_settles(self) -> None:
        approval_renderer = function_block(
            self.main,
            "function renderAgentRuntimeApproval(profile, selectedThread)",
        )
        resolver = function_block(
            self.main,
            "async function resolveAgentRuntimeApproval(subject, decision)",
        )
        console_renderer = function_block(
            self.main,
            "function renderAgentRuntimeConsole(subject)",
        )
        interrupt = function_block(
            self.main,
            "async function interruptAgentRuntimeThread(subject)",
        )
        self.assertIn(
            "profile.approvalInFlight || profile.interruptInFlight || expired",
            approval_renderer,
        )
        self.assertRegex(
            resolver,
            r"profile\.approvalInFlight\s*\n\s*\|\| profile\.interruptInFlight",
        )
        stop_assignment = re.search(
            r"els\.modalAgentStopButton\.disabled\s*=\s*([^;]+);",
            console_renderer,
        )
        self.assertIsNotNone(stop_assignment)
        self.assertIn("profile.interruptInFlight", stop_assignment.group(1))
        self.assertNotIn("profile.approvalInFlight", stop_assignment.group(1))
        self.assertIn('agentRuntimeThreadEndpoint(thread?.id, "/interrupt")', interrupt)
        self.assertIn("profile.interruptInFlight = true", interrupt)

    def test_full_agent_console_has_dedicated_responsive_styles(self) -> None:
        for selector in (
            ".agent-runtime-console",
            ".agent-runtime-settings",
            ".agent-runtime-readiness",
            ".agent-runtime-activity",
            '.agent-runtime-state[data-state="limited"]',
        ):
            with self.subTest(selector=selector):
                self.assertIn(selector, self.styles)
        self.assertIn("@media (max-width: 980px)", self.styles)

    def test_capability_matrix_explains_truthful_modes_and_locked_next_action(self) -> None:
        for element_id in (
            "modalAgentCapabilityMatrix",
            "modalAgentLockGuidance",
            "modalAgentLockedReason",
            "modalAgentNextAction",
        ):
            with self.subTest(element_id=element_id):
                self.assertEqual(self.index.count(f'id="{element_id}"'), 1)

        normalizer = function_block(self.main, "function normalizeAgentRuntimeStatus(payload)")
        renderer = function_block(self.main, "function renderAgentRuntimeCapabilityMatrix(status, selectedThread)")
        guidance = function_block(self.main, "function agentRuntimeLockPresentation(status, truth)")
        self.assertIn("workspaceActivationBlockers", normalizer)
        self.assertIn("AGENT_RUNTIME_BLOCKER_PRESENTATION", normalizer)
        self.assertIn("live_write_sentinel_failed_unapproved_write", self.main)
        self.assertIn('label: "Chat"', renderer)
        self.assertIn('label: "Workspace"', renderer)
        self.assertIn('label: "Full Agent"', renderer)
        self.assertIn('row.dataset.state = mode.ready ? "ready" : "locked"', renderer)
        self.assertIn("ไม่ควบคุมคอม ไม่เรียก MCP/Plugin", renderer)
        self.assertIn("ขั้นตอนถัดไป", renderer)
        self.assertIn("Frontend จะไม่เปิด Tool เอง", guidance)
        self.assertIn("ห้ามปลดล็อก Workspace/Full Access", guidance)
        self.assertIn("#modalAgentCapabilityMatrix", self.styles)
        self.assertIn(".agent-runtime-lock-guidance", self.styles)
        self.assertIn('.agent-runtime-readiness span[data-state="locked"]', self.styles)

    def test_refresh_thread_control_uses_existing_read_only_runtime_reads(self) -> None:
        handler_start = self.main.index('els.modalAgentRefreshThread?.addEventListener("click"')
        handler_end = self.main.index('els.modalAgentArchiveThread?.addEventListener', handler_start)
        handler = self.main[handler_start:handler_end]
        self.assertIn("loadAgentRuntimeWorkspace(subject.id, { force: true })", handler)
        self.assertNotIn("postJson", handler)
        renderer = function_block(self.main, "function renderAgentRuntimeConsole(subject)")
        self.assertIn("agentRuntimeThreadMetaText(selectedThread)", renderer)
        self.assertIn("profile.loading || profile.actionInFlight", renderer)

    def test_each_agent_modal_exposes_truthful_full_access_control(self) -> None:
        for element_id in (
            "modalAgentFullAccessButton",
            "modalAgentFullAccessHelp",
            "modalAgentAttachmentBadge",
            "modalAgentArtifactBadge",
        ):
            with self.subTest(element_id=element_id):
                self.assertEqual(self.index.count(f'id="{element_id}"'), 1)

        renderer = function_block(self.main, "function renderAgentRuntimeConsole(subject)")
        self.assertIn('"Full Access · Locked"', renderer)
        self.assertIn("agentRuntimeCapabilityTruth(status)", renderer)
        truth = function_block(self.main, "function agentRuntimeCapabilityTruth(status)")
        self.assertIn('status?.fullAgentReady === true', truth)
        self.assertIn('status?.toolExecutionEnabled === true', truth)
        self.assertIn('status?.modeReadiness?.full === true', truth)
        self.assertIn('setAttribute("aria-disabled"', renderer)
        self.assertIn("profile.actionInFlight || !fullAgentReady || settingsLocked", renderer)

        handler_start = self.main.index('els.modalAgentFullAccessButton?.addEventListener("click"')
        handler_end = self.main.index('els.modalAgentStopButton?.addEventListener', handler_start)
        handler = self.main[handler_start:handler_end]
        self.assertIn("if (!fullAgentReady)", handler)
        self.assertIn("ไม่มีการข้ามสิทธิ์", handler)
        self.assertIn('saveAgentRuntimeThreadSettings(subject, "mode"', handler)

    def test_attachment_input_is_backend_gated_and_never_persists_local_files(self) -> None:
        for element_id in (
            "modalAgentAttachmentInput",
            "modalAgentAttachButton",
            "modalAgentAttachmentPolicy",
            "modalAgentAttachmentDrafts",
        ):
            with self.subTest(element_id=element_id):
                self.assertEqual(self.index.count(f'id="{element_id}"'), 1)

        normalizer = function_block(self.main, "function normalizeAgentRuntimeStatus(payload)")
        self.assertIn("attachmentContract.ready === true", normalizer)
        self.assertIn("attachmentContract.uploadTemplate === AGENT_RUNTIME_ATTACHMENT_UPLOAD_TEMPLATE", normalizer)
        self.assertIn("acceptedExtensions.length > 0", normalizer)

        uploader = function_block(self.main, "async function uploadAgentRuntimeAttachment(threadId")
        self.assertIn("fileName: draft.name", uploader)
        self.assertIn("mediaType: draft.mediaType", uploader)
        self.assertIn("dataBase64", uploader)
        self.assertIn("attachment?.modelInputReady !== true", uploader)
        self.assertNotIn("file.path", uploader)
        self.assertNotIn("webkitRelativePath", self.main)

        save_block = function_block(self.main, "function saveSessionSnapshot()")
        self.assertNotIn("attachmentDrafts", save_block)
        self.assertNotIn("dataBase64", save_block)

    def test_attachment_ids_are_sent_to_turn_only_after_upload_confirmation(self) -> None:
        turn = function_block(self.main, "async function postAgentRuntimeTurn(subject")
        sender = function_block(self.main, "async function handleModalSend()")
        self.assertIn("attachmentIds: safeAttachmentIds", turn)
        self.assertIn("await uploadPendingAgentAttachments(subject)", sender)
        self.assertIn("postAgentRuntimeTurn(subject, prompt, { attachmentIds })", sender)
        self.assertIn("clearAgentAttachmentDrafts(runtimeProfile)", sender)
        self.assertIn("attachment_turn_endpoint_unavailable", sender)

    def test_agent_artifacts_render_only_allowlisted_backend_urls_without_html_injection(self) -> None:
        url_guard = function_block(self.main, "function getSafeAgentRuntimeArtifactUrl(value)")
        normalizer = function_block(self.main, "function normalizeAgentRuntimeArtifacts(value)")
        renderer = function_block(self.main, "function appendAgentRuntimeArtifactCards(container, artifacts)")

        self.assertIn("parsed.origin !== window.location.origin", url_guard)
        self.assertIn("parsed.username", url_guard)
        self.assertIn("parsed.password", url_guard)
        self.assertIn("parsed.search", url_guard)
        self.assertIn("parsed.hash", url_guard)
        self.assertIn("/api\\/agent-runtime\\/artifacts", url_guard)
        self.assertIn("item.available !== true", normalizer)
        self.assertIn(r"image\/(?:png|jpeg|webp)", normalizer)
        self.assertIn("document.createElement", renderer)
        self.assertIn("textContent", renderer)
        self.assertIn("status?.attachments?.outputReady !== true", renderer)
        self.assertIn("เปิดตัวอย่างรูป", renderer)
        self.assertIn("ดาวน์โหลดไฟล์", renderer)
        self.assertNotIn("innerHTML", renderer)
        self.assertNotIn("item.path", normalizer)

    def test_approval_details_are_redacted_and_countdown_is_live(self) -> None:
        safe_projection = function_block(self.main, "function safeAgentRuntimeApprovalDetail(value")
        countdown = function_block(self.main, "function startAgentRuntimeApprovalCountdown(profile, approval)")
        approval_renderer = function_block(self.main, "function renderAgentRuntimeApproval(profile, selectedThread)")
        self.assertIn("client[_ -]?secret", safe_projection)
        self.assertIn("[พาธในเครื่องที่ซ่อน]", safe_projection)
        self.assertIn("window.setInterval", countdown)
        self.assertIn("updateAgentRuntimeApprovalCountdown(approval)", countdown)
        self.assertIn("startAgentRuntimeApprovalCountdown(profile, approval)", approval_renderer)
        self.assertIn('role="alertdialog"', self.index)
        self.assertIn('id="modalAgentApprovalSafety"', self.index)

    def test_attachment_composer_and_chat_keyboard_have_responsive_accessible_controls(self) -> None:
        self.assertIn(".agent-attachment-composer", self.styles)
        self.assertIn(".agent-attachment-drafts", self.styles)
        self.assertIn(".agent-runtime-artifact-gallery", self.styles)
        self.assertIn("grid-template-columns: 1fr", self.styles)
        self.assertIn('event.key !== "Enter"', self.main)
        self.assertIn("event.shiftKey", self.main)
        self.assertIn("event.isComposing", self.main)


if __name__ == "__main__":
    unittest.main()
