"""Existing balance is usable only with exact, fresh, expiring Build consent."""
import copy
import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock

from test_automation_quota_policy import load_module, BRIDGE_PATH, RUNNER_PATH


class CodexExistingCreditRunnerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.runner = load_module("existing_credit_runner_test", RUNNER_PATH)
        cls.bridge = load_module("existing_credit_bridge_test", BRIDGE_PATH)

    def raw(self):
        return {"rateLimitsByLimitId": {"codex": {
            "primary": {"usedPercent": 100, "windowDurationMins": 10080, "resetsAt": 1792893665},
            "secondary": None, "rateLimitReachedType": "rate_limit_reached",
            "spendControlReached": False, "individualLimit": None,
            "credits": {"hasCredits": True, "unlimited": False, "balance": "123.75"},
        }}}

    def quota(self):
        return self.bridge.codex_rate_limits_read_model(self.runner.sanitize_rate_limits_response(self.raw()))

    def test_canonical_meter_preserves_paid_eligibility_not_account_balance(self):
        raw = self.raw()
        raw["rateLimits"] = {"primary": {"usedPercent": 0}, "credits": {"hasCredits": True, "balance": "999"}}
        raw["rateLimitsByLimitId"]["codex"].update(account={"email": "private@example.invalid"}, planType="private-plan")
        result = self.bridge.codex_rate_limits_read_model(self.runner.sanitize_rate_limits_response(raw))
        self.assertEqual(result["primary"]["remainingPercent"], 0)
        self.assertTrue(result["limitReached"])
        self.assertTrue(result["paidUsage"]["available"])
        for forbidden in ("balance", "123.75", "private", "account", "planType"):
            self.assertNotIn(forbidden, json.dumps(result))

    def test_malformed_secondary_is_not_silently_absent(self):
        for secondary in ({"usedPercent": "bad"}, {}, [], {"usedPercent": True}):
            raw = self.raw()
            raw["rateLimitsByLimitId"]["codex"]["secondary"] = secondary
            self.assertFalse(self.runner.sanitize_rate_limits_response(raw)["ok"])
        result = self.quota()
        result["secondary"] = {"usedPercent": "bad"}
        self.assertFalse(self.bridge.codex_rate_limits_read_model(result)["ok"])

    def test_build_consent_is_required_and_does_not_change_included_reserve(self):
        quota = self.quota()
        with mock.patch.object(self.bridge, "automation_min_remaining_percent", return_value=15), mock.patch.object(
            self.bridge, "_mission_existing_credit_consent", return_value=None
        ) as consent:
            self.assertFalse(self.bridge._collaboration_quota_gate({}, refresh=False, quota=quota)["allowed"])
            consent.return_value = {"buildId": "ea-build-consented"}
            admitted = self.bridge._collaboration_quota_gate({}, refresh=False, quota=quota, mission={"id": "mission-bound"})
            self.assertEqual(admitted["billingSource"], "existing_credits")
            self.assertEqual(admitted["remainingPercent"], 0)
            quota.update(limitReached=False, primary={"remainingPercent": 14})
            self.assertEqual(self.bridge._collaboration_quota_gate({}, refresh=False, quota=quota)["reason"], "quota_below_reserve")

    def test_provider_hard_stop_beats_valid_consent_and_plan_quota(self):
        quota = self.quota()
        with mock.patch.object(self.bridge, "automation_min_remaining_percent", return_value=0), mock.patch.object(
            self.bridge, "_mission_existing_credit_consent", return_value={"buildId": "ea-build-consented"}
        ):
            quota["paidUsage"]["spendControlReached"] = True
            for reached in (True, False):
                quota.update(limitReached=reached, primary={"remainingPercent": 100})
                result = self.bridge._collaboration_quota_gate({}, refresh=False, quota=quota)
                self.assertFalse(result["allowed"])
                self.assertEqual(result["reason"], "quota_provider_hard_stop")

    def test_stale_missing_or_future_timestamp_cannot_become_paid_evidence(self):
        for timestamp in (None, "", "invalid", (datetime.now(timezone.utc) - timedelta(seconds=100)).isoformat(),
                          (datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat()):
            quota = self.quota()
            quota["checkedAt"] = timestamp
            reshaped = self.bridge.codex_rate_limits_read_model(quota)
            with mock.patch.object(self.bridge, "automation_min_remaining_percent", return_value=0), mock.patch.object(
                self.bridge, "_mission_existing_credit_consent", return_value={"buildId": "ea-build-consented"}
            ):
                self.assertFalse(self.bridge._collaboration_quota_gate({}, refresh=False, quota=reshaped)["allowed"])

    def test_paid_repairs_recheck_grant_and_balance_before_each_subprocess(self):
        now = datetime.now(timezone.utc)
        grant = {"buildId": "ea-build-consented", "buildIdentityDigest": "a" * 64, "allowExistingCredits": True,
                 "allowedAt": now.isoformat(), "expiresAt": (now + timedelta(hours=1)).isoformat()}
        quota = self.quota()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "dashboard-workflow-settings.json"
            path.write_text(json.dumps({"existingCreditPolicy": {"schemaVersion": "existing-credit-policy-v1", "grants": [grant]}}), encoding="utf-8")
            with mock.patch.object(self.runner, "RUNTIME_DIR", Path(directory)), mock.patch.object(
                self.runner, "ALLOW_EXISTING_CODEX_CREDITS", True
            ), mock.patch.object(self.runner, "EXISTING_CODEX_CREDIT_CONSENT", grant), mock.patch.object(
                self.runner, "read_rate_limits", return_value=quota
            ), mock.patch.object(self.runner, "run_chat_command", return_value={"ok": True, "processStarted": True}) as run:
                self.assertTrue(self.runner.run_quota_guarded_semantic_repair(["synthetic"])["ok"])
                path.write_text(json.dumps({"existingCreditPolicy": {"schemaVersion": "existing-credit-policy-v1", "grants": []}}), encoding="utf-8")
                denied = self.runner.run_quota_guarded_semantic_repair(["synthetic"])
                self.assertFalse(denied["processStarted"])
                self.assertEqual(run.call_count, 1)
                path.write_text(json.dumps({"existingCreditPolicy": {"schemaVersion": "existing-credit-policy-v1", "grants": [grant]}}), encoding="utf-8")
                quota["paidUsage"]["available"] = False
                self.assertFalse(self.runner.run_quota_guarded_semantic_repair(["synthetic"])["processStarted"])
                self.assertEqual(run.call_count, 1)

    def test_repair_consent_rejects_corrupt_unrelated_rows_and_duplicate_json_keys(self):
        now = datetime.now(timezone.utc)
        grant = {"buildId": "ea-build-consented", "buildIdentityDigest": "a" * 64, "allowExistingCredits": True,
                 "allowedAt": now.isoformat(), "expiresAt": (now + timedelta(hours=1)).isoformat()}
        policy = {"schemaVersion": "existing-credit-policy-v1", "grants": [grant]}
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "settings.json"
            for grants in ([grant, {}], [grant, grant], [grant, {**grant, "buildId": "ea-build-another", "buildIdentityDigest": "bad"}]):
                path.write_text(json.dumps({"existingCreditPolicy": {**policy, "grants": grants}}), encoding="utf-8")
                self.assertFalse(self.runner.existing_consent_current(path, grant))
            serialized = json.dumps({"existingCreditPolicy": policy})
            serialized = serialized.replace('"allowExistingCredits": true', '"allowExistingCredits": false, "allowExistingCredits": true')
            path.write_text(serialized, encoding="utf-8")
            self.assertFalse(self.runner.existing_consent_current(path, grant))

    def test_runner_cannot_spend_build_a_consent_on_build_b_review(self):
        with mock.patch.object(self.runner, "ALLOW_EXISTING_CODEX_CREDITS", True), mock.patch.object(
            self.runner, "EXISTING_CODEX_CREDIT_CONSENT", {"buildId": "ea-build-authorized"}
        ), mock.patch.object(self.runner, "validate_ea_factory_source_review_prompt", return_value={"buildId": "ea-build-unrelated"}), mock.patch.object(
            self.runner, "chat_status", side_effect=AssertionError("Must reject before Codex readiness/process")
        ):
            result = self.runner.run_codex("Backend review", "ea_developer", "mission-review", execution_mode="auto_guarded",
                                           read_only_work=True, result_profile=self.runner.EA_FACTORY_SOURCE_REVIEW_RESULT_PROFILE)
            self.assertFalse(result["processStarted"])
            self.assertEqual(result["status"], "existing_credit_scope_invalid")


if __name__ == "__main__":
    unittest.main()
