"""Fixed-clock, provider-free readiness and diagnostic privacy contracts."""
import copy
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import sys
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend/local-runner"))
from hq_backend.operations.preflight import build_preflight
from hq_backend.operations.diagnostics import build_diagnostics


class OperationsHelperTests(unittest.TestCase):
    NOW = datetime(2026, 10, 29, 10, 59, 30, tzinfo=timezone.utc)

    def ready(self):
        return dict(now=self.NOW, enabled=True, terminal_locks_ready=True,
                    snapshot={"status": "ready", "identityReady": True,
                              "observedAt": (self.NOW-timedelta(seconds=3)).isoformat(), "maximumAgeSeconds": 60},
                    quota_gate={"allowed": True, "reason": "ready", "quota": {"checkedAt": self.NOW.isoformat(), "cacheAgeSeconds": 2}},
                    runner={"status": "ready", "cacheAgeSeconds": 2}, operator_mode="auto_guarded", active_round=False,
                    next_bar_at=(self.NOW+timedelta(seconds=30)).isoformat())

    def check(self, result, identifier):
        return next(c for c in result["checks"] if c["id"] == identifier)

    def test_ready_is_advisory_and_never_authorizes(self):
        args = self.ready(); before = copy.deepcopy(args)
        result = build_preflight(**args)
        self.assertEqual(result["status"], "ready")
        self.assertTrue(result["advisory"])
        self.assertFalse(result["canAuthorizeAnalysis"])
        self.assertEqual(args, before)
        self.assertEqual(len(result["checks"]), 7)

    def test_stale_cache_cannot_present_green_even_when_old_gate_allowed(self):
        args = self.ready(); args["quota_gate"]["quota"]["cacheAgeSeconds"] = 76
        result = build_preflight(**args)
        self.assertEqual(result["status"], "unknown")
        self.assertEqual(self.check(result,"quota")["reasonCode"], "quota_stale")

    def test_unavailable_is_distinct_from_exhausted_even_without_timestamp(self):
        args = self.ready(); args["quota_gate"] = {"allowed": False, "reason": "quota_unavailable"}
        missing = self.check(build_preflight(**args), "quota")
        self.assertEqual(missing["status"], "unknown")
        self.assertEqual(missing["reasonCode"], "quota_unavailable")
        args["quota_gate"] = {"allowed": False, "reason": "quota_limit_reached", "quota":{"checkedAt":self.NOW.isoformat()}}
        exhausted = self.check(build_preflight(**args),"quota")
        self.assertEqual(exhausted["status"], "blocked")
        self.assertNotEqual(missing["reasonCode"], exhausted["reasonCode"])

    def test_future_or_naive_snapshot_is_not_ready(self):
        for stamp in [(self.NOW+timedelta(minutes=2)).isoformat(), self.NOW.replace(tzinfo=None).isoformat()]:
            args=self.ready(); args["snapshot"]["observedAt"] = stamp
            self.assertEqual(self.check(build_preflight(**args),"snapshot")["status"],"unknown")

    def test_stale_snapshot_and_unverified_identity_are_not_ready(self):
        args=self.ready(); args["snapshot"]["observedAt"]=(self.NOW-timedelta(seconds=61)).isoformat()
        self.assertEqual(self.check(build_preflight(**args),"snapshot")["reasonCode"],"snapshot_stale")
        args=self.ready(); args["snapshot"].pop("identityReady")
        self.assertNotEqual(self.check(build_preflight(**args),"snapshot")["status"],"ready")

    def test_pause_and_active_round_do_not_generate_work(self):
        args=self.ready(); args["enabled"]=False
        self.assertEqual(build_preflight(**args)["status"],"paused")
        args=self.ready(); args["active_round"]=True
        self.assertEqual(self.check(build_preflight(**args),"round")["status"],"waiting")
        args["operator_mode"]="manual"
        self.assertEqual(self.check(build_preflight(**args),"mode")["status"],"blocked")

    def test_runner_ready_cache_expires_and_missing_time_is_unknown(self):
        for runner, reason in (({"status": "ready"}, "runner_time_unverified"),
                               ({"status": "ready", "cacheAgeSeconds": 31}, "runner_status_stale"),
                               ({"status": "ready", "observedAt": (self.NOW+timedelta(seconds=60)).isoformat()}, "runner_time_unverified")):
            args = self.ready(); args["runner"] = runner
            check = self.check(build_preflight(**args), "runner")
            self.assertEqual(check["status"], "unknown")
            self.assertEqual(check["reasonCode"], reason)

    def test_next_bar_is_not_fabricated_from_naive_or_past_clock(self):
        args=self.ready()
        for value in (None, "2026-10-29T18:00:00", (self.NOW-timedelta(seconds=1)).isoformat()):
            args["next_bar_at"]=value
            self.assertIsNone(build_preflight(**args)["nextBarAt"])

    def test_export_drops_unknown_fields_and_poisoned_known_strings(self):
        poison="PRIVATE_CANARY sk-live-SECRET user@example.com C:/Users/Student account=123456"
        event={"id":poison,"type":poison,"status":poison,"reasonCode":poison,
               "messageTh":poison,"symbol":poison,"evidence":{"path":poison,"source":poison},
               "startedAt":poison,"token":poison}
        ops={"events":[event],"incidents":{"active":[event],"recovered":[]},
             "readiness":{"status":poison,"checks":[{"id":poison,"reasonCode":poison,"messageTh":poison}]}}
        raw={"accountNumber":123456,"token":poison,"state":{"symbol":poison,"reason":poison}}
        result=build_diagnostics(now=self.NOW, version=poison,health={"status":poison,"token":poison},operations=ops,council=raw,
                                 rounds=[{"id":poison,"prompt":poison,"roles":{"technical":{"decision":poison,"output":poison}}}])
        text=json.dumps(result,ensure_ascii=False)
        for word in ("PRIVATE_CANARY","SECRET","user@example.com","C:/Users/Student","123456","accountNumber","prompt"):
            self.assertNotIn(word,text)
        self.assertTrue(result["redacted"])
        self.assertEqual(result["operations"]["events"][0]["reasonCode"],"unknown")

    def test_export_keeps_useful_known_facts_without_source_mutation(self):
        ops={"available":True,"events":[{"id":"event-1","type":"gap","status":"closed","certainty":"unknown",
              "reasonCode":"heartbeat_gap","startedAt":self.NOW.isoformat(),"symbol":"XAUUSD","timeframe":"H1"}],
             "readiness":build_preflight(**self.ready())}
        before=copy.deepcopy(ops)
        result=build_diagnostics(now=self.NOW, version="0.9.27",health={"ok":True,"status":"ready"},operations=ops)
        self.assertEqual(result["operations"]["events"][0]["reasonCode"],"heartbeat_gap")
        self.assertEqual(result["operations"]["events"][0]["symbol"],"XAUUSD")
        self.assertEqual(ops,before)

    def test_export_is_bounded_and_json_numbers_are_finite(self):
        e={"occurrences":float("inf"),"evidence":{"completeRoleCount":True}}
        result=build_diagnostics(now=self.NOW,version="0.9.27",health={},operations={"events":[e]*201},rounds=[{}]*51)
        self.assertEqual(len(result["operations"]["events"]),200)
        self.assertTrue(result["operations"]["hasMore"])
        self.assertEqual(len(result["rounds"]),50)
        json.dumps(result,allow_nan=False)

    def test_helpers_do_not_open_files_or_network_connections(self):
        with mock.patch("builtins.open",side_effect=AssertionError("disk IO")), mock.patch("socket.socket",side_effect=AssertionError("network IO")):
            p=build_preflight(**self.ready())
            build_diagnostics(now=self.NOW,version="0.9.27",health={},operations={"readiness":p})

    def test_naive_observation_clock_is_rejected(self):
        args=self.ready();args["now"]=self.NOW.replace(tzinfo=None)
        with self.assertRaises(ValueError):build_preflight(**args)
        with self.assertRaises(ValueError):build_diagnostics(now=args["now"],version="0.9.27",health={},operations={})


if __name__ == "__main__":
    unittest.main()
