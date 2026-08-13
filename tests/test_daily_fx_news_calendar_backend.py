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

    def test_default_and_legacy_migration_remain_opt_in_but_suggest_two_daily_runs(self) -> None:
        default = self.bridge._default_dashboard_workflow_settings()["newsBiasSchedule"]
        self.assertFalse(default["requestedEnabled"])
        self.assertEqual(default["times"], ["07:00", "20:00"])
        self.assertEqual(default["minimumImpact"], "low")
        legacy = self.bridge._dashboard_workflow_settings_shape({
            "newsBiasSchedule": {
                "requestedEnabled": False,
                "times": ["07:00", "13:00", "19:00"],
                "minimumImpact": "high",
                "savedAt": None,
            }
        })["newsBiasSchedule"]
        self.assertFalse(legacy["requestedEnabled"])
        self.assertEqual(legacy["times"], ["07:00", "20:00"])
        self.assertEqual(legacy["minimumImpact"], "low")
        saved = self.bridge._dashboard_workflow_settings_shape({
            "newsBiasSchedule": {
                "requestedEnabled": True,
                "times": ["09:15"],
                "minimumImpact": "high",
                "savedAt": "2026-08-14T00:00:00Z",
            }
        })["newsBiasSchedule"]
        self.assertTrue(saved["requestedEnabled"])
        self.assertEqual(saved["times"], ["09:15"])
        self.assertEqual(saved["minimumImpact"], "high")

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

    def test_daily_bias_requires_claim_specific_horizon_evidence(self) -> None:
        report = self.report(
            "horizon-evidence",
            updated_at="2026-08-14T01:00:00Z",
            events=[self.event()],
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
                "currencies": ["USD"],
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

    def test_manual_effective_form_gets_backend_bangkok_date(self) -> None:
        profile = self.bridge._trusted_workflow_plugin_profile(
            "left_signal_cube", "analyze_daily_market_news"
        )
        form = self.bridge._workflow_effective_form(
            profile,
            {},
            action_id="analyze_daily_market_news",
        )
        self.assertRegex(form["marketDate"], r"^\d{4}-\d{2}-\d{2}$")
        self.assertEqual(form["minimumImpact"], "low")


if __name__ == "__main__":
    unittest.main()
