from __future__ import annotations

import importlib.util
import hashlib
import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest import mock


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BRIDGE_PATH = PROJECT_ROOT / "backend" / "local-runner" / "bridge_server.py"
RUNNER_PATH = PROJECT_ROOT / "runner" / "codex_cli_runner.py"
POLICY_PATH = (
    PROJECT_ROOT
    / "contracts"
    / "research"
    / "radar-website-source-policy-v1.json"
)
COMPATIBILITY_PATH = (
    PROJECT_ROOT
    / "contracts"
    / "research"
    / "radar-website-tool-compatibility-v1.json"
)
EQUIPMENT_MAP_PATH = (
    PROJECT_ROOT / "contracts" / "workflows" / "equipment-plugin-map.json"
)
TOOL_PERMISSION_PATH = (
    PROJECT_ROOT / "contracts" / "tools" / "tool-permission-contract.json"
)
REPORT_CONTRACT_PATH = PROJECT_ROOT / "contracts" / "reports" / "report-contract.json"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class RadarSourcePolicyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.bridge = load_module("radar_source_policy_bridge", BRIDGE_PATH)
        cls.runner = load_module("radar_source_policy_runner", RUNNER_PATH)
        cls.policy = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
        cls.compatibility = json.loads(
            COMPATIBILITY_PATH.read_text(encoding="utf-8")
        )
        cls.equipment_map = json.loads(
            EQUIPMENT_MAP_PATH.read_text(encoding="utf-8")
        )
        cls.tool_permission = json.loads(
            TOOL_PERMISSION_PATH.read_text(encoding="utf-8")
        )
        cls.report_contract = json.loads(
            REPORT_CONTRACT_PATH.read_text(encoding="utf-8")
        )

    @staticmethod
    def entry(url: str, **overrides) -> dict:
        row = {
            "toolName": (
                "Public Radar "
                + hashlib.sha256(url.encode("utf-8")).hexdigest()[:12]
            ),
            "toolKind": "indicator",
            "platform": "mt4",
            "category": "trend",
            "version": "unknown",
            "summaryTh": "ข้อมูลหน้าเว็บสาธารณะสำหรับตรวจต่อ",
            "sourceTitle": "Public source page",
            "sourceUrl": url,
            "publishedAt": None,
            "checkedAt": datetime.now(timezone.utc).isoformat(),
            "verificationStatus": "partially_verified",
            "availability": "public",
            "eaReadiness": "needs_clarification",
            "missingRules": ["compile และ backtest"],
            "sourceLimitations": ["อ่านเฉพาะ metadata หน้าเว็บ"],
            "screenshot": {
                "available": False,
                "status": "not_available",
                "attachmentId": None,
                "artifactRef": None,
            },
        }
        row.update(overrides)
        return row

    @staticmethod
    def evidence(urls: list[str]) -> list[dict]:
        return [
            {"label": f"Source {index}", "url": url, "note": "public page"}
            for index, url in enumerate(urls, start=1)
        ]

    def normalize(
        self,
        entries: list[dict],
        *,
        scheduled: bool,
        mission_started_at: datetime | None = None,
        existing_identities: tuple[set[str], set[str]] | None = None,
    ) -> tuple[list[dict] | None, list[str], list[dict]]:
        mission = {
            "id": "radar-policy-test",
            "startedAt": (
                mission_started_at
                or datetime.now(timezone.utc) - timedelta(minutes=1)
            ).isoformat(),
            "workflowContext": {},
        }
        urls = [str(item["sourceUrl"]) for item in entries]
        patches = [
            mock.patch.object(
                self.bridge,
                "_radar_complete_daily_batch_required",
                return_value=scheduled,
            ),
            mock.patch.object(
                self.bridge,
                "_radar_existing_catalog_fingerprints",
                return_value=set(),
            ),
            mock.patch.object(
                self.bridge,
                "_radar_existing_catalog_identities",
                return_value=(
                    existing_identities
                    if existing_identities is not None
                    else (set(), set())
                ),
            ),
        ]
        with patches[0], patches[1], patches[2]:
            return self.bridge._normalize_radar_contract_entries(
                mission,
                {},
                self.evidence(urls),
                entries,
            )

    def test_contract_declares_exact_five_rotating_primary_sources(self) -> None:
        rotation = self.policy["rotation"]
        primary = rotation["primarySources"]
        self.assertEqual(
            [item["id"] for item in primary],
            [
                "tradingfinder",
                "forex_station",
                "indicator_spot",
                "soehoe",
                "forexcracked",
            ],
        )
        self.assertEqual(rotation["fixedEpoch"], self.bridge.RADAR_FREE_SOURCE_ROTATION_EPOCH)
        self.assertEqual(
            [item[0] for item in self.bridge.RADAR_FREE_SOURCE_ROTATION],
            [item["id"] for item in primary],
        )
        selection = self.compatibility["sourceSelection"]
        self.assertEqual(
            selection["policyRef"],
            "contracts/research/radar-website-source-policy-v1.json",
        )
        self.assertEqual(selection["maximumMql5EntriesPerSixItemBatch"], 1)
        self.assertFalse(selection["scheduledPaidEntriesAllowed"])
        self.assertEqual(selection["attemptOrderEnforcement"], "prompt_bound")
        self.assertTrue(selection["resultGuardsBackendEnforced"])
        self.assertFalse(selection["sourceClassificationVerifiedByBackend"])
        self.assertTrue(selection["policyRelevantEntryDigestRequired"])
        self.assertTrue(selection["researchSheetRequiresValidDailyReservation"])
        equipment_policy = self.equipment_map["equipment"]["left_audit_crystals"][
            "sourcePolicy"
        ]
        self.assertEqual(equipment_policy["policyRef"], selection["policyRef"])
        self.assertEqual(equipment_policy["mql5FallbackMaximumPerSixItemBatch"], 1)
        self.assertEqual(equipment_policy["attemptOrderEnforcement"], "prompt_bound")
        self.assertTrue(equipment_policy["resultGuardsBackendEnforced"])
        self.assertFalse(equipment_policy["sourceClassificationVerifiedByBackend"])
        self.assertTrue(equipment_policy["policyRelevantEntryDigestRequired"])
        self.assertTrue(
            equipment_policy["researchSheetRequiresValidDailyReservation"]
        )
        tool_policy = next(
            item
            for item in self.tool_permission["tools"]
            if item["id"] == "discover_new_indicators"
        )
        self.assertEqual(tool_policy["sourcePolicyRef"], selection["policyRef"])
        self.assertEqual(tool_policy["mql5FallbackMaximumPerSixItemBatch"], 1)
        self.assertTrue(tool_policy["sourceResultGuardsBackendEnforced"])
        self.assertFalse(tool_policy["sourceClassificationVerifiedByBackend"])
        self.assertTrue(tool_policy["sourcePolicyRelevantEntryDigestRequired"])
        self.assertTrue(tool_policy["researchSheetRequiresValidDailyReservation"])
        for runtime_row, contract_row in zip(
            self.bridge.RADAR_FREE_SOURCE_ROTATION,
            primary,
        ):
            self.assertEqual(runtime_row[0], contract_row["id"])
            self.assertIn(runtime_row[1], contract_row["seedUrls"])
        self.assertEqual(
            self.policy["rotation"]["attemptOrderEnforcement"],
            "prompt_bound",
        )
        self.assertEqual(self.policy["resultGuard"]["enforcement"], "backend_fail_closed")
        self.assertFalse(
            self.policy["resultGuard"]["sourceClassificationVerifiedByBackend"]
        )
        self.assertFalse(
            self.policy["resultGuard"]["declaredPublicRestrictedAccessClaimsAllowed"]
        )
        self.assertTrue(
            self.policy["resultGuard"]["policyRelevantEntryDigestRequired"]
        )
        self.assertTrue(
            self.policy["resultGuard"]["researchSheetRequiresValidDailyReservation"]
        )
        self.assertTrue(
            self.policy["resultGuard"]["scheduledCheckedAtMustFollowMissionStart"]
        )
        self.assertEqual(
            self.policy["resultGuard"]["missionClockSkewSeconds"],
            self.bridge.RADAR_CHECKED_AT_CLOCK_SKEW_SECONDS,
        )
        self.assertFalse(
            self.policy["resultGuard"]["directArtifactQueryFlagsAllowed"]
        )

        reports = self.report_contract["typed_report_schemas"]
        self.assertNotIn("sourcePolicy", reports["trading_system_discovery_report"])
        self.assertEqual(
            reports["indicator_scout_report"]["sourcePolicy"]["policyRef"],
            selection["policyRef"],
        )
        self.assertFalse(
            reports["indicator_scout_report"]["sourcePolicy"][
                "sourceClassificationVerifiedByBackend"
            ]
        )
        self.assertTrue(
            reports["indicator_scout_report"]["sourcePolicy"][
                "policyRelevantEntryDigestRequired"
            ]
        )
        self.assertTrue(
            reports["indicator_scout_report"]["sourcePolicy"][
                "researchSheetRequiresValidDailyReservation"
            ]
        )

    def test_rotation_is_stable_per_day_and_cycles_all_five_sources(self) -> None:
        start = datetime(2026, 9, 7, 9, 0, tzinfo=timezone(timedelta(hours=7)))
        first = self.bridge._radar_rotated_free_sources(start)
        self.assertEqual(
            first,
            self.bridge._radar_rotated_free_sources(start.replace(hour=22)),
        )
        leading_sources = {
            self.bridge._radar_rotated_free_sources(start + timedelta(days=offset))[0][0]
            for offset in range(5)
        }
        self.assertEqual(
            leading_sources,
            {item[0] for item in self.bridge.RADAR_FREE_SOURCE_ROTATION},
        )

    def test_prompt_is_bound_to_rotation_date_and_keeps_all_safety_rules(self) -> None:
        prompt = self.bridge._workflow_prompt(
            "discover_new_indicators",
            {"maxItems": 6},
            None,
            None,
            radar_rotation_date="2026-09-07",
        )
        for marker in (
            "FREE-FIRST",
            "tradingfinder.com",
            "forex-station.com",
            "indicatorspot.com",
            "soehoe.id",
            "forexcracked.com",
            "github.com",
            "tradingview.com",
            "MQL5 เป็น fallback",
            "ไม่เกิน 1 รายการ",
            "ห้าม URL ต่อกัน",
            "ห้าม Sign in",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, prompt)
        self.assertLessEqual(len(prompt), 7900)

    def test_nested_absolute_url_and_direct_artifacts_fail_closed(self) -> None:
        concatenated = (
            "https://tradingfinder.com/https://forex-station.com/"
            "https://indicatorspot.com/"
        )
        self.assertIsNone(self.bridge._normalized_contract_public_url(concatenated))
        self.assertEqual(self.runner.normalize_web_evidence_url(concatenated), "")
        self.assertEqual(
            self.runner.normalize_trading_system_corrective_candidate_url(
                concatenated
            ),
            "",
        )
        for url in (
            "https://example.com/files/tool.ex5",
            "https://example.com/files/source.mqh",
            "https://example.com/files/package.tar.gz",
            "https://example.com/files/package.tgz",
            "https://example.com/attachments/tool.zip",
            "https://example.com/download/package",
            "https://example.com/download",
            "https://example.com/download?id=42",
            "https://example.com/download.php?id=42",
            "https://example.com/tool.php?action=download",
            "https://example.com/tool.zip/",
            "https://example.com/tool?download=1",
            "https://example.com/tool?download",
            "https://example.com/tool?attachment",
            "https://example.com/tool?download_file=42",
            "https://example.com/tool?file_download=42",
            "https://example.com/tool?get_file=42",
            "https://example.com/tool?getfile=42",
            "https://github.com/example/repo/blob/main/README.md?raw=1",
            "https://example.com/file.txt?dl=1",
            "https://example.com/tool?export=download",
            "https://example.com/tool?response-content-disposition=attachment",
            "https://example.com/tool?alt=media",
            "https://example.com/tool?file=tool.zip%3Fraw=1",
        ):
            with self.subTest(url=url):
                self.assertTrue(self.bridge._radar_source_url_is_direct_artifact(url))
                self.assertTrue(self.runner.radar_source_url_is_direct_artifact(url))

        normalized, errors, _audit = self.normalize(
            [self.entry("https://example.com/files/tool.ex5")],
            scheduled=False,
        )
        self.assertIsNone(normalized)
        self.assertIn("entry_1_direct_artifact_source_rejected", errors)

        canonical_query = (
            "https://example.com/article?canonical="
            "https%3A%2F%2Forigin.example%2Fitem"
        )
        self.assertIsNotNone(
            self.bridge._normalized_contract_public_url(canonical_query)
        )
        self.assertTrue(self.runner.normalize_web_evidence_url(canonical_query))

    def test_host_matching_is_exact_and_mql5_is_limited_to_one(self) -> None:
        self.assertEqual(
            self.bridge._radar_source_hostname("https://WWW.MQL5.COM:443/en/market"),
            "mql5.com",
        )
        self.assertEqual(
            self.bridge._radar_source_hostname("https://mql5.com.evil.example/item"),
            "mql5.com.evil.example",
        )
        self.assertTrue(
            self.bridge._radar_hostname_matches(
                "https://docs.mql5.com/item",
                self.bridge.RADAR_MQL5_HOSTS,
            )
        )
        self.assertFalse(
            self.bridge._radar_hostname_matches(
                "https://mql5.com.evil.example/item",
                self.bridge.RADAR_MQL5_HOSTS,
            )
        )
        urls = [
            "https://www.mql5.com/en/market/product/100001",
            "https://mql5.com/en/market/product/100002",
            "https://tradingfinder.com/products/indicators/mt4/item-a",
            "https://forex-station.com/thread-a.html",
            "https://indicatorspot.com/indicators/item-a/",
            "https://github.com/example/public-mt4-tool",
        ]
        normalized, errors, _audit = self.normalize(
            [self.entry(url) for url in urls],
            scheduled=False,
        )
        self.assertIsNone(normalized)
        self.assertEqual(errors, ["mql5_fallback_limit_exceeded"])
        with self.assertRaisesRegex(ValueError, "free-first source policy"):
            self.runner.validate_radar_required_open_urls(urls)
        self.assertIsNone(self.bridge._radar_evidence_candidate_block(urls))

    def test_product_fingerprint_is_url_independent_and_normalized(self) -> None:
        first = self.bridge._radar_entry_fingerprint(
            "https://publisher-a.example/quantum-trend",
            "Quantum-Trend Pro v1.0",
            "MetaTrader 4",
            "v1.0",
        )
        mirrored = self.bridge._radar_entry_fingerprint(
            "https://publisher-b.example/reviews/quantum-trend",
            "  QUANTUM trend pro  ",
            "mql4",
            "Version 1.0",
        )
        self.assertEqual(first, mirrored)
        self.assertNotEqual(
            first,
            self.bridge._radar_entry_fingerprint(
                "https://publisher-c.example/quantum-trend-v2",
                "Quantum Trend Pro",
                "mt4",
                "2.0",
            ),
        )
        self.assertNotEqual(
            first,
            self.bridge._radar_entry_fingerprint(
                "https://publisher-c.example/quantum-trend",
                "Quantum Trend Pro",
                "mt5",
                "1.0",
            ),
        )

    def test_scheduled_batch_rejects_six_mirror_urls_as_one_product(self) -> None:
        rows = []
        for index in range(1, 7):
            rows.append(self.entry(
                f"https://mirror-{index}.example/quantum-trend",
                toolName=(
                    "Quantum-Trend Pro v1.0"
                    if index % 2
                    else "  QUANTUM trend pro  "
                ),
                platform="MetaTrader 4" if index % 2 else "mt4",
                version="v1.0" if index % 2 else "Version 1.0",
            ))
        normalized, errors, _audit = self.normalize(rows, scheduled=True)
        self.assertIsNone(normalized)
        self.assertEqual(
            errors,
            [
                f"entry_{index}_duplicate_product_in_batch"
                for index in range(2, 7)
            ],
        )
        self.assertEqual(
            self.bridge._radar_retryable_dedup_output_progress(
                {
                    "applicable": True,
                    "valid": False,
                    "failureCode": "radar_output_contract_invalid",
                    "procedureId": self.bridge.RADAR_WORKFLOW_PROCEDURE_ID,
                    "sourceUrlCount": 6,
                    "entryErrors": errors,
                },
                [row["sourceUrl"] for row in rows],
            ),
            1,
        )

    def test_scheduled_history_rejects_product_rediscovered_on_new_url(self) -> None:
        rows = [
            self.entry(
                f"https://publisher-{index}.example/tool-{index}",
                toolName=f"New Radar Product {index}",
                platform="mt5",
                version="1.0",
            )
            for index in range(1, 7)
        ]
        historical_fingerprint = self.bridge._radar_entry_fingerprint(
            "https://old-publisher.example/tool-1",
            rows[0]["toolName"],
            rows[0]["platform"],
            rows[0]["version"],
        )
        normalized, errors, _audit = self.normalize(
            rows,
            scheduled=True,
            existing_identities=({historical_fingerprint}, set()),
        )
        self.assertIsNone(normalized)
        self.assertEqual(errors, ["entry_1_historical_product_duplicate"])

    def test_legacy_sheet_row_is_reindexed_by_product_identity_fields(self) -> None:
        expected = self.bridge._radar_entry_fingerprint(
            "https://new-mirror.example/quantum-trend",
            "Quantum Trend Pro",
            "mt4",
            "1.0",
        )
        legacy_row = {
            "duplicate_fingerprint": "a" * 24,
            "tool_name": "QUANTUM-trend pro",
            "platform": "mql4",
            "version": "Version 1.0",
            "normalized_source_url": "https://old.example/quantum-trend",
            "first_mission_id": "mission-old",
            "latest_mission_id": "mission-old",
        }
        with (
            mock.patch.object(
                self.bridge,
                "RESEARCH_SHEET_AUTO_SYNC_ENABLED",
                True,
            ),
            mock.patch.object(
                self.bridge,
                "_research_sheet_cached_rows",
                return_value=[legacy_row],
            ),
            mock.patch.object(
                self.bridge,
                "load_runtime_reports",
                return_value=[],
            ),
        ):
            fingerprints, source_keys = (
                self.bridge._radar_existing_catalog_identities()
            )
        self.assertIn("a" * 24, fingerprints)
        self.assertIn(expected, fingerprints)
        self.assertIn("old.example/quantum-trend", source_keys)

    def test_scheduled_batch_rejects_paid_unknown_and_insufficient_rows(self) -> None:
        urls = [
            "https://tradingfinder.com/products/indicators/mt4/item-a",
            "https://forex-station.com/thread-a.html",
            "https://indicatorspot.com/indicators/item-a/",
            "https://github.com/example/public-mt4-tool",
            "https://www.tradingview.com/script/PublicTool/",
            "https://example.org/public-indicator",
        ]
        paid = [self.entry(url) for url in urls]
        paid[2]["availability"] = "commercial"
        normalized, errors, _audit = self.normalize(paid, scheduled=True)
        self.assertIsNone(normalized)
        self.assertEqual(errors, ["daily_batch_requires_free_public_entries"])

        weak = [self.entry(url) for url in urls]
        weak[3]["verificationStatus"] = "insufficient_evidence"
        normalized, errors, _audit = self.normalize(weak, scheduled=True)
        self.assertIsNone(normalized)
        self.assertEqual(errors, ["daily_batch_requires_verified_public_entries"])

        unknown = [self.entry(url) for url in urls]
        unknown[0]["availability"] = "unknown"
        normalized, errors, _audit = self.normalize(unknown, scheduled=True)
        self.assertIsNone(normalized)
        self.assertEqual(errors, ["daily_batch_requires_free_public_entries"])

        unverified = [self.entry(url) for url in urls]
        unverified[0]["verificationStatus"] = "unverified"
        normalized, errors, _audit = self.normalize(unverified, scheduled=True)
        self.assertIsNone(normalized)
        self.assertEqual(errors, ["daily_batch_requires_verified_public_entries"])

    def test_metadata_only_sources_are_usable_but_never_ea_ready(self) -> None:
        safe = self.entry(
            "https://soehoe.id/forums/indicators-dan-tools.31/",
            eaReadiness="needs_clarification",
            availability="public",
            sourceLimitations=["metadata only; ตรวจ licence ต่อ"],
        )
        normalized, errors, _audit = self.normalize([safe], scheduled=False)
        self.assertEqual(errors, [])
        self.assertEqual(normalized[0]["eaReadiness"], "needs_clarification")

        unsafe = dict(safe, eaReadiness="ready")
        normalized, errors, _audit = self.normalize([unsafe], scheduled=False)
        self.assertIsNone(normalized)
        self.assertIn("entry_1_metadata_only_source_claim_invalid", errors)

        prohibited = self.entry(
            "https://www.forexcracked.com/forex-ea/cracked-gold-ea/",
            toolName="Premium Gold EA",
            sourceTitle="Premium Gold EA metadata",
            sourceLimitations=["Page appears to redistribute an unlicensed build"],
        )
        normalized, errors, _audit = self.normalize([prohibited], scheduled=False)
        self.assertIsNone(normalized)
        self.assertIn("entry_1_prohibited_distribution_claim", errors)

        restricted = self.entry(
            "https://indicatorspot.com/indicators/premium-gold-indicator/",
            toolName="Premium paid indicator $99",
            sourceTitle="Gold indicator",
            sourceLimitations=["Paid license required"],
            availability="public",
        )
        normalized, errors, _audit = self.normalize([restricted], scheduled=False)
        self.assertIsNone(normalized)
        self.assertIn("entry_1_restricted_access_claim", errors)

        for restricted_title in (
            "Members only access",
            "paid_version",
            "premium_tool",
            "commercial_license",
            "invite_only",
            "members_only",
            "Password-protected download",
            "Protected content requires login",
        ):
            with self.subTest(restricted_title=restricted_title):
                restricted = self.entry(
                    "https://indicatorspot.com/indicators/restricted-item/",
                    sourceTitle=restricted_title,
                    availability="public",
                )
                normalized, errors, _audit = self.normalize(
                    [restricted],
                    scheduled=False,
                )
                self.assertIsNone(normalized)
                self.assertIn("entry_1_restricted_access_claim", errors)

        for public_signal_name in (
            "Buy/Sell Arrow Indicator",
            "BUY arrow with SELL confirmation",
            "Protected Profit Indicator",
        ):
            with self.subTest(public_signal_name=public_signal_name):
                public_signal = self.entry(
                    "https://indicatorspot.com/indicators/buy-sell-arrow/",
                    toolName=public_signal_name,
                    sourceTitle=public_signal_name,
                    summaryTh="แสดง BUY arrow และ SELL arrow จากเงื่อนไขอินดิเคเตอร์",
                    availability="public",
                )
                normalized, errors, _audit = self.normalize(
                    [public_signal],
                    scheduled=False,
                )
                self.assertEqual(errors, [])
                self.assertEqual(normalized[0]["toolName"], public_signal_name)

        for prohibited_marker in (
            "BlackDiamond Indicator (Unloked)",
            "Gold EA Crak",
            "Decompiled source",
            "cracked_v1",
            "unlocked_build",
            "unlicensed_copy",
            "download_only",
        ):
            with self.subTest(prohibited_marker=prohibited_marker):
                unsafe_marker = self.entry(
                    "https://soehoe.id/forums/indicators-dan-tools.31/",
                    sourceTitle=prohibited_marker,
                )
                normalized, errors, _audit = self.normalize(
                    [unsafe_marker],
                    scheduled=False,
                )
                self.assertIsNone(normalized)
                self.assertIn("entry_1_prohibited_distribution_claim", errors)

        hidden_prohibited = self.entry(
            "https://www.forexcracked.com/forex-indicator/item/",
            version="Cracked",
        )
        normalized, errors, _audit = self.normalize(
            [hidden_prohibited],
            scheduled=False,
        )
        self.assertIsNone(normalized)
        self.assertIn("entry_1_prohibited_distribution_claim", errors)

        hidden_restricted = self.entry(
            "https://indicatorspot.com/indicators/item/",
            category="paid",
            availability="public",
        )
        normalized, errors, _audit = self.normalize(
            [hidden_restricted],
            scheduled=False,
        )
        self.assertIsNone(normalized)
        self.assertIn("entry_1_restricted_access_claim", errors)

        missing_rule_claim = self.entry(
            "https://soehoe.id/forums/indicators-dan-tools.31/",
            missingRules=["Need to verify unlicensed distribution"],
        )
        normalized, errors, _audit = self.normalize(
            [missing_rule_claim],
            scheduled=False,
        )
        self.assertIsNone(normalized)
        self.assertIn("entry_1_prohibited_distribution_claim", errors)

    def test_scheduled_batch_rejects_checked_at_before_mission_start(self) -> None:
        mission_started_at = datetime.now(timezone.utc) - timedelta(minutes=1)
        stale_checked_at = mission_started_at - timedelta(minutes=6)
        urls = [f"https://example.org/freshness-{index}" for index in range(1, 7)]
        rows = [
            self.entry(url, checkedAt=stale_checked_at.isoformat())
            for url in urls
        ]
        normalized, errors, _audit = self.normalize(
            rows,
            scheduled=True,
            mission_started_at=mission_started_at,
        )
        self.assertIsNone(normalized)
        self.assertEqual(
            errors,
            [f"entry_{index}_checked_at_stale" for index in range(1, 7)],
        )
        self.assertTrue(
            self.bridge._radar_retryable_source_policy_output_failure(
                {
                    "applicable": True,
                    "valid": False,
                    "failureCode": "radar_output_contract_invalid",
                    "procedureId": self.bridge.RADAR_WORKFLOW_PROCEDURE_ID,
                    "sourceUrlCount": 6,
                    "entryErrors": errors,
                },
                urls,
            )
        )

    def test_sheet_ready_gate_rechecks_free_source_policy(self) -> None:
        urls = [
            "https://tradingfinder.com/products/indicators/mt4/item-a",
            "https://forex-station.com/thread-a.html",
            "https://indicatorspot.com/indicators/item-a/",
            "https://github.com/example/public-mt4-tool",
            "https://www.tradingview.com/script/PublicTool/",
            "https://soehoe.id/forums/indicators-dan-tools.31/",
        ]
        rows = []
        for index, url in enumerate(urls, start=1):
            row = self.entry(url)
            fingerprint = self.bridge._radar_entry_fingerprint(
                url,
                row["toolName"],
                row["platform"],
                row["version"],
            )
            row.update({
                "recordId": f"radar-ready-{index}",
                "duplicateFingerprint": fingerprint,
                "duplicateStatus": "unique",
                "duplicateScope": "none",
            })
            rows.append(row)
        report = {
            "id": "report-radar-ready-policy",
            "type": "indicator_scout_report",
            "linkedMissionId": "mission-radar-ready-policy",
            "linkedPropId": "left_audit_crystals",
            "status": "ready",
            "evidence": self.evidence(urls),
            "workflowContext": {
                "schemaVersion": "dashboard-workflow-lineage-v1",
                "propId": "left_audit_crystals",
                "actionId": "discover_new_indicators",
                "inputDigest": "a" * 64,
                "inputs": {"maxItems": 6},
                "triggerSource": "schedule",
                "executionReservation": {"bangkokDate": "2026-09-07"},
                "submittedAt": "2026-09-07T09:00:00+07:00",
            }
        }
        report["workflowContext"]["executionReservation"].update({
            "settingsKey": "indicatorScoutSchedule",
            "slotKey": "indicatorScoutSchedule:2026-09-07:0900",
            "maximumRunsPerDay": 1,
            "source": "schedule",
        })
        policy_receipt = self.bridge._radar_source_policy_receipt(report, rows)
        report["metrics"] = {
            "entries": rows,
            "workflowOutput": {
                "applicable": True,
                "valid": True,
                "failureCode": None,
                "procedureId": self.bridge.RADAR_WORKFLOW_PROCEDURE_ID,
                "providedFields": ["entries"],
                "missingFields": [],
                "missingEvidenceKinds": [],
                "entryErrors": [],
                "oversizedFields": [],
                "values": {"entries": json.dumps(rows, ensure_ascii=False)},
                "radarSourcePolicy": policy_receipt,
            }
        }
        projected_rows = self.bridge._radar_report_entries(report)
        self.assertEqual(
            self.bridge._radar_source_policy_entries_digest(projected_rows),
            policy_receipt["policyEntriesDigestSha256"],
        )
        self.assertTrue(
            self.bridge._radar_verified_ready_batch(report, projected_rows)
        )
        with mock.patch.object(
            self.bridge,
            "_radar_existing_catalog_identities",
            return_value=(set(), set()),
        ):
            self.assertEqual(len(self.bridge._research_sheet_radar_rows(report)), 6)

        historical_product = projected_rows[0]["duplicateFingerprint"]
        with mock.patch.object(
            self.bridge,
            "_radar_existing_catalog_identities",
            return_value=({historical_product}, set()),
        ):
            self.assertEqual(self.bridge._research_sheet_radar_rows(report), [])

        mirror_report = json.loads(json.dumps(report, ensure_ascii=False))
        mirror_rows = mirror_report["metrics"]["entries"]
        for index, row in enumerate(mirror_rows, start=1):
            row["toolName"] = (
                "Quantum-Trend Pro v1.0"
                if index % 2
                else "QUANTUM trend pro"
            )
            row["platform"] = "mt4"
            row["version"] = "v1.0" if index % 2 else "Version 1.0"
            row["duplicateFingerprint"] = self.bridge._radar_entry_fingerprint(
                row["sourceUrl"],
                row["toolName"],
                row["platform"],
                row["version"],
            )
            row["duplicateStatus"] = "unique"
            row["duplicateScope"] = "none"
        mirror_output = mirror_report["metrics"]["workflowOutput"]
        mirror_output["values"]["entries"] = json.dumps(
            mirror_rows,
            ensure_ascii=False,
        )
        mirror_output["radarSourcePolicy"] = (
            self.bridge._radar_source_policy_receipt(
                mirror_report,
                mirror_rows,
            )
        )
        projected_mirror_rows = self.bridge._radar_report_entries(mirror_report)
        self.assertFalse(
            self.bridge._radar_verified_ready_batch(
                mirror_report,
                projected_mirror_rows,
            )
        )
        self.assertEqual(
            self.bridge._research_sheet_radar_rows(mirror_report),
            [],
        )

        legacy_report = json.loads(json.dumps(report, ensure_ascii=False))
        legacy_report["metrics"]["workflowOutput"].pop("radarSourcePolicy")
        self.assertFalse(
            self.bridge._radar_verified_ready_batch(legacy_report, projected_rows)
        )
        paid_rows = json.loads(json.dumps(projected_rows, ensure_ascii=False))
        paid_rows[0]["availability"] = "commercial"
        self.assertFalse(
            self.bridge._radar_verified_ready_batch(report, paid_rows)
        )
        tampered_rows = json.loads(json.dumps(projected_rows, ensure_ascii=False))
        tampered_rows[-1]["toolName"] = "Cracked paid EA"
        tampered_rows[-1]["eaReadiness"] = "ready"
        tampered_rows[-1]["sourceLimitations"] = []
        self.assertFalse(
            self.bridge._radar_verified_ready_batch(report, tampered_rows)
        )

        forged_report = json.loads(json.dumps(report, ensure_ascii=False))
        forged_report["metrics"]["entries"] = tampered_rows
        forged_output = forged_report["metrics"]["workflowOutput"]
        forged_output["values"]["entries"] = json.dumps(
            tampered_rows,
            ensure_ascii=False,
        )
        forged_output["radarSourcePolicy"] = (
            self.bridge._radar_source_policy_receipt(
                forged_report,
                tampered_rows,
            )
        )
        self.assertFalse(
            self.bridge._radar_verified_ready_batch(
                forged_report,
                tampered_rows,
            )
        )

        stale_report = json.loads(json.dumps(report, ensure_ascii=False))
        stale_rows = stale_report["metrics"]["entries"]
        for row in stale_rows:
            row["checkedAt"] = "2020-01-01T00:00:00Z"
        stale_output = stale_report["metrics"]["workflowOutput"]
        stale_output["values"]["entries"] = json.dumps(
            stale_rows,
            ensure_ascii=False,
        )
        stale_output["radarSourcePolicy"] = (
            self.bridge._radar_source_policy_receipt(
                stale_report,
                stale_rows,
            )
        )
        projected_stale_rows = self.bridge._radar_report_entries(stale_report)
        self.assertFalse(
            self.bridge._radar_verified_ready_batch(
                stale_report,
                projected_stale_rows,
            )
        )
        self.assertEqual(
            self.bridge._research_sheet_radar_rows(stale_report),
            [],
        )

        downgraded_report = json.loads(json.dumps(report, ensure_ascii=False))
        downgraded_report["workflowContext"] = {}
        downgraded_report["metrics"]["entries"] = tampered_rows
        self.assertFalse(
            self.bridge._radar_verified_ready_batch(
                downgraded_report,
                tampered_rows,
            )
        )
        self.assertEqual(
            self.bridge._research_sheet_radar_rows(downgraded_report),
            [],
        )

    def test_mixed_policy_and_duplicate_errors_receive_fresh_repair(self) -> None:
        urls = [f"https://example.org/tool-{index}" for index in range(1, 7)]
        receipt = {
            "applicable": True,
            "valid": False,
            "failureCode": "radar_output_contract_invalid",
            "procedureId": self.bridge.RADAR_WORKFLOW_PROCEDURE_ID,
            "sourceUrlCount": 6,
            "entryErrors": [
                "entry_1_restricted_access_claim",
                "entry_2_historical_source_duplicate",
            ],
        }
        self.assertTrue(
            self.bridge._radar_retryable_source_policy_output_failure(
                receipt,
                urls,
            )
        )
        receipt["entryErrors"] = ["entry_2_historical_source_duplicate"]
        self.assertFalse(
            self.bridge._radar_retryable_source_policy_output_failure(
                receipt,
                urls,
            )
        )

    def test_backend_source_policy_receipt_is_reservation_bound(self) -> None:
        rows = [
            self.entry("https://tradingfinder.com/products/indicators/item-a/"),
            self.entry("https://github.com/example/public-mt4-tool"),
            self.entry("https://docs.mql5.com/public-item"),
        ]
        receipt = self.bridge._radar_source_policy_receipt(
            {
                "workflowContext": {
                    "executionReservation": {"bangkokDate": "2026-09-07"},
                    "submittedAt": "2026-09-08T01:00:00+07:00",
                }
            },
            rows,
        )
        self.assertEqual(receipt["rotationDate"], "2026-09-07")
        self.assertEqual(receipt["mql5EntryCount"], 1)
        self.assertEqual(receipt["primaryEntryCount"], 1)
        self.assertEqual(receipt["supplementalEntryCount"], 1)
        self.assertEqual(receipt["directArtifactCount"], 0)
        self.assertRegex(receipt["policyEntriesDigestSha256"], r"^[0-9a-f]{64}$")
        self.assertEqual(
            receipt["policyEntriesDigestSha256"],
            self.bridge._radar_source_policy_entries_digest(rows),
        )
        enriched_rows = json.loads(json.dumps(rows, ensure_ascii=False))
        enriched_rows[0]["screenshot"] = {
            "available": True,
            "status": "verified_publisher_image",
            "attachmentId": "attachment-one",
        }
        self.assertEqual(
            self.bridge._radar_source_policy_entries_digest(enriched_rows),
            receipt["policyEntriesDigestSha256"],
        )
        enriched_rows[0]["toolName"] = "Changed after receipt"
        self.assertNotEqual(
            self.bridge._radar_source_policy_entries_digest(enriched_rows),
            receipt["policyEntriesDigestSha256"],
        )
        self.assertFalse(receipt["attemptOrderVerified"])
        self.assertEqual(receipt["attemptOrderEnforcement"], "prompt_bound")
        self.assertTrue(receipt["resultGuardsBackendEnforced"])
        self.assertFalse(receipt["sourceClassificationVerifiedByBackend"])
        self.assertTrue(receipt["backendComputed"])

    def test_metadata_only_image_enrichment_never_calls_network_capture(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            report_id = "report-source-policy-image"
            report_dir = Path(temp_dir)
            report_dir.mkdir(parents=True, exist_ok=True)
            report = {
                "id": report_id,
                "type": "indicator_scout_report",
                "status": "ready",
                "updatedAt": "2026-09-07T09:00:00+07:00",
                "artifacts": [],
                "metrics": {
                    "entries": [
                        {
                            "recordId": "record-one",
                            "sourceUrl": "https://soehoe.id/forums/indicators-dan-tools.31/",
                            "checkedAt": "2026-09-07T09:00:00+07:00",
                        }
                    ]
                },
            }
            (report_dir / f"{report_id}.json").write_text(
                json.dumps(report),
                encoding="utf-8",
            )
            reasons: list[str] = []

            def adapter(payload, *, capture_entry, **_kwargs):
                outcome = capture_entry(payload["metrics"]["entries"][0])
                reasons.append(outcome.reason_code)
                return SimpleNamespace(
                    report=payload,
                    diagnostics=[],
                    attached_count=0,
                )

            with (
                mock.patch.object(self.bridge, "RUNTIME_REPORTS_DIR", report_dir),
                mock.patch.object(
                    self.bridge,
                    "enrich_radar_report_with_publisher_images",
                    side_effect=adapter,
                ),
                mock.patch.object(self.bridge, "capture_publisher_og_image") as capture,
                mock.patch.object(self.bridge, "create_report", return_value=report),
                mock.patch.object(
                    self.bridge,
                    "_refresh_completed_radar_batch_report_digest",
                ),
                mock.patch.object(self.bridge, "append_audit"),
            ):
                self.bridge._run_radar_publisher_image_enrichment(report_id)

            capture.assert_not_called()
            self.assertEqual(reasons, ["source_policy_metadata_only"])


if __name__ == "__main__":
    unittest.main()
