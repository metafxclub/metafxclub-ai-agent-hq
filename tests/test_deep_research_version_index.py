from __future__ import annotations

import importlib.util
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
    def report(report_id: str, source_record_id: str, ordinal: int) -> dict:
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
                }
            },
            "metrics": {
                "workflowOutput": {"applicable": True, "valid": True},
                "systemIdentity": {
                    "systemName": f"System {source_record_id}",
                    "strategyFamily": "trend_following",
                },
                "entrySteps": ["enter on close"],
                "exitSteps": ["exit on signal"],
                "riskModel": {"stopLoss": "1 ATR", "takeProfit": "2 ATR"},
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
        target_index = version_index[target_source]
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

        # The live/current projection demotes only the prior current row, not
        # every historical version. This bounds one report to two upserts.
        self.assertEqual(len(first_rows), 1)
        self.assertEqual(len(second_rows), 2)
        sheet_rows: dict[str, dict] = {}
        for row in [*first_rows, *second_rows]:
            sheet_rows.setdefault(row["research_id"], {}).update(row)
        self.assertEqual(len(sheet_rows), 2)
        self.assertEqual(
            sorted(row["research_version"] for row in sheet_rows.values()),
            ["1", "2"],
        )
        current_rows = [
            row for row in sheet_rows.values() if row.get("is_current") == "TRUE"
        ]
        self.assertEqual(len(current_rows), 1)
        self.assertEqual(current_rows[0]["research_version"], "2")

    def test_backfill_builds_complete_index_once_and_reuses_it(self) -> None:
        reports = [
            self.report(f"target-{ordinal:03d}", "world-target", ordinal)
            for ordinal in range(240)
        ]
        version_index = self.bridge._research_sheet_build_deep_version_index(reports)
        received_indexes: list[object] = []

        def queue_report(_report: dict, **kwargs) -> dict:
            received_indexes.append(kwargs.get("deep_version_index"))
            return {"queued": 1}

        with (
            patch.object(self.bridge, "load_runtime_reports", return_value=reports),
            patch.object(
                self.bridge,
                "_research_sheet_runtime_deep_version_index",
                return_value=version_index,
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
            ),
        ):
            result = self.bridge._research_sheet_backfill_recent_reports(
                {"deepResearch"}
            )

        self.assertEqual(result["queued"], 240)
        build_index.assert_called_once_with()
        self.assertEqual(len(received_indexes), 240)
        self.assertTrue(all(value is version_index for value in received_indexes))

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
        ):
            result = self.bridge._research_sheet_backfill_recent_reports(
                {"worldSystem"}
            )

        self.assertEqual(result["queued"], 0)
        queue_report.assert_not_called()


if __name__ == "__main__":
    unittest.main()
