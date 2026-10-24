// Backend read models only; callers own state, rendering, requests and approvals.
function createCodexRateModel({ clamp, formatCodexRatePercent }) {
  function normalizeCodexRateTimestamp(value) {
    if (value === null || value === undefined || value === "") return null;
    const numericValue = typeof value === "number" || /^\d+(?:\.\d+)?$/.test(String(value).trim())
      ? Number(value)
      : null;
    const milliseconds = Number.isFinite(numericValue)
      ? (numericValue < 1_000_000_000_000 ? numericValue * 1000 : numericValue)
      : value;
    const date = new Date(milliseconds);
    return Number.isFinite(date.getTime()) ? date.toISOString() : null;
  }

  function normalizeCodexRateWindow(value) {
    if (!value || typeof value !== "object" || Array.isArray(value)) return null;
    const parsePercent = (raw) => {
      if (raw === null || raw === undefined || raw === "" || typeof raw === "boolean") return Number.NaN;
      const numeric = Number(raw);
      return Number.isFinite(numeric) && numeric >= 0 && numeric <= 100 ? numeric : Number.NaN;
    };
    const hasUsed = Object.prototype.hasOwnProperty.call(value, "usedPercent");
    const hasRemaining = Object.prototype.hasOwnProperty.call(value, "remainingPercent");
    const rawUsed = parsePercent(value.usedPercent);
    const rawRemaining = parsePercent(value.remainingPercent);
    if ((hasUsed && !Number.isFinite(rawUsed)) || (hasRemaining && !Number.isFinite(rawRemaining))) return null;
    if (!Number.isFinite(rawUsed) && !Number.isFinite(rawRemaining)) return null;
    if (Number.isFinite(rawUsed) && Number.isFinite(rawRemaining) && Math.abs((rawUsed + rawRemaining) - 100) > 1) return null;
    const usedPercent = clamp(Number.isFinite(rawUsed) ? rawUsed : 100 - rawRemaining, 0, 100);
    const durationValue = Number(value.windowDurationMinutes ?? value.windowDurationMins);
    return {
      usedPercent,
      remainingPercent: clamp(100 - usedPercent, 0, 100),
      windowDurationMinutes: Number.isFinite(durationValue) && durationValue > 0
        ? Math.round(durationValue)
        : null,
      resetsAt: normalizeCodexRateTimestamp(value.resetsAt),
    };
  }

  function normalizeCodexRateReservePercent(...values) {
    for (const value of values) {
      if (
        value === null
        || value === undefined
        || typeof value === "boolean"
        || typeof value === "object"
        || String(value).trim() === ""
      ) continue;
      const numeric = Number(value);
      if (Number.isInteger(numeric) && numeric >= 0 && numeric <= 100) return numeric;
    }
    return null;
  }

  function codexRateLimitWasReached(value) {
    if (value === true) return true;
    if (typeof value !== "string") return false;
    const normalized = value.trim().toLowerCase();
    return Boolean(normalized && !["none", "null", "false", "available"].includes(normalized));
  }

  function normalizeCodexRatePayload(payload) {
    if (!payload || typeof payload !== "object" || Array.isArray(payload)) {
      return { status: "unavailable", primary: null, secondary: null };
    }

    const buckets = Array.isArray(payload.buckets) ? payload.buckets : [];
    const canonicalBucket = buckets.find((item) => String(item?.id || item?.limitId || "").toLowerCase() === "codex")
      || buckets[0]
      || null;
    const nestedSnapshot = canonicalBucket
      || payload.rateLimit
      || payload.rateLimits
      || payload.snapshot
      || payload;
    const windows = nestedSnapshot?.windows && typeof nestedSnapshot.windows === "object"
      ? nestedSnapshot.windows
      : nestedSnapshot;
    const primary = normalizeCodexRateWindow(windows?.primary);
    const secondary = normalizeCodexRateWindow(windows?.secondary);
    const primaryProvided = windows?.primary !== null && windows?.primary !== undefined;
    const secondaryProvided = windows?.secondary !== null && windows?.secondary !== undefined;
    const invalidQuotaWindow = (primaryProvided && !primary) || (secondaryProvided && !secondary);
    const rawStatus = String(payload.status || nestedSnapshot?.status || "").trim().toLowerCase();
    const stale = Boolean(payload.stale || nestedSnapshot?.stale || rawStatus === "stale");
    const reachedValue = nestedSnapshot?.limitReached
      ?? nestedSnapshot?.rateLimitReached
      ?? nestedSnapshot?.rateLimitReachedType;
    const policy = payload.policy && typeof payload.policy === "object" ? payload.policy : {};
    const automationPolicy = payload.automationPolicy && typeof payload.automationPolicy === "object"
      ? payload.automationPolicy
      : {};
    const settings = payload.settings && typeof payload.settings === "object" ? payload.settings : {};
    const preferences = payload.agentPreferences && typeof payload.agentPreferences === "object"
      ? payload.agentPreferences
      : {};
    const nestedPolicy = nestedSnapshot?.policy && typeof nestedSnapshot.policy === "object"
      ? nestedSnapshot.policy
      : {};
    const rateReservePercent = normalizeCodexRateReservePercent(
      payload.rateReservePercent,
      payload.minRemainingPercent,
      policy.rateReservePercent,
      policy.minRemainingPercent,
      automationPolicy.rateReservePercent,
      automationPolicy.minRemainingPercent,
      settings.rateReservePercent,
      preferences.rateReservePercent,
      nestedSnapshot?.rateReservePercent,
      nestedSnapshot?.minRemainingPercent,
      nestedPolicy.rateReservePercent,
      nestedPolicy.minRemainingPercent,
    );

    const checkedAt = normalizeCodexRateTimestamp(
      payload.capturedAt || payload.checkedAt || payload.updatedAt || nestedSnapshot?.capturedAt,
    );
    const unavailableStatus = ["auth_required", "config_error", "timeout", "missing", "unavailable"].includes(rawStatus)
      ? rawStatus : "unavailable";
    const sourceReady = !rawStatus || ["ready", "ok", "available"].includes(rawStatus);
    return {
      status: primary && !invalidQuotaWindow
        ? (stale ? "stale" : sourceReady && checkedAt ? "ready" : unavailableStatus)
        : unavailableStatus,
      source: "codex_app_server",
      meter: "codex",
      primary: invalidQuotaWindow ? null : primary,
      secondary: invalidQuotaWindow ? null : secondary,
      quotaWindowsValid: !invalidQuotaWindow,
      limitReached: codexRateLimitWasReached(reachedValue),
      rateReservePercent,
      checkedAt,
    };
  }

  function codexRatePolicyRemainingPercent(snapshot) {
    if (snapshot?.quotaWindowsValid === false) return null;
    const windows = [snapshot?.primary];
    if (snapshot?.secondary !== null && snapshot?.secondary !== undefined) windows.push(snapshot.secondary);
    if (!windows[0] || windows.some((windowData) => !windowData || typeof windowData !== "object")) return null;
    const remaining = windows.map((windowData) => windowData.remainingPercent);
    if (remaining.some((value) => (
      typeof value !== "number"
      || !Number.isFinite(value)
      || value < 0
      || value > 100
    ))) return null;
    return Math.min(...remaining);
  }

  function codexRateReservePresentation(snapshot, reservePercent) {
    const threshold = normalizeCodexRateReservePercent(reservePercent) ?? 15;
    const remaining = codexRatePolicyRemainingPercent(snapshot);
    const displayState = getCodexRateDisplayState(snapshot);
    if (displayState === "stale") {
      return { tone: "warning", text: `ข้อมูลโควตาเดิม • รอตรวจข้อมูลล่าสุดก่อนยืนยันความพร้อม • เกณฑ์ส่วนกลาง ≥ ${threshold}%` };
    }
    if (["unavailable", "loading"].includes(displayState)) {
      return { tone: "neutral", text: `เกณฑ์ส่วนกลาง ≥ ${threshold}% • ยังยืนยันโควตาล่าสุดไม่ได้` };
    }
    if (snapshot?.limitReached === true) {
      return { tone: "error", text: `โควตาถึงขีดจำกัด • เกณฑ์ส่วนกลาง ≥ ${threshold}%` };
    }
    if (remaining === null) {
      return { tone: "neutral", text: `เกณฑ์ส่วนกลาง ≥ ${threshold}% • รอข้อมูลโควตา` };
    }
    if (remaining < threshold) {
      return {
        tone: "warning",
        text: `พักคิวที่ ${formatCodexRatePercent(remaining)} • ต้องเหลืออย่างน้อย ${threshold}%`,
      };
    }
    return {
      tone: "ready",
      text: `พร้อมเริ่มงาน • ต่ำสุด ${formatCodexRatePercent(remaining)} ≥ ${threshold}%`,
    };
  }

  function getCodexRateDisplayState(snapshot) {
    if (!snapshot?.primary) return snapshot?.status === "loading" ? "loading" : "unavailable";
    if (snapshot.status === "stale") return "stale";
    if (snapshot.status !== "ready" || !normalizeCodexRateTimestamp(snapshot.checkedAt)) return "unavailable";
    return getCodexRateSeverity(snapshot);
  }

  function getCodexRateSeverity(snapshot) {
    if (!snapshot?.primary) return "unavailable";
    const usedPercent = Math.max(
      Number(snapshot.primary?.usedPercent) || 0,
      Number(snapshot.secondary?.usedPercent) || 0,
    );
    if (snapshot.limitReached || usedPercent >= 90) return "critical";
    if (usedPercent >= 70) return "warning";
    return "ready";
  }

  return {
    normalizeCodexRateTimestamp,
    normalizeCodexRateWindow,
    normalizeCodexRateReservePercent,
    codexRateLimitWasReached,
    normalizeCodexRatePayload,
    codexRatePolicyRemainingPercent,
    codexRateReservePresentation,
    getCodexRateDisplayState,
    getCodexRateSeverity,
  };
}

export { createCodexRateModel };
