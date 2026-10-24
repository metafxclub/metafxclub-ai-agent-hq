"""Acceptance cases for new-bar-only recovery; no live terminal/AI actions."""
from __future__ import annotations

import copy
import unittest
from datetime import datetime, timedelta, timezone
from unittest import mock

import test_ai_trade_council_per_bar_automation as fixtures


class CouncilSchedulerRecoveryTests(unittest.TestCase):
    def setUp(self):
        self.f = fixtures.AiTradeCouncilPerBarAutomationTests()
        self.f.setUp()
        self.b = self.f.bridge
        self.b.load_missions = lambda: []

    def tearDown(self):
        self.f.tearDown()

    def capture(self):
        self.f._save_observed_store()
        self.f._advance_bar()
        self.b.ai_trade_council_automation_tick()
        store = self.b.load_ai_trade_council_automation_store()
        store['state']['pendingDetectedAt'] = (
            datetime.now(timezone.utc)-timedelta(seconds=20)
        ).isoformat()
        self.b._save_ai_trade_council_automation_store(store)
        return self.b.load_ai_trade_council_automation_store()

    def test_restart_during_settle_skips_capture_and_waits_for_next_bar(self):
        captured = self.capture()['state']['pendingQueue'][0]
        self.b.SERVER_STARTED_AT = 'restarted-bridge'
        self.b.ai_trade_council_automation_tick()
        state = self.b.load_ai_trade_council_automation_store()['state']
        self.assertEqual(state['pendingQueue'], [])
        self.assertEqual(state['coverageRecords'][0]['snapshotArtifactDigest'], captured['snapshotArtifactDigest'])
        self.assertEqual(state['coverageRecords'][0]['reasonCode'], 'new_bar_only_restart_baseline')
        self.b.ai_trade_council_automation_tick()
        self.assertEqual(self.f.calls, [])
        self.f._advance_bar()
        self.b.ai_trade_council_automation_tick()
        self.f._finish_settle()
        self.assertEqual(len(self.f.calls), 1)

    def test_expired_capture_never_runs_audit_ai(self):
        original_snapshot = self.f._snapshot
        def old_snapshot():
            snapshot = original_snapshot()
            snapshot['chartSnapshot']['observedAt'] = (datetime.now(timezone.utc)-timedelta(seconds=901)).isoformat()
            return snapshot
        self.f._snapshot = old_snapshot
        self.capture()
        state = self.b.load_ai_trade_council_automation_store()['state']
        self.assertEqual(state['pendingQueue'], [])
        self.assertEqual(state['coverageRecords'][0]['status'], 'skipped')
        self.assertEqual(state['coverageRecords'][0]['reasonCode'], 'analysis_snapshot_expired_before_start')
        self.assertIsNone(state['coverageRecords'][0]['snapshotArtifact'])
        self.f._snapshot = original_snapshot
        self.b.ai_trade_council_automation_tick()
        self.b.ai_trade_council_automation_tick()
        self.assertEqual(self.f.calls, [])

    def test_switch_away_and_return_skips_old_capture_until_next_bar(self):
        self.capture()
        self.f.timeframe = 'H1'
        self.b.ai_trade_council_automation_tick()
        self.f.timeframe = 'M5'
        self.b.ai_trade_council_automation_tick()
        self.b.ai_trade_council_automation_tick()
        self.assertEqual(self.f.calls, [])
        self.assertEqual(self.b.load_ai_trade_council_automation_store()['state']['pendingQueue'], [])
        self.f._advance_bar()
        self.b.ai_trade_council_automation_tick()
        self.f._finish_settle()
        self.assertEqual(len(self.f.calls), 1)

    def test_baseline_cannot_demote_completed_or_queued_coverage(self):
        store = self.capture()
        original = store['state']['pendingQueue'][0]
        for status in ('queued', 'analyzed'):
            with self.subTest(status=status):
                row = {**original, 'status': status, 'missionId': 'mission-original'}
                self.b._ai_trade_council_coverage_upsert(store, row)
                self.b._ai_trade_council_coverage_upsert(store, {
                    **original, 'status': 'skipped', 'missionId': None,
                    'reasonCode': 'stream_change_baseline',
                })
                saved = store['state']['coverageRecords'][0]
                self.assertEqual(saved['status'], status)
                self.assertEqual(saved['missionId'], 'mission-original')

    def test_restart_crash_after_published_parent_never_starts_second_round(self):
        store = self.capture()
        pending = store['state']['pendingQueue'][0]
        existing = {
            'id': 'mission-existing', 'status': 'completed',
            'analysisContext': {
                'kind': 'ai_trade_council_parent',
                'closedBarIdentity': {'streamKey': pending['streamKey'], 'closedBarTime': pending['closedBarTime']},
                'automation': {
                    'executionPolicy': 'current_exact_snapshot', 'tradeCommandAllowed': True,
                    'source': 'backend_scheduler', 'dayKey': self.b._automation_day_key(),
                },
            },
            'tradeGateway': {'commandPublished': True, 'commandId': 'command-existing'},
        }
        self.b.load_missions = lambda: [copy.deepcopy(existing)]
        self.b.mission_read_model_item = lambda mission: mission
        self.b.SERVER_STARTED_AT = 'restart-after-publish'
        first = self.b.ai_trade_council_automation_tick()
        self.b.ai_trade_council_automation_tick()
        self.assertEqual(first['kind'], 'ai_trade_council_automation_baseline')
        self.assertEqual(len(self.f.calls), 0)
        saved = self.b.load_ai_trade_council_automation_store()['state']['coverageRecords'][0]
        self.assertEqual(saved['missionId'], existing['id'])
        self.assertEqual(saved['status'], 'analyzed')
        self.assertEqual(existing['tradeGateway']['commandId'], 'command-existing')
        self.assertEqual(self.b.load_ai_trade_council_automation_store()['state']['dailyRunCount'], 1)

    def test_restart_recovers_unstarted_skipped_parent_as_skipped_not_analyzed(self):
        pending = self.capture()['state']['pendingQueue'][0]
        parent = {
            'id': 'mission-skipped-parent', 'status': 'blocked',
            'analysisContext': {
                'kind': 'ai_trade_council_parent',
                'closedBarIdentity': {'streamKey': pending['streamKey'], 'closedBarTime': pending['closedBarTime']},
                'automation': {'source': 'backend_scheduler', 'dayKey': self.b._automation_day_key()},
            },
        }
        children = [{
            'id': f'mission-skipped-{role}', 'parentMissionId': parent['id'], 'status': 'blocked',
            'errorCode': 'council_new_bar_quota_unavailable',
            'execution': {'newBarSkipped': True, 'processStarted': False},
            'analysisContext': {'kind': 'ai_trade_council_vote', 'roleId': role, 'automation': {'source': 'backend_scheduler'}},
        } for role in ('technical', 'price_action', 'news')]
        self.b.load_missions = lambda: [parent, *children]
        self.b.SERVER_STARTED_AT = 'restart-after-unstarted-skip'
        self.b.ai_trade_council_automation_tick()
        state = self.b.load_ai_trade_council_automation_store()['state']
        row = state['coverageRecords'][0]
        self.assertEqual(row['status'], 'skipped')
        self.assertEqual(row['reasonCode'], 'council_new_bar_quota_unavailable')
        self.assertEqual(row['missionId'], parent['id'])
        self.assertIsNone(state['lastAnalyzedClosedBarTime'])
        self.assertEqual(self.f.calls, [])

    def test_weekend_or_session_break_does_not_invent_missing_bars(self):
        self.f._save_observed_store()
        previous = self.f.closed_bar_time
        self.f.closed_bar_time += 2*86400 + 300
        snapshot = self.f._snapshot()
        snapshot['chartSnapshot']['bars'] = [{'time': previous}, {'time': self.f.closed_bar_time}]
        self.b.metatrader_snapshot_read_model = lambda _: snapshot
        self.b.ai_trade_council_automation_tick()
        rows = self.b.load_ai_trade_council_automation_store()['state']['coverageRecords']
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['status'], 'pending')

    def test_recovered_previous_day_parent_cannot_resurrect_yesterdays_count(self):
        day = ['2026-10-22']
        self.b._automation_day_key = lambda *args: day[0]
        store = self.capture()
        store['state']['dailyRunCount'] = 7
        self.b._save_ai_trade_council_automation_store(store)
        pending = store['state']['pendingQueue'][0]
        parent = {
            'id': 'mission-previous-day', 'status': 'completed',
            'analysisContext': {
                'kind': 'ai_trade_council_parent',
                'closedBarIdentity': {'streamKey': pending['streamKey'], 'closedBarTime': pending['closedBarTime']},
                'automation': {'source': 'backend_scheduler', 'dayKey': '2026-10-22'},
            },
        }
        def crosses_midnight():
            day[0] = '2026-10-23'
            return [parent]
        self.b.load_missions = crosses_midnight
        self.b.mission_read_model_item = lambda mission: mission
        self.b.ai_trade_council_automation_tick()
        saved = self.b.load_ai_trade_council_automation_store()['state']
        self.assertEqual(saved['dailyRunDate'], '2026-10-23')
        self.assertEqual(saved['dailyRunCount'], 0)
        self.assertEqual(saved['coverageRecords'][0]['missionId'], parent['id'])

    def test_actual_missed_bar_is_recorded_without_inventing_snapshot(self):
        self.f._save_observed_store()
        previous = self.f.closed_bar_time
        self.f.closed_bar_time += 900
        snapshot = self.f._snapshot()
        snapshot['chartSnapshot']['bars'] = [
            {'time': previous}, {'time': previous+300}, {'time': self.f.closed_bar_time},
        ]
        self.b.metatrader_snapshot_read_model = lambda _: snapshot
        self.b.ai_trade_council_automation_tick()
        rows = self.b.load_ai_trade_council_automation_store()['state']['coverageRecords']
        self.assertEqual([row['closedBarTime'] for row in rows], [previous+300, previous+900])
        self.assertEqual(rows[0]['status'], 'skipped')
        self.assertIsNone(rows[0]['snapshotArtifact'])

    def test_midnight_preserves_ten_second_old_capture(self):
        store = self.capture()
        store['state']['dailyRunDate'] = '2026-10-22'
        store['state']['dailyRunCount'] = 10
        row = store['state']['coverageRecords'][0]
        row['detectedAt'] = '2026-10-22T23:59:50+07:00'
        before = copy.deepcopy(store['state']['coverageRecords'])
        rolled, changed = self.b._rollover_ai_trade_council_automation_day(
            store, datetime.fromisoformat('2026-10-23T00:00:00+07:00'),
        )
        self.assertTrue(changed)
        self.assertEqual(rolled['state']['dailyRunCount'], 0)
        self.assertEqual(rolled['state']['coverageRecords'], before)
        self.assertEqual(len(rolled['state']['pendingQueue']), 1)

    def test_first_ever_observation_does_not_start_historical_analysis(self):
        store = self.b._ai_trade_council_automation_default_store()
        store['config']['enabled'] = True
        self.b._save_ai_trade_council_automation_store(store)
        self.b.ai_trade_council_automation_tick()
        self.b.ai_trade_council_automation_tick()
        saved = self.b.load_ai_trade_council_automation_store()['state']
        self.assertEqual(saved['coverageRecords'], [])
        self.assertEqual(len(self.f.calls), 0)

    def test_invalid_future_capture_is_history_only(self):
        snapshot = self.f._snapshot()
        snapshot['chartSnapshot']['observedAt'] = (datetime.now(timezone.utc)+timedelta(hours=1)).isoformat()
        identity, _ = self.b._ai_trade_council_closed_bar_identity(snapshot)
        preflight = self.b._ai_trade_council_analysis_start_preflight(snapshot, identity)
        self.assertEqual(preflight['status'], 'audit_only')
        self.assertEqual(preflight['reasonCode'], 'analysis_snapshot_time_invalid_before_start')

    def test_bar_regression_reobservation_cannot_replace_capture_or_upgrade_audit(self):
        store = self.capture()
        row = store['state']['pendingQueue'][0]
        row['executionPolicy'] = 'audit_only_no_stale_dispatch'
        row['reasonCode'] = 'analysis_snapshot_expired_before_start'
        self.b._save_ai_trade_council_coverage_records([row])
        original = self.b.load_ai_trade_council_automation_store()['state']['pendingQueue'][0]
        current_time = self.f.closed_bar_time
        self.f.closed_bar_time -= 300
        self.b.ai_trade_council_automation_tick()
        self.f.closed_bar_time = current_time
        self.f.snapshot_id = 'f'*64
        result = self.b.ai_trade_council_automation_tick()
        self.assertEqual(result['kind'], 'ai_trade_council_automation_reobserved')
        recovered = self.b.load_ai_trade_council_automation_store()['state']['coverageRecords'][0]
        self.assertEqual(recovered['snapshotArtifactDigest'], original['snapshotArtifactDigest'])
        self.assertEqual(recovered['snapshotId'], original['snapshotId'])
        self.assertEqual(recovered['detectedAt'], original['detectedAt'])
        self.assertEqual(recovered['executionPolicy'], 'audit_only_no_stale_dispatch')
        self.b.ai_trade_council_automation_tick()
        self.assertEqual(self.f.calls, [])
        self.assertEqual(recovered['status'], 'skipped')

    def test_multi_day_quota_outage_has_no_capture_and_no_midbar_resume(self):
        self.f._save_observed_store()
        self.b._collaboration_quota_gate = lambda *a, **kw: {'allowed': False, 'reason': 'quota_limit_reached'}
        with mock.patch.object(self.b, '_write_ai_trade_council_snapshot_artifact') as capture:
            for day in range(3):
                self.f.closed_bar_time += 86400
                result = self.b.ai_trade_council_automation_tick()
                self.assertEqual(result['reason'], 'quota_limit_reached')
            capture.assert_not_called()
        self.b._collaboration_quota_gate = lambda *a, **kw: {'allowed': True}
        self.b.ai_trade_council_automation_tick()
        self.assertEqual(self.f.calls, [])
        self.f._advance_bar()
        self.b.ai_trade_council_automation_tick()
        self.f._finish_settle()
        self.b.ai_trade_council_automation_tick()
        self.assertEqual(len(self.f.calls), 1)
        self.assertEqual(self.f.calls[0]['automationContext']['closedBarTime'], self.f.closed_bar_time)
        state = self.b.load_ai_trade_council_automation_store()['state']
        self.assertEqual(state['pendingQueue'], [])
        self.assertEqual(sum(row['status'] == 'skipped' for row in state['coverageRecords']), 3)

    def test_gate_exception_consumes_trigger_and_cannot_resume_same_bar(self):
        for error in (OSError('offline'), ValueError('bad telemetry'), self.b.DataIntegrityError('bad store'), self.b.RequestError('blocked', 409)):
            with self.subTest(error=type(error).__name__):
                self.f._save_observed_store()
                self.f._advance_bar()
                with mock.patch.object(self.b, '_ai_trade_council_new_bar_gate', side_effect=error):
                    result = self.b.ai_trade_council_automation_tick()
                self.assertEqual(result['kind'], 'ai_trade_council_automation_skipped')
                state = self.b.load_ai_trade_council_automation_store()['state']
                self.assertEqual(state['coverageRecords'][-1]['status'], 'skipped')
                self.b.ai_trade_council_automation_tick()
                self.assertEqual(self.f.calls, [])

    def test_settle_window_expiry_is_terminal(self):
        store = self.capture()
        row = store['state']['pendingQueue'][0]
        row['triggerExpiresAt'] = (datetime.now(timezone.utc)-timedelta(seconds=1)).isoformat()
        self.b._save_ai_trade_council_coverage_records([row])
        result = self.b.ai_trade_council_automation_tick()
        self.assertEqual(result['reason'], 'new_bar_only_trigger_window_expired')
        self.b.ai_trade_council_automation_tick()
        self.assertEqual(self.f.calls, [])
        self.assertEqual(self.b.load_ai_trade_council_automation_store()['state']['pendingQueue'], [])

    def test_bar_changes_during_quota_refresh_cannot_dispatch_previous_capture(self):
        self.capture()
        def changes_bar(*a, **kw):
            self.f._advance_bar()
            return {'allowed': True}
        self.b._collaboration_quota_gate = changes_bar
        result = self.b.ai_trade_council_automation_tick()
        self.assertEqual(result['reason'], 'new_bar_only_trigger_window_expired')
        self.assertEqual(self.f.calls, [])

    def test_scheduler_outage_baselines_newest_bar_without_ai(self):
        self.f._save_observed_store()
        store = self.b.load_ai_trade_council_automation_store()
        store['state']['lastSchedulerTickAt'] = (datetime.now(timezone.utc)-timedelta(minutes=5)).isoformat()
        self.b._save_ai_trade_council_automation_store(store)
        self.f._advance_bar()
        result = self.b.ai_trade_council_automation_tick()
        self.assertEqual(result['reason'], 'new_bar_only_missed_trigger')
        self.b.ai_trade_council_automation_tick()
        self.assertEqual(self.f.calls, [])

    def test_disable_reenable_midbar_baselines_even_with_short_pause(self):
        self.f._save_observed_store()
        store = self.b.load_ai_trade_council_automation_store()
        store['config']['enabled'] = False
        self.b._save_ai_trade_council_automation_store(store)
        self.b.ai_trade_council_automation_tick()
        self.f._advance_bar()
        store = self.b.load_ai_trade_council_automation_store()
        store['config']['enabled'] = True
        self.b._save_ai_trade_council_automation_store(store)
        result = self.b.ai_trade_council_automation_tick()
        self.assertEqual(result['kind'], 'ai_trade_council_automation_baseline')
        self.b.ai_trade_council_automation_tick()
        self.assertEqual(self.f.calls, [])

    def test_midbar_restart_h1_waits_for_h1_close_and_m30_for_m30_close(self):
        for timeframe, seconds in (('H1', 3600), ('M30', 1800)):
            with self.subTest(timeframe=timeframe):
                self.f.calls.clear()
                self.f.timeframe = timeframe
                self.f._save_observed_store(startup_id='old-process')
                self.assertEqual(self.b.ai_trade_council_automation_tick()['kind'], 'ai_trade_council_automation_baseline')
                self.b.ai_trade_council_automation_tick()
                self.assertEqual(self.f.calls, [])
                self.f.closed_bar_time += seconds
                self.b.ai_trade_council_automation_tick()
                self.f._finish_settle()
                self.assertEqual(len(self.f.calls), 1)
                self.assertEqual(self.f.calls[0]['automationContext']['timeframe'], timeframe)

    def test_skipped_coverage_cannot_be_revived_as_pending(self):
        store = self.capture()
        row = store['state']['pendingQueue'][0]
        self.b._ai_trade_council_coverage_upsert(store, {**row, 'status': 'skipped', 'reasonCode': 'quota_limit_reached'})
        self.b._ai_trade_council_coverage_upsert(store, {**row, 'status': 'pending'})
        self.assertEqual(store['state']['coverageRecords'][0]['status'], 'skipped')

    def test_large_legacy_backlog_is_cancelled_without_any_ai(self):
        self.f._save_observed_store()
        store = self.b.load_ai_trade_council_automation_store()
        rows = [{
            'streamKey': store['state']['streamKey'], 'candidateId': self.f.candidate_id,
            'symbol': self.f.symbol, 'timeframe': self.f.timeframe,
            'closedBarTime': self.f.closed_bar_time - (520-index)*300,
            'snapshotId': f'{index+1:064x}', 'status': 'pending',
            'reasonCode': 'new_closed_bar_detected', 'executionPolicy': 'audit_only_no_stale_dispatch',
            'detectedAt': (datetime.now(timezone.utc)-timedelta(days=3)).isoformat(),
        } for index in range(520)]
        store['state']['coverageRecords'] = rows
        self.b._save_ai_trade_council_automation_store(store)
        self.b.ai_trade_council_automation_tick()
        state = self.b.load_ai_trade_council_automation_store()['state']
        self.assertEqual(len(state['coverageRecords']), 520)
        self.assertTrue(all(row['status'] == 'skipped' for row in state['coverageRecords']))
        self.assertEqual(state['pendingQueue'], [])
        self.assertEqual(self.f.calls, [])
        self.f._advance_bar()
        self.b.ai_trade_council_automation_tick()
        self.f._finish_settle()
        self.assertEqual(len(self.f.calls), 1)


if __name__ == '__main__':
    unittest.main()
