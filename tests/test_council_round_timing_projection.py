"""Public Council timing retains stored deadlines without exposing private data."""
import copy
import unittest

import test_ai_trade_council_agent_blockers as fixtures


class CouncilRoundTimingProjectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.b = fixtures.load_bridge()

    def mission(self):
        return {
            "id": "mission-council-timing", "status": "queued",
            "reportType": "ai_trade_council_report", "createdAt": "2026-10-27T01:00:20Z",
            "analysisContext": {
                "kind": "ai_trade_council_parent", "roundStartedAt": "2026-10-27T01:00:00Z",
                "roundDeadlineAt": "2026-10-27T01:05:00Z",
                "snapshotArtifact": "private-snapshot-path",
                "automation": {"quotaAdmittedAt": "2026-10-27T01:00:00Z",
                               "triggerExpiresAt": "2026-10-27T01:05:00Z", "privateField": "do-not-expose"},
            },
            "delegation": {"mode": "ai_trade_council_read_only"},
        }

    def test_card_projects_validated_times_without_analysis_packet_or_mutating_history(self):
        mission = self.mission()
        before = copy.deepcopy(mission)
        card = self.b.mission_read_model_item(mission)
        timing = card["delegation"]
        self.assertEqual(timing["roundStartedAt"], "2026-10-27T01:00:00Z")
        self.assertEqual(timing["roundDeadlineAt"], "2026-10-27T01:05:00Z")
        self.assertEqual(timing["triggerMode"], "auto_on_new_closed_bar")
        self.assertEqual(timing["roundTimingSource"], "recorded_round")
        self.assertNotIn("analysisContext", card)
        self.assertNotIn("automation", timing)
        self.assertNotIn("private-snapshot-path", str(card))
        self.assertNotIn("do-not-expose", str(card))
        self.assertEqual(mission, before)

    def test_recorded_legacy_240_round_precedes_60_second_launch_window(self):
        mission = self.mission()
        mission["analysisContext"].update(roundStartedAt="2026-10-27T01:00:20Z",
                                           roundDeadlineAt="2026-10-27T01:04:20Z")
        mission["analysisContext"]["automation"]["triggerExpiresAt"] = "2026-10-27T01:01:00Z"
        timing = self.b.mission_read_model_item(mission)["delegation"]
        self.assertEqual(timing["roundStartedAt"], "2026-10-27T01:00:20Z")
        self.assertEqual(timing["roundDeadlineAt"], "2026-10-27T01:04:20Z")
        self.assertEqual(timing["roundTimingSource"], "recorded_round")

    def test_recorded_60_and_missing_round_legacy_60_are_not_extended(self):
        for recorded in (True, False):
            with self.subTest(recorded=recorded):
                mission = self.mission()
                context = mission["analysisContext"]
                context["automation"]["triggerExpiresAt"] = "2026-10-27T01:01:00Z"
                if recorded:
                    context["roundDeadlineAt"] = "2026-10-27T01:01:00Z"
                else:
                    context.pop("roundStartedAt")
                    context.pop("roundDeadlineAt")
                timing = self.b.mission_read_model_item(mission)["delegation"]
                self.assertEqual(timing["roundDeadlineAt"], "2026-10-27T01:01:00Z")
                self.assertEqual(timing["roundTimingSource"], "recorded_round" if recorded else "legacy_admission_window")

    def test_invalid_times_fall_back_to_stored_delegation_and_normalize_timezone(self):
        mission = self.mission()
        mission["analysisContext"].update(roundStartedAt={"bad": True}, roundDeadlineAt="not-a-time")
        mission["delegation"].update(roundStartedAt="2026-10-27T08:00:00+07:00",
                                     roundDeadlineAt="2026-10-27T08:04:00+07:00", triggerMode="manual")
        timing = self.b.mission_read_model_item(mission)["delegation"]
        self.assertEqual(timing["roundStartedAt"], "2026-10-27T01:00:00Z")
        self.assertEqual(timing["roundDeadlineAt"], "2026-10-27T01:04:00Z")
        self.assertEqual(timing["triggerMode"], "manual")

    def test_missing_times_are_not_reconstructed_from_current_policy(self):
        mission = self.mission()
        mission["analysisContext"] = {"kind": "ai_trade_council_parent", "automation": {"executionPolicy": "new_bar_only"}}
        timing = self.b.mission_read_model_item(mission)["delegation"]
        self.assertIsNone(timing["roundStartedAt"])
        self.assertIsNone(timing["roundDeadlineAt"])
        self.assertEqual(timing["triggerMode"], "auto_on_new_closed_bar")

    def test_unrelated_mission_projection_is_unchanged(self):
        card = self.b.mission_read_model_item({"id": "mission-unrelated", "status": "queued"})
        self.assertNotIn("roundStartedAt", card["delegation"])
        self.assertNotIn("roundDeadlineAt", card["delegation"])
        self.assertNotIn("triggerMode", card["delegation"])


if __name__ == '__main__':
    unittest.main()
