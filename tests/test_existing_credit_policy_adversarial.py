"""Independent fail-closed checks for scoped existing-credit admission.

These tests use synthetic account evidence and isolated stores only. They never
start Codex, alter billing, invoke MetaTrader, or write live Runtime data.
"""
from __future__ import annotations

import copy
import importlib.util
import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock

import test_ea_factory_cancelled_resume_adversarial as continuation_support
import test_ea_factory_followup_hardening as factory_support


ROOT = Path(__file__).resolve().parents[1]


def load_paid_usage_module():
    path = ROOT / "backend" / "local-runner" / "hq_backend" / "runtime" / "codex_quota.py"
    spec = importlib.util.spec_from_file_location("existing_credit_adversarial_evidence", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ExistingCreditEvidenceAdversarialTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.policy = load_paid_usage_module()

    def provider(self):
        return {
            "rateLimitReachedType": "rate_limit_reached",
            "spendControlReached": False,
            "individualLimit": None,
            "credits": {"hasCredits": True, "unlimited": False, "balance": "100.25"},
        }

    def quota(self):
        return {
            "ok": True,
            "source": "codex_app_server",
            "stale": False,
            "limitReached": True,
            "checkedAt": datetime.now(timezone.utc).isoformat(),
            "cacheAgeSeconds": 0,
            "paidUsage": self.policy.sanitize_provider_paid_usage(self.provider()),
        }

    def test_only_explicit_positive_finite_existing_balance_is_eligible(self):
        self.assertTrue(self.policy.sanitize_provider_paid_usage(self.provider())["available"])
        invalid = [None, True, False, "", "NaN", "sNaN", "Infinity", "-Infinity", 0,
                   -1, "-0.1", {}, [], "private-account-data", "1" * 101]
        for balance in invalid:
            with self.subTest(balance=repr(balance)):
                source = self.provider()
                source["credits"]["balance"] = balance
                result = self.policy.sanitize_provider_paid_usage(source)
                self.assertFalse(result["available"])
                self.assertNotIn("balance", result)
                self.assertNotIn("credits", result)
        for flag in (None, False, 1, "true"):
            source = self.provider()
            source["credits"]["hasCredits"] = flag
            self.assertFalse(self.policy.sanitize_provider_paid_usage(source)["available"])
        for flag in (None, True, 0, "false"):
            source = self.provider()
            source["credits"]["unlimited"] = flag
            self.assertFalse(self.policy.sanitize_provider_paid_usage(source)["available"])

    def test_unknown_limit_reasons_never_grant_or_raise(self):
        for reason in ([], {}, ["rate_limit_reached"], True, 1, "", "future_unknown_limit", "none"):
            with self.subTest(reason=repr(reason)):
                provider = self.provider()
                provider["rateLimitReachedType"] = reason
                paid = self.policy.sanitize_provider_paid_usage(provider)
                self.assertFalse(paid["available"])
                self.assertTrue(self.policy.provider_hard_stop({"paidUsage": paid}))
                quota = self.quota()
                quota["paidUsage"] = {"available": True, "spendControlReached": False,
                                      "providerLimitReason": reason}
                self.assertFalse(self.policy.existing_paid_usage_available(quota))

    def test_spend_controls_override_positive_balance(self):
        for spend in (True, None, "false", 0, [], {}):
            with self.subTest(spend=repr(spend)):
                source = self.provider()
                source["spendControlReached"] = spend
                self.assertFalse(self.policy.sanitize_provider_paid_usage(source)["available"])
        source = self.provider()
        source["rateLimitReachedType"] = "spend_control_limit_reached"
        paid = self.policy.sanitize_provider_paid_usage(source)
        self.assertFalse(paid["available"])
        self.assertTrue(self.policy.provider_hard_stop({"paidUsage": paid}))

    def test_nonnull_individual_limit_cannot_be_bypassed_by_credit(self):
        for limit in ({"limitReached": True}, {"remaining": 0}, {}, [], False, "blocked"):
            with self.subTest(limit=repr(limit)):
                source = self.provider()
                source["individualLimit"] = limit
                paid = self.policy.sanitize_provider_paid_usage(source)
                self.assertFalse(paid["available"])
                self.assertTrue(self.policy.provider_hard_stop({"paidUsage": paid}))

    def test_credit_eligibility_requires_exact_trusted_snapshot_flags(self):
        self.assertTrue(self.policy.existing_paid_usage_available(self.quota()))
        changes = [("ok", 1), ("ok", False), ("stale", None), ("stale", True),
                   ("source", "browser"), ("source", None), ("limitReached", False),
                   ("limitReached", 1), ("paidUsage", None), ("paidUsage", [])]
        for key, value in changes:
            with self.subTest(key=key, value=repr(value)):
                quota = self.quota()
                quota[key] = value
                self.assertFalse(self.policy.existing_paid_usage_available(quota))

    def test_missing_stale_future_naive_or_invalid_timestamp_cannot_spend(self):
        now = datetime.now(timezone.utc)
        for checked in (None, "", "bad", now.replace(tzinfo=None).isoformat(),
                        (now - timedelta(seconds=76)).isoformat(),
                        (now + timedelta(seconds=5)).isoformat()):
            with self.subTest(checked=checked):
                quota = self.quota()
                quota["checkedAt"] = checked
                self.assertFalse(self.policy.existing_paid_usage_available(quota))

    def test_cache_age_cannot_be_forged_to_extend_paid_eligibility(self):
        for age in (None, True, -0.1, 76, "NaN", "Infinity", {}, []):
            with self.subTest(age=repr(age)):
                quota = self.quota()
                quota["cacheAgeSeconds"] = age
                self.assertFalse(self.policy.existing_paid_usage_available(quota))

    def test_paid_projection_drops_unrelated_account_and_payment_data(self):
        provider = self.provider()
        provider.update(email="private@example.invalid", paymentMethod="private-card",
                        accountId="private-account", token="private-token")
        projected = self.policy.sanitize_provider_paid_usage(provider)
        self.assertNotIn("private", str(projected))
        internal = copy.deepcopy(projected)
        internal.update(balance="private-credit", card="private-card", token="private-token")
        self.assertNotIn("private", str(self.policy.sanitize_paid_usage(internal)))

    def test_runner_rejects_malformed_unrelated_grants_not_only_matching_row(self):
        now = datetime.now(timezone.utc)
        grant = {"buildId": "ea-build-independent-consent", "buildIdentityDigest": "a" * 64,
                 "allowedAt": now.isoformat(), "expiresAt": (now + timedelta(hours=1)).isoformat(),
                 "allowExistingCredits": True}
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "dashboard-workflow-settings.json"
            def write(grants):
                path.write_text(json.dumps({"existingCreditPolicy": {
                    "schemaVersion": "existing-credit-policy-v1", "grants": grants}}), encoding="utf-8")
            write([grant])
            self.assertTrue(self.policy.existing_consent_current(path, grant))
            for bad in ({}, [], None, {**grant, "buildId": "ea-build-other", "allowExistingCredits": "true"},
                        {**grant, "buildId": "ea-build-other", "buildIdentityDigest": "invalid"}):
                with self.subTest(unrelated=repr(bad)):
                    write([grant, bad])
                    self.assertFalse(self.policy.existing_consent_current(path, grant))

    def test_runner_rejects_duplicate_json_keys_in_consent_store(self):
        now = datetime.now(timezone.utc)
        grant = {"buildId": "ea-build-independent-consent", "buildIdentityDigest": "a" * 64,
                 "allowedAt": now.isoformat(), "expiresAt": (now + timedelta(hours=1)).isoformat(),
                 "allowExistingCredits": True}
        policy = {"schemaVersion": "existing-credit-policy-v1", "grants": [grant]}
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "dashboard-workflow-settings.json"
            duplicate_policy = '{"existingCreditPolicy":null,"existingCreditPolicy":' + json.dumps(policy) + '}'
            duplicate_grant = json.dumps({"existingCreditPolicy": policy}).replace(
                '"allowExistingCredits": true', '"allowExistingCredits": false, "allowExistingCredits": true')
            for text in (duplicate_policy, duplicate_grant):
                path.write_text(text, encoding="utf-8")
                self.assertFalse(self.policy.existing_consent_current(path, grant))


class ExistingCreditBuildConsentAdversarialTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bridge = factory_support.load_bridge()
        cls.policy = load_paid_usage_module()

    def setUp(self):
        self.fixture = continuation_support.EaFactoryCancelledResumeAdversarialTests()
        self.fixture.bridge = self.bridge
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.build = self.fixture.build
        self.mission = self.fixture.mission
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.settings_path = Path(temporary.name) / "dashboard-workflow-settings.json"
        self.fixture.patch("DASHBOARD_WORKFLOW_SETTINGS_PATH", new=self.settings_path)
        self.fixture.patch("MISSION_WORKER_WAKE", new=mock.Mock())
        self.fixture.patch("_wake_ai_quota_policy_consumers", side_effect=AssertionError("No global quota wake"))

    def save(self, allowed=True):
        return self.bridge.save_existing_credit_policy({"buildId": self.build["id"], "allowed": allowed})

    def settings(self):
        return self.bridge._load_dashboard_workflow_settings_read_only()

    def active(self):
        self.fixture.submit()

    def quota(self):
        source = {
            "rateLimitReachedType": "rate_limit_reached", "spendControlReached": False,
            "individualLimit": None,
            "credits": {"hasCredits": True, "unlimited": False, "balance": "100.25"},
        }
        return {
            "ok": True, "source": "codex_app_server", "stale": False, "limitReached": True,
            "checkedAt": datetime.now(timezone.utc).isoformat(), "cacheAgeSeconds": 0,
            "primary": {"remainingPercent": 0}, "secondary": None,
            "paidUsage": self.policy.sanitize_provider_paid_usage(source),
        }

    def gate(self, *, mission=None, quota=None, settings=None):
        return self.bridge._collaboration_quota_gate(
            {}, refresh=False, quota=quota if quota is not None else self.quota(),
            settings=settings if settings is not None else self.settings(),
            mission=mission if mission is not None else self.mission,
        )

    def test_save_and_replay_preserve_existing_build_and_mission_without_dispatch(self):
        original = copy.deepcopy(self.fixture.state), copy.deepcopy(self.fixture.missions)
        first = self.save()
        persisted = self.settings()
        again = self.save()
        self.assertEqual(self.settings()["existingCreditPolicy"], persisted["existingCreditPolicy"])
        self.assertTrue(again["idempotentReplay"])
        self.assertFalse(first["purchasesAllowed"])
        self.assertFalse(first["automaticReloadAllowed"])
        self.assertEqual(first["missionsCreated"], 0)
        self.assertFalse(first["processStarted"])
        self.assertEqual((self.fixture.state, self.fixture.missions), original)
        self.fixture.dispatch.assert_not_called()
        self.fixture.retry.assert_not_called()
        self.fixture.start.assert_not_called()

    def test_same_existing_mission_admitted_only_after_explicit_resume(self):
        self.save()
        self.assertFalse(self.gate()["allowed"])
        self.active()
        result = self.gate()
        self.assertTrue(result["allowed"], result)
        self.assertEqual(result["reason"], "existing_credits_authorized")
        self.assertEqual(result["remainingPercent"], 0)
        self.assertTrue(result["quota"]["limitReached"])
        self.assertEqual(len(self.fixture.missions), 1)

    def test_policy_survives_settings_normalization_and_other_preference_changes(self):
        self.save()
        grant = copy.deepcopy(self.settings()["existingCreditPolicy"])
        self.bridge._mutate_dashboard_workflow_settings(
            lambda value: {**value, "agentPreferences": {**value["agentPreferences"], "rateReservePercent": 57}}
        )
        shaped = self.settings()
        self.assertEqual(shaped["existingCreditPolicy"], grant)
        self.assertEqual(shaped["agentPreferences"]["rateReservePercent"], 57)
        self.assertEqual(len(self.bridge.existing_credit_policy_read_model()["grants"]), 1)

    def test_revocation_is_observed_by_next_admission_without_restart(self):
        self.save()
        self.active()
        self.assertTrue(self.gate()["allowed"])
        self.save(False)
        self.assertFalse(self.gate()["allowed"])
        self.assertIsNone(self.bridge._mission_existing_credit_consent(self.mission))
        self.assertEqual(self.bridge.existing_credit_policy_read_model()["grants"], [])

    def test_same_consent_follows_verified_source_to_bound_review_only(self):
        self.save()
        self.active()
        self.assertTrue(self.gate()["allowed"])
        _review, mission = self.fixture.queued_review()
        result = self.gate(mission=mission)
        self.assertTrue(result["allowed"], result)
        self.assertEqual(result["existingCreditBuildId"], self.build["id"])
        self.assertEqual(len(self.bridge.existing_credit_policy_read_model()["grants"]), 1)

    def test_expired_or_future_grant_never_admits_and_replay_does_not_renew(self):
        self.save()
        self.active()
        for offset in (-48, 1):
            with self.subTest(offset=offset):
                shifted = datetime.now(timezone.utc) + timedelta(hours=offset)
                def expire(value):
                    grant = value["existingCreditPolicy"]["grants"][0]
                    grant["allowedAt"] = shifted.isoformat()
                    grant["expiresAt"] = (shifted + timedelta(hours=24)).isoformat()
                    return value
                self.bridge._mutate_dashboard_workflow_settings(expire)
                before = self.settings()["existingCreditPolicy"]
                self.assertFalse(self.gate()["allowed"])
                self.assertTrue(self.save()["idempotentReplay"])
                self.assertEqual(self.settings()["existingCreditPolicy"], before)

    def test_unrelated_missions_and_forged_workflow_markers_never_admit(self):
        self.save()
        self.active()
        baseline = copy.deepcopy(self.mission)
        edits = [
            ("id", "mission-other"), ("owner", "manager"), ("requester", "agent"),
            ("toolId", "codex_web_research"), ("targetId", "mission_table"),
            ("executionMode", "manual"), ("requiresHumanApproval", True),
            ("autoEligible", False), ("idempotencyKey", "different-key"),
        ]
        for key, value in edits:
            with self.subTest(key=key):
                modified = copy.deepcopy(baseline)
                modified[key] = value
                self.assertFalse(self.gate(mission=modified)["allowed"])
        for key, value in (("triggerSource", "frontend"), ("actionId", "review_source_code"),
                           ("inputDigest", "0" * 64)):
            with self.subTest(context_key=key):
                modified = copy.deepcopy(baseline)
                modified["workflowContext"][key] = value
                self.assertFalse(self.gate(mission=modified)["allowed"])
        self.assertFalse(self.gate(mission={})["allowed"])

    def test_changed_build_identity_and_stage_receipt_cannot_reuse_consent(self):
        self.save()
        self.active()
        old_digest = self.build["createRequestDigest"]
        self.build["createRequestDigest"] = "f" * 64
        self.assertFalse(self.gate()["allowed"])
        with self.assertRaises(self.bridge.RequestError):
            self.save()
        self.build["createRequestDigest"] = old_digest
        self.fixture.source["requestDigest"] = "0" * 64
        self.assertFalse(self.gate()["allowed"])

    def test_cancelled_failed_completed_or_malformed_run_cannot_spend(self):
        self.save()
        self.active()
        live = copy.deepcopy(self.build["oneClickRun"])
        for status in ("cancelled", "failed", "completed", "blocked", "unknown"):
            with self.subTest(status=status):
                changed = copy.deepcopy(live)
                changed.update(status=status, completedAt=datetime.now(timezone.utc).isoformat(),
                               failureCode="operator_cancelled" if status != "completed" else None)
                self.build["oneClickRun"] = changed
                self.assertFalse(self.gate()["allowed"])
        self.build["oneClickRun"] = None
        self.assertFalse(self.gate()["allowed"])

    def test_hard_provider_stop_and_malformed_windows_override_valid_consent(self):
        self.save()
        self.active()
        baseline = self.quota()
        for key, value in (("primary", None), ("secondary", {"remainingPercent": True}),
                           ("secondary", {"remainingPercent": "NaN"}), ("stale", True)):
            with self.subTest(key=key, value=repr(value)):
                quota = copy.deepcopy(baseline)
                quota[key] = value
                self.assertFalse(self.gate(quota=quota)["allowed"])
        hard = copy.deepcopy(baseline)
        hard.update(limitReached=False, primary={"remainingPercent": 100})
        hard["paidUsage"]["spendControlReached"] = True
        self.assertFalse(self.gate(quota=hard)["allowed"])

    def test_invalid_policy_payloads_and_unverified_build_are_rejected(self):
        self.save()
        original = self.settings()
        payloads = [None, {}, {"buildId": self.build["id"], "allowed": 1},
                    {"buildId": self.build["id"], "allowed": True, "purchase": True},
                    {"buildId": "../ea-build-escape", "allowed": True},
                    {"buildId": "ea-build-nonexistent", "allowed": True}]
        for payload in payloads:
            with self.subTest(payload=payload), self.assertRaises(self.bridge.RequestError):
                self.bridge.save_existing_credit_policy(payload)
        self.assertEqual(self.settings(), original)
        self.build["workspace"]["strategySpecDigest"] = "invalid"
        with self.assertRaises(self.bridge.RequestError):
            self.save()

    def test_corrupt_or_duplicate_grants_fail_closed_without_partial_authorization(self):
        self.save()
        self.active()
        baseline = self.settings()
        grant = baseline["existingCreditPolicy"]["grants"][0]
        variants = [[grant, grant], [grant, {}], [grant] * 33,
                    [{**grant, "allowExistingCredits": "true"}],
                    [{**grant, "expiresAt": (datetime.now(timezone.utc) + timedelta(days=5)).isoformat()}],
                    [{**grant, "allowedAt": datetime.now(timezone.utc).replace(tzinfo=None).isoformat(),
                      "expiresAt": (datetime.now(timezone.utc) + timedelta(hours=1)).replace(tzinfo=None).isoformat()}],
                    [{**grant, "buildIdentityDigest": "bad"}], [{**grant, "untrusted": True}]]
        for grants in variants:
            with self.subTest(grants=repr(grants)[:80]):
                settings = copy.deepcopy(baseline)
                settings["existingCreditPolicy"]["grants"] = grants
                self.assertFalse(self.gate(settings=settings)["allowed"])
