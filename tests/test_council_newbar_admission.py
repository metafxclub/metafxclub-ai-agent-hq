"""Verify real parent/child creation binds the scheduler's one-shot admission."""
from datetime import datetime, timedelta, timezone
import unittest

import test_ai_trade_council_failure_injection as fixtures


class CouncilNewBarAdmissionTests(unittest.TestCase):
    def test_automatic_parent_and_three_votes_preserve_admission_stamps(self):
        fixture = fixtures.AiTradeCouncilFailureInjectionTests()
        fixture.setUp()
        try:
            b = fixture.bridge
            fixture._configure_selected_mt4()
            snapshot = b.metatrader_snapshot_read_model(b.AI_TRADE_COUNCIL_PROP_ID)
            identity, _ = b._ai_trade_council_closed_bar_identity(snapshot)
            admitted_at = datetime.now(timezone.utc)
            stamps = {
                'triggerPolicy': 'new_closed_bar_only_no_backfill',
                'triggerStartupId': b.SERVER_STARTED_AT,
                'quotaAdmittedAt': admitted_at.isoformat(),
                'triggerExpiresAt': (admitted_at + timedelta(seconds=60)).isoformat(),
            }
            context = {
                'triggerMode': 'last_closed_candle_time_change',
                'streamKey': identity['streamKey'], 'symbol': identity['symbol'],
                'timeframe': identity['timeframe'], 'closedBarTime': identity['lastClosedBarTime'],
                'analysisBarCount': b.AI_TRADE_COUNCIL_DEFAULT_ANALYSIS_BAR_COUNT,
                'dayKey': b._automation_day_key(), 'executionPolicy': 'current_exact_snapshot',
                'tradeCommandAllowed': True, **stamps,
            }
            patches = fixture._analysis_patches()
            with patches[0], patches[1], patches[2], patches[3]:
                result = b.run_ai_trade_council_analysis(
                    {'snapshotId': identity['snapshotId']},
                    automation_context=context, _snapshot_model=snapshot,
                )
            self.assertEqual(result['kind'], 'ai_trade_council_queued')
            parent_id = result['parent']['id']
            missions = [row for row in b.load_missions()
                        if row['id'] == parent_id or row.get('parentMissionId') == parent_id]
            self.assertEqual(len(missions), 4)
            for mission in missions:
                with self.subTest(mission=mission['id']):
                    automation = mission['analysisContext']['automation']
                    self.assertEqual({key: automation[key] for key in stamps}, stamps)
                    self.assertTrue(automation['tradeCommandAllowed'])
                    self.assertEqual(automation['executionPolicy'], 'current_exact_snapshot')
        finally:
            fixture.tearDown()


if __name__ == '__main__':
    unittest.main()
