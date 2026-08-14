from __future__ import annotations

import importlib.util
import json
import math
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest import mock


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BRIDGE_PATH = PROJECT_ROOT / "backend" / "local-runner" / "bridge_server.py"
RUNNER_PATH = PROJECT_ROOT / "runner" / "codex_cli_runner.py"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class DailyFxNewsCalendarBackendTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.bridge = load_module("metafx_daily_fx_news_bridge", BRIDGE_PATH)
        cls.runner = load_module("metafx_daily_fx_news_runner", RUNNER_PATH)

    def pair_rows(self, source_ref: str = "official-1") -> list[dict]:
        return [
            {
                "pair": pair,
                "short": {
                    "bias": "BULLISH" if pair == "EURUSD" else "INSUFFICIENT_DATA",
                    "confidence": 70 if pair == "EURUSD" else None,
                    "sourceRefs": [source_ref] if pair == "EURUSD" else [],
                },
                "medium": {"bias": "INSUFFICIENT_DATA", "confidence": None, "sourceRefs": []},
                "long": {"bias": "INSUFFICIENT_DATA", "confidence": None, "sourceRefs": []},
                "confidence": 70 if pair == "EURUSD" else None,
                "verified": pair == "EURUSD",
            }
            for pair in self.bridge.FX_BIAS_PAIRS
        ]

    def insufficient_pair_rows(self) -> list[dict]:
        return [
            {
                "pair": pair,
                "short": {"bias": "INSUFFICIENT_DATA", "confidence": None, "sourceRefs": []},
                "medium": {"bias": "INSUFFICIENT_DATA", "confidence": None, "sourceRefs": []},
                "long": {"bias": "INSUFFICIENT_DATA", "confidence": None, "sourceRefs": []},
                "confidence": None,
                "verified": False,
            }
            for pair in self.bridge.FX_BIAS_PAIRS
        ]

    def report(
        self,
        report_id: str,
        *,
        updated_at: str,
        events: list[dict],
        quiet_day: bool = False,
        source_status: str = "success",
        danger_windows: list[dict] | None = None,
    ) -> dict:
        source_url = "https://www.bls.gov/news.release/cpi.nr0.htm"
        return {
            "id": report_id,
            "linkedPropId": "left_signal_cube",
            "type": "fx_news_bias_report",
            "status": "ready",
            "createdAt": updated_at,
            "updatedAt": updated_at,
            "workflowContext": {
                "propId": "left_signal_cube",
                "actionId": "analyze_daily_market_news",
                "inputs": {"marketDate": "2026-08-14"},
            },
            "metrics": {
                "marketDate": "2026-08-14",
                "sourceStatus": source_status,
                "quietDay": quiet_day,
                "events": events,
                "dangerWindows": danger_windows or [],
                "pairBias": self.pair_rows(),
                "sourceLinks": [{
                    "id": "official-1",
                    "title": "BLS release",
                    "url": source_url,
                    "checkedAt": updated_at,
                }],
            },
            "evidence": [{"label": "BLS release", "url": source_url}],
        }

    def event(
        self,
        *,
        actual=None,
        actual_status: str = "pending",
        scheduled_at: str = "2026-08-14T08:30:00-04:00",
        title: str = "US CPI",
        event_id: str | None = "bls-cpi-2026-08",
    ) -> dict:
        return {
            "eventId": event_id,
            "titleTh": title,
            "summaryTh": "ประกาศดัชนีราคาผู้บริโภคจากหน่วยงานต้นทาง",
            "detailTh": "ข้อมูลต้นฉบับสำหรับการประเมินผลกระทบหลังประกาศ",
            "currencies": ["USD"],
            "scheduledAt": scheduled_at,
            "timeKind": "timed",
            "impact": "high",
            "actual": actual,
            "actualStatus": actual_status,
            "forecast": "0.2%",
            "previous": "0.3%",
            "sourceRefs": ["official-1"],
            "pairImpacts": {
                "EURUSD": {
                    "impact": "BEARISH",
                    "confidence": 71,
                    "sourceRefs": ["official-1"],
                    "reasonTh": "USD แข็งกว่าคาด",
                }
            } if actual_status in {"released", "revised"} else {},
        }

    def test_direct_service_v3_migrates_once_then_preserves_enabled_and_times(self) -> None:
        default = self.bridge._default_dashboard_workflow_settings()["newsBiasSchedule"]
        self.assertTrue(default["requestedEnabled"])
        self.assertEqual(default["times"], ["00:00", "12:00"])
        self.assertEqual(default["minimumImpact"], "low")
        self.assertEqual(default["automaticDailyCalendarVersion"], 3)
        legacy = self.bridge._dashboard_workflow_settings_shape({
            "newsBiasSchedule": {
                "requestedEnabled": False,
                "times": ["07:00", "13:00", "19:00"],
                "minimumImpact": "high",
                "savedAt": "2026-08-13T00:00:00Z",
                "automaticDailyCalendarVersion": 2,
                "pendingSlotKey": "2026-08-13@20:00",
                "pendingScheduledAt": "2026-08-13T13:00:00Z",
                "dailyExecutionDate": "2026-08-13",
                "dailyExecutionCount": 2,
                "dailyExecutionSlotKeys": ["2026-08-13@07:00", "2026-08-13@20:00"],
            }
        })["newsBiasSchedule"]
        self.assertTrue(legacy["requestedEnabled"])
        self.assertEqual(legacy["times"], ["00:00", "12:00"])
        self.assertEqual(legacy["minimumImpact"], "low")
        self.assertEqual(legacy["automaticDailyCalendarVersion"], 3)
        self.assertIsNone(legacy["pendingSlotKey"])
        self.assertIsNone(legacy["pendingScheduledAt"])
        self.assertIsNone(legacy["dailyExecutionDate"])
        self.assertEqual(legacy["dailyExecutionCount"], 0)
        self.assertEqual(legacy["dailyExecutionSlotKeys"], [])
        saved = self.bridge._dashboard_workflow_settings_shape({
            "newsBiasSchedule": {
                "requestedEnabled": False,
                "times": ["09:15"],
                "minimumImpact": "high",
                "savedAt": "2026-08-14T00:00:00Z",
                "automaticDailyCalendarVersion": 3,
            }
        })["newsBiasSchedule"]
        self.assertFalse(saved["requestedEnabled"])
        self.assertEqual(saved["times"], ["09:15"])
        self.assertEqual(saved["minimumImpact"], "low")

    def test_same_event_is_upserted_and_released_zero_never_regresses_to_pending(self) -> None:
        morning = self.report(
            "morning",
            updated_at="2026-08-14T00:05:00Z",
            events=[self.event()],
        )
        released = self.report(
            "evening",
            updated_at="2026-08-14T13:05:00Z",
            events=[self.event(actual=0, actual_status="released", scheduled_at="2026-08-14T12:30:00Z")],
        )
        late_pending = self.report(
            "late-pending",
            updated_at="2026-08-14T13:10:00Z",
            events=[self.event(actual=None, actual_status="pending", scheduled_at="2026-08-14T19:30:00+07:00")],
        )
        model = self.bridge._fx_news_read_model(
            [morning, released, late_pending],
            now_local=datetime.fromisoformat("2026-08-14T21:00:00+07:00"),
        )
        self.assertEqual(model["eventCount"], 1)
        row = model["events"][0]
        self.assertEqual(row["actual"], "0")
        self.assertEqual(row["actualStatus"], "released")
        self.assertEqual(row["releaseState"], "released")
        self.assertEqual(row["scheduledAtUtc"], "2026-08-14T12:30:00Z")
        self.assertEqual(row["analyzedPairCount"], 1)
        self.assertEqual(row["affectedPairImpacts"][0]["impact"], "bearish")
        self.assertLessEqual(row["analyzedPairCount"], 14)

    def test_schedule_revision_updates_same_occurrence_and_revised_status_never_regresses(self) -> None:
        initial = self.report(
            "initial",
            updated_at="2026-08-14T00:05:00Z",
            events=[self.event(actual="0.1%", actual_status="revised")],
        )
        revised_time = self.report(
            "time-revision",
            updated_at="2026-08-14T02:05:00Z",
            events=[self.event(actual="0.2%", actual_status="released", scheduled_at="2026-08-14T13:00:00Z")],
        )
        model = self.bridge._fx_news_read_model(
            [initial, revised_time],
            now_local=datetime.fromisoformat("2026-08-14T21:00:00+07:00"),
        )
        self.assertEqual(model["eventCount"], 1)
        self.assertEqual(model["events"][0]["scheduledAtUtc"], "2026-08-14T13:00:00Z")
        self.assertEqual(model["events"][0]["actualStatus"], "revised")
        self.assertEqual(model["events"][0]["actual"], "0.1%")

    def test_same_title_separate_occurrences_remain_distinct(self) -> None:
        first = self.event(
            scheduled_at="2026-08-14T01:00:00Z",
            event_id="publisher-occurrence-1",
        )
        second = self.event(
            scheduled_at="2026-08-14T03:00:00Z",
            event_id="publisher-occurrence-2",
        )
        model = self.bridge._fx_news_read_model(
            [self.report("two-occurrences", updated_at="2026-08-14T00:05:00Z", events=[first, second])],
            now_local=datetime.fromisoformat("2026-08-14T12:00:00+07:00"),
        )
        self.assertEqual(model["eventCount"], 2)

    def test_same_title_without_publisher_ids_two_hours_apart_stays_distinct(self) -> None:
        first = self.event(scheduled_at="2026-08-14T01:00:00Z", event_id=None)
        second = self.event(scheduled_at="2026-08-14T03:00:00Z", event_id=None)
        model = self.bridge._fx_news_read_model(
            [self.report("no-id-occurrences", updated_at="2026-08-14T00:05:00Z", events=[first, second])],
            now_local=datetime.fromisoformat("2026-08-14T12:00:00+07:00"),
        )
        self.assertEqual(model["eventCount"], 2)

    def test_bangkok_day_filters_cross_midnight_and_requires_offset(self) -> None:
        valid = self.event(scheduled_at="2026-08-13T20:30:00-04:00")  # 07:30 Bangkok
        previous_bangkok_day = self.event(
            scheduled_at="2026-08-13T17:30:00Z",  # 00:30 Bangkok on the 14th is valid
            title="valid UTC boundary",
            event_id="valid-utc-boundary",
        )
        wrong_day = self.event(
            scheduled_at="2026-08-14T22:30:00+03:00",  # 02:30 Bangkok on the 15th
            title="wrong Bangkok day",
        )
        naive = self.event(scheduled_at="2026-08-14T08:30:00", title="naive")
        model = self.bridge._fx_news_read_model(
            [self.report("tz", updated_at="2026-08-14T01:00:00Z", events=[valid, previous_bangkok_day, wrong_day, naive])],
            now_local=datetime.fromisoformat("2026-08-14T10:00:00+07:00"),
        )
        self.assertEqual(model["eventCount"], 2)
        self.assertEqual({item["marketDate"] for item in model["events"]}, {"2026-08-14"})

    def test_tentative_released_zero_is_released_and_pending_actual_is_rejected(self) -> None:
        released = self.event(actual=0, actual_status="released", scheduled_at="2026-08-14T12:30:00Z")
        released["timeKind"] = "tentative"
        released["scheduledAt"] = None
        released["marketDate"] = "2026-08-14"
        model = self.bridge._fx_news_read_model(
            [self.report("tentative", updated_at="2026-08-14T01:00:00Z", events=[released])],
            now_local=datetime.fromisoformat("2026-08-14T10:00:00+07:00"),
        )
        self.assertEqual(model["events"][0]["actual"], "0")
        self.assertEqual(model["events"][0]["releaseState"], "released")
        invalid = dict(released, actualStatus="pending")
        invalid_model = self.bridge._fx_news_read_model(
            [self.report("invalid-actual", updated_at="2026-08-14T01:05:00Z", events=[invalid])],
            now_local=datetime.fromisoformat("2026-08-14T10:00:00+07:00"),
        )
        self.assertEqual(invalid_model["eventCount"], 0)

    def test_verified_quiet_day_is_distinct_from_no_report_and_source_failure(self) -> None:
        quiet = self.bridge._fx_news_read_model(
            [self.report("holiday", updated_at="2026-08-14T00:05:00Z", events=[], quiet_day=True, source_status="quiet_day")],
            now_local=datetime.fromisoformat("2026-08-14T08:00:00+07:00"),
        )
        self.assertEqual(quiet["dataStatus"], "verified_empty")
        self.assertTrue(quiet["verifiedEmpty"])
        self.assertFalse(quiet["failClosed"])
        missing = self.bridge._fx_news_read_model(
            [],
            now_local=datetime.fromisoformat("2026-08-14T08:00:00+07:00"),
        )
        self.assertEqual(missing["dataStatus"], "no_verified_data")
        self.assertTrue(missing["failClosed"])

    def test_later_source_failure_is_authoritative_but_preserves_labeled_last_good(self) -> None:
        good = self.report("good", updated_at="2026-08-14T01:00:00Z", events=[self.event()])
        failed = self.report(
            "failed",
            updated_at="2026-08-14T02:00:00Z",
            events=[],
            source_status="source_failure",
        )
        failed["status"] = "blocked"
        failed["metrics"] = {
            "marketDate": "2026-08-14",
            "error": "upstream unavailable",
        }
        model = self.bridge._fx_news_read_model(
            [good, failed],
            now_local=datetime.fromisoformat("2026-08-14T10:00:00+07:00"),
        )
        self.assertEqual(model["dataStatus"], "degraded_last_good")
        self.assertEqual(model["sourceStatus"], "source_failure")
        self.assertTrue(model["failClosed"])
        self.assertFalse(model["currentDataAvailable"])
        self.assertEqual(model["eventCount"], 1)
        bias = self.bridge._fx_bias_read_model(
            [good, failed],
            now_local=datetime.fromisoformat("2026-08-14T10:00:00+07:00"),
        )
        self.assertEqual(bias["dataStatus"], "source_failure")
        self.assertEqual(bias["verifiedPairCount"], 0)

    def test_blocked_only_attempt_is_source_failure_not_no_report(self) -> None:
        blocked = self.report("blocked-only", updated_at="2026-08-14T02:00:00Z", events=[])
        blocked["status"] = "blocked"
        blocked["metrics"] = {"marketDate": "2026-08-14", "error": "source timeout"}
        news = self.bridge._fx_news_read_model(
            [blocked],
            now_local=datetime.fromisoformat("2026-08-14T10:00:00+07:00"),
        )
        bias = self.bridge._fx_bias_read_model(
            [blocked],
            now_local=datetime.fromisoformat("2026-08-14T10:00:00+07:00"),
        )
        self.assertEqual(news["dataStatus"], "source_failure")
        self.assertEqual(news["sourceStatus"], "source_failure")
        self.assertTrue(news["failClosed"])
        self.assertEqual(bias["dataStatus"], "source_failure")
        self.assertEqual(bias["verifiedPairCount"], 0)

    def test_missing_source_status_fails_closed_for_news_and_bias(self) -> None:
        legacy = self.report("legacy", updated_at="2026-08-14T01:00:00Z", events=[self.event()])
        legacy["metrics"].pop("sourceStatus")
        news = self.bridge._fx_news_read_model(
            [legacy],
            now_local=datetime.fromisoformat("2026-08-14T10:00:00+07:00"),
        )
        bias = self.bridge._fx_bias_read_model(
            [legacy],
            now_local=datetime.fromisoformat("2026-08-14T10:00:00+07:00"),
        )
        self.assertNotEqual(news["dataStatus"], "verified")
        self.assertEqual(bias["verifiedPairCount"], 0)

    def test_declared_market_date_survives_cross_midnight_persistence_time(self) -> None:
        report = self.report(
            "cross-midnight",
            updated_at="2026-08-14T17:05:00Z",  # 15 Aug 00:05 Bangkok
            events=[self.event()],
        )
        model = self.bridge._fx_news_read_model(
            [report],
            now_local=datetime.fromisoformat("2026-08-14T23:55:00+07:00"),
        )
        self.assertEqual(model["eventCount"], 1)
        self.assertFalse(model["stale"])

    def test_danger_window_requires_order_currency_offset_same_day_and_six_hour_bound(self) -> None:
        good = {
            "currencies": ["USD"],
            "startsAt": "2026-08-14T12:15:00Z",
            "endsAt": "2026-08-14T12:45:00Z",
            "reasonTh": "ช่วงประกาศ",
            "sourceRefs": ["official-1"],
        }
        too_long = {**good, "endsAt": "2026-08-14T20:45:00Z"}
        backwards = {**good, "endsAt": "2026-08-14T11:45:00Z"}
        model = self.bridge._fx_news_read_model(
            [self.report("windows", updated_at="2026-08-14T01:00:00Z", events=[self.event()], danger_windows=[good, too_long, backwards])],
            now_local=datetime.fromisoformat("2026-08-14T10:00:00+07:00"),
        )
        self.assertEqual(len(model["dangerWindows"]), 1)

    def test_daily_contract_rejects_reference_only_hosts_and_invalid_calendar(self) -> None:
        procedure = self.bridge.equipment_action_profile("left_signal_cube", "analyze_daily_market_news")
        mission = {
            "createdAt": "2026-08-14T12:00:00Z",
            "budget": {"outputLimitChars": 20000},
            "workflowContext": {
                "propId": "left_signal_cube",
                "actionId": "analyze_daily_market_news",
                "inputs": {"marketDate": "2026-08-14"},
                "pluginProcedure": procedure,
            },
        }
        fields = {
            "marketDate": "2026-08-14",
            "sourceStatus": "success",
            "quietDay": False,
            "events": [self.event()],
            "dangerWindows": [],
            "pairBias": self.pair_rows(),
            "sourceLinks": [{"id": "official-1", "url": "https://www.forexfactory.com./calendar"}],
            "checkedAt": "2026-08-14T00:00:00Z",
            "updatedAt": "2026-08-14T00:00:00Z",
            "limitations": [],
        }
        result = {
            "contractFields": [
                {"field": key, "value": json.dumps(value, ensure_ascii=False, separators=(",", ":"))}
                for key, value in fields.items()
            ],
            "evidenceKinds": list(procedure["evidenceRequired"]),
            "evidence": [{"label": "reference", "url": "https://www.forexfactory.com./calendar", "note": ""}],
        }
        contract = self.bridge.validate_dashboard_workflow_output_contract(mission, result)
        self.assertFalse(contract["valid"])
        self.assertIn("source_link_not_admissible", contract["entryErrors"])
        for url in (
            "https://forexfactory.com/calendar",
            "https://sub.forexfactory.com/calendar",
            "https://nfs.faireconomy.media./calendar.json",
        ):
            self.assertTrue(self.bridge._fx_reference_only_host(url))

    def test_daily_contract_rejects_directional_horizon_before_related_actual(self) -> None:
        procedure = self.bridge.equipment_action_profile(
            "left_signal_cube",
            "analyze_daily_market_news",
        )
        mission = {
            "createdAt": "2026-08-14T01:00:00Z",
            "budget": {"outputLimitChars": 20000},
            "workflowContext": {
                "propId": "left_signal_cube",
                "actionId": "analyze_daily_market_news",
                "inputs": {"marketDate": "2026-08-14"},
                "pluginProcedure": procedure,
            },
        }
        source_url = "https://www.bls.gov/news.release/cpi.nr0.htm"
        fields = {
            "marketDate": "2026-08-14",
            "sourceStatus": "verified",
            "quietDay": False,
            "events": [self.event()],
            "dangerWindows": [],
            "pairBias": self.pair_rows(),
            "sourceLinks": [{
                "id": "official-1",
                "title": "BLS release",
                "url": source_url,
                "checkedAt": "2026-08-14T01:00:00Z",
            }],
            "checkedAt": "2026-08-14T01:00:00Z",
            "updatedAt": "2026-08-14T01:00:00Z",
            "limitations": [],
        }
        result = {
            "contractFields": [
                {
                    "field": key,
                    "value": json.dumps(value, ensure_ascii=False, separators=(",", ":")),
                }
                for key, value in fields.items()
            ],
            "evidenceKinds": list(procedure["evidenceRequired"]),
            "evidence": [{"label": "BLS release", "url": source_url, "note": ""}],
        }
        contract = self.bridge.validate_dashboard_workflow_output_contract(
            mission,
            result,
        )
        self.assertFalse(contract["valid"])
        self.assertIn(
            "source_url_per_supported_bias",
            contract["missingEvidenceKinds"],
        )

    def test_exact_pair_contract_rejects_nonfinite_and_boolean_horizon_confidence(self) -> None:
        rows = self.pair_rows()
        rows[0] = {
            **rows[0],
            "short": {"bias": "BULLISH", "confidence": math.inf},
            "shortBias": None,
        }
        self.assertIsNone(self.bridge._contract_pair_bias_rows({"pairBias": json.dumps(rows)}))
        rows[0]["short"]["confidence"] = True
        self.assertIsNone(self.bridge._contract_pair_bias_rows({"pairBias": json.dumps(rows)}))
        rows[0]["short"]["confidence"] = 0
        self.assertIsNotNone(self.bridge._contract_pair_bias_rows({"pairBias": json.dumps(rows)}))

    def test_daily_bias_requires_released_actual_and_claim_specific_horizon_evidence(self) -> None:
        pending_report = self.report(
            "pending-horizon-evidence",
            updated_at="2026-08-14T01:00:00Z",
            events=[self.event()],
        )
        pending_model = self.bridge._fx_bias_read_model(
            [pending_report],
            now_local=datetime.fromisoformat("2026-08-14T10:00:00+07:00"),
        )
        pending_eurusd = next(
            row for row in pending_model["pairs"] if row["pair"] == "EURUSD"
        )
        self.assertEqual(pending_eurusd["shortBias"], "insufficient_data")
        self.assertEqual(pending_eurusd["assessmentStatus"], "upcoming_event")
        self.assertEqual(pending_model["directionalPairCount"], 0)

        report = self.report(
            "horizon-evidence",
            updated_at="2026-08-14T01:00:00Z",
            events=[self.event(actual="0.1%", actual_status="released")],
        )
        report["metrics"]["pairBias"][0]["medium"] = {
            "bias": "BEARISH",
            "confidence": 60,
            "sourceRefs": [],
        }
        model = self.bridge._fx_bias_read_model(
            [report],
            now_local=datetime.fromisoformat("2026-08-14T10:00:00+07:00"),
        )
        eurusd = next(row for row in model["pairs"] if row["pair"] == "EURUSD")
        self.assertEqual(eurusd["shortBias"], "bullish")
        self.assertEqual(eurusd["mediumBias"], "insufficient_data")
        self.assertEqual(eurusd["assessmentStatus"], "directional_ready")
        self.assertTrue(eurusd["assessmentComplete"])
        self.assertEqual(model["directionalPairCount"], 1)

    def test_verified_upcoming_calendar_assesses_all_pairs_without_faking_direction(self) -> None:
        events = [
            self.event(
                event_id=f"usd-upcoming-{index}",
                title=f"USD release {index}",
                scheduled_at=f"2026-08-14T{12 + index:02d}:30:00Z",
            )
            for index in range(4)
        ]
        report = self.report(
            "upcoming-assessment",
            updated_at="2026-08-14T01:00:00Z",
            events=events,
        )
        report["metrics"]["pairBias"] = self.insufficient_pair_rows()

        model = self.bridge._fx_bias_read_model(
            [report],
            now_local=datetime.fromisoformat("2026-08-14T10:00:00+07:00"),
        )

        self.assertEqual(model["schemaVersion"], "fx-pair-bias-read-model-v3")
        self.assertEqual(model["assessedPairCount"], 28)
        self.assertEqual(model["directionalPairCount"], 0)
        self.assertEqual(model["verifiedPairCount"], 0)
        self.assertEqual(model["upcomingEventPairCount"], 7)
        self.assertEqual(model["awaitingEventPairCount"], 7)
        self.assertEqual(model["noDirectEventPairCount"], 21)
        self.assertTrue(model["assessmentComplete"])
        self.assertTrue(model["currentDataAvailable"])
        self.assertEqual(model["dataStatus"], "verified")
        eurusd = next(row for row in model["pairs"] if row["pair"] == "EURUSD")
        self.assertEqual(eurusd["assessmentStatus"], "upcoming_event")
        self.assertTrue(eurusd["assessmentComplete"])
        self.assertEqual(eurusd["relevantEventCount"], 4)
        self.assertEqual(len(eurusd["relevantEvents"]), 3)
        self.assertTrue(eurusd["nextEvent"]["eventId"].startswith("fxevent-"))
        self.assertEqual(eurusd["nextEvent"]["titleTh"], "USD release 0")
        self.assertEqual(
            eurusd["nextEvent"]["scheduledAtBangkok"],
            "2026-08-14T19:30:00+07:00",
        )
        self.assertTrue(all(
            eurusd["nextEvent"].get(field) is not None
            for field in ("titleTh", "currencies", "impact", "timeKind", "actualStatus")
        ))
        self.assertTrue(all(
            eurusd["horizons"][horizon]["bias"] == "insufficient_data"
            for horizon in ("short", "medium", "long")
        ))
        audcad = next(row for row in model["pairs"] if row["pair"] == "AUDCAD")
        self.assertEqual(audcad["assessmentStatus"], "no_direct_event")
        self.assertEqual(audcad["relevantEvents"], [])
        self.assertIsNone(audcad["nextEvent"])

    def test_pair_assessment_distinguishes_awaiting_actual_and_released_without_direction(self) -> None:
        pending_report = self.report(
            "pending-actual",
            updated_at="2026-08-14T13:05:00Z",
            events=[self.event(scheduled_at="2026-08-14T12:30:00Z")],
        )
        pending_report["metrics"]["pairBias"] = self.insufficient_pair_rows()
        pending_model = self.bridge._fx_bias_read_model(
            [pending_report],
            now_local=datetime.fromisoformat("2026-08-14T21:00:00+07:00"),
        )
        eurusd_pending = next(
            row for row in pending_model["pairs"] if row["pair"] == "EURUSD"
        )
        self.assertEqual(eurusd_pending["assessmentStatus"], "awaiting_actual")
        self.assertEqual(pending_model["awaitingActualPairCount"], 7)
        self.assertEqual(pending_model["awaitingEventPairCount"], 7)

        pending_event = pending_model["pairs"][self.bridge.FX_BIAS_PAIRS.index("EURUSD")][
            "relevantEvents"
        ][0]
        self.assertEqual(pending_event["timingState"], "past")
        self.assertEqual(pending_event["releaseState"], "unconfirmed")
        self.assertEqual(pending_event["analysisStatus"], "awaiting_actual")

        news_model = self.bridge._fx_news_read_model(
            [pending_report],
            now_local=datetime.fromisoformat("2026-08-14T21:00:00+07:00"),
        )
        self.assertEqual(news_model["events"][0]["releaseState"], "unconfirmed")
        self.assertEqual(news_model["events"][0]["analysisStatus"], "awaiting_actual")
        self.assertEqual(news_model["scheduledCount"], 0)

        released_event = self.event(
            actual="0.1%",
            actual_status="released",
            scheduled_at="2026-08-14T12:30:00Z",
        )
        released_event["pairImpacts"] = {}
        released_report = self.report(
            "released-no-direction",
            updated_at="2026-08-14T13:10:00Z",
            events=[released_event],
        )
        released_report["metrics"]["pairBias"] = self.insufficient_pair_rows()
        released_model = self.bridge._fx_bias_read_model(
            [released_report],
            now_local=datetime.fromisoformat("2026-08-14T21:00:00+07:00"),
        )
        eurusd_released = next(
            row for row in released_model["pairs"] if row["pair"] == "EURUSD"
        )
        self.assertEqual(eurusd_released["assessmentStatus"], "released_no_direction")
        self.assertEqual(eurusd_released["relevantEvents"][0]["actual"], "0.1%")
        self.assertIsNone(eurusd_released["nextEvent"])
        self.assertEqual(released_model["releasedNoDirectionPairCount"], 7)

    def test_pair_assessment_never_calls_non_release_released(self) -> None:
        self.assertEqual(
            self.bridge._fx_pair_assessment_status(
                directional_ready=False,
                relevant_events=[{
                    "timeKind": "holiday",
                    "timingState": "current",
                    "releaseState": "not_applicable",
                    "actualStatus": "not_applicable",
                }],
            ),
            "upcoming_event",
        )
        self.assertEqual(
            self.bridge._fx_pair_assessment_status(
                directional_ready=False,
                relevant_events=[{
                    "timeKind": "timed",
                    "timingState": "past",
                    "releaseState": "unconfirmed",
                    "actualStatus": "unavailable",
                }],
            ),
            "awaiting_actual",
        )
        self.assertEqual(
            self.bridge._fx_pair_assessment_status(
                directional_ready=False,
                relevant_events=[{
                    "timeKind": "timed",
                    "timingState": "current",
                    "releaseState": "scheduled",
                    "actualStatus": "pending",
                }],
            ),
            "upcoming_event",
        )

    def test_duplicate_pair_rows_cannot_inflate_directional_count(self) -> None:
        report = self.report(
            "duplicate-pair-rows",
            updated_at="2026-08-14T13:00:00Z",
            events=[self.event(actual=0, actual_status="released")],
        )
        report["metrics"]["pairBias"] = self.pair_rows() * 2
        model = self.bridge._fx_bias_read_model(
            [report],
            now_local=datetime.fromisoformat("2026-08-14T21:00:00+07:00"),
        )
        self.assertEqual(model["directionalPairCount"], 1)
        self.assertEqual(model["verifiedPairCount"], 1)
        self.assertEqual(model["insufficientDataPairCount"], 27)

    def test_dashboard_news_and_pair_assessment_share_one_bangkok_clock(self) -> None:
        with (
            mock.patch.object(
                self.bridge,
                "_fx_news_read_model",
                return_value={"schemaVersion": "news"},
            ) as news_reader,
            mock.patch.object(
                self.bridge,
                "_fx_bias_read_model",
                return_value={"schemaVersion": "bias"},
            ) as bias_reader,
        ):
            self.bridge.workflow_dashboard_read_model(
                "left_signal_cube",
                reports=[],
                bridge={},
                missions=[],
            )
        news_now = news_reader.call_args_list[0].kwargs["now_local"]
        bias_now = bias_reader.call_args.kwargs["now_local"]
        self.assertIs(news_now, bias_now)
        self.assertEqual(news_now.tzinfo, self.bridge.THAILAND_TIMEZONE)

    def test_verified_quiet_day_assesses_all_pairs_as_no_direct_event(self) -> None:
        report = self.report(
            "verified-quiet-assessment",
            updated_at="2026-08-14T01:00:00Z",
            events=[],
            quiet_day=True,
            source_status="quiet_day",
        )
        report["metrics"]["pairBias"] = self.insufficient_pair_rows()
        model = self.bridge._fx_bias_read_model(
            [report],
            now_local=datetime.fromisoformat("2026-08-14T10:00:00+07:00"),
        )
        self.assertEqual(model["assessedPairCount"], 28)
        self.assertEqual(model["noDirectEventPairCount"], 28)
        self.assertEqual(model["unavailablePairCount"], 0)
        self.assertTrue(model["assessmentComplete"])
        self.assertEqual({row["assessmentStatus"] for row in model["pairs"]}, {"no_direct_event"})

    def test_pair_assessment_is_unavailable_when_daily_sources_fail_closed(self) -> None:
        good = self.report(
            "assessment-good",
            updated_at="2026-08-14T01:00:00Z",
            events=[self.event()],
        )
        good["metrics"]["pairBias"] = self.insufficient_pair_rows()
        failed = self.report(
            "assessment-failed",
            updated_at="2026-08-14T02:00:00Z",
            events=[],
            source_status="source_failure",
        )
        failed["status"] = "blocked"
        failed["metrics"] = {"marketDate": "2026-08-14", "error": "source timeout"}
        model = self.bridge._fx_bias_read_model(
            [good, failed],
            now_local=datetime.fromisoformat("2026-08-14T10:00:00+07:00"),
        )
        self.assertEqual(model["dataStatus"], "source_failure")
        self.assertEqual(model["assessedPairCount"], 0)
        self.assertEqual(model["unavailablePairCount"], 28)
        self.assertFalse(model["assessmentComplete"])
        self.assertFalse(model["currentDataAvailable"])
        self.assertEqual({row["assessmentStatus"] for row in model["pairs"]}, {"unavailable"})

    def test_daily_contract_rejects_directional_event_pair_without_pair_source(self) -> None:
        event = self.event(actual="0.1%", actual_status="released")
        event["pairImpacts"]["EURUSD"].pop("sourceRefs")
        fields = {
            "marketDate": "2026-08-14",
            "sourceStatus": "success",
            "quietDay": False,
            "events": [event],
            "dangerWindows": [],
            "pairBias": self.pair_rows(),
            "sourceLinks": [{"id": "official-1", "url": "https://www.bls.gov/news.release/cpi.nr0.htm"}],
            "checkedAt": "2026-08-14T00:00:00Z",
            "updatedAt": "2026-08-14T00:00:00Z",
            "limitations": [],
        }
        valid, errors = self.bridge._fx_daily_calendar_contract_valid(
            {key: json.dumps(value, ensure_ascii=False) for key, value in fields.items()},
            [{"url": "https://www.bls.gov/news.release/cpi.nr0.htm"}],
            mission_row={
                "workflowContext": {
                    "actionId": "analyze_daily_market_news",
                    "inputs": {"marketDate": "2026-08-14"},
                }
            },
        )
        self.assertFalse(valid)
        self.assertIn("event_pair_impact_invalid", errors)

    def test_daily_contract_rejects_directional_event_pair_before_actual(self) -> None:
        event = self.event()
        event["pairImpacts"] = {
            "EURUSD": {
                "impact": "BEARISH",
                "confidence": 70,
                "sourceRefs": ["official-1"],
            }
        }
        fields = {
            "marketDate": "2026-08-14",
            "sourceStatus": "success",
            "quietDay": False,
            "events": [event],
            "dangerWindows": [],
            "pairBias": self.insufficient_pair_rows(),
            "sourceLinks": [{
                "id": "official-1",
                "title": "BLS release",
                "url": "https://www.bls.gov/news.release/cpi.nr0.htm",
                "checkedAt": "2026-08-14T01:00:00Z",
            }],
            "checkedAt": "2026-08-14T01:00:00Z",
            "updatedAt": "2026-08-14T01:00:00Z",
            "limitations": [],
        }
        valid, errors = self.bridge._fx_daily_calendar_contract_valid(
            {key: json.dumps(value, ensure_ascii=False) for key, value in fields.items()},
            [{"url": "https://www.bls.gov/news.release/cpi.nr0.htm"}],
            mission_row={
                "createdAt": "2026-08-14T01:00:00Z",
                "workflowContext": {
                    "actionId": "analyze_daily_market_news",
                    "inputs": {"marketDate": "2026-08-14"},
                },
            },
        )
        self.assertFalse(valid)
        self.assertIn("event_pair_impact_invalid", errors)

    def test_legacy_pending_event_pair_impacts_are_suppressed_on_read(self) -> None:
        pending = self.event()
        pending["pairImpacts"] = {
            "EURUSD": {
                "impact": "BEARISH",
                "confidence": 70,
                "sourceRefs": ["official-1"],
            }
        }
        rows, complete = self.bridge._fx_event_pair_impact_rows(
            pending,
            source_event_id="legacy-pending",
            metrics={},
            event_sources=[{
                "id": "official-1",
                "url": "https://www.bls.gov/news.release/cpi.nr0.htm",
            }],
        )
        self.assertEqual(rows, [])
        self.assertFalse(complete)

        released = {**pending, "actual": 0, "actualStatus": "released"}
        released_rows, released_complete = self.bridge._fx_event_pair_impact_rows(
            released,
            source_event_id="released",
            metrics={},
            event_sources=[{
                "id": "official-1",
                "url": "https://www.bls.gov/news.release/cpi.nr0.htm",
            }],
        )
        self.assertEqual(released_rows[0]["pair"], "EURUSD")
        self.assertEqual(released_rows[0]["impact"], "bearish")
        self.assertFalse(released_complete)

    def test_source_checked_at_must_be_zoned_and_not_future(self) -> None:
        base_fields = {
            "marketDate": "2026-08-14",
            "sourceStatus": "success",
            "quietDay": False,
            "events": [self.event()],
            "dangerWindows": [],
            "pairBias": self.pair_rows(),
            "checkedAt": "2026-08-14T01:00:00Z",
            "updatedAt": "2026-08-14T01:00:00Z",
            "limitations": [],
        }
        for checked_at in (None, "2026-08-14T01:00:00", "2026-08-14T02:00:00Z"):
            fields = {
                **base_fields,
                "sourceLinks": [{
                    "id": "official-1",
                    "url": "https://www.bls.gov/news.release/cpi.nr0.htm",
                    "checkedAt": checked_at,
                }],
            }
            valid, errors = self.bridge._fx_daily_calendar_contract_valid(
                {
                    key: (
                        value
                        if isinstance(value, str)
                        else json.dumps(value, ensure_ascii=False, separators=(",", ":"))
                    )
                    for key, value in fields.items()
                },
                [{"url": "https://www.bls.gov/news.release/cpi.nr0.htm"}],
                mission_row={"workflowContext": {"inputs": {"marketDate": "2026-08-14"}}},
            )
            self.assertFalse(valid)
            self.assertIn("source_link_not_admissible", errors)

    def test_daily_contract_requires_explicit_status_time_and_boolean_coherence(self) -> None:
        base_event = self.event()
        base_fields = {
            "marketDate": "2026-08-14",
            "sourceStatus": "success",
            "quietDay": False,
            "events": [base_event],
            "dangerWindows": [],
            "pairBias": self.pair_rows(),
            "sourceLinks": [{
                "id": "official-1",
                "url": "https://www.bls.gov/news.release/cpi.nr0.htm",
                "checkedAt": "2026-08-14T01:00:00Z",
            }],
            "checkedAt": "2026-08-14T01:00:00Z",
            "updatedAt": "2026-08-14T01:00:00Z",
            "limitations": [],
        }
        variants = []
        missing_time_kind = dict(base_event)
        missing_time_kind.pop("timeKind")
        variants.append({**base_fields, "events": [missing_time_kind]})
        missing_actual_status = dict(base_event)
        missing_actual_status.pop("actualStatus")
        variants.append({**base_fields, "events": [missing_actual_status]})
        tentative_naive = dict(base_event, timeKind="tentative", scheduledAt="2026-08-14T08:30:00")
        variants.append({**base_fields, "events": [tentative_naive]})
        variants.append({**base_fields, "quietDay": "not-a-boolean"})
        variants.append({**base_fields, "updatedAt": "2026-08-14T01:00:00"})
        for fields in variants:
            valid, errors = self.bridge._fx_daily_calendar_contract_valid(
                {
                    key: (
                        value
                        if isinstance(value, str)
                        else json.dumps(value, ensure_ascii=False, separators=(",", ":"))
                    )
                    for key, value in fields.items()
                },
                [{"url": "https://www.bls.gov/news.release/cpi.nr0.htm"}],
                mission_row={
                    "createdAt": "2026-08-14T01:00:00Z",
                    "workflowContext": {"inputs": {"marketDate": "2026-08-14"}},
                },
            )
            self.assertFalse(valid, errors)

    def test_live_combined_status_and_event_aliases_stay_fail_closed_with_exact_prompt_enums(self) -> None:
        procedure = self.bridge.equipment_action_profile(
            "left_signal_cube",
            "analyze_daily_market_news",
        )
        prompt = self.bridge._workflow_prompt(
            "analyze_daily_market_news",
            {"marketDate": "2026-08-14", "minimumImpact": "low"},
            None,
            procedure,
        )
        self.assertIn('["success","verified","quiet_day"]', prompt)
        self.assertIn('ห้ามใช้ "scheduled" หรือ "published"', prompt)
        self.assertIn(
            'actual ต้องเป็น null เมื่อ actualStatus เป็น pending/unavailable/not_applicable',
            prompt,
        )
        report_contract = json.loads(
            (PROJECT_ROOT / "contracts" / "reports" / "report-contract.json").read_text(
                encoding="utf-8"
            )
        )
        enum_rules = report_contract["typed_report_schemas"]["fx_news_bias_report"]["enumRules"]
        self.assertEqual(
            enum_rules["sourceStatus"],
            ["success", "verified", "quiet_day", "partial_success", "source_failure"],
        )
        self.assertEqual(
            enum_rules["events[].timeKind"],
            ["timed", "tentative", "all_day", "holiday"],
        )

        released = self.event(actual="0.4% q/q", actual_status="released")
        released["timeKind"] = "published"
        pending = self.event(
            event_id="official-upcoming-1",
            title="Eurostat GDP/จ้างงาน Q2",
        )
        pending["timeKind"] = "scheduled"
        fields = {
            "marketDate": "2026-08-14",
            # Exact malformed scalar observed in the live Mission: this is
            # two alternatives, not one trustworthy enum choice.
            "sourceStatus": "success/verified",
            "quietDay": False,
            "events": [released, pending],
            "dangerWindows": [],
            "pairBias": self.pair_rows(),
            "sourceLinks": [{
                "id": "official-1",
                "url": "https://www.bls.gov/news.release/cpi.nr0.htm",
                "checkedAt": "2026-08-14T01:00:00Z",
            }],
            "checkedAt": "2026-08-14T01:00:00Z",
            "updatedAt": "2026-08-14T01:00:00Z",
            "limitations": [],
        }
        encoded = {
            key: (
                value
                if isinstance(value, str)
                else json.dumps(value, ensure_ascii=False, separators=(",", ":"))
            )
            for key, value in fields.items()
        }
        mission = {
            "createdAt": "2026-08-14T12:00:00Z",
            "workflowContext": {
                "actionId": "analyze_daily_market_news",
                "inputs": {"marketDate": "2026-08-14"},
            },
        }
        valid, errors = self.bridge._fx_daily_calendar_contract_valid(
            encoded,
            [{"url": "https://www.bls.gov/news.release/cpi.nr0.htm"}],
            mission_row=mission,
        )
        self.assertFalse(valid)
        self.assertIn("event_semantic_invalid", errors)
        self.assertIn("source_status_invalid", errors)

        # The Backend does not guess between combined values or reinterpret
        # release-state aliases.  A canonical retry is accepted once every
        # field makes one explicit, coherent choice.
        released["timeKind"] = "timed"
        pending["timeKind"] = "timed"
        fields["sourceStatus"] = "verified"
        fields["events"] = [released, pending]
        canonical = {
            key: (
                value
                if isinstance(value, str)
                else json.dumps(value, ensure_ascii=False, separators=(",", ":"))
            )
            for key, value in fields.items()
        }
        valid, errors = self.bridge._fx_daily_calendar_contract_valid(
            canonical,
            [{"url": "https://www.bls.gov/news.release/cpi.nr0.htm"}],
            mission_row=mission,
        )
        self.assertTrue(valid, errors)

    def test_maximum_compact_runner_envelope_fits_daily_budget_and_field_caps(self) -> None:
        source_url = "https://www.bls.gov/news.release/cpi.nr0.htm"
        horizon = {
            "bias": "SIDEWAY",
            "confidence": 100,
            "reasonTh": "x" * 18,
            "sourceRefs": ["official-1"],
        }
        pair_rows = [
            {
                "pair": pair,
                "short": dict(horizon),
                "medium": dict(horizon),
                "long": dict(horizon),
                "verified": True,
            }
            for pair in self.bridge.FX_BIAS_PAIRS
        ]
        events = [
            {
                "eventId": f"official-event-{index}",
                "titleTh": "t" * 60,
                "summaryTh": "s" * 100,
                "detailTh": "d" * 100,
                "outcomeTh": "o" * 80,
                "surprise": "p" * 40,
                "currencies": (
                    sorted(self.bridge.FX_MAJOR_CURRENCIES)
                    if index == 0
                    else ["USD"]
                ),
                "scheduledAt": f"2026-08-14T{index + 1:02d}:00:00Z",
                "timeKind": "timed",
                "impact": "low",
                "actual": 0,
                "actualStatus": "released",
                "forecast": "0.2%",
                "previous": "0.1%",
                "sourceRefs": ["official-1"],
                "pairImpacts": [
                    {
                        "pair": "EURUSD",
                        "impact": "SIDEWAY",
                        "confidence": 100,
                        "sourceRefs": ["official-1"],
                    },
                    {
                        "pair": "USDJPY",
                        "impact": "SIDEWAY",
                        "confidence": 100,
                        "sourceRefs": ["official-1"],
                    },
                ],
            }
            for index in range(self.bridge.FX_DAILY_NEWS_MAX_EVENTS_PER_REPORT)
        ]
        windows = [
            {
                "currencies": ["USD"],
                "startsAt": f"2026-08-14T{index + 1:02d}:00:00Z",
                "endsAt": f"2026-08-14T{index + 1:02d}:30:00Z",
                "reasonTh": "w" * 120,
                "sourceRefs": ["official-1"],
            }
            for index in range(self.bridge.FX_DAILY_NEWS_MAX_WINDOWS_PER_REPORT)
        ]
        fields = {
            "marketDate": "2026-08-14",
            "sourceStatus": "success",
            "quietDay": False,
            "events": events,
            "dangerWindows": windows,
            "pairBias": pair_rows,
            "sourceLinks": [
                {
                    "id": f"official-{index + 1}",
                    "title": "T" * 40,
                    "url": (
                        source_url
                        if index == 0
                        else f"https://source{index + 1}.example.gov/{'x' * 88}"
                    ),
                    "publishedAt": "2026-08-14T11:00:00Z",
                    "checkedAt": "2026-08-14T12:00:00Z",
                }
                for index in range(self.bridge.FX_DAILY_NEWS_MAX_SOURCES_PER_REPORT)
            ],
            "checkedAt": "2026-08-14T12:00:00Z",
            "updatedAt": "2026-08-14T12:00:00Z",
            "limitations": [],
        }
        contract_fields = [
            {
                "field": key,
                "value": (
                    value
                    if isinstance(value, str)
                    else json.dumps(value, ensure_ascii=False, separators=(",", ":"))
                ),
            }
            for key, value in fields.items()
        ]
        procedure = self.bridge.equipment_action_profile("left_signal_cube", "analyze_daily_market_news")
        result = {
            "status": "completed",
            "summary": "compact daily calendar",
            "findings": [
                "Verified six bounded calendar events against the listed public sources."
            ],
            "nextSteps": [
                "Refresh this market date after the next scheduled official release."
            ],
            "blockedCapability": "",
            "contractFields": contract_fields,
            "evidenceKinds": list(procedure["evidenceRequired"]),
            "evidence": [
                {
                    "label": "Official",
                    "url": source["url"],
                    "note": "Checked read-only against the published release.",
                }
                for source in fields["sourceLinks"]
            ],
        }
        envelope = json.dumps(result, ensure_ascii=False, separators=(",", ":"))
        values = {item["field"]: item["value"] for item in contract_fields}
        self.assertLessEqual(len(values["events"]), 12000)
        self.assertLessEqual(len(values["pairBias"]), 12000)
        self.assertLessEqual(len(envelope), 20000)
        parsed = self.runner.parse_work_result(envelope, 20000)
        self.assertEqual(parsed["structuredResultChars"], len(envelope))
        mission = {
            "createdAt": "2026-08-14T12:00:00Z",
            "budget": {"outputLimitChars": 20000},
            "workflowContext": {
                "propId": "left_signal_cube",
                "actionId": "analyze_daily_market_news",
                "inputs": {"marketDate": "2026-08-14"},
                "pluginProcedure": procedure,
            },
        }
        runner_transport = {
            "workStatus": parsed["workStatus"],
            "structuredSummary": parsed["summary"],
            "structuredResultChars": parsed["structuredResultChars"],
            "findings": parsed["findings"],
            "nextSteps": parsed["nextSteps"],
            "evidence": parsed["evidence"],
            "blockedCapability": parsed["blockedCapability"],
            "contractFields": parsed["contractFields"],
            "evidenceKinds": parsed["evidenceKinds"],
        }
        contract = self.bridge.validate_dashboard_workflow_output_contract(
            mission,
            runner_transport,
        )
        self.assertTrue(contract["valid"], contract)
        self.assertLessEqual(contract["resultEnvelopeChars"], 20000)
        self.assertEqual(contract["resultEnvelopeChars"], len(envelope))

    def test_retired_mission_form_is_not_used_by_direct_service(self) -> None:
        profile = self.bridge._trusted_workflow_plugin_profile(
            "left_signal_cube", "analyze_daily_market_news"
        )
        self.assertTrue(profile["retired"])
        self.assertEqual(profile["rejection"], "direct_service_required")
        form = self.bridge._workflow_effective_form(
            profile,
            {},
            action_id="analyze_daily_market_news",
        )
        # The parser remains available solely for validating historical reports;
        # the generic route rejects before this compatibility form can dispatch.
        self.assertEqual(form["minimumImpact"], "low")

    def test_legacy_news_actions_reject_before_any_mission_or_agent_work(self) -> None:
        with (
            mock.patch.object(self.bridge, "run_bridge_task") as run_bridge_task,
            mock.patch.object(self.bridge, "find_room_prop") as find_room_prop,
            mock.patch.object(self.bridge, "append_audit") as append_audit,
        ):
            for action_id in (
                "save_news_bias_schedule",
                "refresh_daily_market_news",
                "analyze_daily_market_news",
                "build_fx_pair_bias",
            ):
                with self.subTest(action_id=action_id):
                    with self.assertRaises(self.bridge.RequestError) as caught:
                        self.bridge.run_dashboard_workflow_action(
                            "left_signal_cube",
                            {"actionId": action_id, "form": {}},
                        )
                    self.assertEqual(caught.exception.status, 410)
                    self.assertEqual(str(caught.exception), "direct_service_required")
        run_bridge_task.assert_not_called()
        find_room_prop.assert_not_called()
        append_audit.assert_not_called()

    def test_direct_schedule_accepts_only_enabled_and_times_without_mission(self) -> None:
        saved = {
            "requestedEnabled": True,
            "times": ["00:00", "12:00"],
            "minimumImpact": "low",
            "timezone": "Asia/Bangkok",
        }
        with (
            mock.patch.object(self.bridge, "_save_dashboard_schedule_preference", return_value=saved) as save,
            mock.patch.object(self.bridge, "_fx_daily_news_direct_service_read_model", return_value={"status": "ready"}),
            mock.patch.object(self.bridge, "run_bridge_task") as run_bridge_task,
            mock.patch.object(self.bridge, "append_audit"),
        ):
            result = self.bridge.save_direct_daily_fx_news_schedule({
                "enabled": True,
                "times": ["12:00", "00:00"],
            })
        save.assert_called_once_with(
            "newsBiasSchedule",
            {"enabled": True, "times": ["00:00", "12:00"]},
        )
        run_bridge_task.assert_not_called()
        self.assertIsNone(result["mission"])
        self.assertFalse(result["missionCreated"])
        self.assertFalse(result["agentUsed"])
        self.assertFalse(result["aiUsed"])
        with self.assertRaises(self.bridge.RequestError):
            self.bridge.save_direct_daily_fx_news_schedule({
                "enabled": True,
                "times": ["00:00"],
                "minimumImpact": "high",
            })

    def test_direct_refresh_persists_snapshot_without_mission_or_agent_dispatch(self) -> None:
        empty_store = self.bridge.fx_news_direct.empty_store()
        collection = {"marketDate": "2026-08-14", "sourceCache": {}}
        snapshot = {
            "snapshotId": "fxnews-2026-08-14-unit",
            "marketDate": "2026-08-14",
            "updatedAt": "2026-08-14T05:00:00Z",
            "currentDataAvailable": True,
            "sourceStatus": "quiet_day",
            "dataStatus": "verified_empty",
            "events": [],
        }
        persisted = {
            **empty_store,
            "latestSnapshotId": snapshot["snapshotId"],
            "latestSuccessfulSnapshotId": snapshot["snapshotId"],
            "history": [snapshot],
        }
        with (
            mock.patch.object(self.bridge, "_load_fx_daily_news_direct_store", return_value=empty_store),
            mock.patch.object(self.bridge.fx_news_direct, "collect_official_sources", return_value=collection),
            mock.patch.object(self.bridge.fx_news_direct, "build_snapshot", return_value=snapshot),
            mock.patch.object(self.bridge.fx_news_direct, "append_snapshot", return_value=persisted),
            mock.patch.object(self.bridge, "_save_fx_daily_news_direct_store", return_value=persisted) as save_store,
            mock.patch.object(self.bridge, "_fx_daily_news_direct_service_read_model", return_value={"status": "ready"}),
            mock.patch.object(self.bridge, "_fx_news_read_model", return_value={"dataStatus": "verified_empty"}),
            mock.patch.object(self.bridge, "_fx_bias_read_model", return_value={"assessedPairCount": 28}),
            mock.patch.object(self.bridge, "run_bridge_task") as run_bridge_task,
            mock.patch.object(self.bridge, "append_audit"),
        ):
            result = self.bridge.refresh_deterministic_daily_fx_news(
                trigger_source="frontend",
                now_utc=datetime.fromisoformat("2026-08-14T05:00:00+00:00"),
            )
        save_store.assert_called_once_with(persisted)
        run_bridge_task.assert_not_called()
        self.assertEqual(result["snapshotId"], snapshot["snapshotId"])
        self.assertIsNone(result["mission"])
        self.assertFalse(result["missionCreated"])
        self.assertFalse(result["agentUsed"])
        self.assertFalse(result["aiUsed"])

    def test_partial_direct_coverage_assesses_only_pairs_with_both_currencies(self) -> None:
        report = self.report(
            "direct-partial-quiet",
            updated_at="2026-08-14T05:00:00Z",
            events=[],
            source_status="partial_success",
        )
        report["workflowContext"]["actionId"] = "refresh_daily_market_news"
        report["metrics"].update({
            "partialQuietDay": True,
            "coverageCurrencies": ["EUR", "USD"],
            "failedCurrencies": ["AUD", "CAD", "CHF", "GBP", "JPY", "NZD"],
            "pairBias": self.insufficient_pair_rows(),
        })
        model = self.bridge._fx_bias_read_model(
            [report],
            now_local=datetime.fromisoformat("2026-08-14T12:00:00+07:00"),
        )
        self.assertEqual(model["dataStatus"], "degraded")
        self.assertEqual(model["sourceStatus"], "partial_success")
        self.assertEqual(model["assessedPairCount"], 1)
        self.assertEqual(model["noDirectEventPairCount"], 1)
        self.assertEqual(model["unavailablePairCount"], 27)
        self.assertFalse(model["assessmentComplete"])
        eurusd = next(row for row in model["pairs"] if row["pair"] == "EURUSD")
        self.assertTrue(eurusd["assessmentComplete"])
        self.assertEqual(eurusd["assessmentStatus"], "no_direct_event")
        audusd = next(row for row in model["pairs"] if row["pair"] == "AUDUSD")
        self.assertFalse(audusd["assessmentComplete"])
        self.assertEqual(audusd["assessmentStatus"], "unavailable")

    def test_current_direct_snapshot_excludes_legacy_ai_news_and_bias(self) -> None:
        direct = self.report(
            "direct-quiet",
            updated_at="2026-08-14T01:00:00Z",
            events=[],
            quiet_day=True,
            source_status="quiet_day",
        )
        direct["workflowContext"]["actionId"] = "refresh_daily_market_news"
        direct["metrics"].update({
            "coverageCurrencies": sorted(self.bridge.FX_MAJOR_CURRENCIES),
            "failedCurrencies": [],
            "pairBias": self.insufficient_pair_rows(),
        })
        legacy = self.report(
            "legacy-ai-later",
            updated_at="2026-08-14T02:00:00Z",
            events=[self.event(actual="0.1%", actual_status="released")],
        )
        now = datetime.fromisoformat("2026-08-14T12:00:00+07:00")
        news = self.bridge._fx_news_read_model([direct, legacy], now_local=now)
        bias = self.bridge._fx_bias_read_model([direct, legacy], now_local=now)
        self.assertEqual(news["eventCount"], 0)
        self.assertTrue(news["verifiedEmpty"])
        self.assertEqual(news["sourceReportId"], "direct-quiet")
        self.assertEqual(bias["directionalPairCount"], 0)
        self.assertEqual(bias["assessedPairCount"], 28)
        self.assertEqual(bias["noDirectEventPairCount"], 28)
        self.assertEqual(bias["sourceReportId"], "direct-quiet")

    def test_latest_partial_direct_snapshot_evicts_prior_failed_currency_event_and_window(self) -> None:
        morning = self.report(
            "direct-morning-usd",
            updated_at="2026-08-14T01:00:00Z",
            events=[self.event(title="US CPI")],
            danger_windows=[{
                "currencies": ["USD"],
                "startsAt": "2026-08-14T12:15:00Z",
                "endsAt": "2026-08-14T12:45:00Z",
                "reasonTh": "US CPI",
                "sourceRefs": ["official-1"],
            }],
        )
        morning["workflowContext"]["actionId"] = "refresh_daily_market_news"
        morning["metrics"].update({
            "coverageCurrencies": sorted(self.bridge.FX_MAJOR_CURRENCIES),
            "failedCurrencies": [],
        })
        morning["metrics"]["events"][0]["actionableMacro"] = True

        aud_event = self.event(
            title="AUD CPI",
            event_id="aud-cpi",
            scheduled_at="2026-08-14T08:00:00Z",
        )
        aud_event["currencies"] = ["AUD"]
        aud_event["pairImpacts"] = {}
        aud_event["actionableMacro"] = True
        later = self.report(
            "direct-later-partial",
            updated_at="2026-08-14T05:00:00Z",
            events=[aud_event],
            source_status="partial_success",
        )
        later["workflowContext"]["actionId"] = "refresh_daily_market_news"
        later["metrics"].update({
            "coverageCurrencies": ["AUD", "EUR"],
            "failedCurrencies": ["USD"],
            "partialQuietDay": False,
            "pairBias": self.insufficient_pair_rows(),
        })

        now = datetime.fromisoformat("2026-08-14T12:00:00+07:00")
        news = self.bridge._fx_news_read_model([morning, later], now_local=now)
        bias = self.bridge._fx_bias_read_model([morning, later], now_local=now)
        self.assertEqual(news["sourceReportId"], "direct-later-partial")
        self.assertEqual(news["eventCount"], 1)
        self.assertEqual(news["events"][0]["currencies"], ["AUD"])
        self.assertEqual(news["dangerWindows"], [])
        self.assertNotIn("USD", news["coverageCurrencies"])
        self.assertEqual(bias["dataStatus"], "degraded")
        self.assertEqual(bias["assessedPairCount"], 1)
        self.assertEqual(bias["unavailablePairCount"], 27)

    def test_all_direct_sources_fail_with_history_is_degraded_last_good_not_blank_unknown(self) -> None:
        last_good = self.report(
            "direct-last-good",
            updated_at="2026-08-14T05:00:00Z",
            events=[self.event()],
        )
        last_good["workflowContext"]["actionId"] = "refresh_daily_market_news"
        last_good["metrics"].update({
            "coverageCurrencies": sorted(self.bridge.FX_MAJOR_CURRENCIES),
            "failedCurrencies": [],
        })
        failed = self.report(
            "direct-current-failure",
            updated_at="2026-08-15T05:00:00Z",
            events=[],
            source_status="source_failure",
        )
        failed["status"] = "failed"
        failed["workflowContext"]["actionId"] = "refresh_daily_market_news"
        failed["workflowContext"]["inputs"]["marketDate"] = "2026-08-15"
        failed["metrics"].update({
            "marketDate": "2026-08-15",
            "coverageCurrencies": [],
            "failedCurrencies": sorted(self.bridge.FX_MAJOR_CURRENCIES),
        })
        now = datetime.fromisoformat("2026-08-15T12:00:00+07:00")
        news = self.bridge._fx_news_read_model([last_good, failed], now_local=now)
        bias = self.bridge._fx_bias_read_model([last_good, failed], now_local=now)
        self.assertEqual(news["dataStatus"], "degraded_last_good")
        self.assertEqual(news["sourceStatus"], "source_failure")
        self.assertTrue(news["stale"])
        self.assertFalse(news["currentDataAvailable"])
        self.assertEqual(news["eventCount"], 0)
        self.assertEqual(news["lastGoodCalendarDate"], "2026-08-14")
        self.assertEqual(bias["dataStatus"], "degraded_last_good")
        self.assertEqual(bias["assessedPairCount"], 0)

    def test_direct_service_history_uses_canonical_event_contract(self) -> None:
        event = self.event(title="US CPI", scheduled_at="2026-08-14T12:30:00Z")
        event["actionableMacro"] = True
        snapshot = {
            "snapshotId": "fxnews-history-canonical",
            "marketDate": "2026-08-14",
            "createdAt": "2026-08-14T01:00:00Z",
            "updatedAt": "2026-08-14T01:00:00Z",
            "triggerSource": "schedule",
            "providerMode": self.bridge.fx_news_direct.PROVIDER_MODE,
            "sourceStatus": "success",
            "dataStatus": "verified",
            "quietDay": False,
            "partialQuietDay": False,
            "currentDataAvailable": True,
            "failClosed": False,
            "coverageCurrencies": sorted(self.bridge.FX_MAJOR_CURRENCIES),
            "failedCurrencies": [],
            "successfulSourceCount": 8,
            "failedSourceCount": 0,
            "sourceHealth": [],
            "sourceLinks": [{
                "id": "official-1",
                "title": "BLS release",
                "url": "https://www.bls.gov/news.release/cpi.nr0.htm",
                "checkedAt": "2026-08-14T01:00:00Z",
            }],
            "events": [event],
            "dangerWindows": [],
            "pairBias": self.insufficient_pair_rows(),
        }
        store = self.bridge.fx_news_direct.append_snapshot(
            self.bridge.fx_news_direct.empty_store(),
            snapshot,
            {},
        )
        service = self.bridge._fx_daily_news_direct_service_read_model(
            settings=self.bridge._default_dashboard_workflow_settings(),
            store=store,
            now_local=datetime.fromisoformat("2026-08-14T10:00:00+07:00"),
        )
        self.assertTrue(service["directRefreshAvailable"])
        self.assertEqual(service["refreshEndpoint"], "/api/props/left_signal_cube/news/refresh")
        self.assertEqual(service["scheduleEndpoint"], "/api/props/left_signal_cube/news/schedule")
        history = service["historyDays"][0]
        self.assertEqual(history["calendarDate"], "2026-08-14")
        canonical = history["events"][0]
        self.assertTrue(all(
            field in canonical
            for field in (
                "releaseState", "timingState", "analysisStatus", "actualStatus", "sourceLinks"
            )
        ))
        self.assertNotIn("publicationStatus", canonical)

    def test_macro_press_conference_precedes_broad_informational_conference_rule(self) -> None:
        macro = "ECB monetary policy press conference"
        research = "Central bank research conference on productivity"
        self.assertEqual(self.bridge.fx_news_direct.impact_for_title(macro), "medium")
        self.assertEqual(
            self.bridge.fx_news_direct.event_taxonomy(macro),
            ("economic_release", True),
        )
        self.assertEqual(self.bridge.fx_news_direct.impact_for_title(research), "low")
        self.assertEqual(
            self.bridge.fx_news_direct.event_taxonomy(research),
            ("informational_publication", False),
        )

    def test_scheduler_runs_direct_news_before_mission_gate(self) -> None:
        pending = {
            "settingsKey": "newsBiasSchedule",
            "propId": "left_signal_cube",
            "actionId": "refresh_daily_market_news",
            "slotKey": "2026-08-14@12:00",
            "schedule": {},
        }
        direct_result = {
            "ok": True,
            "kind": "news_direct_refresh",
            "snapshotId": "fxnews-2026-08-14-direct",
            "marketNews": {"dataStatus": "verified_empty"},
            "idempotentReplay": False,
        }
        with (
            mock.patch.object(self.bridge, "_dashboard_workflow_reconcile_schedule_states"),
            mock.patch.object(self.bridge, "_dashboard_workflow_capture_due_slots", return_value=[]),
            mock.patch.object(self.bridge, "_dashboard_workflow_pending_jobs", return_value=[pending]),
            mock.patch.object(self.bridge, "_dashboard_workflow_pending_is_current", return_value=True),
            mock.patch.object(self.bridge, "_dashboard_workflow_retry_ready", return_value=True),
            mock.patch.object(self.bridge, "_dashboard_workflow_reserve_daily_execution", return_value={"allowed": True}),
            mock.patch.object(self.bridge, "refresh_deterministic_daily_fx_news", return_value=direct_result) as refresh,
            mock.patch.object(self.bridge, "_dashboard_workflow_update_schedule_state") as update_state,
            mock.patch.object(self.bridge, "_active_dashboard_workflow_schedule_mission") as active_mission,
            mock.patch.object(self.bridge, "run_dashboard_workflow_action") as mission_dispatch,
            mock.patch.object(self.bridge, "append_audit"),
        ):
            result = self.bridge.dashboard_workflow_scheduler_tick(
                datetime.fromisoformat("2026-08-14T12:00:00+07:00"),
                refresh_quota=False,
            )
        refresh.assert_called_once()
        active_mission.assert_not_called()
        mission_dispatch.assert_not_called()
        self.assertTrue(update_state.called)
        self.assertTrue(result["dispatched"])
        self.assertEqual(result["snapshotId"], "fxnews-2026-08-14-direct")
        self.assertIsNone(result["missionId"])


if __name__ == "__main__":
    unittest.main()
