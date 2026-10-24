"""Versioned Radar publication policy and pure native-evidence checks."""

import hashlib
import json
import re

RESULT_PROFILE = "radar_website_tool_v2"
MANIFEST_SCHEMA = "metafx-radar-url-open-verification-v2"
MAX_ITEMS = 3


def is_v2(row: object) -> bool:
    record = row if isinstance(row, dict) else {}
    context = record.get("workflowContext")
    if not isinstance(context, dict):
        return False
    inputs = context.get("inputs")
    return bool(
        context.get("propId") == "left_audit_crystals"
        and context.get("actionId") == "discover_new_indicators"
        and isinstance(inputs, dict)
        and type(inputs.get("radarPublicationVersion")) is int
        and inputs["radarPublicationVersion"] == 2
        and type(inputs.get("maxItems")) is int
        and inputs["maxItems"] == MAX_ITEMS
    )


def policy_v2() -> dict:
    return {"version": 2, "mode": "up_to_maximum",
            "maximumItemCount": MAX_ITEMS, "minimumItemCount": 0}


def invalid_policy(row: object) -> bool:
    record = row if isinstance(row, dict) else {}
    context = record.get("workflowContext")
    inputs = context.get("inputs") if isinstance(context, dict) else None
    return bool(isinstance(inputs, dict) and "radarPublicationVersion" in inputs and not is_v2(row))


def urls_digest(urls: list[str]) -> str:
    return hashlib.sha256(json.dumps(urls, ensure_ascii=False,
                                    separators=(",", ":")).encode("utf-8")).hexdigest()


def valid_manifest(manifest: object, urls: list[str], run_id: str) -> bool:
    if not isinstance(manifest, dict) or not 0 <= len(urls) <= MAX_ITEMS:
        return False
    if len(set(urls)) != len(urls):
        return False
    if set(manifest) != {
        "schemaVersion", "verificationType", "resultProfile", "runId",
        "requiredUrlCount", "requiredUrlDigest", "mainRequiredOpenCount",
        "mainRequiredOpenIndexes", "posthocVerificationCount", "rows",
        "completedSearchCount", "completedSearchEvents",
    }:
        return False
    events = manifest.get("completedSearchEvents")
    if not isinstance(events, list) or not 1 <= len(events) <= 100:
        return False
    ids = set()
    for event in events:
        if (not isinstance(event, dict)
                or set(event) != {"completedEventId", "completedEventDigest"}
                or not isinstance(event.get("completedEventId"), str)
                or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.:-]{0,159}", event["completedEventId"])
                or not isinstance(event.get("completedEventDigest"), str)
                or not re.fullmatch(r"[0-9a-f]{64}", event["completedEventDigest"])
                or event["completedEventId"] in ids):
            return False
        ids.add(event["completedEventId"])
    count = len(urls)
    return bool(
        manifest.get("schemaVersion") == MANIFEST_SCHEMA
        and manifest.get("verificationType") == "main_native_search_and_open"
        and manifest.get("resultProfile") == RESULT_PROFILE
        and manifest.get("runId") == run_id
        and type(manifest.get("requiredUrlCount")) is int
        and manifest["requiredUrlCount"] == count
        and manifest.get("requiredUrlDigest") == urls_digest(urls)
        and type(manifest.get("mainRequiredOpenCount")) is int
        and manifest["mainRequiredOpenCount"] == count
        and isinstance(manifest.get("mainRequiredOpenIndexes"), list)
        and all(type(index) is int for index in manifest["mainRequiredOpenIndexes"])
        and manifest["mainRequiredOpenIndexes"] == list(range(count))
        and type(manifest.get("posthocVerificationCount")) is int
        and manifest["posthocVerificationCount"] == 0
        and manifest.get("rows") == []
        and type(manifest.get("completedSearchCount")) is int
        and manifest["completedSearchCount"] == len(events)
    )
