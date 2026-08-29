from __future__ import annotations

import copy
import csv
import hashlib
import importlib.util
import io
import json
import tempfile
import unittest
from pathlib import Path
from urllib.request import Request
from unittest import mock


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BRIDGE_PATH = PROJECT_ROOT / "backend" / "local-runner" / "bridge_server.py"


def load_bridge():
    spec = importlib.util.spec_from_file_location(
        "metafx_ea_factory_adversarial",
        BRIDGE_PATH,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to import {BRIDGE_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class EaFactoryAdversarialTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.bridge = load_bridge()

    def valid_values(self, *, verification_status: str = "verified") -> dict:
        return {
            "record_id": "system-adversarial-001",
            "system_name": "Adversarial Trend System",
            "strategy_family": "trend_following",
            "symbols_market": "EURUSD / Forex",
            "timeframe": "H1",
            "entry_rules": "Buy only after a confirmed trend rule",
            "exit_rules": "Exit only after the opposite confirmed rule",
            "stop_loss": "fixed 100 points",
            "take_profit": "fixed 200 points",
            "recovery": "none",
            "lot_risk": "1 percent fixed fractional",
            "indicators": "EMA 20 and EMA 50",
            "special_conditions": "one position at a time",
            "source_urls": "https://example.org/public-system",
            "verification_status": verification_status,
            "backtest_status": "not_run",
            "backtest_report": "",
            "optimization_status": "not_run",
            "optimization_report": "",
            "issues": "none",
            "next_action": "build",
            "target_platform": "mt4",
            "updated_at": "2026-08-24T09:00:00+07:00",
        }

    def normalized_record(
        self,
        *,
        source_key: str = "sheet-adversarial",
        verification_status: str = "verified",
    ) -> dict:
        record = self.bridge._ea_factory_normalize_record(
            self.valid_values(verification_status=verification_status),
            source_kind="google_sheet_public_csv",
            source_key=source_key,
            source_report_id="report-sheet-source",
            source_mission_id="mission-sheet-source",
        )
        self.assertIsInstance(record, dict)
        return record

    def csv_payload(self, header: list[str] | tuple[str, ...], values: dict | None = None) -> bytes:
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(header)
        row_values = values or self.valid_values()
        writer.writerow(
            [
                row_values.get(field, "")
                for _column, field, _label, _group in self.bridge.EA_FACTORY_SHEET_COLUMNS
            ]
        )
        return output.getvalue().encode("utf-8")

    def snapshot(self, record: dict, *, source_key: str = "sheet-adversarial") -> dict:
        header_digest = self.bridge.payload_digest(
            "ea-factory-a-w-header-v1",
            [
                field
                for _column, field, _label, _group in self.bridge.EA_FACTORY_SHEET_COLUMNS
            ],
        )
        snapshot = {
            "schemaVersion": "ea-factory-sheet-snapshot-v1",
            "sourceKey": source_key,
            "sheetReferenceMasked": "ABCDEF…1234",
            "tabName": "EA_Full_Cycle",
            "status": "ready",
            "recordCount": 1,
            "rejectedRowCount": 0,
            "headerExact": True,
            "headerDigest": header_digest,
            "records": [record],
            "syncedAt": "2026-08-24T02:00:00+00:00",
            "missionId": "mission-sheet-source",
            "reportId": "report-sheet-source",
            "lastErrorCode": None,
        }
        snapshot["snapshotDigest"] = self.bridge._ea_factory_snapshot_digest(
            source_key,
            snapshot["tabName"],
            snapshot["records"],
        )
        return snapshot

    def make_build_workspace(
        self,
        root: Path,
        *,
        build_id: str = "ea-build-adversarial",
        platform: str = "mt4",
        source_key: str = "sheet-adversarial",
    ) -> tuple[dict, dict]:
        record = self.normalized_record(source_key=source_key)
        with mock.patch.object(self.bridge, "PROJECT_ROOT", root):
            workspace = self.bridge._ea_factory_create_build_workspace(
                build_id,
                record,
                platform,
            )
        stages = self.bridge._ea_factory_initial_stages(
            platform,
            {"id": "mission-strategy-spec"},
            {"id": "report-strategy-spec"},
        )
        build = {
            "schemaVersion": "ea-factory-build-v1",
            "id": build_id,
            "sourceRecordId": record["sourceRecordId"],
            "sourceDisplayName": record["displayName"],
            "sourceRecordDigest": record["recordDigest"],
            "sourceReportId": "report-strategy-spec",
            "sourceMissionId": "mission-strategy-spec",
            "platform": platform,
            "brief": "bounded adversarial fixture",
            "status": "ready",
            "workspace": workspace,
            "stages": stages,
            "versions": [],
            "createIdempotencyKey": "create-adversarial",
            "createIdempotencyKeys": ["create-adversarial"],
            "createRequestDigest": self.bridge._ea_factory_create_request_digest(
                record["sourceRecordId"],
                platform,
                "bounded adversarial fixture",
            ),
            "createdAt": "2026-08-24T02:00:00+00:00",
            "updatedAt": "2026-08-24T02:00:00+00:00",
        }
        return build, record

    def source_path(self, root: Path, build: dict, name: str = "TrendEA.mq4") -> Path:
        return (
            root
            / "workspace"
            / "ea-factory"
            / str(build["id"])
            / "Source"
            / name
        )

    def generation_report(self, build: dict, relative_path: str, source_digest: str) -> dict:
        source_record_digest = str(build["sourceRecordDigest"])
        spec_digest = str(build["workspace"]["strategySpecDigest"])
        platform = str(build["platform"])
        inputs = {
            "sourceReportId": build["sourceReportId"],
            "platform": platform,
            "brief": self.bridge._ea_factory_generation_brief(build),
        }
        return {
            "id": "report-generation-proof",
            "type": "ea_build_report",
            "status": "ready",
            "linkedPropId": "right_server_racks",
            "workflowContext": {
                "propId": "right_server_racks",
                "actionId": "build_strategy_code",
                "inputDigest": self.bridge.payload_digest(
                    "dashboard-workflow-input-v1",
                    "right_server_racks",
                    "build_strategy_code",
                    json.dumps(inputs, ensure_ascii=False, sort_keys=True),
                ),
                "inputs": inputs,
                "source": {"reportId": build["sourceReportId"]},
            },
            "metrics": {
                "workflowOutput": {
                    "applicable": True,
                    "valid": True,
                    "expectedFields": [
                        "sourceFiles",
                        "sourceDigest",
                        "sourceRecordDigest",
                        "strategySpecDigest",
                        "platform",
                    ],
                    "providedFields": [
                        "sourceFiles",
                        "sourceDigest",
                        "sourceRecordDigest",
                        "strategySpecDigest",
                        "platform",
                    ],
                    "missingFields": [],
                    "expectedEvidenceKinds": ["project_relative_source_path"],
                    "providedEvidenceKinds": ["project_relative_source_path"],
                    "missingEvidenceKinds": [],
                    "values": {
                        "sourceFiles": json.dumps([relative_path]),
                        "sourceDigest": source_digest,
                        "sourceRecordDigest": source_record_digest,
                        "strategySpecDigest": spec_digest,
                        "platform": platform,
                    },
                }
            },
        }

    def review_report(self, build: dict, compile_status: str) -> dict:
        digest = str(build["versions"][0]["sourceDigest"])
        source_record_digest = str(build["sourceRecordDigest"])
        spec_digest = str(build["workspace"]["strategySpecDigest"])
        platform = str(build["platform"])
        generation_report_id = self.bridge._ea_factory_stage_row(
            build,
            "generate_source",
        )["reportId"]
        inputs = {
            "sourceReportId": generation_report_id,
            "platform": platform,
            "brief": self.bridge._ea_factory_review_brief(build),
        }
        covered_fields = [
            field
            for _column, field, _label, group in self.bridge.EA_FACTORY_SHEET_COLUMNS
            if group == "core"
        ]
        return {
            "id": "report-review-proof",
            "type": "ea_build_report",
            "status": "ready",
            "linkedPropId": "right_server_racks",
            "workflowContext": {
                "propId": "right_server_racks",
                "actionId": "review_source_code",
                "inputDigest": self.bridge.payload_digest(
                    "dashboard-workflow-input-v1",
                    "right_server_racks",
                    "review_source_code",
                    json.dumps(inputs, ensure_ascii=False, sort_keys=True),
                ),
                "inputs": inputs,
                "source": {"reportId": generation_report_id},
            },
            "metrics": {
                "workflowOutput": {
                    "applicable": True,
                    "valid": True,
                    "values": {
                        "sourceDigest": digest,
                        "compileStatus": compile_status,
                        "sourceRecordDigest": source_record_digest,
                        "strategySpecDigest": spec_digest,
                        "platform": platform,
                        "strategyCoverage": json.dumps(
                            {
                                "coveredFields": covered_fields,
                                "uncoveredFields": [],
                            }
                        ),
                        "severity": "no_issue",
                        "reviewStatus": "review_passed",
                        "issues": "[]",
                    },
                }
            },
        }

    def read_model_patches(self, state: dict):
        return (
            mock.patch.object(
                self.bridge,
                "_load_ea_factory_state_unlocked",
                return_value=state,
            ),
            mock.patch.object(self.bridge, "load_missions", return_value=[]),
            mock.patch.object(self.bridge, "load_runtime_reports", return_value=[]),
            mock.patch.object(self.bridge, "_ea_factory_source_catalog", return_value=[]),
            mock.patch.object(
                self.bridge,
                "_ea_factory_build_read_model",
                side_effect=lambda build: {
                    "id": build.get("id"),
                    "stages": [],
                },
            ),
            mock.patch.object(
                self.bridge,
                "peek_metatrader_status",
                return_value={"status": "not_checked", "candidates": []},
            ),
            mock.patch.object(
                self.bridge,
                "_metatrader_selection_read_model",
                return_value={
                    "candidates": [],
                    "selectedCandidate": None,
                    "adapterReady": False,
                },
            ),
            mock.patch.object(
                self.bridge,
                "_ea_factory_terminal_gate",
                return_value={"required": False, "ready": False, "adapterReady": False},
            ),
        )

    def test_headers_accept_only_exact_canonical_or_bundled_bilingual(self) -> None:
        canonical = [
            field
            for _column, field, _label, _group in self.bridge.EA_FACTORY_SHEET_COLUMNS
        ]
        bundled_bilingual = list(self.bridge.EA_FACTORY_SHEET_TEMPLATE_HEADERS)
        for header in (canonical, bundled_bilingual):
            with self.subTest(header="canonical" if header is canonical else "bilingual"):
                records = self.bridge._ea_factory_parse_sheet_rows(
                    self.csv_payload(header),
                    "sheet-header-exact",
                )
                self.assertEqual(len(records), 1)
                self.assertTrue(records[0]["buildReady"])

        arbitrary_suffix = list(canonical)
        arbitrary_suffix[0] = "record_id/arbitrary suffix that is not bundled"
        reordered = list(bundled_bilingual)
        reordered[5], reordered[6] = reordered[6], reordered[5]
        for bad_header in (arbitrary_suffix, reordered):
            with self.subTest(bad_header=bad_header[:7]):
                with self.assertRaises(self.bridge.RequestError):
                    self.bridge._ea_factory_parse_sheet_rows(
                        self.csv_payload(bad_header),
                        "sheet-header-rejected",
                    )

    def test_recomputed_snapshot_tamper_cannot_override_build_readiness(self) -> None:
        source_key = "sheet-snapshot-sealed"
        legitimate = self.normalized_record(source_key=source_key)
        legitimate_snapshot = self.snapshot(legitimate, source_key=source_key)
        validated = self.bridge._ea_factory_revalidated_snapshot(legitimate_snapshot)
        self.assertTrue(validated["records"][0]["buildReady"])

        tampered_values = self.valid_values(verification_status="pending")
        tampered_values["entry_rules"] = "attacker replaced the persisted strategy"
        recomputed = self.bridge._ea_factory_normalize_record(
            tampered_values,
            source_kind="google_sheet_public_csv",
            source_key=source_key,
            source_report_id="report-sheet-source",
            source_mission_id="mission-sheet-source",
        )
        self.assertIsInstance(recomputed, dict)
        self.assertFalse(recomputed["buildReady"])
        recomputed["buildReady"] = True
        recomputed["missingCoreFields"] = []
        recomputed["readinessIssues"] = []
        forged_snapshot = self.snapshot(recomputed, source_key=source_key)

        # All public hashes have been recomputed.  Without a separate trust
        # root the loader may reject the snapshot or rederive its canonical
        # readiness fields.  Either behavior is valid, but the forged True bit
        # must never reach build creation.
        try:
            revalidated = self.bridge._ea_factory_revalidated_snapshot(
                forged_snapshot
            )
        except self.bridge.DataIntegrityError:
            return
        revalidated_record = revalidated["records"][0]
        self.assertFalse(revalidated_record["buildReady"])
        self.assertIn(
            "verification_status",
            revalidated_record["missingCoreFields"],
        )
        state = {
            "schemaVersion": self.bridge.EA_FACTORY_STATE_SCHEMA_VERSION,
            "sourceSnapshots": [revalidated],
            "builds": [],
            "updatedAt": "2026-08-24T02:00:00+00:00",
        }
        with (
            mock.patch.object(
                self.bridge,
                "_load_ea_factory_state_unlocked",
                return_value=state,
            ),
            mock.patch.object(
                self.bridge,
                "_ea_factory_create_build_workspace",
            ) as create_workspace,
            mock.patch.object(self.bridge, "_ea_factory_source_report") as source_report,
        ):
            with self.assertRaises(self.bridge.RequestError) as raised:
                self.bridge.create_ea_factory_build(
                    {
                        "sourceRecordId": revalidated_record["sourceRecordId"],
                        "platform": "mt4",
                        "idempotencyKey": "forged-build-ready",
                    }
                )
        self.assertEqual(raised.exception.status, 422)
        create_workspace.assert_not_called()
        source_report.assert_not_called()

    def test_recomputed_build_and_spec_digests_do_not_authorize_state_tamper(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            build, _record = self.make_build_workspace(root)
            reports_dir = root / "data" / "runtime" / "reports"
            reports_dir.mkdir(parents=True)
            trusted_binding = {
                "schemaVersion": "ea-factory-strategy-spec-v1",
                "buildId": build["id"],
                "sourceRecordId": build["sourceRecordId"],
                "recordDigest": build["sourceRecordDigest"],
                "platform": build["platform"],
                "strategySpecFile": build["workspace"]["strategySpecFile"],
                "strategySpecDigest": build["workspace"]["strategySpecDigest"],
                "immutable": True,
            }
            trusted_report = {
                "id": build["sourceReportId"],
                "type": "trading_system_research_report",
                "status": "ready",
                "linkedMissionId": build["sourceMissionId"],
                "linkedPropId": "left_server_racks",
                "metrics": {"eaFactoryStrategySpec": trusted_binding},
            }
            (reports_dir / f"{build['sourceReportId']}.json").write_text(
                json.dumps(trusted_report, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            with (
                mock.patch.object(self.bridge, "PROJECT_ROOT", root),
                mock.patch.object(self.bridge, "RUNTIME_REPORTS_DIR", reports_dir),
            ):
                self.bridge._ea_factory_revalidated_build(build)
                spec_path = self.source_path(root, build, "strategy-spec-v01.json")
                spec = json.loads(spec_path.read_text(encoding="utf-8"))
                spec["core"]["entry_rules"] = "persisted state attacker rewrite"
                spec["recordDigest"] = "b" * 64
                spec_path.write_text(
                    json.dumps(spec, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8",
                )
                forged = copy.deepcopy(build)
                forged["sourceRecordDigest"] = "b" * 64
                forged["workspace"]["strategySpecDigest"] = hashlib.sha256(
                    spec_path.read_bytes()
                ).hexdigest()
                with self.assertRaises(self.bridge.DataIntegrityError):
                    self.bridge._ea_factory_revalidated_build(forged)

    def test_strategy_source_report_binds_record_platform_and_spec_digest(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            build, record = self.make_build_workspace(root)
            captured: dict = {}

            def fake_create_report(payload):
                captured.update(copy.deepcopy(payload))
                return {**copy.deepcopy(payload), "id": "report-strategy-spec"}

            with (
                mock.patch.object(
                    self.bridge,
                    "create_mission",
                    return_value={"id": "mission-strategy-spec"},
                ),
                mock.patch.object(self.bridge, "create_report", side_effect=fake_create_report),
                mock.patch.object(self.bridge, "_ea_factory_complete_local_mission"),
            ):
                self.bridge._ea_factory_source_report(
                    str(build["id"]),
                    record,
                    str(build["platform"]),
                    build["workspace"],
                    idempotency_key="source-report-binding",
                )
            binding = captured["metrics"]["eaFactoryStrategySpec"]
            self.assertEqual(binding["buildId"], build["id"])
            self.assertEqual(binding["recordDigest"], build["sourceRecordDigest"])
            self.assertEqual(binding["platform"], build["platform"])
            self.assertEqual(
                binding["strategySpecDigest"],
                build["workspace"]["strategySpecDigest"],
            )

    def test_generated_source_report_binding_rejects_each_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            build, _record = self.make_build_workspace(root)
            source = self.source_path(root, build)
            source.write_text(
                "#property strict\nint OnInit(){return(INIT_SUCCEEDED);}\n",
                encoding="utf-8",
            )
            digest = hashlib.sha256(source.read_bytes()).hexdigest()
            relative = source.relative_to(root).as_posix()
            baseline = self.generation_report(build, relative, digest)

            with mock.patch.object(self.bridge, "PROJECT_ROOT", root):
                self.assertTrue(
                    self.bridge._ea_factory_generation_evidence_valid(
                        copy.deepcopy(build),
                        copy.deepcopy(baseline),
                        ingest_sources=False,
                    )
                )

                mutations = {
                    "source report": lambda report: report["workflowContext"]["source"].__setitem__(
                        "reportId", "report-other-build"
                    ),
                    "platform": lambda report: report["workflowContext"]["inputs"].__setitem__(
                        "platform", "mt5"
                    ),
                    "source record digest": lambda report: report["metrics"]["workflowOutput"]["values"].__setitem__(
                        "sourceRecordDigest", "c" * 64
                    ),
                    "strategy spec digest": lambda report: report["metrics"]["workflowOutput"]["values"].__setitem__(
                        "strategySpecDigest", "d" * 64
                    ),
                }
                for label, mutate in mutations.items():
                    with self.subTest(binding=label):
                        forged_report = copy.deepcopy(baseline)
                        mutate(forged_report)
                        self.assertFalse(
                            self.bridge._ea_factory_generation_evidence_valid(
                                copy.deepcopy(build),
                                forged_report,
                                ingest_sources=False,
                            )
                        )

    def test_existing_source_and_version_tamper_or_symlink_fails_closed(self) -> None:
        original = b"#property strict\nint OnInit(){return(INIT_SUCCEEDED);}\n"
        for folder, mode in (
            ("Source", "modified"),
            ("Source", "deleted"),
            ("Source", "symlink"),
            ("EA_Versions", "modified"),
            ("EA_Versions", "deleted"),
            ("EA_Versions", "symlink"),
        ):
            with self.subTest(folder=folder, mode=mode), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                build, _record = self.make_build_workspace(root)
                build_dir = root / "workspace" / "ea-factory" / str(build["id"])
                source = build_dir / "Source" / "TrendEA.mq4"
                version = build_dir / "EA_Versions" / "TrendEA_v01.mq4"
                source.write_bytes(original)
                version.write_bytes(original)
                digest = hashlib.sha256(original).hexdigest()
                build["versions"] = [
                    {
                        "version": 1,
                        "fileName": version.name,
                        "sourceDigest": digest,
                        "sourceFile": "Source/TrendEA.mq4",
                        "versionFile": "EA_Versions/TrendEA_v01.mq4",
                        "sourceReportId": "report-generation-proof",
                        "immutable": True,
                        "createdAt": "2026-08-24T02:05:00+00:00",
                    }
                ]
                target = source if folder == "Source" else version
                with mock.patch.object(self.bridge, "PROJECT_ROOT", root):
                    self.assertTrue(
                        self.bridge._ea_factory_existing_versions_valid(
                            build,
                            {"id": "report-generation-proof"},
                        )
                    )
                    if mode == "modified":
                        target.write_bytes(original + b"// tampered\n")
                    elif mode == "deleted":
                        target.unlink()
                    else:
                        sibling = target.with_name("real-immutable-copy.mq4")
                        sibling.write_bytes(original)
                        target.unlink()
                        try:
                            target.symlink_to(sibling.name)
                        except OSError as error:
                            self.skipTest(f"symbolic links unavailable: {error}")
                    self.assertFalse(
                        self.bridge._ea_factory_existing_versions_valid(
                            build,
                            {"id": "report-generation-proof"},
                        )
                    )

    def test_review_compile_status_uses_exact_allowlist(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            build, _record = self.make_build_workspace(root)
            digest = "a" * 64
            build["versions"] = [
                {
                    "sourceDigest": digest,
                    "sourceReportId": "report-generation-proof",
                    "immutable": True,
                }
            ]
            generation_stage = self.bridge._ea_factory_stage_row(build, "generate_source")
            generation_stage.update(
                {
                    "status": "completed",
                    "missionId": "mission-generation",
                    "reportId": "report-generation-proof",
                    "evidenceVerified": True,
                }
            )
            self.assertTrue(
                self.bridge._ea_factory_review_evidence_valid(
                    build,
                    self.review_report(build, "not_run"),
                )
            )
            self.assertFalse(
                self.bridge._ea_factory_review_evidence_valid(
                    build,
                    self.review_report(build, "compiled_static_success"),
                )
            )
            blocking = self.review_report(build, "not_run")
            blocking_values = blocking["metrics"]["workflowOutput"]["values"]
            blocking_values["severity"] = "critical"
            blocking_values["reviewStatus"] = "repair_required"
            blocking_values["issues"] = json.dumps(
                [{"severity": "critical", "status": "unresolved", "message": "unsafe lot sizing"}]
            )
            self.assertTrue(self.bridge._ea_factory_review_requires_repair(blocking))
            self.assertFalse(
                self.bridge._ea_factory_review_evidence_valid(build, blocking),
                "Critical unresolved review findings must require a new immutable version, not advance",
            )

    def test_review_rehashes_manifest_source_version_and_spec_before_acceptance(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            build, _record = self.make_build_workspace(
                root,
                build_id="ea-build-review-rehash",
            )
            build_dir = root / "workspace" / "ea-factory" / build["id"]
            source = build_dir / "Source" / "TrendEA.mq4"
            version = build_dir / "EA_Versions" / "TrendEA_v01.mq4"
            payload = "#property strict\n#define SIGNAL_NONE -1\nvoid OnTick(){}\n"
            source.write_text(payload, encoding="utf-8")
            version.write_text(payload, encoding="utf-8")
            digest = hashlib.sha256(source.read_bytes()).hexdigest()
            build["versions"] = [{
                "version": 1,
                "fileName": source.name,
                "sourceDigest": digest,
                "sourceFile": "Source/TrendEA.mq4",
                "versionFile": "EA_Versions/TrendEA_v01.mq4",
                "sourceReportId": "report-generation-proof",
                "immutable": True,
            }]
            build["artifactManifest"] = []
            build["artifactManifestDigest"] = None
            with mock.patch.object(self.bridge, "PROJECT_ROOT", root):
                self.bridge._ea_factory_register_artifacts(
                    build,
                    [
                        {
                            "relativePath": "Source/strategy-spec-v01.json",
                            "stageId": "strategy_spec",
                            "reportId": "report-strategy-spec",
                            "artifactKind": "strategy_spec",
                        },
                        {
                            "relativePath": "Source/TrendEA.mq4",
                            "stageId": "generate_source",
                            "reportId": "report-generation-proof",
                            "artifactKind": "generated_source",
                        },
                        {
                            "relativePath": "EA_Versions/TrendEA_v01.mq4",
                            "stageId": "generate_source",
                            "reportId": "report-generation-proof",
                            "artifactKind": "immutable_version",
                        },
                    ],
                )
                self.assertTrue(
                    self.bridge._ea_factory_review_artifact_snapshot_valid(build)
                )
                source.write_text(payload + "// tampered\n", encoding="utf-8")
                self.assertFalse(
                    self.bridge._ea_factory_review_artifact_snapshot_valid(build)
                )

    def test_pine_validation_crash_replay_is_byte_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            build, _record = self.make_build_workspace(
                root,
                platform="tradingview",
            )
            build_dir = root / "workspace" / "ea-factory" / str(build["id"])
            source = build_dir / "EA_Versions" / "TrendEA_v01.pine"
            source.write_text(
                "//@version=5\nstrategy('Adversarial fixture', overlay=true)\n",
                encoding="utf-8",
            )
            digest = hashlib.sha256(source.read_bytes()).hexdigest()
            build["versions"] = [
                {
                    "version": 1,
                    "fileName": source.name,
                    "sourceDigest": digest,
                    "sourceFile": "Source/TrendEA.pine",
                    "versionFile": "EA_Versions/TrendEA_v01.pine",
                    "sourceReportId": "report-generation-proof",
                    "immutable": True,
                    "createdAt": "2026-08-24T02:05:00+00:00",
                }
            ]
            for stage_id in ("generate_source", "source_review"):
                self.bridge._ea_factory_stage_row(build, stage_id)["status"] = "completed"
            stage = self.bridge._ea_factory_stage_row(build, "compile_validate")
            stage["startedAt"] = "2026-08-24T02:10:00+00:00"
            stage["missionIdempotencyKey"] = "pine-crash-replay"
            persisted_before_side_effect = copy.deepcopy(build)
            report_sequence: list[str] = []

            def fake_mission(payload, status="queued"):
                return {
                    "id": payload.get("id") or "mission-pine-validation",
                    "status": status,
                }

            def fake_report(payload):
                report_id = payload.get("id")
                if not report_id:
                    report_id = f"report-pine-validation-{len(report_sequence) + 1}"
                report_sequence.append(report_id)
                return {**copy.deepcopy(payload), "id": report_id}

            with (
                mock.patch.object(self.bridge, "PROJECT_ROOT", root),
                mock.patch.object(self.bridge, "create_mission", side_effect=fake_mission),
                mock.patch.object(self.bridge, "create_report", side_effect=fake_report),
                mock.patch.object(self.bridge, "_ea_factory_complete_local_mission"),
            ):
                first_mission, first_report = self.bridge._ea_factory_complete_pine_validation(
                    build,
                    stage,
                )
                artifact = build_dir / "Reports" / "pine-static-validation-v01.json"
                first_bytes = artifact.read_bytes()

                replay_build = copy.deepcopy(persisted_before_side_effect)
                replay_stage = self.bridge._ea_factory_stage_row(
                    replay_build,
                    "compile_validate",
                )
                replay_mission, replay_report = self.bridge._ea_factory_complete_pine_validation(
                    replay_build,
                    replay_stage,
                )
                self.assertEqual(artifact.read_bytes(), first_bytes)
                self.assertEqual(replay_mission["id"], first_mission["id"])
                self.assertEqual(replay_report["id"], first_report["id"])
                self.assertEqual(
                    json.loads(first_bytes)["validatedAt"],
                    "2026-08-24T02:10:00+00:00",
                )

    def test_final_report_crash_replay_is_deterministic_and_records_completion(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            build, _record = self.make_build_workspace(
                root,
                platform="tradingview",
            )
            for stage_id in (
                "generate_source",
                "source_review",
                "compile_validate",
            ):
                self.bridge._ea_factory_stage_row(build, stage_id)["status"] = "completed"
            final_stage = self.bridge._ea_factory_stage_row(build, "final_report")
            final_stage["startedAt"] = "2026-08-24T02:20:00+00:00"
            final_stage["missionIdempotencyKey"] = "final-crash-replay"
            persisted_before_side_effect = copy.deepcopy(build)
            build_dir = root / "workspace" / "ea-factory" / str(build["id"])

            def fake_mission(payload, status="queued"):
                return {"id": payload.get("id") or "mission-final-report", "status": status}

            def fake_report(payload):
                return {
                    **copy.deepcopy(payload),
                    "id": payload.get("id") or "report-final-report",
                }

            with (
                mock.patch.object(self.bridge, "PROJECT_ROOT", root),
                mock.patch.object(self.bridge, "create_mission", side_effect=fake_mission),
                mock.patch.object(self.bridge, "create_report", side_effect=fake_report),
                mock.patch.object(self.bridge, "_ea_factory_complete_local_mission"),
                mock.patch.object(self.bridge, "tail_jsonl", return_value=[]),
                mock.patch.object(self.bridge, "append_audit") as append_audit,
            ):
                self.bridge._ea_factory_complete_final_report(build, final_stage)
                summary_path = build_dir / "Summaries" / "final-report-v01.json"
                markdown_path = build_dir / "Summaries" / "final-report-v01.md"
                first_summary = summary_path.read_bytes()
                first_markdown = markdown_path.read_bytes()

                summary = json.loads(first_summary)
                final_row = next(
                    row for row in summary["stages"] if row["id"] == "final_report"
                )
                self.assertEqual(final_row["status"], "completed")
                self.assertTrue(final_stage["evidenceVerified"])
                self.assertEqual(len(final_stage["artifacts"]), 4)
                self.assertRegex(final_stage["artifactManifestDigest"], r"^[0-9a-f]{64}$")
                self.assertRegex(final_stage["auditLineageId"], r"^ea-lineage-")
                append_audit.assert_called_once()

                lineage_path = build_dir / "Summaries" / "final-audit-lineage-v01.json"
                manifest_path = build_dir / "Summaries" / "artifact-manifest-v01.json"
                first_lineage = lineage_path.read_bytes()
                first_manifest = manifest_path.read_bytes()

                replay_build = copy.deepcopy(persisted_before_side_effect)
                replay_stage = self.bridge._ea_factory_stage_row(
                    replay_build,
                    "final_report",
                )
                self.bridge._ea_factory_complete_final_report(
                    replay_build,
                    replay_stage,
                )
                self.assertEqual(summary_path.read_bytes(), first_summary)
                self.assertEqual(markdown_path.read_bytes(), first_markdown)
                self.assertEqual(lineage_path.read_bytes(), first_lineage)
                self.assertEqual(manifest_path.read_bytes(), first_manifest)
                self.assertEqual(replay_stage["artifacts"], final_stage["artifacts"])

    def test_read_model_never_requests_source_ingestion(self) -> None:
        state = {
            "schemaVersion": self.bridge.EA_FACTORY_STATE_SCHEMA_VERSION,
            "sourceSnapshots": [],
            "builds": [{"id": "ea-build-read-only"}],
            "updatedAt": None,
        }
        sync = mock.Mock(return_value=False)
        patches = self.read_model_patches(state)
        with (
            patches[0],
            patches[1],
            patches[2],
            patches[3],
            patches[4],
            patches[5],
            patches[6],
            patches[7],
            mock.patch.object(self.bridge, "_ea_factory_sync_build_status", sync),
            mock.patch.object(
                self.bridge,
                "_ea_factory_copy_generated_sources",
            ) as ingest,
        ):
            self.bridge.ea_factory_read_model()
        ingest.assert_not_called()
        for call in sync.call_args_list:
            self.assertFalse(
                call.kwargs.get("ingest_sources", False),
                "GET/read-model must never authorize Source -> EA_Versions ingestion",
            )

    def test_read_model_never_persists_state_or_filesystem_changes(self) -> None:
        state = {
            "schemaVersion": self.bridge.EA_FACTORY_STATE_SCHEMA_VERSION,
            "sourceSnapshots": [],
            "builds": [{"id": "ea-build-read-only"}],
            "updatedAt": None,
        }
        patches = self.read_model_patches(state)
        with (
            patches[0],
            patches[1],
            patches[2],
            patches[3],
            patches[4],
            patches[5],
            patches[6],
            patches[7],
            mock.patch.object(
                self.bridge,
                "_ea_factory_sync_build_status",
                return_value=True,
            ),
            mock.patch.object(
                self.bridge,
                "_write_ea_factory_state_unlocked",
            ) as write_state,
            mock.patch.object(self.bridge, "write_json") as write_file,
            mock.patch.object(self.bridge.shutil, "copyfile") as copy_file,
        ):
            self.bridge.ea_factory_read_model()
        write_state.assert_not_called()
        write_file.assert_not_called()
        copy_file.assert_not_called()

    def test_redirect_handler_blocks_bad_location_before_following(self) -> None:
        handler = self.bridge._EaFactoryGoogleRedirectHandler()
        request = Request("https://docs.google.com/spreadsheets/d/example/gviz/tq")
        with mock.patch.object(
            self.bridge.HTTPRedirectHandler,
            "redirect_request",
            autospec=True,
        ) as follow:
            with self.assertRaises(self.bridge.RequestError):
                handler.redirect_request(
                    request,
                    None,
                    302,
                    "Found",
                    {},
                    "https://attacker.example/steal.csv",
                )
        follow.assert_not_called()

    def test_artifact_download_rejects_traversal_and_in_root_symlink(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            build_id = "ea-build-download-adversarial"
            build_dir = root / "workspace" / "ea-factory" / build_id
            source_dir = build_dir / "Source"
            source_dir.mkdir(parents=True)
            outside = build_dir.parent / "outside.mq4"
            outside.write_text("#property strict\n", encoding="utf-8")
            outside_payload = outside.read_bytes()
            outside_digest = hashlib.sha256(outside_payload).hexdigest()
            traversal_file_id = "ea-file-" + self.bridge.payload_digest(
                "ea-factory-file-v1",
                build_id,
                "..",
                outside.name,
                len(outside_payload),
                outside_digest,
            )[:24]
            malicious_row = {
                "fileId": traversal_file_id,
                "folder": "..",
                "fileName": outside.name,
                "sha256": outside_digest,
            }
            state = {
                "schemaVersion": self.bridge.EA_FACTORY_STATE_SCHEMA_VERSION,
                "sourceSnapshots": [],
                "builds": [{"id": build_id}],
                "updatedAt": None,
            }
            with (
                mock.patch.object(self.bridge, "PROJECT_ROOT", root),
                mock.patch.object(
                    self.bridge,
                    "_load_ea_factory_state_unlocked",
                    return_value=state,
                ),
                mock.patch.object(
                    self.bridge,
                    "_ea_factory_file_catalog",
                    return_value=[malicious_row],
                ),
            ):
                self.assertIsNone(
                    self.bridge.resolve_ea_factory_file(
                        build_id,
                        traversal_file_id,
                    )
                )

            target = source_dir / "real.mq4"
            target.write_text("#property strict\n", encoding="utf-8")
            target_payload = target.read_bytes()
            target_digest = hashlib.sha256(target_payload).hexdigest()
            alias = source_dir / "alias.mq4"
            try:
                alias.symlink_to(target.name)
            except OSError as error:
                self.skipTest(f"symbolic links unavailable: {error}")
            symlink_file_id = "ea-file-" + self.bridge.payload_digest(
                "ea-factory-file-v1",
                build_id,
                "Source",
                target.name,
                len(target_payload),
                target_digest,
            )[:24]
            symlink_row = {
                "fileId": symlink_file_id,
                "folder": "Source",
                "fileName": alias.name,
                "sha256": target_digest,
            }
            with (
                mock.patch.object(self.bridge, "PROJECT_ROOT", root),
                mock.patch.object(
                    self.bridge,
                    "_load_ea_factory_state_unlocked",
                    return_value=state,
                ),
                mock.patch.object(
                    self.bridge,
                    "_ea_factory_file_catalog",
                    return_value=[symlink_row],
                ),
            ):
                self.assertIsNone(
                    self.bridge.resolve_ea_factory_file(
                        build_id,
                        symlink_file_id,
                    ),
                    "A same-folder symlink must not become downloadable after resolve()",
                )

    def test_manual_stage_order_and_idempotent_replay_are_strict(self) -> None:
        build = {
            "id": "ea-build-manual-order",
            "platform": "mt4",
            "sourceRecordDigest": "a" * 64,
            "sourceReportId": "report-strategy-spec",
            "brief": "manual only",
            "createRequestDigest": self.bridge._ea_factory_create_request_digest(
                "ea-source-manual-order",
                "mt4",
                "manual only",
            ),
            "stages": self.bridge._ea_factory_initial_stages(
                "mt4",
                {"id": "mission-strategy-spec"},
                {"id": "report-strategy-spec"},
            ),
        }
        state = {
            "schemaVersion": self.bridge.EA_FACTORY_STATE_SCHEMA_VERSION,
            "sourceSnapshots": [],
            "builds": [build],
            "updatedAt": None,
        }
        with (
            mock.patch.object(
                self.bridge,
                "_load_ea_factory_state_unlocked",
                return_value=state,
            ),
            mock.patch.object(
                self.bridge,
                "_ea_factory_sync_build_status",
                return_value=False,
            ),
            mock.patch.object(self.bridge, "_write_ea_factory_state_unlocked") as write_state,
            mock.patch.object(self.bridge, "run_dashboard_workflow_action") as dispatch,
        ):
            with self.assertRaises(self.bridge.RequestError) as raised:
                self.bridge.advance_ea_factory_build(
                    build["id"],
                    {
                        "stageId": "source_review",
                        "idempotencyKey": "cannot-skip-generate",
                    },
                )
        self.assertEqual(raised.exception.status, 409)
        write_state.assert_not_called()
        dispatch.assert_not_called()

        generation_stage = self.bridge._ea_factory_stage_row(build, "generate_source")
        generation_stage["status"] = "queued"
        generation_stage["requestIdempotencyKey"] = "generation-replay"
        generation_stage["requestDigest"] = self.bridge._ea_factory_advance_request_digest(
            build,
            "generate_source",
        )
        generation_stage["startedAt"] = "2026-08-24T02:30:00+00:00"
        generation_stage["missionIdempotencyKey"] = (
            self.bridge._ea_factory_stage_mission_idempotency_key(
                build["id"],
                "generate_source",
                "generation-replay",
            )
        )
        read_model = {
            "schemaVersion": self.bridge.EA_FACTORY_SCHEMA_VERSION,
            "builds": [{"id": build["id"], "stages": []}],
        }
        with (
            mock.patch.object(
                self.bridge,
                "_load_ea_factory_state_unlocked",
                return_value=state,
            ),
            mock.patch.object(
                self.bridge,
                "_ea_factory_sync_build_status",
                return_value=False,
            ),
            mock.patch.object(self.bridge, "_write_ea_factory_state_unlocked") as write_state,
            mock.patch.object(self.bridge, "run_dashboard_workflow_action") as dispatch,
            mock.patch.object(self.bridge, "deliver_dashboard_report") as transfer,
            mock.patch.object(self.bridge, "append_audit"),
            mock.patch.object(
                self.bridge,
                "ea_factory_read_model",
                return_value=read_model,
            ),
        ):
            replay = self.bridge.advance_ea_factory_build(
                build["id"],
                {
                    "stageId": "generate_source",
                    "idempotencyKey": "generation-retry-after-crash",
                },
            )
        self.assertTrue(replay["idempotentReplay"])
        self.assertEqual(replay["kind"], "ea_factory_stage_replayed")
        self.assertEqual(generation_stage["requestIdempotencyKey"], "generation-replay")
        write_state.assert_not_called()
        dispatch.assert_not_called()
        transfer.assert_not_called()

        tampered = copy.deepcopy(state)
        tampered_stage = self.bridge._ea_factory_stage_row(
            tampered["builds"][0],
            "generate_source",
        )
        tampered_stage["requestDigest"] = "f" * 64
        with (
            mock.patch.object(
                self.bridge,
                "_load_ea_factory_state_unlocked",
                return_value=tampered,
            ),
            mock.patch.object(
                self.bridge,
                "_ea_factory_sync_build_status",
                return_value=False,
            ),
        ):
            with self.assertRaises(self.bridge.RequestError) as raised:
                self.bridge.advance_ea_factory_build(
                    build["id"],
                    {
                        "stageId": "generate_source",
                        "idempotencyKey": "generation-retry-after-crash-2",
                    },
                )
        self.assertEqual(raised.exception.status, 409)

    def test_stage_replay_persists_explicit_post_reconciliation_without_redispatch(self) -> None:
        build = {
            "id": "ea-build-reconcile-replay",
            "platform": "mt4",
            "sourceRecordDigest": "a" * 64,
            "sourceReportId": "report-strategy-spec",
            "brief": "manual reconciliation",
            "createRequestDigest": "b" * 64,
            "stages": self.bridge._ea_factory_initial_stages(
                "mt4",
                {"id": "mission-strategy-spec"},
                {"id": "report-strategy-spec"},
            ),
        }
        stage = self.bridge._ea_factory_stage_row(build, "generate_source")
        stage.update({
            "status": "queued",
            "missionId": "mission-generation-existing",
            "requestIdempotencyKey": "original-browser-key",
            "requestDigest": self.bridge._ea_factory_advance_request_digest(
                build,
                "generate_source",
            ),
            "startedAt": "2026-08-24T03:00:00+00:00",
            "missionIdempotencyKey": self.bridge._ea_factory_stage_mission_idempotency_key(
                build["id"],
                "generate_source",
                "original-browser-key",
            ),
        })
        state = {
            "schemaVersion": self.bridge.EA_FACTORY_STATE_SCHEMA_VERSION,
            "sourceSnapshots": [],
            "builds": [build],
            "createReservations": [],
            "updatedAt": None,
        }

        def reconcile(row, **_kwargs):
            reconciled = self.bridge._ea_factory_stage_row(row, "generate_source")
            reconciled.update({
                "status": "completed",
                "reportId": "report-generation-existing",
                "evidenceVerified": True,
                "blockedReasonCode": None,
            })
            return True

        model = {
            "schemaVersion": self.bridge.EA_FACTORY_SCHEMA_VERSION,
            "builds": [{"id": build["id"], "stages": []}],
        }
        with (
            mock.patch.object(
                self.bridge,
                "_load_ea_factory_state_unlocked",
                return_value=state,
            ),
            mock.patch.object(
                self.bridge,
                "_ea_factory_sync_build_status",
                side_effect=reconcile,
            ),
            mock.patch.object(
                self.bridge,
                "_write_ea_factory_state_unlocked",
            ) as write_state,
            mock.patch.object(
                self.bridge,
                "load_missions",
                return_value=[{
                    "id": "mission-generation-existing",
                    "status": "completed",
                }],
            ),
            mock.patch.object(self.bridge, "run_dashboard_workflow_action") as dispatch,
            mock.patch.object(self.bridge, "deliver_dashboard_report") as transfer,
            mock.patch.object(self.bridge, "append_audit"),
            mock.patch.object(
                self.bridge,
                "ea_factory_read_model",
                return_value=model,
            ),
        ):
            replay = self.bridge.advance_ea_factory_build(
                build["id"],
                {
                    "stageId": "generate_source",
                    "idempotencyKey": "new-browser-key-after-crash",
                },
            )

        self.assertTrue(replay["idempotentReplay"])
        self.assertEqual(replay["mission"]["id"], "mission-generation-existing")
        self.assertEqual(stage["requestIdempotencyKey"], "original-browser-key")
        write_state.assert_called_once_with(state)
        dispatch.assert_not_called()
        transfer.assert_not_called()


if __name__ == "__main__":
    unittest.main()
