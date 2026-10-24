"""Static contracts for new-bar admission; no Backend import or live I/O."""
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class CouncilNewBarPolicyContractTests(unittest.TestCase):
    def test_all_published_council_contracts_agree_on_no_backfill(self):
        def walk(value):
            if isinstance(value, dict):
                for key, item in value.items():
                    if key == 'backlogPolicy':
                        yield item
                    yield from walk(item)
            elif isinstance(value, list):
                for item in value:
                    yield from walk(item)

        for name in ('orchestration/orchestration-contract.json', 'reports/report-contract.json',
                     'connections/dashboard-connection-contract.json'):
            with self.subTest(contract=name):
                contract = json.loads((ROOT / 'contracts' / name).read_text(encoding='utf-8-sig'))
                self.assertEqual(list(walk(contract)), ['new_closed_bar_only_no_backfill'])

    def test_coverage_contract_no_longer_spends_ai_on_missed_or_expired_captures(self):
        contract = json.loads((ROOT / 'contracts/orchestration/orchestration-contract.json').read_text(encoding='utf-8-sig'))
        policy = contract['aiTradeCouncilAutoAnalysis']['coveragePolicy']
        self.assertEqual(policy['pendingQueueOrder'], 'new_closed_bar_only')
        self.assertEqual(policy['maximumRunnablePending'], 1)
        self.assertEqual(policy['pendingCapacityPolicy'], 'no_backfill')
        self.assertEqual(policy['analysisStartPolicy'], 'expired_or_missed_capture_skipped_without_ai')
        self.assertEqual(policy['quotaResumePolicy'], 'wait_for_next_closed_bar')
        self.assertEqual(policy['historyInvariant'], 'expected_equals_analyzed_plus_skipped_plus_pending_plus_queued')


if __name__ == '__main__':
    unittest.main()
