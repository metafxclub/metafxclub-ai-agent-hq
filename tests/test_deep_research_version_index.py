from __future__ import annotations

import importlib.util
import json
import os
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import Mock, patch


ROOT = Path(__file__).resolve().parents[1]
BRIDGE_PATH = ROOT / "backend" / "local-runner" / "bridge_server.py"


def load_bridge():
    spec = importlib.util.spec_from_file_location(
        "deep_research_version_index_test_bridge",
        BRIDGE_PATH,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to import {BRIDGE_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class DeepResearchVersionIndexTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.bridge = load_bridge()

    @staticmethod
    def report(
        report_id: str,
        source_record_id: str,
        ordinal: int,
        *,
        source_report_id: str | None = "world-source-default",
    ) -> dict:
        created_at = (
            datetime(2026, 1, 1, tzinfo=timezone.utc)
            + timedelta(seconds=ordinal)
        ).isoformat().replace("+00:00", "Z")
        return {
            "id": report_id,
            "type": "trading_system_research_report",
            "title": f"Deep research {report_id}",
            "status": "ready",
            "linkedPropId": "left_server_racks",
            "linkedMissionId": f"mission-{report_id}",
            "createdAt": created_at,
            "updatedAt": created_at,
            "workflowContext": {
                "source": {
                    "recordId": source_record_id,
                    "systemId": f"system-{source_record_id}",
                    **(
                        {"reportId": source_report_id}
                        if source_report_id is not None
                        else {}
                    ),
                }
            },
            "metrics": {
                "workflowOutput": {"applicable": True, "valid": True},
                "strategyBrief": {
                    "schemaVersion": "ea-strategy-brief/1.0.0",
                    "systemName": f"System {source_record_id} {report_id}",
                    "systemOverview": "Trend following on a user-selected market and timeframe.",
                    "entryRules": "Buy on a confirmed closed-bar signal; Sell on the inverse signal.",
                    "recoveryRules": "ไม่มีการแก้ไม้",
                    "exitRules": "Close on the opposite signal; SL and TP remain user inputs.",
                    "moneyManagement": "Use a user-selected fixed lot with one open position.",
                    "orderExecution": "Use market Buy or Sell after the bar closes.",
                    "displayRequirements": "Show system name, signal, Balance, Equity and Spread.",
                    "additionalNotes": "ไม่มีหมายเหตุเพิ่มเติม",
                    "sourceLinks": [
                        "https://www.investopedia.com/terms/m/movingaverage.asp",
                        "https://www.babypips.com/learn/forex/moving-averages",
                    ],
                    "checkedAt": "2026-09-10T12:00:00+07:00",
                    "limitations": ["Research specification only; compile separately."],
                },
            },
        }

    def test_more_than_2000_interleaved_reports_keep_one_current_version(self) -> None:
        target_source = "world-target"
        first = self.report("target-v1", target_source, 0)
        unrelated = [
            self.report(f"other-{ordinal:04d}", f"world-other-{ordinal:04d}", ordinal)
            for ordinal in range(1, 2102)
        ]
        second = self.report("target-v2", target_source, 2102)
        reports = [first, *unrelated, second]

        report_paths = [
            Path("virtual-reports") / f"{index:04d}.json"
            for index in range(len(reports))
        ]
        payload_by_path = dict(zip(report_paths, reports))
        runtime_reports_dir = Mock()
        runtime_reports_dir.glob.return_value = report_paths
        with (
            patch.object(self.bridge, "RUNTIME_REPORTS_DIR", runtime_reports_dir),
            patch.object(self.bridge, "ensure_runtime_dir"),
            patch.object(
                self.bridge,
                "read_json",
                side_effect=lambda path, _default: payload_by_path[path],
            ) as read_report,
        ):
            version_index = self.bridge._research_sheet_runtime_deep_version_index()

        runtime_reports_dir.glob.assert_called_once_with("*.json")
        self.assertEqual(read_report.call_count, 2103)
        target_index = version_index[("world-source-default", target_source)]
        self.assertEqual(len(reports), 2103)
        self.assertEqual(
            [item["reportId"] for item in target_index["ordered"]],
            ["target-v1", "target-v2"],
        )
        self.assertEqual(target_index["currentReportId"], "target-v2")

        with patch.object(
            self.bridge,
            "_research_sheet_runtime_deep_version_index",
            side_effect=AssertionError("shared index must prevent a per-report rescan"),
        ):
            first_rows = self.bridge._research_sheet_deep_rows(
                first,
                version_index=version_index,
            )[0]
            second_rows = self.bridge._research_sheet_deep_rows(
                second,
                version_index=version_index,
            )[0]

        # A-J uses one stable record_id. Each accepted revision projects one
        # replacement row; revision history remains in the Backend ledger.
        self.assertEqual(len(first_rows), 1)
        self.assertEqual(len(second_rows), 1)
        sheet_rows: dict[str, dict] = {}
        for row in [*first_rows, *second_rows]:
            sheet_rows[row["record_id"]] = row
        self.assertEqual(len(sheet_rows), 1)
        current_row = next(iter(sheet_rows.values()))
        self.assertIn("target-v2", current_row["system_name"])
        self.assertEqual(
            set(current_row),
            set(self.bridge.RESEARCH_SHEET_DEEP_WRITE_HEADERS),
        )

    def test_version_identity_uses_source_report_and_record_pair(self) -> None:
        same_pair_v1 = self.report(
            "pair-a-v1", "system-1", 1, source_report_id="world-report-a"
        )
        same_pair_v2 = self.report(
            "pair-a-v2", "system-1", 2, source_report_id="world-report-a"
        )
        different_report = self.report(
            "pair-b-v1", "system-1", 3, source_report_id="world-report-b"
        )
        legacy_one = self.report(
            "legacy-one", "system-1", 4, source_report_id=None
        )
        legacy_two = self.report(
            "legacy-two", "system-1", 5, source_report_id=None
        )

        index = self.bridge._research_sheet_build_deep_version_index([
            same_pair_v1,
            same_pair_v2,
            different_report,
            legacy_one,
            legacy_two,
        ])

        self.assertEqual(
            [item["reportId"] for item in index[("world-report-a", "system-1")]["ordered"]],
            ["pair-a-v1", "pair-a-v2"],
        )
        self.assertEqual(
            [item["researchVersion"] for item in index[("world-report-a", "system-1")]["ordered"]],
            [1, 2],
        )
        self.assertEqual(
            index[("world-report-b", "system-1")]["ordered"][0]["researchVersion"],
            1,
        )
        self.assertIn(("legacy:legacy-one", "system-1"), index)
        self.assertIn(("legacy:legacy-two", "system-1"), index)
        self.assertEqual(index[("legacy:legacy-one", "system-1")]["currentReportId"], "legacy-one")
        self.assertEqual(index[("legacy:legacy-two", "system-1")]["currentReportId"], "legacy-two")

    def test_backfill_preserves_compact_rows_without_scanning_complete_history(self) -> None:
        reports = [
            self.report(f"target-{ordinal:03d}", "world-target", ordinal)
            for ordinal in range(3)
        ]
        version_index = self.bridge._research_sheet_build_deep_version_index(reports)
        projected = []

        def queue_report(report: dict, **kwargs) -> dict:
            self.assertFalse(kwargs["flush"])
            self.assertEqual(kwargs["allowed_consumer_ids"], {"deepResearch"})
            self.assertIsNone(kwargs.get("deep_version_index"))
            items = self.bridge._research_sheet_report_items(
                report, 3, deep_version_index=kwargs.get("deep_version_index")
            )
            projected.extend(items)
            return {"queued": len(items)}

        with (
            patch.object(self.bridge, "utc_now", return_value="2026-10-27T00:00:00Z"),
            patch.object(self.bridge, "_deep_research_report_is_human_confirmed", return_value=True),
            patch.object(self.bridge, "load_runtime_reports", return_value=reports) as load_recent,
            patch.object(
                self.bridge,
                "_research_sheet_runtime_deep_version_index",
                side_effect=AssertionError("compact projection must not scan full history"),
            ) as build_index,
            patch.object(
                self.bridge,
                "_research_sheet_queue_report",
                side_effect=queue_report,
            ),
            patch.object(
                self.bridge,
                "_flush_research_sheet_outbox",
                return_value={"processed": 0, "synced": 0},
            ) as flush,
            patch.object(
                self.bridge,
                "_research_sheet_drain_deferred_reports",
                return_value={"queued": 0, "eligibleDeferred": 0},
            ) as drain,
        ):
            expected = [
                item
                for report in reversed(reports)
                for item in self.bridge._research_sheet_report_items(
                    report, 3, deep_version_index=version_index
                )
            ]
            result = self.bridge._research_sheet_backfill_recent_reports(
                {"deepResearch"}
            )

        self.assertEqual(result["queued"], 3)
        self.assertEqual(projected, expected)
        self.assertEqual(len(projected), 3)
        self.assertTrue(all(set(item["row"]) == set(self.bridge.RESEARCH_SHEET_DEEP_WRITE_HEADERS) for item in projected))
        load_recent.assert_called_once_with(limit=240)
        build_index.assert_not_called()
        flush.assert_called_once_with(max_items=50)
        drain.assert_called_once_with(
            max_reports=self.bridge.RESEARCH_SHEET_DEFERRED_REPORT_DRAIN_BATCH_LIMIT,
            allowed_consumer_ids={"deepResearch"},
        )

    def test_backfill_reads_only_recent_cap_with_large_synthetic_history(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            reports_dir = Path(directory)
            for ordinal in range(260):
                report = self.report(f"history-{ordinal:03d}", "world-target", ordinal)
                path = reports_dir / (report["id"] + ".json")
                path.write_text(json.dumps(report), encoding="utf-8")
                stamp = 1_700_000_000 + ordinal
                os.utime(path, (stamp, stamp))
            with (
                patch.object(self.bridge, "RUNTIME_REPORTS_DIR", reports_dir),
                patch.object(self.bridge, "ensure_runtime_dir"),
                patch.object(self.bridge, "read_json", wraps=self.bridge.read_json) as read_report,
                patch.object(self.bridge, "load_missions", side_effect=AssertionError("backfill must not read Missions")),
                patch.object(self.bridge, "_research_sheet_runtime_deep_version_index", side_effect=AssertionError("full archive scan")) as build_index,
                patch.object(self.bridge, "_research_sheet_queue_report", return_value={"queued": 1}) as queue,
                patch.object(self.bridge, "_flush_research_sheet_outbox", return_value={"processed": 0, "synced": 0}),
                patch.object(self.bridge, "_research_sheet_drain_deferred_reports", return_value={"queued": 0, "eligibleDeferred": 0}),
            ):
                result = self.bridge._research_sheet_backfill_recent_reports({"deepResearch"})
            self.assertEqual(result["queued"], 240)
            self.assertEqual(read_report.call_count, 240)
            self.assertEqual([call.args[0]["id"] for call in queue.call_args_list], [f"history-{i:03d}" for i in range(20, 260)])
            build_index.assert_not_called()

    def test_non_deep_backfill_does_not_scan_deep_version_history(self) -> None:
        deep_report = self.report("target-001", "world-target", 1)
        with (
            patch.object(
                self.bridge,
                "load_runtime_reports",
                return_value=[deep_report],
            ),
            patch.object(
                self.bridge,
                "_research_sheet_runtime_deep_version_index",
                side_effect=AssertionError("excluded consumer must not scan history"),
            ),
            patch.object(self.bridge, "_research_sheet_queue_report") as queue_report,
            patch.object(
                self.bridge,
                "_flush_research_sheet_outbox",
                return_value={"processed": 0, "synced": 0},
            ),
            patch.object(
                self.bridge,
                "_research_sheet_drain_deferred_reports",
                return_value={"queued": 0, "eligibleDeferred": 0},
            ),
        ):
            result = self.bridge._research_sheet_backfill_recent_reports(
                {"worldSystem"}
            )

        self.assertEqual(result["queued"], 0)
        queue_report.assert_not_called()


if __name__ == "__main__":
    unittest.main()
