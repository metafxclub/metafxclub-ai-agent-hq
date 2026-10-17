// Backend read models only; callers own state, rendering, requests and approvals.
function createMeetingSessionModel({ getOfficeAgent }) {
  function normalizeMeetingText(value, maxLength = 4000) {
    if (value === null || value === undefined) return "";
    return String(value).replace(/\u0000/g, "").trim().slice(0, maxLength);
  }

  function normalizeMeetingTextList(value, maximumItems, maximumChars) {
    if (!Array.isArray(value)) return [];
    return value
      .slice(0, Math.max(0, Number(maximumItems) || 0))
      .filter((item) => ["string", "number"].includes(typeof item))
      .map((item) => normalizeMeetingText(item, maximumChars))
      .filter(Boolean);
  }

  function normalizeMeetingParticipant(value) {
    const raw = value && typeof value === "object" && !Array.isArray(value)
      ? value
      : { agentId: value };
    const agentId = normalizeMeetingText(raw.agentId || raw.id || raw.participantAgentId, 160);
    const agent = agentId ? getOfficeAgent(agentId) : null;
    const name = normalizeMeetingText(raw.name || raw.displayName || raw.agentName, 160)
      || normalizeMeetingText(agent?.name, 160)
      || agentId
      || "Backend ไม่ระบุชื่อ";
    return {
      agentId,
      name,
      role: normalizeMeetingText(raw.role || raw.agentRole, 160)
        || normalizeMeetingText(agent?.role, 160)
        || "Backend ไม่ระบุบทบาท",
      status: normalizeMeetingText(raw.status || raw.participantStatus, 80),
    };
  }

  function normalizeMeetingMessage(value, index = 0) {
    if (!value || typeof value !== "object" || Array.isArray(value)) return null;
    const text = normalizeMeetingText(value.message ?? value.text ?? value.content ?? value.body, 12000);
    if (!text) return null;
    const speakerAgentId = normalizeMeetingText(
      value.speakerAgentId || value.agentId || value.fromAgentId || value.speakerId,
      160,
    );
    const agent = speakerAgentId ? getOfficeAgent(speakerAgentId) : null;
    const rawSpeakerKind = normalizeMeetingText(
      value.speakerType || value.authorType || value.senderType || value.role,
      80,
    ).toLowerCase();
    const isUser = value.isUser === true || ["user", "human", "operator"].includes(rawSpeakerKind);
    return {
      id: normalizeMeetingText(value.id || value.messageId || value.turnId, 200) || `message-${index}`,
      speakerAgentId,
      speakerName: normalizeMeetingText(value.speakerName || value.speakerLabel || value.authorName, 160)
        || (isUser ? "คุณ" : normalizeMeetingText(agent?.name, 160))
        || "Backend ไม่ระบุผู้พูด",
      speakerRole: normalizeMeetingText(value.speakerRole || value.agentRole || value.authorRole, 160)
        || (isUser ? "ผู้ใช้" : normalizeMeetingText(agent?.role, 160))
        || "Backend ไม่ระบุบทบาท",
      speakerStatus: normalizeMeetingText(value.status || value.turnStatus, 80),
      createdAt: normalizeMeetingText(value.createdAt || value.timestamp || value.time, 80),
      text,
      isUser,
    };
  }

  function normalizeMeetingProposal(rawSession = {}) {
    const canonicalSessionProposal = rawSession.proposal
      && typeof rawSession.proposal === "object"
      && !Array.isArray(rawSession.proposal)
      ? rawSession.proposal
      : null;
    const nested = canonicalSessionProposal
      || (rawSession.implementationProposal
        && typeof rawSession.implementationProposal === "object"
        && !Array.isArray(rawSession.implementationProposal)
        ? rawSession.implementationProposal
        : {});
    const implementationMission = nested.implementationMission && typeof nested.implementationMission === "object"
      ? nested.implementationMission
      : rawSession.implementationMission && typeof rawSession.implementationMission === "object"
        ? rawSession.implementationMission
        : {};
    const approval = rawSession.approval && typeof rawSession.approval === "object"
      ? rawSession.approval
      : nested.approval && typeof nested.approval === "object"
        ? nested.approval
        : {};
    const sessionManagerDecision = rawSession.managerDecision
      && typeof rawSession.managerDecision === "object"
      && !Array.isArray(rawSession.managerDecision)
      ? rawSession.managerDecision
      : {};
    const nestedManagerDecision = nested.managerDecision
      && typeof nested.managerDecision === "object"
      && !Array.isArray(nested.managerDecision)
      ? nested.managerDecision
      : sessionManagerDecision.decision
        && typeof sessionManagerDecision.decision === "object"
        && !Array.isArray(sessionManagerDecision.decision)
        ? sessionManagerDecision.decision
        : {};
    const structuredProposal = [
      nested.proposal,
      nested.structuredProposal,
      rawSession.structuredProposal,
      sessionManagerDecision.proposal,
    ].find((candidate) => (
      ["string", "number"].includes(typeof candidate)
      && String(candidate).trim()
    ));
    const risks = Array.isArray(nested.risks) ? nested.risks : sessionManagerDecision.risks;
    const acceptanceChecks = Array.isArray(nested.acceptanceChecks)
      ? nested.acceptanceChecks
      : sessionManagerDecision.acceptanceChecks;
    const summary = normalizeMeetingText(
      nested.text
      || nested.summary
      || nested.plan
      || rawSession.proposalSummary
      || (typeof rawSession.proposal === "string" ? rawSession.proposal : ""),
      8000,
    );
    const normalizedStructuredProposal = normalizeMeetingText(structuredProposal, 700);
    const normalizedRisks = normalizeMeetingTextList(risks, 3, 240);
    const normalizedAcceptanceChecks = normalizeMeetingTextList(acceptanceChecks, 4, 240);
    const managerDecisionStatus = normalizeMeetingText(nestedManagerDecision.status, 80).toLowerCase();
    const managerDecisionSummary = normalizeMeetingText(nestedManagerDecision.summary, 360);
    const digest = normalizeMeetingText(
      nested.digest || nested.proposalDigest || rawSession.proposalDigest,
      256,
    );
    const digestVersion = normalizeMeetingText(nested.digestVersion, 120);
    const managerTurnId = normalizeMeetingText(
      nested.managerTurnId || sessionManagerDecision.turnId,
      200,
    );
    const risksAreComplete = Array.isArray(nested.risks)
      && nested.risks.length <= 3
      && normalizedRisks.length === nested.risks.length
      && nested.risks.every((item, index) => (
        typeof item === "string"
        && normalizeMeetingText(item, 240) === item
        && normalizedRisks[index] === item
      ));
    const checksAreComplete = Array.isArray(nested.acceptanceChecks)
      && nested.acceptanceChecks.length <= 4
      && normalizedAcceptanceChecks.length === nested.acceptanceChecks.length
      && nested.acceptanceChecks.every((item, index) => (
        typeof item === "string"
        && normalizeMeetingText(item, 240) === item
        && normalizedAcceptanceChecks[index] === item
      ));
    const managerDecisionIsComplete = nested.managerDecision
      && typeof nested.managerDecision === "object"
      && !Array.isArray(nested.managerDecision)
      && Object.keys(nested.managerDecision).sort().join(",") === "status,summary"
      && ["accepted", "revision_required", "rejected", "deferred"].includes(managerDecisionStatus)
      && managerDecisionStatus === nested.managerDecision.status
      && Boolean(managerDecisionSummary)
      && managerDecisionSummary === nested.managerDecision.summary;
    const optionalAliasesAreConsistent = (
      (!Object.prototype.hasOwnProperty.call(nested, "structuredProposal")
        || nested.structuredProposal === nested.proposal)
      && (!Object.prototype.hasOwnProperty.call(nested, "summary")
        || nested.summary === nested.text)
      && (!Object.prototype.hasOwnProperty.call(nested, "plan")
        || nested.plan === nested.text)
      && (!Object.prototype.hasOwnProperty.call(nested, "proposalDigest")
        || nested.proposalDigest === nested.digest)
    );
    const visibleConsentPacketComplete = Boolean(
      canonicalSessionProposal
      && typeof nested.text === "string"
      && summary
      && summary === nested.text
      && typeof nested.proposal === "string"
      && normalizedStructuredProposal
      && normalizedStructuredProposal === nested.proposal
      && risksAreComplete
      && checksAreComplete
      && managerDecisionIsComplete
      && optionalAliasesAreConsistent
      && typeof nested.digest === "string"
      && /^[0-9a-f]{64}$/.test(digest)
      && digest === nested.digest
      && typeof nested.digestVersion === "string"
      && digestVersion === "interactive-meeting-proposal-v2"
      && digestVersion === nested.digestVersion
      && typeof nested.managerTurnId === "string"
      && managerTurnId
      && managerTurnId === nested.managerTurnId
    );
    return {
      summary,
      structuredProposal: normalizedStructuredProposal,
      risks: normalizedRisks,
      acceptanceChecks: normalizedAcceptanceChecks,
      managerDecision: {
        status: managerDecisionStatus,
        summary: managerDecisionSummary,
      },
      digest,
      digestVersion,
      managerTurnId,
      visibleConsentPacketComplete,
      implementationMissionId: normalizeMeetingText(
        nested.implementationMissionId
        || rawSession.implementationMissionId
        || approval.implementationMissionId
        || implementationMission.id
        || implementationMission.missionId,
        200,
      ),
      status: normalizeMeetingText(
        nested.status
        || rawSession.proposalStatus
        || approval.status
        || rawSession.approvalStatus
        || rawSession.status,
        80,
      ).toLowerCase(),
      readyToExecute: nested.readyToExecute === true
        || rawSession.readyToExecute === true
        || approval.readyToExecute === true
        || implementationMission.readyToExecute === true,
      frozenAt: normalizeMeetingText(nested.frozenAt || nested.createdAt || rawSession.proposalFrozenAt, 80),
    };
  }

  function normalizeMeetingSession(value) {
    if (!value || typeof value !== "object" || Array.isArray(value)) return null;
    const id = normalizeMeetingText(value.id || value.sessionId, 200);
    if (!id) return null;
    const participantSource = Array.isArray(value.participants)
      ? value.participants
      : Array.isArray(value.participantAgentIds)
        ? value.participantAgentIds
        : [];
    const messageSource = Array.isArray(value.messages)
      ? value.messages
      : Array.isArray(value.transcript)
        ? value.transcript
        : Array.isArray(value.turns)
          ? value.turns
          : [];
    const progress = value.progress && typeof value.progress === "object" && !Array.isArray(value.progress)
      ? value.progress
      : {};
    const latestManagerDecisionTurn = [...messageSource].reverse().find((item) => (
      item
      && typeof item === "object"
      && !Array.isArray(item)
      && item.role === "agent"
      && item.speakerAgentId === "manager"
      && item.intent === "decision"
    ));
    const decision = value.managerDecision
      ?? value.decision
      ?? value.decisionSummary
      ?? latestManagerDecisionTurn?.message;
    const nestedDecision = decision
      && typeof decision === "object"
      && !Array.isArray(decision)
      && decision.decision
      && typeof decision.decision === "object"
      && !Array.isArray(decision.decision)
      ? decision.decision
      : {};
    const decisionText = decision && typeof decision === "object" && !Array.isArray(decision)
      ? [
          decision.message,
          decision.summary,
          decision.text,
          nestedDecision.summary,
          nestedDecision.message,
          typeof decision.decision === "string" ? decision.decision : "",
          latestManagerDecisionTurn?.message,
        ].find((candidate) => (
          ["string", "number"].includes(typeof candidate)
          && String(candidate).trim()
        )) || ""
      : decision;
    const roundCount = Number.isFinite(Number(progress.currentRound ?? value.currentRound ?? value.roundCount))
      ? Math.max(0, Math.floor(Number(progress.currentRound ?? value.currentRound ?? value.roundCount)))
      : null;
    const currentRoundTurns = roundCount === null
      ? []
      : messageSource.filter((item) => Number(item?.roundNumber) === roundCount);
    const configuredAiTurns = Number(
      value.aiTurnsPerRound
      ?? value.ai_turns_per_round
      ?? progress.aiTurnsPerRound
      ?? value.maxTurnsPerRound,
    );
    const agenda = normalizeMeetingText(value.agenda || value.topic || value.title, 2400);
    const developmentGoal = normalizeMeetingText(
      value.developmentGoal || value.development_goal || value.goal || value.developmentObjective,
      2400,
    );
    const visibleMeetingContextComplete = Boolean(
      typeof value.agenda === "string"
      && agenda
      && agenda === value.agenda
      && typeof value.developmentGoal === "string"
      && developmentGoal
      && developmentGoal === value.developmentGoal
      && Number.isInteger(value.aiTurnsPerRound)
      && value.aiTurnsPerRound >= 2
      && value.aiTurnsPerRound <= 8
      && configuredAiTurns === value.aiTurnsPerRound
    );
    return {
      id,
      agenda,
      developmentGoal,
      aiTurnsPerRound: Number.isInteger(configuredAiTurns) && configuredAiTurns >= 2 && configuredAiTurns <= 8
        ? configuredAiTurns
        : null,
      status: normalizeMeetingText(value.status || value.sessionStatus, 80).toLowerCase() || "unknown",
      participants: participantSource.map(normalizeMeetingParticipant),
      messages: messageSource.map(normalizeMeetingMessage).filter(Boolean),
      currentRound: roundCount,
      totalRounds: Number.isFinite(Number(progress.totalRounds ?? value.totalRounds ?? value.maxRounds))
        ? Math.max(0, Math.floor(Number(progress.totalRounds ?? value.totalRounds ?? value.maxRounds)))
        : null,
      currentTurn: Number.isFinite(Number(progress.currentTurn ?? value.currentTurn))
        ? Math.max(0, Math.floor(Number(progress.currentTurn ?? value.currentTurn)))
        : roundCount !== null
          ? currentRoundTurns.length
        : null,
      totalTurns: Number.isFinite(Number(progress.totalTurns ?? value.totalTurns ?? value.maxTurnsPerRound))
        ? Math.max(0, Math.floor(Number(progress.totalTurns ?? value.totalTurns ?? value.maxTurnsPerRound)))
        : null,
      managerDecision: normalizeMeetingText(decisionText, 8000),
      managerDecisionAt: normalizeMeetingText(
        (decision && typeof decision === "object" ? decision.createdAt || decision.decidedAt : "")
        || latestManagerDecisionTurn?.createdAt
        || value.decisionAt,
        80,
      ),
      proposal: normalizeMeetingProposal(value),
      visibleMeetingContextComplete,
      approvalNote: normalizeMeetingText(value.approvalNote, 1200),
      createdAt: normalizeMeetingText(value.createdAt || value.startedAt, 80),
      updatedAt: normalizeMeetingText(value.updatedAt || value.completedAt || value.createdAt, 80),
    };
  }

  function normalizeMeetingSessionPayload(payload) {
    const value = payload?.session ?? payload?.data?.session ?? payload?.data ?? payload;
    if (!value || typeof value !== "object" || Array.isArray(value)) return null;
    const envelope = payload && typeof payload === "object" && !Array.isArray(payload) ? payload : {};
    return normalizeMeetingSession({
      ...value,
      status: envelope.status ?? value.status,
      implementationMissionId: envelope.implementationMissionId ?? value.implementationMissionId,
      implementationMission: envelope.mission ?? value.implementationMission,
      readyToExecute: envelope.readyToExecute ?? value.readyToExecute,
    });
  }

  function normalizeMeetingSessionsPayload(payload) {
    const values = Array.isArray(payload)
      ? payload
      : Array.isArray(payload?.sessions)
        ? payload.sessions
        : Array.isArray(payload?.items)
          ? payload.items
          : Array.isArray(payload?.data?.sessions)
            ? payload.data.sessions
            : [];
    return values.map(normalizeMeetingSession).filter(Boolean);
  }

  return {
    normalizeMeetingText,
    normalizeMeetingTextList,
    normalizeMeetingParticipant,
    normalizeMeetingMessage,
    normalizeMeetingProposal,
    normalizeMeetingSession,
    normalizeMeetingSessionPayload,
    normalizeMeetingSessionsPayload,
  };
}

export { createMeetingSessionModel };
