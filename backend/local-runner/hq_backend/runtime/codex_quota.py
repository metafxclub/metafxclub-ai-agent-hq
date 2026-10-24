"""Privacy-preserving evidence for explicitly authorized existing-credit usage."""
from __future__ import annotations

import math
import json
import re
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path


def sanitize_provider_paid_usage(snapshot: object) -> dict:
    source = snapshot if isinstance(snapshot, dict) else {}
    raw_reason = source.get("rateLimitReachedType")
    reason = raw_reason if raw_reason in (None, "rate_limit_reached", "spend_control_limit_reached") else "unknown"
    if source.get("individualLimit") is not None:
        reason = "unknown"  # A separate spend restriction needs explicit interpretation.
    spend = source.get("spendControlReached")
    spend = spend if isinstance(spend, bool) else None
    credits = source.get("credits")
    positive_balance = False
    if isinstance(credits, dict) and credits.get("hasCredits") is True and credits.get("unlimited") is False:
        raw = credits.get("balance")
        if isinstance(raw, (str, int, float)) and not isinstance(raw, bool) and len(str(raw)) <= 100:
            try:
                balance = Decimal(str(raw))
                positive_balance = balance.is_finite() and balance > 0
            except InvalidOperation:
                pass
    return {
        "available": bool(positive_balance and spend is False and reason == "rate_limit_reached"),
        "spendControlReached": spend,
        "providerLimitReason": reason,
    }


def sanitize_paid_usage(value: object) -> dict | None:
    if not isinstance(value, dict):
        return None
    reason = value.get("providerLimitReason")
    reason = reason if reason in (None, "rate_limit_reached", "spend_control_limit_reached") else "unknown"
    spend = value.get("spendControlReached")
    spend = spend if isinstance(spend, bool) else None
    return {
        "available": value.get("available") is True and spend is False and reason == "rate_limit_reached",
        "spendControlReached": spend,
        "providerLimitReason": reason,
    }


def provider_hard_stop(quota: object) -> bool:
    paid = sanitize_paid_usage(quota.get("paidUsage")) if isinstance(quota, dict) else None
    return bool(paid and (paid["spendControlReached"] is True or paid["providerLimitReason"] in {"unknown", "spend_control_limit_reached"}))


def existing_paid_usage_available(quota: object, max_age_seconds: float = 75) -> bool:
    if not isinstance(quota, dict) or quota.get("ok") is not True or quota.get("stale") is not False:
        return False
    if quota.get("source") != "codex_app_server" or quota.get("limitReached") is not True:
        return False
    paid = sanitize_paid_usage(quota.get("paidUsage"))
    if not paid or paid["available"] is not True or provider_hard_stop(quota):
        return False
    try:
        checked = datetime.fromisoformat(str(quota.get("checkedAt") or "").replace("Z", "+00:00"))
        if checked.tzinfo is None:
            return False
        age = (datetime.now(timezone.utc) - checked).total_seconds()
        if not 0 <= age <= max_age_seconds:
            return False
        if "cacheAgeSeconds" in quota:
            raw_age = quota["cacheAgeSeconds"]
            cache_age = float(raw_age)
            if isinstance(raw_age, bool) or not math.isfinite(cache_age) or not 0 <= cache_age <= max_age_seconds:
                return False
    except (ValueError, TypeError, OverflowError):
        return False
    return True


def validated_existing_credit_grants(policy: object) -> list[dict] | None:
    if not isinstance(policy, dict) or policy.get("schemaVersion") != "existing-credit-policy-v1":
        return None
    grants = policy.get("grants")
    if not isinstance(grants, list) or len(grants) > 32:
        return None
    seen = set()
    for grant in grants:
        if not isinstance(grant, dict) or set(grant) != {"buildId", "buildIdentityDigest", "allowedAt", "expiresAt", "allowExistingCredits"}:
            return None
        build_id = grant.get("buildId")
        if not (isinstance(build_id, str) and re.fullmatch(r"ea-build-[A-Za-z0-9_-]+", build_id)
                and build_id not in seen and grant.get("allowExistingCredits") is True
                and isinstance(grant.get("buildIdentityDigest"), str)
                and re.fullmatch(r"[0-9a-f]{64}", grant["buildIdentityDigest"])):
            return None
        try:
            times = [datetime.fromisoformat(str(grant[key]).replace("Z", "+00:00")) for key in ("allowedAt", "expiresAt")]
            if not all(isinstance(grant[key], str) for key in ("allowedAt", "expiresAt")) or not all(value.tzinfo for value in times):
                return None
            if not 0 < (times[1] - times[0]).total_seconds() <= 86400:
                return None
        except (ValueError, TypeError, OverflowError):
            return None
        seen.add(build_id)
    return grants


def _unique_object(pairs: list[tuple]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate consent-store JSON key")
        result[key] = value
    return result


def existing_consent_current(settings_path: Path, expected: object) -> bool:
    """Re-read the exact expiring grant before every paid subprocess, including repairs."""
    if not isinstance(expected, dict) or set(expected) != {"buildId", "buildIdentityDigest", "allowedAt", "expiresAt", "allowExistingCredits"}:
        return False
    try:
        if settings_path.is_symlink() or settings_path.stat().st_size > 2 * 1024 * 1024:
            return False
        source = json.loads(settings_path.read_text(encoding="utf-8"), object_pairs_hook=_unique_object)
        grants = validated_existing_credit_grants(source.get("existingCreditPolicy"))
        if grants is None:
            return False
        matches = [row for row in grants if isinstance(row, dict) and row.get("buildId") == expected.get("buildId")]
        if matches != [expected] or expected.get("allowExistingCredits") is not True:
            return False
        start = datetime.fromisoformat(str(expected["allowedAt"]).replace("Z", "+00:00"))
        end = datetime.fromisoformat(str(expected["expiresAt"]).replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        return bool(start.tzinfo and end.tzinfo and start <= now < end and 0 < (end - start).total_seconds() <= 86400)
    except (OSError, ValueError, TypeError, AttributeError, OverflowError):
        return False
