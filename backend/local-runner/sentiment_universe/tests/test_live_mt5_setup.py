import copy
import hashlib
import json
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch

from live_backend.mt5_setup import MT5Setup, MT5SetupError, discover_bindings
from live_backend import mt5_setup as setup_module
from live_backend import correlation, mt5_reader
from live_backend.server import MarketService


class MT5SetupTests(unittest.TestCase):
    def binding(self, root, running=1):
        install, data = root / "Broker MT5", root / "profile"
        install.mkdir(exist_ok=True)
        data.mkdir(exist_ok=True)
        (install / "terminal64.exe").touch()
        return {"terminalPath": str(install/"terminal64.exe"), "dataPath": str(data), "runningCount":running,
                "reasonCode": None if running==1 else "selected_terminal_ambiguous"}

    def test_discovery_is_opaque_selection_returns_only_private_config(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            binding=self.binding(root)
            setup=MT5Setup(root/"state",discoverer=lambda:[binding])
            public=setup.discover()
            encoded=json.dumps(public)
            self.assertNotIn(str(root),encoded)
            self.assertNotIn("terminalPath",encoded)
            row=public["candidates"][0]
            config=setup.resolve_selection(row["candidateId"],public["discoveryRevision"])
            self.assertTrue(config["enabled"])
            self.assertEqual(config["selectionId"],row["candidateId"])
            self.assertNotIn("terminalPid",config)
            self.assertNotIn("candidateId",config)  # independent of HQ platform locks
            self.assertNotIn(str(root),json.dumps(setup.status(config)))

    def test_terminal_restart_retains_identity_without_persisting_pid(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            binding=self.binding(root)
            setup=MT5Setup(root/"state",discoverer=lambda:[binding])
            first=setup.discover()
            # Discovery identity uses executable+data directory, not process id.
            binding["pid"]=99999
            second=setup.discover()
            self.assertEqual(first["candidates"][0]["candidateId"],second["candidates"][0]["candidateId"])
            with self.assertRaisesRegex(MT5SetupError,"discovery_expired"):
                setup.resolve_selection(first["candidates"][0]["candidateId"],first["discoveryRevision"])
            config=setup.resolve_selection(second["candidates"][0]["candidateId"],second["discoveryRevision"])
            self.assertNotIn("terminalPid",config)

    def test_selection_rejects_disappeared_or_changed_candidate(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            bindings=[self.binding(root)]
            setup=MT5Setup(root/"state",discoverer=lambda:copy.deepcopy(bindings))
            scan=setup.discover()
            bindings.clear()
            with self.assertRaises(MT5SetupError) as caught:
                setup.resolve_selection(scan["candidates"][0]["candidateId"],scan["discoveryRevision"])
            self.assertEqual(caught.exception.code,"mt5_candidate_changed")

    def test_duplicate_running_executable_is_not_selectable(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            setup=MT5Setup(root/"state",discoverer=lambda:[self.binding(root,running=2)])
            scan=setup.discover()
            self.assertFalse(scan["candidates"][0]["selectable"])
            with self.assertRaisesRegex(MT5SetupError,"candidate_unavailable"):
                setup.resolve_selection(scan["candidates"][0]["candidateId"],scan["discoveryRevision"])

    def test_discovery_reads_origin_only_and_matches_running_executable(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            binding=self.binding(root)
            data_root=root/"Terminal"
            profile=data_root/"opaque-profile"
            (profile/"MQL5").mkdir(parents=True)
            (profile/"origin.txt").write_text(str(Path(binding["terminalPath"]).parent),encoding="utf-16")
            rows=discover_bindings(processes=[{"terminalPath":binding["terminalPath"],"pid":123}],data_root=data_root)
            self.assertEqual(len(rows),1)
            # Windows temp roots may use an 8.3 alias for the same directory.
            self.assertTrue(Path(rows[0]["dataPath"]).samefile(profile))
            self.assertEqual(rows[0]["runningCount"],1)
            self.assertEqual(discover_bindings(processes=[],data_root=data_root),[])

    def test_selection_preserves_installer_python_runtime(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            runtime=root/"python.exe"
            runtime.touch()
            state=root/"state"
            state.mkdir()
            (state/"config.json").write_text(json.dumps({"mt5":{"pythonPath":str(runtime)}}))
            setup=MT5Setup(state,discoverer=lambda:[self.binding(root)])
            scan=setup.discover()
            config=setup.resolve_selection(scan["candidates"][0]["candidateId"],scan["discoveryRevision"])
            self.assertEqual(config["pythonPath"],str(runtime))


class SelectionFailureRaceTests(unittest.TestCase):
    def test_old_collector_exception_cannot_replace_new_selection(self):
        with tempfile.TemporaryDirectory() as directory:
            market=MarketService(directory)
            market.config={"mt5":{"selectionId":"old"}}
            market.update("correlations",{"status":"ready","source":"MT5","items":[{"source":"OLD","target":"TERMINAL"}]})
            entered,release=threading.Event(),threading.Event()
            def failed_old_collect(config,_):
                self.assertEqual(config["selectionId"],"old")
                entered.set()
                self.assertTrue(release.wait(3))
                raise RuntimeError("PRIVATE_OLD_TERMINAL_FAILURE")
            class Setup:
                def resolve_selection(self,candidate,revision):
                    return {"enabled":True,"selectionId":candidate}
            market.mt5_setup=Setup()
            with patch("live_backend.correlation.collect_for_service",side_effect=failed_old_collect):
                worker=threading.Thread(target=market.collect_correlation)
                worker.start()
                try:
                    self.assertTrue(entered.wait(2))
                    market.select_mt5("new","opaque-revision")
                    expected=market.read()["correlations"]
                finally:
                    release.set()
                    worker.join(3)
            self.assertFalse(worker.is_alive())
            self.assertEqual(market.read()["correlations"],expected)
            self.assertEqual(expected["status"],"loading")
            self.assertEqual(expected["items"],[])

    def test_generic_worker_exception_never_publishes_correlation_state(self):
        with tempfile.TemporaryDirectory() as directory:
            market=MarketService(directory)
            market.update("correlations",{"status":"loading","items":[],"errorCode":"verifying_selected_terminal"})
            expected=market.read()["correlations"]
            def failure():
                market.stop.set()
                raise RuntimeError("PRIVATE_NATIVE_ERROR")
            market.worker("correlations",failure,0)
            self.assertEqual(market.read()["correlations"],expected)


class LegacyMigrationTests(unittest.TestCase):
    NOW=1792843200  # Saturday 12:00 UTC.

    def prepare(self, root, *, current_hash=False):
        from tests.test_live_correlation import fixture, NOW
        state=root/"private"
        state.mkdir()
        terminal=root/"Broker MT5"/"terminal64.exe"
        terminal.parent.mkdir()
        terminal.touch()
        data=root/"terminal-data"
        data.mkdir()
        upstream=root/"hq-snapshot.json"
        config={"myfxbook":{"intervalSeconds":1200},"newsProvider":"forexfactory", "mt5":{
            "enabled":True,"terminalPath":str(terminal),"dataPath":str(data),"terminalPid":123,
            "candidateId":"proven-hq-candidate","inputCachePath":str(upstream),"pythonPath":"LOCAL_INSTALLER_RUNTIME"}}
        snapshot=fixture()
        snapshot["schemaVersion"]="sentiment-mt5-h1-snapshot-v1"
        snapshot["source"]["kind"]="mt5_guarded_closed_bars"
        snapshot["source"]["clock"]["verifiedAt"]=correlation.iso(NOW)
        template=snapshot["pairs"][0]
        snapshot["pairs"]=[]
        for symbol in correlation.INSTRUMENTS:
            row=copy.deepcopy(template)
            row.update(pair=symbol,brokerSymbol=symbol)
            if symbol in ("WTI","BRENT"):
                row.update(series={},errors=[{"code":"symbol_unavailable"}])
            snapshot["pairs"].append(row)
        hq=copy.deepcopy(snapshot)
        hq["source"]["terminalCandidateId"]="proven-hq-candidate"
        hq["pairs"]=hq["pairs"][:28]
        upstream.write_text(json.dumps(hq))
        names=("terminalPath","dataPath","selectionId","candidateId","symbolMap") if current_hash else ("terminalPath","dataPath","candidateId","symbolMap")
        metadata={"binding":hashlib.sha256(json.dumps({key:config["mt5"].get(key) for key in names},sort_keys=True).encode()).hexdigest(),"lastAttemptAt":correlation.iso(NOW)}
        for filename,value in (("config.json",config),("mt5-h1-snapshot.json",snapshot),("mt5-h1-collector-state.json",metadata)):
            (state/filename).write_text(json.dumps(value))
        binding={"terminalPath":str(terminal),"dataPath":str(data),"runningCount":1,"reasonCode":None}
        return state,config,snapshot,binding

    def test_migration_preserves_thirty_series_and_clock_then_is_idempotent(self):
        for current_hash in (False,True):
            with self.subTest(current_hash=current_hash),tempfile.TemporaryDirectory() as directory:
                state,config,original,binding=self.prepare(Path(directory),current_hash=current_hash)
                setup=MT5Setup(state,discoverer=lambda:[binding])
                commits=[]
                real_write=setup_module._replace_bytes
                def observed_write(path,raw):
                    commits.append(path.name)
                    real_write(path,raw)
                with patch.object(setup_module.time,"time",return_value=self.NOW),patch.object(setup_module,"_replace_bytes",side_effect=observed_write),patch.object(mt5_reader,"collect_snapshot",side_effect=AssertionError("No native API during migration")):
                    result=setup.migrate_legacy(config)
                self.assertEqual(result,{"migrated":True,"reason":"independent_binding_migrated"})
                self.assertEqual(commits[-1],"config.json")
                updated=json.loads((state/"config.json").read_text())
                self.assertEqual(updated["myfxbook"],config["myfxbook"])
                self.assertEqual(updated["mt5"]["pythonPath"],"LOCAL_INSTALLER_RUNTIME")
                for obsolete in ("candidateId","inputCachePath","terminalPid"):
                    self.assertNotIn(obsolete,updated["mt5"])
                saved=json.loads((state/"mt5-h1-snapshot.json").read_text())
                self.assertEqual(saved["pairs"],original["pairs"])
                self.assertEqual(saved["collectedAt"],original["collectedAt"])
                self.assertEqual(saved["source"]["clock"]["verifiedAt"],original["source"]["clock"]["verifiedAt"])
                self.assertEqual(saved["source"]["clock"]["bindingId"],mt5_reader.terminal_binding(updated["mt5"]))
                with patch.object(correlation.time,"time",return_value=self.NOW):
                    market=correlation.collect_for_service(updated["mt5"],state,terminal_collector=lambda _:self.fail("Weekend migration must not attach"))
                self.assertEqual(market["coverage"]["available"],30)
                self.assertEqual(sum(edge["status"]=="ready" for edge in market["items"]),435)
                with patch.object(setup,"discoverer",side_effect=AssertionError("Idempotent path must not discover")):
                    self.assertEqual(setup.migrate_legacy(updated),{"migrated":False,"reason":"already_independent"})
                self.assertNotIn(str(state),json.dumps(result))
                self.assertNotIn("terminalPath",json.dumps(setup.status(updated["mt5"],market)))

    def test_changed_terminal_candidate_binding_or_expired_clock_fail_without_writes(self):
        for change,reason in (("terminal","legacy_terminal_not_uniquely_proven"),
                              ("multiple_profiles","legacy_terminal_not_uniquely_proven"),
                              ("candidate","legacy_candidate_mismatch"),
                              ("metadata","legacy_cache_binding_mismatch"),
                              ("clock","legacy_clock_not_proven")):
            with self.subTest(change=change),tempfile.TemporaryDirectory() as directory:
                state,config,original,binding=self.prepare(Path(directory))
                bindings=[binding]
                if change=="terminal":
                    binding["dataPath"]+="-changed"
                if change=="multiple_profiles":
                    bindings.append({**binding,"dataPath":binding["dataPath"]+"-other"})
                if change=="candidate":
                    path=Path(config["mt5"]["inputCachePath"])
                    value=json.loads(path.read_text())
                    value["source"]["terminalCandidateId"]="different-candidate"
                    path.write_text(json.dumps(value))
                if change=="metadata":
                    (state/"mt5-h1-collector-state.json").write_text('{"binding":"different-terminal"}')
                if change=="clock":
                    original["source"]["clock"]["verifiedAt"]=correlation.iso(self.NOW-9*86400)
                    (state/"mt5-h1-snapshot.json").write_text(json.dumps(original))
                before={path.name:path.read_bytes() for path in state.iterdir()}
                with patch.object(setup_module.time,"time",return_value=self.NOW):
                    result=MT5Setup(state,discoverer=lambda:bindings).migrate_legacy(config)
                self.assertEqual(result,{"migrated":False,"reason":reason})
                self.assertEqual(before,{path.name:path.read_bytes() for path in state.iterdir()})

    def test_config_commit_failure_restores_original_private_files(self):
        with tempfile.TemporaryDirectory() as directory:
            state,config,_,binding=self.prepare(Path(directory))
            before={path.name:path.read_bytes() for path in state.iterdir()}
            real_write=setup_module._replace_bytes
            def fail_config(path,raw):
                if path.name=="config.json":
                    raise OSError("PRIVATE_PATH_MUST_NOT_ESCAPE")
                real_write(path,raw)
            with patch.object(setup_module.time,"time",return_value=self.NOW),patch.object(setup_module,"_replace_bytes",side_effect=fail_config):
                result=MT5Setup(state,discoverer=lambda:[binding]).migrate_legacy(config)
            self.assertEqual(result,{"migrated":False,"reason":"legacy_migration_write_failed"})
            self.assertEqual(before,{path.name:path.read_bytes() for path in state.iterdir()})

    def test_unknown_discovery_failure_is_sanitized_and_does_not_write(self):
        with tempfile.TemporaryDirectory() as directory:
            state,config,_,_=self.prepare(Path(directory))
            before={path.name:path.read_bytes() for path in state.iterdir()}
            def unavailable():
                raise RuntimeError("PRIVATE_PROCESS_DETAILS")
            result=MT5Setup(state,discoverer=unavailable).migrate_legacy(config)
            self.assertEqual(result,{"migrated":False,"reason":"legacy_migration_evidence_unavailable"})
            self.assertEqual(before,{path.name:path.read_bytes() for path in state.iterdir()})


if __name__=="__main__":
    unittest.main()
