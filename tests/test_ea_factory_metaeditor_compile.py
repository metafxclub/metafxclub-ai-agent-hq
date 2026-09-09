from __future__ import annotations

import hashlib
import importlib.util
import os
import shutil
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock


PROJECT_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    PROJECT_ROOT
    / "backend"
    / "local-runner"
    / "ea_factory_metaeditor_compile.py"
)
BRIDGE_PATH = PROJECT_ROOT / "backend" / "local-runner" / "bridge_server.py"


def load_module():
    spec = importlib.util.spec_from_file_location(
        "ea_factory_metaeditor_compile_test_module",
        MODULE_PATH,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to import {MODULE_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_bridge():
    spec = importlib.util.spec_from_file_location(
        "ea_factory_metaeditor_compile_integration_bridge",
        BRIDGE_PATH,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to import {BRIDGE_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class EaFactoryMetaEditorCompileTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.adapter = load_module()

    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        # Canonicalize the temporary root before deriving any expected paths.
        # On Windows, tempfile may expose the same directory through a short
        # (8.3) or long spelling depending on the Python/runtime combination,
        # while the production adapter deliberately resolves every managed
        # path before use.  Keeping the fixture canonical makes failure-
        # injection path comparisons address the same file on every supported
        # Python version instead of silently missing the injected branch.
        self.root = Path(self.temp.name).resolve(strict=True)
        self.install = self.root / "terminal"
        self.install.mkdir()
        self.versions = self.root / "workspace" / "EA_Versions"
        self.reports = self.root / "workspace" / "Reports"
        self.versions.mkdir(parents=True)
        self.reports.mkdir(parents=True)
        self.source = self.versions / "Safe_v01.mq4"
        self.source.write_text(
            "#property strict\nint OnInit(){return(INIT_SUCCEEDED);}\nvoid OnTick(){}\n",
            encoding="utf-8",
        )
        self.compiler = self.install / "metaeditor.exe"
        self.terminal = self.install / "terminal.exe"
        self.compiler.write_bytes(b"safe compiler fixture")
        self.terminal.write_bytes(b"safe terminal fixture")
        self.candidate_id = "mtc-" + ("a" * 26)
        local = str(self.install.resolve())
        identity = hashlib.sha256(
            f"mt4\0{__import__('os').path.normcase(local)}".encode("utf-8")
        ).hexdigest()
        self.record = {
            "candidateId": self.candidate_id,
            "identityKey": identity,
            "platform": "mt4",
            "localPath": local,
            "installPath": local,
            "dataPath": None,
            "available": True,
        }
        self.token = {
            "candidateId": self.candidate_id,
            "selectionRevision": 7,
        }
        self.target = self.adapter.resolve_compile_target(
            self.record,
            self.token,
            "mt4",
        )
        self.source_digest = hashlib.sha256(self.source.read_bytes()).hexdigest()
        self.raw_log = self.reports / "metaeditor-compile-01.raw.log"

    def tearDown(self) -> None:
        self.temp.cleanup()

    def runner(
        self,
        *,
        errors: int = 0,
        warnings: int = 0,
        exit_code: int = 0,
        write_output: bool = True,
        source_label: str | None = None,
        mutate_source: bool = False,
    ):
        def run(command: list[str], cwd: Path, timeout: int) -> dict:
            self.assertEqual(command[0], str(self.compiler.resolve()))
            self.assertEqual(cwd, self.install.resolve())
            self.assertEqual(timeout, 30)
            self.assertEqual(len(command), 3)
            self.assertTrue(command[1].startswith("/compile:"))
            self.assertTrue(command[2].startswith("/log:"))
            source = Path(command[1].split(":", 1)[1])
            log = Path(command[2].split(":", 1)[1])
            if mutate_source:
                source.write_text("// changed", encoding="utf-8")
            if write_output:
                source.with_suffix(".ex4").write_bytes(b"compiled binary")
            label = source_label if source_label is not None else source.name
            log.write_text(
                f"{label} : information: compiling '{label}'\n"
                f"Result: {errors} errors, {warnings} warnings, 8 msec elapsed\n",
                encoding="utf-16",
            )
            return {
                "exitCode": exit_code,
                "durationMs": 8,
                "processStarted": True,
            }

        return run

    def compile(self, **kwargs):
        selection_is_current = kwargs.pop("selection_is_current", lambda: True)
        process_runner = kwargs.pop("process_runner", None)
        if process_runner is None:
            process_runner = self.runner(**kwargs)
        return self.adapter.compile_source(
            self.target,
            self.source,
            self.source_digest,
            self.versions,
            self.raw_log,
            self.reports,
            selection_is_current=selection_is_current,
            timeout_seconds=30,
            process_runner=process_runner,
        )

    def test_exact_zero_error_zero_warning_compile_is_accepted(self) -> None:
        result = self.compile()
        self.assertEqual(result["sourceDigest"], self.source_digest)
        self.assertEqual(result["compiledFileName"], "Safe_v01.ex4")
        self.assertEqual(result["resultLine"], "Result: 0 errors, 0 warnings")
        self.assertEqual(result["processExitCode"], 0)
        self.assertGreater(result["compiledByteSize"], 0)
        self.assertFalse(self.raw_log.exists())

        self.source.with_suffix(".ex4").unlink()
        exit_one = self.compile(process_runner=self.runner(exit_code=1))
        self.assertEqual(exit_one["processExitCode"], 1)
        self.assertEqual(exit_one["resultLine"], "Result: 0 errors, 0 warnings")

    def test_platform_and_identity_mismatch_fail_before_process(self) -> None:
        wrong_platform = dict(self.record, platform="mt5")
        with self.assertRaises(self.adapter.MetaEditorCompileError) as raised:
            self.adapter.resolve_compile_target(wrong_platform, self.token, "mt4")
        self.assertEqual(raised.exception.code, "terminal_platform_mismatch")

        wrong_identity = dict(self.record, identityKey="0" * 64)
        with self.assertRaises(self.adapter.MetaEditorCompileError) as raised:
            self.adapter.resolve_compile_target(wrong_identity, self.token, "mt4")
        self.assertEqual(raised.exception.code, "terminal_identity_invalid")

    def test_reparse_target_is_rejected(self) -> None:
        original = self.adapter._path_has_reparse_component

        def reparse(path: Path) -> bool:
            return Path(path) == self.compiler or original(Path(path))

        with mock.patch.object(
            self.adapter,
            "_path_has_reparse_component",
            side_effect=reparse,
        ):
            with self.assertRaises(self.adapter.MetaEditorCompileError) as raised:
                self.adapter.resolve_compile_target(self.record, self.token, "mt4")
        self.assertEqual(raised.exception.code, "metaeditor_not_available")

    def test_selection_change_after_process_discards_output(self) -> None:
        checks = iter([True, False])
        with self.assertRaises(self.adapter.MetaEditorCompileError) as raised:
            self.compile(selection_is_current=lambda: next(checks))
        self.assertEqual(raised.exception.code, "terminal_selection_changed")
        self.assertFalse(self.source.with_suffix(".ex4").exists())

    def test_timeout_is_propagated_and_attempt_output_is_removed(self) -> None:
        self.raw_log.write_text(
            "Safe_v01.mq4 compiling\nResult: 0 errors, 0 warnings",
            encoding="utf-16",
        )

        def timeout(command: list[str], _cwd: Path, _timeout: int):
            Path(command[1].split(":", 1)[1]).with_suffix(".ex4").write_bytes(
                b"partial current attempt"
            )
            raise self.adapter.MetaEditorCompileError(
                "metaeditor_compile_timeout",
                process_started=True,
                exit_code="timeout",
            )

        with self.assertRaises(self.adapter.MetaEditorCompileError) as raised:
            self.compile(process_runner=timeout)
        self.assertEqual(raised.exception.code, "metaeditor_compile_timeout")
        self.assertFalse(self.source.with_suffix(".ex4").exists())
        self.assertFalse(self.raw_log.exists())

    def test_preexisting_binary_is_preserved_and_never_recompiled(self) -> None:
        binary = self.source.with_suffix(".ex4")
        binary.write_bytes(b"immutable prior output")
        started = False

        def must_not_run(_command: list[str], _cwd: Path, _timeout: int) -> dict:
            nonlocal started
            started = True
            return {"exitCode": 0, "durationMs": 1, "processStarted": True}

        with self.assertRaises(self.adapter.MetaEditorCompileError) as raised:
            self.compile(process_runner=must_not_run)
        self.assertEqual(
            raised.exception.code,
            "compile_output_preexisting_untrusted",
        )
        self.assertFalse(started)
        self.assertEqual(binary.read_bytes(), b"immutable prior output")

    @unittest.skipUnless(os.name == "nt", "Windows process-tree contract")
    def test_default_timeout_kills_the_full_process_tree(self) -> None:
        child_pid_file = self.root / "child.pid"
        child_code = "import time; time.sleep(60)"
        parent_code = (
            "import pathlib,subprocess,sys,time;"
            f"p=subprocess.Popen([sys.executable,'-c',{child_code!r}]);"
            f"pathlib.Path({str(child_pid_file)!r}).write_text(str(p.pid));"
            "time.sleep(60)"
        )
        started = time.perf_counter()
        with self.assertRaises(self.adapter.MetaEditorCompileError) as raised:
            self.adapter._default_process_runner(
                [sys.executable, "-c", parent_code],
                self.root,
                1,
            )
        self.assertEqual(raised.exception.code, "metaeditor_compile_timeout")
        self.assertLess(time.perf_counter() - started, 15)
        self.assertTrue(child_pid_file.is_file())
        child_pid = int(child_pid_file.read_text(encoding="utf-8"))

        import ctypes

        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel32.OpenProcess.argtypes = [ctypes.c_uint32, ctypes.c_int, ctypes.c_uint32]
        kernel32.OpenProcess.restype = ctypes.c_void_p
        kernel32.GetExitCodeProcess.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_uint32)]
        kernel32.GetExitCodeProcess.restype = ctypes.c_int
        handle = kernel32.OpenProcess(0x00001000, False, child_pid)
        if not handle:
            alive = False
        else:
            exit_code = ctypes.c_uint32()
            alive = bool(kernel32.GetExitCodeProcess(handle, ctypes.byref(exit_code))) and exit_code.value == 259
            self.adapter._close_windows_handle(int(handle))
        self.assertFalse(alive, "compiler descendant survived timeout")

    def test_preexisting_spoofed_log_is_not_accepted(self) -> None:
        self.raw_log.write_text(
            "Safe_v01.mq4 compiling\nResult: 0 errors, 0 warnings",
            encoding="utf-16",
        )

        def no_log(command: list[str], _cwd: Path, _timeout: int) -> dict:
            Path(command[1].split(":", 1)[1]).with_suffix(".ex4").write_bytes(b"binary")
            return {"exitCode": 0, "durationMs": 1, "processStarted": True}

        with self.assertRaises(self.adapter.MetaEditorCompileError) as raised:
            self.compile(process_runner=no_log)
        self.assertEqual(raised.exception.code, "compile_log_unsafe")
        self.assertFalse(self.source.with_suffix(".ex4").exists())

    def test_reparse_compile_log_is_rejected_before_process(self) -> None:
        self.raw_log.write_text("untrusted", encoding="utf-8")
        original = self.adapter._path_has_reparse_component

        def reparse(path: Path) -> bool:
            return Path(path) == self.raw_log or original(Path(path))

        with mock.patch.object(
            self.adapter,
            "_path_has_reparse_component",
            side_effect=reparse,
        ):
            with self.assertRaises(self.adapter.MetaEditorCompileError) as raised:
                self.compile()
        self.assertEqual(raised.exception.code, "compile_output_path_unsafe")
        self.assertEqual(self.raw_log.read_text(encoding="utf-8"), "untrusted")

    def test_stale_or_changed_source_is_rejected(self) -> None:
        with self.assertRaises(self.adapter.MetaEditorCompileError) as raised:
            self.adapter.compile_source(
                self.target,
                self.source,
                "0" * 64,
                self.versions,
                self.raw_log,
                self.reports,
                selection_is_current=lambda: True,
                process_runner=self.runner(),
            )
        self.assertEqual(raised.exception.code, "source_digest_mismatch")

        with self.assertRaises(self.adapter.MetaEditorCompileError) as raised:
            self.compile(mutate_source=True)
        self.assertEqual(raised.exception.code, "source_changed_during_compile")
        self.assertFalse(self.source.with_suffix(".ex4").exists())

    def test_same_digest_source_or_compiler_replacement_is_rejected(self) -> None:
        original_source = self.source.read_bytes()

        def replace_source(command: list[str], _cwd: Path, _timeout: int) -> dict:
            source = Path(command[1].split(":", 1)[1])
            log = Path(command[2].split(":", 1)[1])
            source.unlink()
            source.write_bytes(original_source)
            source.with_suffix(".ex4").write_bytes(b"compiled binary")
            log.write_text(
                f"{source.name} : information: compiling '{source.name}'\n"
                "Result: 0 errors, 0 warnings, 8 msec elapsed\n",
                encoding="utf-16",
            )
            return {"exitCode": 0, "durationMs": 8, "processStarted": True}

        with self.assertRaises(self.adapter.MetaEditorCompileError) as raised:
            self.compile(process_runner=replace_source)
        self.assertEqual(raised.exception.code, "source_changed_during_compile")

        self.source_digest = hashlib.sha256(self.source.read_bytes()).hexdigest()
        original_compiler = self.compiler.read_bytes()

        def replace_compiler(command: list[str], _cwd: Path, _timeout: int) -> dict:
            source = Path(command[1].split(":", 1)[1])
            log = Path(command[2].split(":", 1)[1])
            self.compiler.unlink()
            self.compiler.write_bytes(original_compiler)
            source.with_suffix(".ex4").write_bytes(b"compiled binary")
            log.write_text(
                f"{source.name} : information: compiling '{source.name}'\n"
                "Result: 0 errors, 0 warnings, 8 msec elapsed\n",
                encoding="utf-16",
            )
            return {"exitCode": 0, "durationMs": 8, "processStarted": True}

        with self.assertRaises(self.adapter.MetaEditorCompileError) as raised:
            self.compile(process_runner=replace_compiler)
        self.assertEqual(raised.exception.code, "compiler_changed_during_compile")

    def test_compile_error_warning_and_spoofed_source_name_fail_closed(self) -> None:
        for runner, expected in (
            (self.runner(errors=1), "metaeditor_compile_failed"),
            (self.runner(warnings=1), "metaeditor_compile_failed"),
            (self.runner(source_label="Different.mq4"), "metaeditor_log_source_mismatch"),
            (self.runner(write_output=False), "compile_path_unsafe"),
            (self.runner(exit_code=2), "metaeditor_compile_failed"),
        ):
            with self.subTest(expected=expected):
                with self.assertRaises(self.adapter.MetaEditorCompileError) as raised:
                    self.compile(process_runner=runner)
                self.assertEqual(raised.exception.code, expected)

    def test_spoofed_process_result_cannot_pass(self) -> None:
        for process_started, exit_code in ((False, 0), (True, True)):
            with self.subTest(
                process_started=process_started,
                exit_code=exit_code,
            ):
                valid_runner = self.runner()

                def spoofed(command: list[str], cwd: Path, timeout: int) -> dict:
                    result = valid_runner(command, cwd, timeout)
                    result["processStarted"] = process_started
                    result["exitCode"] = exit_code
                    return result

                with self.assertRaises(self.adapter.MetaEditorCompileError) as raised:
                    self.compile(process_runner=spoofed)
                self.assertEqual(
                    raised.exception.code,
                    "metaeditor_process_result_invalid",
                )

    def test_unsafe_compile_directives_are_rejected(self) -> None:
        for directive in (
            '#include "..\\secret.mqh"',
            '#include <../secret.mqh>',
            '#include <CustomHelper.mqh>',
            '#import "unsafe.dll"',
            '#resource "https://example.invalid/x"',
            '#property icon "..\\icon.ico"',
        ):
            with self.subTest(directive=directive):
                self.source.write_text(directive + "\nvoid OnTick(){}", encoding="utf-8")
                digest = hashlib.sha256(self.source.read_bytes()).hexdigest()
                with self.assertRaises(self.adapter.MetaEditorCompileError) as raised:
                    self.adapter.compile_source(
                        self.target,
                        self.source,
                        digest,
                        self.versions,
                        self.raw_log,
                        self.reports,
                        selection_is_current=lambda: True,
                        process_runner=self.runner(),
                    )
                self.assertEqual(raised.exception.code, "source_compile_directive_unsafe")

    def test_include_policy_is_platform_exact_and_fail_closed(self) -> None:
        standard = b"#include <Trade/Trade.mqh>\nvoid OnTick(){}"
        self.assertFalse(
            self.adapter._source_directives_are_safe(standard, "mt4")
        )
        self.assertFalse(
            self.adapter._source_directives_are_safe(
                b"#include <CustomHelper.mqh>\nvoid OnTick(){}",
                "mt5",
            )
        )
        self.assertFalse(
            self.adapter._source_directives_are_safe(
                b"/* prefix */ #include <CustomHelper.mqh>\nvoid OnTick(){}",
                "mt5",
            )
        )
        self.assertTrue(
            self.adapter._source_directives_are_safe(standard, "mt5")
        )
        self.assertTrue(
            self.adapter._source_directives_are_safe(
                b"#include <trade\\TRADE.MQH>\nvoid OnTick(){}",
                "mt5",
            )
        )


@unittest.skipUnless(
    os.name == "nt" and os.environ.get("METAFX_REAL_METAEDITOR_TEST") == "1",
    "opt-in compile-only smoke test for locally installed MetaEditor",
)
class EaFactoryRealMetaEditorSmokeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.adapter = load_module()

    def matching_data_path(self, install: Path, platform: str) -> Path | None:
        appdata = os.environ.get("APPDATA")
        root = Path(appdata) / "MetaQuotes" / "Terminal" if appdata else None
        if root is None or not root.is_dir():
            return None
        for candidate in root.iterdir():
            if not candidate.is_dir():
                continue
            origin = self.adapter._read_origin_install(candidate, platform)
            try:
                if (
                    origin is not None
                    and origin.resolve(strict=True) == install.resolve(strict=True)
                    and (candidate / ("MQL4" if platform == "mt4" else "MQL5")).is_dir()
                ):
                    return candidate
            except (OSError, RuntimeError, ValueError):
                continue
        return None

    def test_real_mt4_and_mt5_ea_and_indicator_fixtures_compile_only(self) -> None:
        indicator_fixtures = PROJECT_ROOT / "tests" / "fixtures" / "indicator-smoke"
        ea_fixtures = PROJECT_ROOT / "tests" / "fixtures" / "ea-smoke"
        matrix = (
            (
                "mt4",
                Path(r"C:\Program Files (x86)\MetaTrader 4 IC Markets Global"),
                indicator_fixtures / "MetafxSmokeIndicator.mq4",
            ),
            (
                "mt5",
                Path(r"C:\Program Files\RoboForex MT5 Terminal"),
                indicator_fixtures / "MetafxSmokeIndicator.mq5",
            ),
            (
                "mt4",
                Path(r"C:\Program Files (x86)\MetaTrader 4 IC Markets Global"),
                ea_fixtures / "MetafxSmokeEA.mq4",
            ),
            (
                "mt5",
                Path(r"C:\Program Files\RoboForex MT5 Terminal"),
                ea_fixtures / "MetafxSmokeEA.mq5",
            ),
        )
        for platform, install, fixture in matrix:
            with self.subTest(platform=platform), tempfile.TemporaryDirectory() as raw:
                root = Path(raw)
                versions = root / "EA_Versions"
                reports = root / "Reports"
                versions.mkdir()
                reports.mkdir()
                source = versions / fixture.name
                shutil.copy2(fixture, source)
                data_path = self.matching_data_path(install, platform)
                if platform == "mt5" and b"#include" in source.read_bytes():
                    self.assertIsNotNone(
                        data_path,
                        "MT5 standard include requires the selected terminal data path",
                    )
                local = str(
                    (data_path or install).resolve(strict=True)
                )
                candidate_id = "mtc-" + (("m" if platform == "mt4" else "n") * 26)
                record = {
                    "candidateId": candidate_id,
                    "identityKey": hashlib.sha256(
                        f"{platform}\0{os.path.normcase(local)}".encode("utf-8")
                    ).hexdigest(),
                    "platform": platform,
                    "localPath": local,
                    "installPath": str(install.resolve(strict=True)),
                    "dataPath": str(data_path.resolve(strict=True)) if data_path else None,
                    "available": True,
                }
                token = {"candidateId": candidate_id, "selectionRevision": 1}
                target = self.adapter.resolve_compile_target(record, token, platform)
                result = self.adapter.compile_source(
                    target,
                    source,
                    hashlib.sha256(source.read_bytes()).hexdigest(),
                    versions,
                    reports / f"{platform}.raw.log",
                    reports,
                    selection_is_current=lambda: True,
                )
                self.assertEqual(result["errorCount"], 0)
                self.assertEqual(result["warningCount"], 0)
                self.assertIn(result["processExitCode"], {0, 1})
                self.assertGreater(result["compiledByteSize"], 0)
                self.assertTrue((versions / result["compiledFileName"]).is_file())


class EaFactoryMetaEditorCompileIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.bridge = load_bridge()

    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        # Match the canonical managed paths returned by the production bridge;
        # see the adapter fixture above for the Windows short/long-path reason.
        self.root = Path(self.temp.name).resolve(strict=True)
        self.build_id = "ea-build-compile-integration"
        self.build_dir = self.root / "workspace" / "ea-factory" / self.build_id
        for folder in self.bridge.EA_FACTORY_BUILD_FOLDER_NAMES:
            (self.build_dir / folder).mkdir(parents=True, exist_ok=True)
        self.source = self.build_dir / "EA_Versions" / "CompileFixture_v01.mq4"
        self.source.write_text(
            "#property strict\nint OnInit(){return(INIT_SUCCEEDED);}\nvoid OnTick(){}\n",
            encoding="utf-8",
        )
        self.source_digest = hashlib.sha256(self.source.read_bytes()).hexdigest()
        self.target = {
            "candidateId": "mtc-" + ("z" * 26),
            "selectionRevision": 4,
            "platform": "mt4",
            "compilerPath": self.root / "metaeditor.exe",
            "installPath": self.root,
            "bindingDigest": "b" * 64,
        }
        self.target["compilerPath"].write_bytes(b"compiler")
        self.build = {
            "id": self.build_id,
            "sourceDisplayName": "Compile Integration",
            "platform": "mt4",
            "artifactKind": "expert_advisor",
            "versions": [{
                "version": 1,
                "fileName": self.source.name,
                "sourceDigest": self.source_digest,
                "sourceFile": "Source/CompileFixture.mq4",
                "versionFile": f"EA_Versions/{self.source.name}",
                "sourceReportId": "report-generation",
                "immutable": True,
                "createdAt": "2026-09-09T00:00:00Z",
            }],
            "artifactManifest": [],
            "artifactManifestDigest": None,
        }
        self.stage = {
            "id": "compile_validate",
            "status": "pending",
            "missionIdempotencyKey": "ea-factory-stage-compile-integration",
            "artifacts": [],
        }

    def tearDown(self) -> None:
        self.temp.cleanup()

    def fake_compile(
        self,
        _target,
        source_path,
        expected_digest,
        _versions_root,
        _raw_log_path,
        _reports_root,
        *,
        selection_is_current,
    ) -> dict:
        self.assertTrue(selection_is_current())
        source_path = Path(source_path)
        self.assertEqual(
            expected_digest,
            hashlib.sha256(source_path.read_bytes()).hexdigest(),
        )
        output = source_path.with_suffix(".ex4")
        output.write_bytes(b"compiled integration artifact")
        return {
            "sourceFileName": source_path.name,
            "sourceDigest": expected_digest,
            "sourceByteSize": source_path.stat().st_size,
            "compiledFileName": output.name,
            "compiledDigest": hashlib.sha256(output.read_bytes()).hexdigest(),
            "compiledByteSize": output.stat().st_size,
            "compilerDigest": hashlib.sha256(b"compiler").hexdigest(),
            "compilerByteSize": len(b"compiler"),
            "standardIncludeTreeDigest": None,
            "standardIncludeFileCount": 0,
            "standardIncludeByteSize": 0,
            "processExitCode": 1,
            "errorCount": 0,
            "warningCount": 0,
            "durationMs": 4,
            "resultLine": "Result: 0 errors, 0 warnings",
        }

    def add_second_version(self) -> Path:
        source = self.build_dir / "EA_Versions" / "CompileFixture_v02.mq4"
        source.write_text(
            "#property strict\nint OnInit(){return(INIT_SUCCEEDED);}\n"
            "void OnTick(){double marker=2.0;}\n",
            encoding="utf-8",
        )
        digest = hashlib.sha256(source.read_bytes()).hexdigest()
        self.build["versions"].append({
            "version": 2,
            "fileName": source.name,
            "sourceDigest": digest,
            "sourceFile": "Source/CompileFixture.mq4",
            "versionFile": f"EA_Versions/{source.name}",
            "sourceReportId": "report-generation-v02",
            "immutable": True,
            "createdAt": "2026-09-09T00:01:00Z",
        })
        return source

    def patches(self, compile_side_effect=None):
        return (
            mock.patch.object(self.bridge, "PROJECT_ROOT", self.root),
            mock.patch.object(
                self.bridge,
                "_ea_factory_metaeditor_target_context",
                return_value=(
                    {
                        "record": {},
                        "token": {
                            "candidateId": self.target["candidateId"],
                            "selectionRevision": 4,
                        },
                    },
                    self.target,
                ),
            ),
            mock.patch.object(
                self.bridge,
                "_ea_factory_metaeditor_selection_is_current",
                return_value=True,
            ),
            mock.patch.object(
                self.bridge,
                "compile_metaeditor_source",
                side_effect=compile_side_effect or self.fake_compile,
            ),
            mock.patch.object(
                self.bridge,
                "create_mission",
                side_effect=lambda payload, status=None: {**payload, "status": status},
            ),
            mock.patch.object(
                self.bridge,
                "create_report",
                side_effect=lambda payload: payload,
            ),
            mock.patch.object(self.bridge, "_ea_factory_complete_local_mission"),
        )

    def test_stage_writes_receipt_binary_and_reuses_them_idempotently(self) -> None:
        from contextlib import ExitStack

        with ExitStack() as stack:
            patches = self.patches()
            for patcher in patches:
                stack.enter_context(patcher)
            mission, report = self.bridge._ea_factory_complete_metaeditor_compile(
                self.build,
                self.stage,
            )

        self.assertEqual(self.stage["status"], "completed")
        self.assertTrue(self.stage["evidenceVerified"])
        self.assertEqual(mission["id"], self.stage["missionId"])
        self.assertEqual(report["id"], self.stage["reportId"])
        self.assertEqual(report["metrics"]["compileStatus"], "passed")
        self.assertFalse(report["metrics"]["backtestExecuted"])
        self.assertTrue((self.build_dir / "EA_Versions" / "CompileFixture_v01.ex4").is_file())
        receipt_path = self.build_dir / "Reports" / "metaeditor-compile-v01.json"
        receipt = self.bridge.read_json(receipt_path, None)
        with mock.patch.object(self.bridge, "PROJECT_ROOT", self.root):
            self.assertTrue(
                self.bridge._ea_factory_compile_receipt_valid(self.build, receipt)
            )
        first_manifest = list(self.build["artifactManifest"])

        second_stage = {
            **self.stage,
            "status": "pending",
            "artifacts": [],
        }
        with ExitStack() as stack:
            patches = self.patches(
                compile_side_effect=AssertionError("idempotent receipt must avoid compile")
            )
            for patcher in patches:
                stack.enter_context(patcher)
            _mission, second_report = self.bridge._ea_factory_complete_metaeditor_compile(
                self.build,
                second_stage,
            )
        self.assertTrue(second_report["metrics"]["compileReceiptReused"])
        self.assertFalse(second_report["metrics"]["compileExecuted"])
        self.assertEqual(self.build["artifactManifest"], first_manifest)

    def test_binary_tamper_invalidates_immutable_receipt(self) -> None:
        from contextlib import ExitStack

        with ExitStack() as stack:
            for patcher in self.patches():
                stack.enter_context(patcher)
            self.bridge._ea_factory_complete_metaeditor_compile(
                self.build,
                self.stage,
            )
        receipt = self.bridge.read_json(
            self.build_dir / "Reports" / "metaeditor-compile-v01.json",
            None,
        )
        (self.build_dir / "EA_Versions" / "CompileFixture_v01.ex4").write_bytes(
            b"tampered"
        )
        with mock.patch.object(self.bridge, "PROJECT_ROOT", self.root):
            self.assertFalse(
                self.bridge._ea_factory_compile_receipt_valid(self.build, receipt)
            )

    def test_multi_version_failure_rolls_back_all_attempt_outputs_and_retries(self) -> None:
        from contextlib import ExitStack

        second_source = self.add_second_version()

        def fail_second(*args, **kwargs):
            source_path = Path(args[1])
            if source_path == second_source:
                source_path.with_suffix(".ex4").write_bytes(b"partial second output")
                raise self.bridge.MetaEditorCompileError(
                    "metaeditor_compile_failed",
                    process_started=True,
                    exit_code=1,
                    errors=1,
                    warnings=0,
                )
            return self.fake_compile(*args, **kwargs)

        with ExitStack() as stack:
            for patcher in self.patches(compile_side_effect=fail_second):
                stack.enter_context(patcher)
            with self.assertRaises(self.bridge.MetaEditorCompileError) as raised:
                self.bridge._ea_factory_complete_metaeditor_compile(
                    self.build,
                    self.stage,
                )
        self.assertEqual(raised.exception.code, "metaeditor_compile_failed")
        for name in ("CompileFixture_v01.ex4", "CompileFixture_v02.ex4"):
            self.assertFalse((self.build_dir / "EA_Versions" / name).exists())
        for name in (
            "metaeditor-compile-v01.json",
            "metaeditor-compile-v01.txt",
            "metaeditor-compile-01.raw.log",
            "metaeditor-compile-02.raw.log",
        ):
            self.assertFalse((self.build_dir / "Reports" / name).exists())

        with ExitStack() as stack:
            for patcher in self.patches():
                stack.enter_context(patcher)
            self.bridge._ea_factory_complete_metaeditor_compile(
                self.build,
                self.stage,
            )
        self.assertTrue(
            (self.build_dir / "EA_Versions" / "CompileFixture_v01.ex4").is_file()
        )
        self.assertTrue(
            (self.build_dir / "EA_Versions" / "CompileFixture_v02.ex4").is_file()
        )
        receipt = self.bridge.read_json(
            self.build_dir / "Reports" / "metaeditor-compile-v01.json",
            None,
        )
        self.assertEqual(len(receipt["sourceResults"]), 2)

    def test_compile_log_write_failure_rolls_back_binary_and_retries(self) -> None:
        from contextlib import ExitStack

        log_path = self.build_dir / "Reports" / "metaeditor-compile-v01.txt"
        original_write_text = Path.write_text

        def fail_log_write(path, data, *args, **kwargs):
            if Path(path) == log_path:
                original_write_text(path, "partial log", encoding="utf-8")
                raise OSError("simulated log write failure")
            return original_write_text(path, data, *args, **kwargs)

        with ExitStack() as stack:
            for patcher in self.patches():
                stack.enter_context(patcher)
            stack.enter_context(mock.patch.object(Path, "write_text", new=fail_log_write))
            with self.assertRaises(self.bridge.MetaEditorCompileError) as raised:
                self.bridge._ea_factory_complete_metaeditor_compile(
                    self.build,
                    self.stage,
                )
        self.assertEqual(raised.exception.code, "compile_evidence_write_failed")
        self.assertFalse(self.source.with_suffix(".ex4").exists())
        self.assertFalse(log_path.exists())
        self.assertFalse(
            (self.build_dir / "Reports" / "metaeditor-compile-v01.json").exists()
        )

        with ExitStack() as stack:
            for patcher in self.patches():
                stack.enter_context(patcher)
            self.bridge._ea_factory_complete_metaeditor_compile(self.build, self.stage)
        self.assertTrue(self.source.with_suffix(".ex4").is_file())

    def test_compile_receipt_write_failure_rolls_back_binary_and_retries(self) -> None:
        from contextlib import ExitStack

        receipt_path = self.build_dir / "Reports" / "metaeditor-compile-v01.json"
        original_write_json = self.bridge.write_json

        def fail_receipt_write(path, payload, *args, **kwargs):
            if Path(path) == receipt_path:
                receipt_path.write_text("{", encoding="utf-8")
                raise OSError("simulated receipt write failure")
            return original_write_json(path, payload, *args, **kwargs)

        with ExitStack() as stack:
            for patcher in self.patches():
                stack.enter_context(patcher)
            stack.enter_context(
                mock.patch.object(
                    self.bridge,
                    "write_json",
                    side_effect=fail_receipt_write,
                )
            )
            with self.assertRaises(self.bridge.MetaEditorCompileError) as raised:
                self.bridge._ea_factory_complete_metaeditor_compile(
                    self.build,
                    self.stage,
                )
        self.assertEqual(raised.exception.code, "compile_evidence_write_failed")
        self.assertFalse(self.source.with_suffix(".ex4").exists())
        self.assertFalse(receipt_path.exists())
        self.assertFalse(
            (self.build_dir / "Reports" / "metaeditor-compile-v01.txt").exists()
        )

        with ExitStack() as stack:
            for patcher in self.patches():
                stack.enter_context(patcher)
            self.bridge._ea_factory_complete_metaeditor_compile(self.build, self.stage)
        self.assertTrue(receipt_path.is_file())
        self.assertTrue(self.source.with_suffix(".ex4").is_file())

    def test_failure_after_receipt_validation_preserves_immutable_outputs(self) -> None:
        from contextlib import ExitStack

        receipt_path = self.build_dir / "Reports" / "metaeditor-compile-v01.json"
        log_path = self.build_dir / "Reports" / "metaeditor-compile-v01.txt"
        binary_path = self.source.with_suffix(".ex4")
        with ExitStack() as stack:
            for patcher in self.patches():
                stack.enter_context(patcher)
            stack.enter_context(
                mock.patch.object(
                    self.bridge,
                    "create_mission",
                    side_effect=RuntimeError("simulated downstream store failure"),
                )
            )
            with self.assertRaises(RuntimeError):
                self.bridge._ea_factory_complete_metaeditor_compile(
                    self.build,
                    self.stage,
                )
        self.assertTrue(receipt_path.is_file())
        self.assertTrue(log_path.is_file())
        self.assertTrue(binary_path.is_file())
        receipt_before = receipt_path.read_bytes()
        binary_before = binary_path.read_bytes()

        retry_stage = {**self.stage, "status": "pending", "artifacts": []}
        with ExitStack() as stack:
            for patcher in self.patches(
                compile_side_effect=AssertionError(
                    "receipt-backed retry must not compile again"
                )
            ):
                stack.enter_context(patcher)
            _mission, report = self.bridge._ea_factory_complete_metaeditor_compile(
                self.build,
                retry_stage,
            )
        self.assertTrue(report["metrics"]["compileReceiptReused"])
        self.assertEqual(receipt_path.read_bytes(), receipt_before)
        self.assertEqual(binary_path.read_bytes(), binary_before)

    def test_receipt_reuse_rehashes_the_selected_compiler(self) -> None:
        from contextlib import ExitStack

        with ExitStack() as stack:
            for patcher in self.patches():
                stack.enter_context(patcher)
            self.bridge._ea_factory_complete_metaeditor_compile(self.build, self.stage)
        binary_path = self.source.with_suffix(".ex4")
        binary_before = binary_path.read_bytes()
        self.target["compilerPath"].write_bytes(b"replaced compiler")

        retry_stage = {**self.stage, "status": "pending", "artifacts": []}
        with ExitStack() as stack:
            for patcher in self.patches(
                compile_side_effect=AssertionError(
                    "invalid receipt must fail before a new compile"
                )
            ):
                stack.enter_context(patcher)
            with self.assertRaises(self.bridge.DataIntegrityError):
                self.bridge._ea_factory_complete_metaeditor_compile(
                    self.build,
                    retry_stage,
                )
        self.assertEqual(binary_path.read_bytes(), binary_before)

    def test_mt5_receipt_reuse_rehashes_the_standard_include_tree(self) -> None:
        from contextlib import ExitStack

        self.source.unlink()
        self.source = self.build_dir / "EA_Versions" / "CompileFixture_v01.mq5"
        self.source.write_text(
            "#property strict\n#include <Trade/Trade.mqh>\n"
            "int OnInit(){return(INIT_SUCCEEDED);}\nvoid OnTick(){}\n",
            encoding="utf-8",
        )
        self.source_digest = hashlib.sha256(self.source.read_bytes()).hexdigest()
        self.build["platform"] = "mt5"
        self.build["versions"][0].update({
            "fileName": self.source.name,
            "sourceDigest": self.source_digest,
            "sourceFile": "Source/CompileFixture.mq5",
            "versionFile": f"EA_Versions/{self.source.name}",
        })
        include_root = self.root / "terminal-data" / "MQL5" / "Include"
        trade_header = include_root / "Trade" / "Trade.mqh"
        trade_header.parent.mkdir(parents=True)
        trade_header.write_text("class CTrade {};\n", encoding="utf-8")
        (include_root / "Object.mqh").write_text("class CObject {};\n", encoding="utf-8")
        self.target.update({
            "platform": "mt5",
            "standardIncludeRoot": include_root,
        })

        def compile_mt5(
            _target,
            source_path,
            expected_digest,
            _versions_root,
            _raw_log_path,
            _reports_root,
            *,
            selection_is_current,
        ):
            self.assertTrue(selection_is_current())
            source_path = Path(source_path)
            output = source_path.with_suffix(".ex5")
            output.write_bytes(b"compiled mt5 integration artifact")
            include_snapshot = self.bridge.snapshot_metaeditor_standard_include_tree(
                include_root
            )
            return {
                "sourceFileName": source_path.name,
                "sourceDigest": expected_digest,
                "sourceByteSize": source_path.stat().st_size,
                "compiledFileName": output.name,
                "compiledDigest": hashlib.sha256(output.read_bytes()).hexdigest(),
                "compiledByteSize": output.stat().st_size,
                "compilerDigest": hashlib.sha256(b"compiler").hexdigest(),
                "compilerByteSize": len(b"compiler"),
                "standardIncludeTreeDigest": include_snapshot["treeDigest"],
                "standardIncludeFileCount": include_snapshot["fileCount"],
                "standardIncludeByteSize": include_snapshot["byteSize"],
                "processExitCode": 1,
                "errorCount": 0,
                "warningCount": 0,
                "durationMs": 4,
                "resultLine": "Result: 0 errors, 0 warnings",
            }

        with ExitStack() as stack:
            for patcher in self.patches(compile_side_effect=compile_mt5):
                stack.enter_context(patcher)
            self.bridge._ea_factory_complete_metaeditor_compile(self.build, self.stage)
        binary_path = self.source.with_suffix(".ex5")
        binary_before = binary_path.read_bytes()
        trade_header.write_text("class CTrade { int changed; };\n", encoding="utf-8")

        retry_stage = {**self.stage, "status": "pending", "artifacts": []}
        with ExitStack() as stack:
            for patcher in self.patches(
                compile_side_effect=AssertionError(
                    "changed include tree must invalidate receipt before compile"
                )
            ):
                stack.enter_context(patcher)
            with self.assertRaises(self.bridge.DataIntegrityError):
                self.bridge._ea_factory_complete_metaeditor_compile(
                    self.build,
                    retry_stage,
                )
        self.assertEqual(binary_path.read_bytes(), binary_before)

    def test_connection_checklist_requires_the_backend_compile_gate(self) -> None:
        connection = {
            "id": "metaeditor_compile_adapter",
            "labelTh": "MetaEditor compile-only",
            "required": False,
            "adapterStatus": (
                "implemented_fail_closed_requires_selected_matching_terminal"
            ),
        }
        selection = {
            "status": "selected",
            "configurationStatus": "configured",
            "selectedCandidate": {
                "candidateId": self.target["candidateId"],
                "platform": "mt4",
            },
        }
        freshness = {"bridge": {}, "codexQuota": {}, "metatrader": {}}
        with mock.patch.object(
            self.bridge,
            "_ea_factory_terminal_gate",
            return_value={
                "ready": True,
                "adapterReady": True,
                "reasonCode": None,
            },
        ):
            ready = self.bridge._connection_item_status(
                connection,
                {},
                {},
                {},
                False,
                freshness,
                selection,
            )
        self.assertEqual(ready["status"], "ready")
        self.assertTrue(ready["adapterReady"])
        self.assertEqual(ready["executionAdapterStatus"], "compile_only_ready")

        with mock.patch.object(
            self.bridge,
            "_ea_factory_terminal_gate",
            return_value={
                "ready": False,
                "adapterReady": False,
                "reasonCode": "terminal_platform_mismatch",
            },
        ):
            blocked = self.bridge._connection_item_status(
                connection,
                {},
                {},
                {},
                False,
                freshness,
                selection,
            )
        self.assertEqual(blocked["status"], "not_connected")
        self.assertFalse(blocked["adapterReady"])
        self.assertEqual(
            blocked["executionAdapterStatus"],
            "terminal_platform_mismatch",
        )


if __name__ == "__main__":
    unittest.main()
