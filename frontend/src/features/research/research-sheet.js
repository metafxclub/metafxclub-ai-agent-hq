// Backend read models only; callers own state, rendering, requests and approvals.
function createResearchSheetModel({ safeDashboardDisplayText, consumers, linkedSystems, queryMaxMatches, queryMaxColumnsPerTab }) {
  const RESEARCH_SHEET_CONSUMERS = consumers;
  const RESEARCH_SHEET_LINKED_SYSTEMS = linkedSystems;
  const RESEARCH_SHEET_CONSUMER_PROP_IDS = new Set(consumers.map((item) => item.propId));
  const RESEARCH_SHEET_QUERY_MAX_MATCHES = queryMaxMatches;
  const RESEARCH_SHEET_QUERY_MAX_COLUMNS_PER_TAB = queryMaxColumnsPerTab;

  function normalizeResearchSheetReference(value) {
    const raw = String(value || "").replace(/\u0000/g, "").trim();
    if (!raw || raw.length > 500) return "";
    if (/^[A-Za-z0-9_-]{20,160}$/.test(raw)) return raw;
    try {
      const parsed = new URL(raw);
      if (parsed.protocol !== "https:" || parsed.hostname.toLowerCase() !== "docs.google.com") return "";
      const match = parsed.pathname.match(/^\/spreadsheets\/d\/([A-Za-z0-9_-]{20,160})(?:\/|$)/);
      return match?.[1] || "";
    } catch {
      return "";
    }
  }

  function researchSheetAuthoritativeLifecycleMatches(hub = {}, nextData = {}) {
    if (hub.dirty !== true) return true;
    const authoritativeSheetId = normalizeResearchSheetReference(nextData.sheetId);
    const attemptedSheetId = normalizeResearchSheetReference(
      hub.draftReference || hub.submittedReference,
    );
    return Boolean(
      authoritativeSheetId
      && attemptedSheetId
      && authoritativeSheetId === attemptedSheetId
    );
  }

  function boundedResearchSheetCount(value, maximum = 999_999) {
    const count = Number(value);
    return Number.isInteger(count) && count >= 0 ? Math.min(count, maximum) : 0;
  }

  function normalizeResearchSheetOutbox(value = {}) {
    const source = value && typeof value === "object" && !Array.isArray(value) ? value : {};
    return {
      pending: boundedResearchSheetCount(source.pending),
      failed: boundedResearchSheetCount(source.failed),
      synced: boundedResearchSheetCount(source.synced),
      deferred: boundedResearchSheetCount(source.deferred),
    };
  }

  function normalizeResearchSheetTimestamp(value) {
    if (typeof value !== "string" || !value.trim()) return null;
    const parsed = new Date(value);
    return Number.isNaN(parsed.getTime()) ? null : parsed.toISOString();
  }

  function normalizeResearchSheetHeaderList(value) {
    if (!Array.isArray(value)) return [];
    return [...new Set(
      value
        .slice(0, 100)
        .map((header) => safeDashboardDisplayText(header, "").slice(0, 120))
        .filter(Boolean),
    )].slice(0, 100);
  }

  function normalizeResearchSheetQueryText(value, maximum = 200) {
    return safeDashboardDisplayText(value, "")
      .replace(/\u0000/g, "")
      .trim()
      .slice(0, maximum);
  }

  function normalizeResearchSheetQueryResult(payload = {}) {
    const root = payload?.query && typeof payload.query === "object" && !Array.isArray(payload.query)
      ? payload.query
      : (payload?.result && typeof payload.result === "object" && !Array.isArray(payload.result)
          ? payload.result
          : (payload && typeof payload === "object" && !Array.isArray(payload) ? payload : {}));
    const rawMatches = Array.isArray(root.matches) ? root.matches : [];
    const matches = rawMatches.slice(0, RESEARCH_SHEET_QUERY_MAX_MATCHES).map((item) => ({
      tabName: normalizeResearchSheetQueryText(item?.tabName, 80),
      columnName: normalizeResearchSheetQueryText(item?.columnName || root.columnName, 120),
      rowNumber: boundedResearchSheetCount(item?.rowNumber, 10_000_000),
      recordKey: normalizeResearchSheetQueryText(item?.recordKey, 240),
      value: normalizeResearchSheetQueryText(item?.value, 1_000),
    }));
    const rawSearchedTabs = Array.isArray(root.searchedTabs) ? root.searchedTabs : [];
    const searchedTabs = rawSearchedTabs.slice(0, RESEARCH_SHEET_CONSUMERS.length).map((item) => ({
      tabName: normalizeResearchSheetQueryText(item?.tabName, 80),
      rowCount: boundedResearchSheetCount(item?.rowCount, 10_000_000),
      observedAt: normalizeResearchSheetTimestamp(item?.observedAt),
      availableColumns: normalizeResearchSheetHeaderList(item?.availableColumns)
        .slice(0, RESEARCH_SHEET_QUERY_MAX_COLUMNS_PER_TAB),
    }));
    if (!searchedTabs.length && Array.isArray(root.availableColumns)) {
      searchedTabs.push({
        tabName: normalizeResearchSheetQueryText(root.tabName, 80) || "แท็บที่เลือก",
        rowCount: 0,
        observedAt: null,
        availableColumns: normalizeResearchSheetHeaderList(root.availableColumns)
          .slice(0, RESEARCH_SHEET_QUERY_MAX_COLUMNS_PER_TAB),
      });
    }
    return {
      ok: root.ok === true,
      kind: /^[a-zA-Z0-9_.:-]{1,120}$/.test(String(root.kind || "")) ? String(root.kind) : "",
      columnName: normalizeResearchSheetQueryText(root.columnName, 120),
      contains: normalizeResearchSheetQueryText(root.contains, 200),
      limit: Math.max(1, boundedResearchSheetCount(root.limit, RESEARCH_SHEET_QUERY_MAX_MATCHES) || 50),
      matchCount: boundedResearchSheetCount(root.matchCount, RESEARCH_SHEET_QUERY_MAX_MATCHES),
      matches,
      searchedTabs,
      freshRead: root.freshRead === true,
      readOnly: root.readOnly === true,
      observedAt: normalizeResearchSheetTimestamp(root.observedAt),
      messageTh: normalizeResearchSheetQueryText(root.messageTh || root.message || root.error, 400),
    };
  }

  function normalizeResearchSheetHub(payload = {}) {
    const root = payload?.researchSheet && typeof payload.researchSheet === "object" && !Array.isArray(payload.researchSheet)
      ? payload.researchSheet
      : {};
    const rawSheetIdAllowed = root.rawSheetIdExposed === true;
    const sheetId = rawSheetIdAllowed
      ? normalizeResearchSheetReference(root.sheetId || root.sheetDisplayValue || root.canonicalUrl)
      : "";
    const rawTabs = root.tabs && typeof root.tabs === "object" && !Array.isArray(root.tabs) ? root.tabs : {};
    const tabs = Object.fromEntries(RESEARCH_SHEET_CONSUMERS.map(({ tabKey }) => [
      tabKey,
      safeDashboardDisplayText(rawTabs[tabKey], ""),
    ]));
    const rawConsumers = Array.isArray(root.consumers) ? root.consumers : [];
    const consumerMap = new Map();
    rawConsumers.slice(0, 20).forEach((item) => {
      const propId = String(item?.propId || "").trim();
      if (!RESEARCH_SHEET_CONSUMER_PROP_IDS.has(propId) || consumerMap.has(propId)) return;
      consumerMap.set(propId, {
        propId,
        tabName: safeDashboardDisplayText(item?.tabName, ""),
        status: String(item?.status || "unknown").trim().toLowerCase().replace(/[ -]+/g, "_").slice(0, 80),
        readReady: item?.readReady === true,
        writeReady: item?.writeReady === true,
        configurationApplied: item?.configurationApplied === true,
        rowCount: boundedResearchSheetCount(item?.rowCount),
        cachedRowCount: boundedResearchSheetCount(item?.cachedRowCount),
        observedAt: normalizeResearchSheetTimestamp(item?.observedAt || item?.rowsObservedAt),
        configRevision: safeDashboardDisplayText(item?.configRevision, ""),
        outbox: normalizeResearchSheetOutbox(item?.outbox),
      });
    });
    const consumers = RESEARCH_SHEET_CONSUMERS.map((definition) => {
      const supplied = consumerMap.get(definition.propId) || {};
      return {
        ...definition,
        propId: definition.propId,
        tabName: supplied.tabName || tabs[definition.tabKey] || "",
        status: supplied.status || "not_reported",
        readReady: supplied.readReady === true,
        writeReady: supplied.writeReady === true,
        configurationApplied: supplied.configurationApplied === true,
        rowCount: supplied.rowCount || 0,
        cachedRowCount: supplied.cachedRowCount || 0,
        observedAt: supplied.observedAt || null,
        configRevision: supplied.configRevision || "",
        outbox: normalizeResearchSheetOutbox(supplied.outbox),
      };
    });
    const consumerByPropId = new Map(consumers.map((consumer) => [consumer.propId, consumer]));
    const rawLinkedSystems = Array.isArray(root.linkedSystems) ? root.linkedSystems : [];
    const suppliedLinkedSystems = new Map();
    rawLinkedSystems.slice(0, 12).forEach((item) => {
      const systemId = String(item?.systemId || item?.id || "").trim();
      if (!RESEARCH_SHEET_LINKED_SYSTEMS.some((definition) => definition.systemId === systemId)) return;
      suppliedLinkedSystems.set(systemId, item);
    });
    const linkedSystems = RESEARCH_SHEET_LINKED_SYSTEMS.map((definition) => {
      const supplied = suppliedLinkedSystems.get(definition.systemId) || {};
      const source = consumerByPropId.get(definition.sourcePropId) || {};
      return {
        ...definition,
        tabName: safeDashboardDisplayText(supplied.tabName || supplied.sourceTabName, "") || source.tabName || "",
        status: String(supplied.status || source.status || "not_reported").trim().toLowerCase().replace(/[ -]+/g, "_").slice(0, 80),
        ready: supplied.ready === true || (!Object.keys(supplied).length && source.readReady === true),
        rowCount: boundedResearchSheetCount(supplied.rowCount ?? source.rowCount),
        cachedRowCount: boundedResearchSheetCount(supplied.cachedRowCount ?? source.cachedRowCount),
        observedAt: normalizeResearchSheetTimestamp(
          supplied.observedAt || supplied.rowsObservedAt || source.observedAt,
        ),
        configRevision: safeDashboardDisplayText(supplied.configRevision, "") || source.configRevision || "",
        outbox: normalizeResearchSheetOutbox(supplied.outbox || source.outbox),
      };
    });
    const rawOutbox = root.outbox && typeof root.outbox === "object" && !Array.isArray(root.outbox) ? root.outbox : {};
    const configRevision = safeDashboardDisplayText(root.configRevision, "");
    const activeConfigRevision = safeDashboardDisplayText(root.activeConfigRevision, "");
    return {
      schemaVersion: safeDashboardDisplayText(root.schemaVersion, ""),
      configured: root.configured === true,
      active: root.active === true,
      operational: root.operational === true,
      sheetId,
      canonicalUrl: sheetId ? `https://docs.google.com/spreadsheets/d/${sheetId}` : "",
      sheetReferenceMasked: safeDashboardDisplayText(root.sheetReferenceMasked, ""),
      sheetTitle: safeDashboardDisplayText(root.sheetTitle, ""),
      applyPhase: String(root.applyPhase || "idle").trim().toLowerCase().replace(/[ -]+/g, "_").slice(0, 80),
      applyStatus: String(root.applyStatus || "unknown").trim().toLowerCase().replace(/[ -]+/g, "_").slice(0, 80),
      verificationStatus: String(root.verificationStatus || "unknown").trim().toLowerCase().replace(/[ -]+/g, "_").slice(0, 80),
      totalConsumerCount: boundedResearchSheetCount(root.totalConsumerCount, consumers.length) || consumers.length,
      appliedConsumerCount: boundedResearchSheetCount(root.appliedConsumerCount, consumers.length),
      verifiedConsumerCount: boundedResearchSheetCount(root.verifiedConsumerCount, consumers.length),
      allConsumersApplied: root.allConsumersApplied === true,
      allConsumersVerified: root.allConsumersVerified === true,
      connected: root.connected === true,
      readReady: root.readReady === true,
      writeReady: root.writeReady === true,
      adapterStatus: String(root.adapterStatus || "unknown").trim().toLowerCase().replace(/[ -]+/g, "_").slice(0, 80),
      authStatus: String(root.authStatus || "unknown").trim().toLowerCase().replace(/[ -]+/g, "_").slice(0, 80),
      credentialMode: String(root.credentialMode || root.authMode || "unknown").trim().toLowerCase().replace(/[ -]+/g, "_").slice(0, 80),
      configRevision,
      activeConfigRevision,
      savedAt: normalizeResearchSheetTimestamp(root.savedAt),
      activationConfirmedAt: normalizeResearchSheetTimestamp(root.activationConfirmedAt),
      lastVerifiedAt: normalizeResearchSheetTimestamp(root.lastVerifiedAt),
      lastErrorCode: /^[a-zA-Z0-9_.:-]{1,120}$/.test(String(root.lastErrorCode || ""))
        ? String(root.lastErrorCode)
        : "",
      tabs,
      consumers,
      linkedSystems,
      outbox: normalizeResearchSheetOutbox(rawOutbox),
      credentialsAcceptedByFrontend: false,
      rawSheetIdExposed: Boolean(rawSheetIdAllowed && sheetId),
    };
  }

  function normalizeResearchSheetGoogleAuth(payload = {}) {
    const candidates = [
      payload?.googleAuth,
      payload?.researchSheetAuth,
      payload?.auth,
      payload?.researchSheet?.googleAuth,
      payload?.researchSheet?.auth,
      payload,
    ];
    const root = candidates.find((item) => item && typeof item === "object" && !Array.isArray(item)) || {};
    const status = String(
      root.status || root.authStatus || root.connectionStatus || payload?.authStatus || "unknown",
    ).trim().toLowerCase().replace(/[ -]+/g, "_").slice(0, 80);
    const connectedStatuses = new Set(["connected", "authenticated", "authorized", "ready"]);
    const adminSetupStatuses = new Set([
      "admin_setup_required",
      "backend_client_missing",
      "client_not_configured",
      "oauth_client_not_configured",
      "not_configured",
    ]);
    const connected = root.connected === true
      || root.authenticated === true
      || root.authorized === true
      || connectedStatuses.has(status);
    const clientConfigured = connected
      || root.clientConfigured === true
      || root.oauthClientConfigured === true
      || root.providerConfigured === true;
    const requiresAdminSetup = root.requiresAdminSetup === true
      || root.adminSetupRequired === true
      || (!clientConfigured && adminSetupStatuses.has(status));
    const explicitStartAvailable = root.startAvailable ?? root.canStartOAuth ?? root.authorizationAvailable;
    const startAvailable = connected || (
      explicitStartAvailable === true
      || (explicitStartAvailable !== false && clientConfigured && !requiresAdminSetup)
    );
    return {
      status,
      connected,
      clientConfigured,
      requiresAdminSetup,
      startAvailable,
      accountHint: safeDashboardDisplayText(
        root.accountHint || root.accountEmailMasked || root.emailMasked || root.accountLabel,
        "",
      ),
      messageTh: safeDashboardDisplayText(root.messageTh || root.message, ""),
      connectedAt: normalizeResearchSheetTimestamp(root.connectedAt || root.authorizedAt),
      clientHint: safeDashboardDisplayText(
        root.clientHint || root.oauthClientHint,
        "",
      ),
      clientSource: String(root.clientSource || root.oauthClientSource || "not_configured")
        .trim().toLowerCase().replace(/[ -]+/g, "_").slice(0, 80),
      credentialsAcceptedByFrontend: false,
    };
  }

  function normalizeResearchSheetAuthorizationUrl(value) {
    try {
      const parsed = new URL(String(value || ""));
      if (parsed.protocol !== "https:" || parsed.hostname.toLowerCase() !== "accounts.google.com") return "";
      if (parsed.username || parsed.password || (parsed.port && parsed.port !== "443")) return "";
      return parsed.toString();
    } catch {
      return "";
    }
  }

  function researchSheetGoogleAuthFailureReason(error = null) {
    const body = error?.body && typeof error.body === "object" && !Array.isArray(error.body)
      ? error.body
      : {};
    const code = String(
      body.code || body.errorCode || body.kind || body.error || error?.code || "auth_unavailable",
    ).trim().toLowerCase().replace(/[ -]+/g, "_").slice(0, 120);
    const reasons = {
      access_denied: "คุณยกเลิกสิทธิ์ หรือ Google ไม่อนุญาตการเชื่อมต่อบัญชีนี้ • ลองใหม่ด้วยบัญชี Google ที่ถูกต้อง หากยังไม่ผ่านให้ติดต่อผู้สอน",
      admin_setup_required: "ผู้ดูแลยังไม่ได้ตั้ง Google OAuth Client ที่ Local Bridge",
      auth_expired: "สิทธิ์ Google หมดอายุ กรุณาเชื่อมบัญชีใหม่",
      backend_client_missing: "ผู้ดูแลยังไม่ได้ตั้ง Google OAuth Client ที่ Local Bridge",
      client_not_configured: "ผู้ดูแลยังไม่ได้ตั้ง Google OAuth Client ที่ Local Bridge",
      oauth_client_not_configured: "ผู้ดูแลยังไม่ได้ตั้ง Google OAuth Client ที่ Local Bridge",
      oauth_failed: "Google ไม่สามารถยืนยันการเชื่อมต่อครั้งนี้ได้",
      oauth_error: "Google ไม่สามารถยืนยันการเชื่อมต่อครั้งนี้ได้",
      popup_blocked: "Browser บล็อกหน้าต่าง Google กรุณาอนุญาต Pop-up แล้วลองใหม่",
      popup_closed: "หน้าต่าง Google ถูกปิดก่อนยืนยันเสร็จ",
      state_invalid: "คำขอเชื่อมต่อหมดอายุหรือไม่ตรงกับ Session นี้",
      timeout: "รอการยืนยันจาก Google เกิน 2 นาที กรุณาลองใหม่",
    };
    return reasons[code]
      || safeDashboardDisplayText(body.messageTh || body.message || error?.message, "")
      || "ยังตรวจสถานะบัญชี Google จาก Backend ไม่ได้";
  }

  function researchSheetGoogleAuthIsTerminalStatus(status) {
    return new Set([
      "access_denied",
      "admin_setup_required",
      "backend_client_missing",
      "callback_failed",
      "client_not_configured",
      "oauth_client_not_configured",
      "oauth_error",
      "oauth_failed",
      "state_invalid",
    ]).has(String(status || "").trim().toLowerCase());
  }

  function normalizeResearchSheetInspection(payload = {}) {
    const root = payload?.verificationPreview && typeof payload.verificationPreview === "object" && !Array.isArray(payload.verificationPreview)
      ? payload.verificationPreview
      : {};
    const sheetId = normalizeResearchSheetReference(root.sheetId || root.canonicalUrl);
    const rawConsumers = Array.isArray(root.consumers) ? root.consumers : [];
    const consumerMap = new Map();
    rawConsumers.slice(0, 12).forEach((item) => {
      const propId = String(item?.propId || "").trim();
      if (!RESEARCH_SHEET_CONSUMER_PROP_IDS.has(propId) || consumerMap.has(propId)) return;
      const evidence = item?.probeEvidence && typeof item.probeEvidence === "object" && !Array.isArray(item.probeEvidence)
        ? item.probeEvidence
        : {};
      consumerMap.set(propId, {
        propId,
        tabName: safeDashboardDisplayText(item?.tabName, ""),
        status: String(item?.status || "unknown").trim().toLowerCase().replace(/[ -]+/g, "_").slice(0, 80),
        readReady: item?.readReady === true,
        rowCount: boundedResearchSheetCount(item?.rowCount),
        cachedRowCount: boundedResearchSheetCount(item?.cachedRowCount),
        observedAt: normalizeResearchSheetTimestamp(item?.observedAt || item?.rowsObservedAt),
        missingHeaders: normalizeResearchSheetHeaderList(item?.missingHeaders),
        duplicateHeaders: normalizeResearchSheetHeaderList(item?.duplicateHeaders),
        probeEvidence: {
          kind: safeDashboardDisplayText(evidence.kind, ""),
          range: safeDashboardDisplayText(evidence.range, ""),
          confirmed: evidence.confirmed === true,
        },
      });
    });
    const consumers = RESEARCH_SHEET_CONSUMERS.map((definition) => ({
      ...definition,
      ...(consumerMap.get(definition.propId) || {
        tabName: "",
        status: "not_reported",
        readReady: false,
        rowCount: 0,
        cachedRowCount: 0,
        observedAt: null,
        missingHeaders: [],
        duplicateHeaders: [],
        probeEvidence: { kind: "", range: "", confirmed: false },
      }),
    }));
    const verificationToken = typeof root.verificationToken === "string"
      && /^[A-Za-z0-9_-]{32,128}$/.test(root.verificationToken)
      ? root.verificationToken
      : "";
    const verifiedConsumerCount = boundedResearchSheetCount(root.verifiedConsumerCount, consumers.length);
    const allConsumersReady = consumers.every((consumer) => (
      consumer.readReady === true && consumer.probeEvidence.confirmed === true
    ));
    return {
      sheetId,
      canonicalUrl: sheetId ? `https://docs.google.com/spreadsheets/d/${sheetId}` : "",
      sheetTitle: safeDashboardDisplayText(root.sheetTitle, ""),
      baseConfigRevision: boundedResearchSheetCount(root.baseConfigRevision, 999_999),
      status: String(root.status || "unknown").trim().toLowerCase().replace(/[ -]+/g, "_").slice(0, 80),
      expiresAt: normalizeResearchSheetTimestamp(root.expiresAt),
      verificationToken,
      totalConsumerCount: boundedResearchSheetCount(root.totalConsumerCount, consumers.length) || consumers.length,
      verifiedConsumerCount,
      consumers,
      readyForConfirmation: root.readyForConfirmation === true
        && Boolean(sheetId)
        && Boolean(verificationToken)
        && verifiedConsumerCount === consumers.length
        && allConsumersReady,
    };
  }

  return {
    normalizeResearchSheetReference,
    researchSheetAuthoritativeLifecycleMatches,
    boundedResearchSheetCount,
    normalizeResearchSheetOutbox,
    normalizeResearchSheetTimestamp,
    normalizeResearchSheetHeaderList,
    normalizeResearchSheetQueryText,
    normalizeResearchSheetQueryResult,
    normalizeResearchSheetHub,
    normalizeResearchSheetGoogleAuth,
    normalizeResearchSheetAuthorizationUrl,
    researchSheetGoogleAuthFailureReason,
    researchSheetGoogleAuthIsTerminalStatus,
    normalizeResearchSheetInspection,
  };
}

export { createResearchSheetModel };
