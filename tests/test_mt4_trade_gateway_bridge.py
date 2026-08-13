from __future__ import annotations

import importlib.util
import json
import tempfile
import time
import unittest
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BRIDGE_PATH = PROJECT_ROOT / "backend" / "local-runner" / "bridge_server.py"


def load_bridge():
    spec = importlib.util.spec_from_file_location(
        "metafx_bridge_trade_gateway_tests",
        BRIDGE_PATH,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load bridge module")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class Mt4TradeGatewayBridgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.bridge = load_bridge()

    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.bridge.RUNTIME_DIR = self.root / "runtime"
        self.bridge.AUDIT_PATH = self.bridge.RUNTIME_DIR / "bridge-audit.jsonl"
        self.bridge.METATRADER_COMMON_FILES_DIR = self.root / "common"
        self.bridge.MT4_TRADE_GATEWAY_MODULE = None
        self.bridge.MT4_TRADE_GATEWAY_REJECTED_ACK_EVENTS.clear()
        self.candidate = {
            "candidateId": "mtc-test-channel",
            "platform": "mt4",
            "available": True,
            "ordinal": 1,
            "runningState": "platform_running_detected",
        }

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_snapshot_symbol_boundary_accepts_hash_but_not_plus_suffix(self) -> None:
        self.assertEqual(self.bridge._safe_snapshot_symbol("EURUSD#"), "EURUSD#")
        self.assertIsNone(self.bridge._safe_snapshot_symbol("EURUSD+"))

    def status_path(self) -> Path:
        return (
            self.bridge.METATRADER_COMMON_FILES_DIR
            / "MetafxHQ"
            / self.candidate["candidateId"]
            / "trade-gateway"
            / "status.json"
        )

    def init_status_path(self) -> Path:
        return self.status_path().with_name("init-status.json")

    def signing_key_id(self) -> str:
        with self.bridge.MT4_TRADE_GATEWAY_LOCK:
            metadata = self.bridge._mt4_trade_gateway_instance().ensure_signing_key(
                self.candidate["candidateId"]
            )
        self.assertTrue(metadata["ok"])
        self.assertEqual(metadata["algorithm"], "HMAC-SHA256")
        self.assertEqual(
            set(metadata),
            {
                "ok",
                "channelId",
                "keyId",
                "algorithm",
                "envelopeSchemaVersion",
                "created",
            },
        )
        return str(metadata["keyId"])

    def write_ea_status(self, **overrides) -> dict:
        payload = {
            "schemaVersion": "metafx-hq-mt4-status-v5",
            "channelId": self.candidate["candidateId"],
            "profile": "special",
            "mode": "shadow",
            "demoAccount": True,
            "accountMode": "demo",
            "liveArmed": False,
            "fixedLot": 0.03,
            "symbol": "XAUUSD",
            "timeframe": "M5",
            "observedAt": int(time.time()),
            "autoTradingAllowed": False,
            "tradeAllowed": False,
            "killSwitchActive": False,
            "commandSchemaVersion": "metafx-hq-mt4-command-v2",
            "ackSchemaVersion": "metafx-hq-mt4-ack-v3",
            "signedCommandVerificationAvailable": True,
            "activeSigningKeyId": self.signing_key_id(),
            "signingKeyPinned": True,
            "signatureAlgorithm": "HMAC-SHA256",
            "lastSignatureVerificationStatus": "NOT_CHECKED",
            "executionGuardReady": True,
            "executionGuardReason": "READY",
            "portfolioPolicyStatus": "ready",
            "portfolioPolicyDigest": "a" * 64,
            "portfolioGuardScope": "MANAGED_MAGIC_NUMBERS_ACCOUNT_WIDE",
            "managedMagicNumbers": "4186001",
            "allowedSymbols": "XAUUSD",
            "allowedTimeframes": "M5,M15,M30,H1,H4,D1,W1,MN1",
            "concurrencyBoundary": "same_windows_user_file_common",
            "crossVpsDistributedLock": False,
            "maxManagedPositions": 1,
            "currentManagedPositions": 0,
            "maxManagedLots": 0.10,
            "currentManagedLots": 0.0,
            "maxTradesToday": 6,
            "currentTradesToday": 0,
            "maxLossPerTradePercent": 1.0,
            "maxDailyLossPercent": 3.0,
            "managedDailyPnl": 0.0,
            "maxAccountEquityDrawdownPercent": 10.0,
            "currentAccountEquityDrawdownPercent": 0.0,
            "minRewardRiskRatio": 1.0,
            "minProjectedMarginLevelPercent": 300.0,
            "currentMarginLevelPercent": 1000.0,
            "maxSnapshotAgeSeconds": 300,
            "maxSignalDriftPoints": 100,
            "maxQuoteAgeSeconds": 30,
        }
        payload.update(overrides)
        path = self.status_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload), encoding="ascii")
        return payload

    def write_ea_init_status(self, **overrides) -> dict:
        payload = {
            "schemaVersion": "metafx-hq-mt4-init-status-v1",
            "eaVersion": "2.13",
            "channelId": self.candidate["candidateId"],
            "profile": "special",
            "gatewayMode": "demo",
            "accountMode": "demo",
            "liveArmed": False,
            "severity": "error",
            "stage": "chart",
            "reasonCode": "SYMBOL_OR_TIMEFRAME_NOT_ALLOWED",
            "warningCode": "",
            "returnCode": 2,
            "observedAt": int(time.time()),
        }
        payload.update(overrides)
        path = self.init_status_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload), encoding="ascii")
        return payload

    def parent(self, *, timeframe: str = "M5") -> dict:
        return {
            "id": "mission-council-test-01",
            "analysisContext": {
                "kind": "ai_trade_council_parent",
                "snapshotId": "a" * 64,
                "referencePrice": 100.0,
                "snapshotObservedAt": datetime.now(timezone.utc).isoformat(),
                "roundDeadlineAt": (
                    datetime.now(timezone.utc) + timedelta(minutes=4)
                ).isoformat(),
                "closedBarIdentity": {
                    "candidateId": self.candidate["candidateId"],
                    "streamKey": self.bridge.payload_digest(
                        self.candidate["candidateId"],
                        "XAUUSD",
                        timeframe,
                    ),
                    "symbol": "XAUUSD",
                    "timeframe": timeframe,
                    "closedBarTime": 1_785_445_200,
                },
            },
        }

    @staticmethod
    def consensus() -> dict:
        return {
            "schemaVersion": "ai-trade-council-consensus-v2",
            "snapshotId": "a" * 64,
            "validUntilBarTime": int(time.time()) + 3_600,
            "ready": True,
            "decision": "BUY",
            "unanimous": True,
            "voteCount": 3,
            "qualityGate": {
                "passed": True,
                "marketState": "verified_open",
                "executionEligibility": {
                    "shadow": True,
                    "demo": True,
                    "live": True,
                },
            },
            "tradePlan": {
                "available": True,
                "direction": "BUY",
                "stopLossPrice": 95.0,
                "takeProfitPrice": 110.0,
                "lotPolicy": "ea_fixed_lot_only",
                "aiLotAllowed": False,
            },
        }

    @contextmanager
    def selected_candidate(self):
        selection_token = {
            "candidateId": self.candidate["candidateId"],
            "selectionRevision": 1,
        }
        with mock.patch.object(
            self.bridge,
            "_selected_metatrader_candidate_record",
            return_value=dict(self.candidate),
        ), mock.patch.object(
            self.bridge,
            "_metatrader_selection_token",
            return_value=selection_token,
        ):
            yield

    def test_gateway_status_reads_fixed_lot_as_ea_owned_read_only_state(self) -> None:
        self.write_ea_status(fixedLot=0.07)
        with self.selected_candidate():
            status = self.bridge.mt4_trade_gateway_status_read_model()

        self.assertTrue(status["connected"])
        self.assertEqual(status["mode"], "shadow")
        self.assertEqual(status["fixedLot"], 0.07)
        self.assertEqual(status["fixedLotSource"], "ea_input_read_only")
        self.assertFalse(status["aiCanSetLotOrRisk"])
        self.assertTrue(status["shadowValidationAvailable"])
        self.assertFalse(status["demoOrderExecutionAvailable"])
        self.assertFalse(status["liveOrderExecutionAvailable"])

    def test_gateway_status_exposes_sanitized_on_init_error_without_replacing_status(self) -> None:
        self.write_ea_init_status()
        with self.selected_candidate():
            status = self.bridge.mt4_trade_gateway_status_read_model()

        self.assertFalse(status["connected"])
        self.assertEqual(status["status"], "awaiting_ea")
        init_status = status["initStatus"]
        self.assertTrue(init_status["available"])
        self.assertEqual(init_status["sourceSchemaVersion"], "metafx-hq-mt4-init-status-v1")
        self.assertEqual(init_status["eaVersion"], "2.13")
        self.assertEqual(init_status["severity"], "error")
        self.assertEqual(init_status["stage"], "chart")
        self.assertEqual(init_status["reasonCode"], "SYMBOL_OR_TIMEFRAME_NOT_ALLOWED")
        self.assertNotIn("channelId", init_status)
        self.assertNotIn("profile", init_status)
        self.assertIn(
            "คู่เงินหรือ Timeframe ของกราฟไม่อยู่ในรายการที่อนุญาต",
            self.bridge._mt4_trade_gateway_init_status_message_th(init_status),
        )

    def test_gateway_status_rejects_init_status_with_unknown_secret_field(self) -> None:
        self.write_ea_init_status(brokerPassword="must-not-leak")
        with self.selected_candidate():
            status = self.bridge.mt4_trade_gateway_status_read_model()

        init_status = status["initStatus"]
        self.assertFalse(init_status["available"])
        self.assertEqual(init_status["readReasonCode"], "gateway_init_status_schema_invalid")
        self.assertNotIn("must-not-leak", json.dumps(status))

    def test_fresh_portfolio_policy_mismatch_is_exposed_without_stale_status(self) -> None:
        self.write_ea_init_status(
            stage="portfolio_policy",
            reasonCode="PORTFOLIO_POLICY_MISMATCH",
        )
        with self.selected_candidate():
            status = self.bridge.mt4_trade_gateway_status_read_model()

        self.assertFalse(status["connected"])
        self.assertEqual(status["portfolioPolicyStatus"], "mismatch")
        self.assertIsNone(status["portfolioPolicyDigest"])
        self.assertEqual(
            status["initStatus"]["reasonCode"],
            "PORTFOLIO_POLICY_MISMATCH",
        )

    def test_stale_init_error_never_replaces_fresh_live_gateway_status(self) -> None:
        self.write_ea_init_status(observedAt=int(time.time()) - (2 * 24 * 60 * 60))
        self.write_ea_status()
        with self.selected_candidate():
            status = self.bridge.mt4_trade_gateway_status_read_model()

        self.assertTrue(status["connected"])
        self.assertEqual(status["status"], "shadow")
        self.assertEqual(status["reasonCode"], "ready")
        init_status = status["initStatus"]
        self.assertTrue(init_status["available"])
        self.assertTrue(init_status["stale"])
        self.assertTrue(init_status["supersededByLiveStatus"])
        self.assertEqual(
            self.bridge._mt4_trade_gateway_init_status_message_th(init_status),
            "",
        )

    def test_successful_init_can_surface_latest_non_blocking_warning(self) -> None:
        self.write_ea_init_status(
            severity="info",
            stage="ready",
            reasonCode="INIT_SUCCEEDED",
            warningCode="OPTIONAL_SIGNING_KEY_PIN_MISMATCH_IGNORED",
            returnCode=0,
        )
        self.write_ea_status()
        with self.selected_candidate():
            status = self.bridge.mt4_trade_gateway_status_read_model()

        self.assertTrue(status["connected"])
        self.assertEqual(status["status"], "shadow")
        self.assertIn(
            "EA เริ่มทำงานแล้ว แต่มีคำเตือน",
            self.bridge._mt4_trade_gateway_init_status_message_th(status["initStatus"]),
        )

    def test_gateway_status_exposes_v5_portfolio_policy_and_execution_state(self) -> None:
        self.write_ea_status(
            eaVersion="2.12",
            mode="demo",
            autoTradingAllowed=True,
            tradeAllowed=True,
            currentManagedPositions=1,
            currentManagedLots=0.03,
            currentTradesToday=2,
            managedDailyPnl=-4.25,
            currentAccountEquityDrawdownPercent=1.5,
            currentMarginLevelPercent=825.0,
        )
        with self.selected_candidate():
            status = self.bridge.mt4_trade_gateway_status_read_model()

        self.assertEqual(status["status"], "demo_ready")
        self.assertEqual(status["eaVersion"], "2.12")
        self.assertTrue(status["executionGuardReady"])
        self.assertEqual(status["executionGuardReason"], "READY")
        self.assertEqual(status["portfolioPolicyStatus"], "ready")
        self.assertEqual(status["portfolioPolicyDigest"], "a" * 64)
        self.assertEqual(
            status["portfolioGuardScope"],
            "MANAGED_MAGIC_NUMBERS_ACCOUNT_WIDE",
        )
        self.assertEqual(status["managedMagicNumbers"], "4186001")
        self.assertEqual(status["allowedSymbols"], "XAUUSD")
        self.assertEqual(
            status["allowedTimeframes"],
            "M5,M15,M30,H1,H4,D1,W1,MN1",
        )
        self.assertEqual(
            status["concurrencyBoundary"],
            "same_windows_user_file_common",
        )
        self.assertFalse(status["crossVpsDistributedLock"])
        self.assertEqual(status["commandSchemaVersion"], "metafx-hq-mt4-command-v2")
        self.assertEqual(status["ackSchemaVersion"], "metafx-hq-mt4-ack-v3")
        self.assertTrue(status["signedCommandVerificationAvailable"])
        self.assertTrue(status["signingKeyPinned"])
        self.assertTrue(status["signingKeyMatch"])
        self.assertEqual(status["signatureAlgorithm"], "HMAC-SHA256")
        self.assertEqual(
            status["activeSigningKeyId"],
            status["backend"]["activeSigningKeyId"],
        )
        self.assertEqual(status["maxManagedPositions"], 1)
        self.assertEqual(status["currentManagedPositions"], 1)
        self.assertEqual(status["maxManagedLots"], 0.1)
        self.assertEqual(status["currentManagedLots"], 0.03)
        self.assertEqual(status["currentTradesToday"], 2)
        self.assertEqual(status["managedDailyPnl"], -4.25)
        self.assertEqual(status["currentAccountEquityDrawdownPercent"], 1.5)
        self.assertEqual(status["currentMarginLevelPercent"], 825.0)
        self.assertTrue(status["demoOrderExecutionAvailable"])

    def test_gateway_status_rejects_malformed_v4_risk_telemetry(self) -> None:
        self.write_ea_status(currentManagedPositions="0")
        with self.selected_candidate():
            status = self.bridge.mt4_trade_gateway_status_read_model()

        self.assertFalse(status["connected"])
        self.assertEqual(status["status"], "awaiting_ea")
        self.assertEqual(status["reasonCode"], "gateway_status_value_invalid")

    def test_gateway_status_rejects_malformed_v5_portfolio_evidence(self) -> None:
        cases = (
            {"portfolioPolicyStatus": "not_ready"},
            {"portfolioPolicyDigest": "A" * 64},
            {"portfolioGuardScope": "PER_CHART"},
            {"managedMagicNumbers": "4186002,4186001"},
            {"managedMagicNumbers": "4186001,4186001"},
            {"allowedSymbols": "xauusd"},
            {"allowedSymbols": "XAUUSD,XAUUSD"},
            {"allowedTimeframes": "M5,M5"},
            {"allowedTimeframes": "M2"},
            {"concurrencyBoundary": "per_chart"},
            {"crossVpsDistributedLock": True},
        )
        for overrides in cases:
            with self.subTest(overrides=overrides):
                self.write_ea_status(**overrides)
                with self.selected_candidate():
                    status = self.bridge.mt4_trade_gateway_status_read_model()

                self.assertFalse(status["connected"])
                self.assertEqual(
                    status["reasonCode"],
                    "gateway_status_portfolio_policy_invalid",
                )

    def test_gateway_status_rejects_malformed_v4_signing_state(self) -> None:
        cases = (
            {"signedCommandVerificationAvailable": "true"},
            {"activeSigningKeyId": "hk-not-a-digest"},
            {"signingKeyPinned": 1},
            {"signatureAlgorithm": "SHA256"},
            {"lastSignatureVerificationStatus": "not_checked"},
        )
        for overrides in cases:
            with self.subTest(overrides=overrides):
                self.write_ea_status(**overrides)
                with self.selected_candidate():
                    status = self.bridge.mt4_trade_gateway_status_read_model()

                self.assertFalse(status["connected"])
                self.assertEqual(status["status"], "awaiting_ea")
                self.assertEqual(status["reasonCode"], "gateway_status_schema_invalid")

    def test_gateway_status_rejects_stale_ea_heartbeat(self) -> None:
        self.write_ea_status(observedAt=int(time.time()) - 60)
        with self.selected_candidate():
            status = self.bridge.mt4_trade_gateway_status_read_model()

        self.assertFalse(status["connected"])
        self.assertEqual(status["status"], "awaiting_ea")
        self.assertEqual(status["reasonCode"], "gateway_status_stale")

    def test_live_status_is_ready_only_when_backend_and_ea_signing_keys_match(self) -> None:
        self.write_ea_status(
            mode="live",
            demoAccount=False,
            accountMode="live",
            liveArmed=True,
            autoTradingAllowed=True,
            tradeAllowed=True,
        )
        with self.selected_candidate():
            status = self.bridge.mt4_trade_gateway_status_read_model()

        self.assertTrue(status["connected"])
        self.assertEqual(status["status"], "live_ready")
        self.assertEqual(status["reasonCode"], "ready")
        self.assertTrue(status["liveOrderExecutionAvailable"])
        self.assertTrue(status["signingKeyMatch"])
        self.assertTrue(status["backend"]["signedCommandRequiredForLive"])
        self.assertTrue(status["backend"]["signedCommandVerificationAvailable"])
        self.assertRegex(
            str(status["backend"]["activeSigningKeyId"]),
            r"^hk-[0-9a-f]{64}$",
        )

    def test_live_status_blocks_unverified_unpinned_or_mismatched_ea_key(self) -> None:
        provisioned_key_id = self.signing_key_id()
        mismatched_key_id = "hk-" + (
            "e" * 64 if provisioned_key_id != "hk-" + "e" * 64 else "f" * 64
        )
        cases = (
            (
                {"signedCommandVerificationAvailable": False},
                "ea_signed_command_verifier_not_ready",
            ),
            (
                {"signingKeyPinned": False},
                "ea_signing_key_not_pinned",
            ),
            (
                {"activeSigningKeyId": mismatched_key_id},
                "signing_key_identity_mismatch",
            ),
        )
        for overrides, expected_reason in cases:
            with self.subTest(expected_reason=expected_reason):
                self.write_ea_status(
                    mode="live",
                    demoAccount=False,
                    accountMode="live",
                    liveArmed=True,
                    autoTradingAllowed=True,
                    tradeAllowed=True,
                    **overrides,
                )
                with self.selected_candidate():
                    status = self.bridge.mt4_trade_gateway_status_read_model()

                self.assertEqual(status["status"], "live_blocked")
                self.assertEqual(status["reasonCode"], expected_reason)
                self.assertFalse(status["liveOrderExecutionAvailable"])
                if expected_reason == "signing_key_identity_mismatch":
                    self.assertFalse(status["signingKeyMatch"])

    def test_demo_accepts_matching_active_key_without_live_trusted_key_pin(self) -> None:
        self.write_ea_status(
            mode="demo",
            autoTradingAllowed=True,
            tradeAllowed=True,
            signingKeyPinned=False,
        )
        with self.selected_candidate():
            ready = self.bridge.mt4_trade_gateway_status_read_model()

        self.assertEqual(ready["status"], "demo_ready")
        self.assertEqual(ready["reasonCode"], "ready")
        self.assertTrue(ready["demoOrderExecutionAvailable"])
        self.assertFalse(ready["signingKeyPinned"])
        self.assertTrue(ready["signingKeyMatch"])

    def test_live_mode_on_demo_account_is_explicitly_blocked(self) -> None:
        self.write_ea_status(
            mode="live",
            demoAccount=True,
            accountMode="demo",
            liveArmed=True,
            autoTradingAllowed=True,
            tradeAllowed=True,
        )
        with self.selected_candidate():
            status = self.bridge.mt4_trade_gateway_status_read_model()

        self.assertTrue(status["connected"])
        self.assertEqual(status["status"], "live_blocked")
        self.assertEqual(status["reasonCode"], "live_mode_requires_non_demo_account")
        self.assertFalse(status["accountModeMatchesGateway"])
        self.assertFalse(status["liveOrderExecutionAvailable"])

    def test_demo_mode_on_live_account_is_explicitly_blocked(self) -> None:
        self.write_ea_status(
            mode="demo",
            demoAccount=False,
            accountMode="live",
            autoTradingAllowed=True,
            tradeAllowed=True,
        )
        with self.selected_candidate():
            status = self.bridge.mt4_trade_gateway_status_read_model()

        self.assertTrue(status["connected"])
        self.assertEqual(status["status"], "demo_blocked")
        self.assertEqual(status["reasonCode"], "demo_mode_requires_demo_account")
        self.assertFalse(status["accountModeMatchesGateway"])
        self.assertFalse(status["demoOrderExecutionAvailable"])

    def test_gateway_status_rejects_inconsistent_or_malformed_account_identity(self) -> None:
        cases = (
            {"demoAccount": "true"},
            {"accountMode": "practice"},
            {"demoAccount": True, "accountMode": "live"},
            {"demoAccount": False, "accountMode": "demo"},
        )
        for overrides in cases:
            with self.subTest(overrides=overrides):
                self.write_ea_status(**overrides)
                with self.selected_candidate():
                    status = self.bridge.mt4_trade_gateway_status_read_model()

                self.assertFalse(status["connected"])
                self.assertEqual(status["reasonCode"], "gateway_status_schema_invalid")

    def test_demo_still_requires_verifier_and_matching_active_key(self) -> None:
        provisioned_key_id = self.signing_key_id()
        mismatched_key_id = "hk-" + (
            "a" * 64 if provisioned_key_id != "hk-" + "a" * 64 else "b" * 64
        )
        cases = (
            (
                {"signedCommandVerificationAvailable": False},
                "ea_signed_command_verifier_not_ready",
            ),
            (
                {"activeSigningKeyId": mismatched_key_id},
                "signing_key_identity_mismatch",
            ),
        )
        for overrides, expected_reason in cases:
            with self.subTest(expected_reason=expected_reason):
                self.write_ea_status(
                    mode="demo",
                    autoTradingAllowed=True,
                    tradeAllowed=True,
                    signingKeyPinned=False,
                    **overrides,
                )
                with self.selected_candidate():
                    status = self.bridge.mt4_trade_gateway_status_read_model()

                self.assertEqual(status["status"], "demo_blocked")
                self.assertEqual(status["reasonCode"], expected_reason)
                self.assertFalse(status["demoOrderExecutionAvailable"])

    def test_v4_ea_status_remains_connected_but_requires_portfolio_evidence(self) -> None:
        payload = self.write_ea_status(
            schemaVersion="metafx-hq-mt4-status-v4",
            mode="demo",
            autoTradingAllowed=True,
            tradeAllowed=True,
        )
        for field in (
            self.bridge.MT4_TRADE_GATEWAY_STATUS_FIELDS
            - self.bridge.MT4_TRADE_GATEWAY_V4_STATUS_FIELDS
        ):
            payload.pop(field)
        self.status_path().write_text(json.dumps(payload), encoding="ascii")
        with self.selected_candidate():
            status = self.bridge.mt4_trade_gateway_status_read_model()

        self.assertTrue(status["connected"])
        self.assertEqual(status["status"], "legacy_status_read_only")
        self.assertEqual(
            status["reasonCode"],
            "portfolio_policy_evidence_required",
        )
        self.assertFalse(status["executionGuardReady"])
        self.assertEqual(
            status["executionGuardReason"],
            "PORTFOLIO_POLICY_EVIDENCE_REQUIRED",
        )
        self.assertFalse(status["demoOrderExecutionAvailable"])
        self.assertFalse(status["liveOrderExecutionAvailable"])

    def test_v3_ea_status_remains_connected_but_cannot_enable_execution(self) -> None:
        payload = self.write_ea_status(schemaVersion="metafx-hq-mt4-status-v3")
        for field in (
            self.bridge.MT4_TRADE_GATEWAY_STATUS_FIELDS
            - self.bridge.MT4_TRADE_GATEWAY_V4_STATUS_FIELDS
        ):
            payload.pop(field)
        payload.pop("demoAccount")
        payload.pop("accountMode")
        self.status_path().write_text(json.dumps(payload), encoding="ascii")
        with self.selected_candidate():
            status = self.bridge.mt4_trade_gateway_status_read_model()

        self.assertTrue(status["connected"])
        self.assertEqual(status["status"], "legacy_status_read_only")
        self.assertEqual(status["reasonCode"], "portfolio_policy_evidence_required")
        self.assertIsNone(status["demoAccount"])
        self.assertFalse(status["accountModeMatchesGateway"])
        self.assertFalse(status["demoOrderExecutionAvailable"])
        self.assertFalse(status["liveOrderExecutionAvailable"])

    def test_v2_ea_status_is_rejected_instead_of_enabling_execution(self) -> None:
        self.write_ea_status(schemaVersion="metafx-hq-mt4-status-v2")
        with self.selected_candidate():
            status = self.bridge.mt4_trade_gateway_status_read_model()

        self.assertFalse(status["connected"])
        self.assertEqual(status["status"], "awaiting_ea")
        self.assertEqual(status["reasonCode"], "gateway_status_schema_invalid")
        self.assertFalse(status["demoOrderExecutionAvailable"])
        self.assertFalse(status["liveOrderExecutionAvailable"])

    def test_execution_unknown_quarantine_requires_exact_revision_and_audits(self) -> None:
        command_id = "cmd-" + ("a" * 24)
        fake_gateway = mock.Mock()
        fake_gateway.quarantine_execution_unknown.return_value = {
            "ok": True,
            "kind": "mt4_execution_unknown_quarantined",
            "commandId": command_id,
            "killSwitchActive": True,
            "barClaimRetained": True,
            "slotReleased": True,
            "ledgerRevision": 8,
        }
        with mock.patch.object(
            self.bridge,
            "_mt4_trade_gateway_instance",
            return_value=fake_gateway,
        ):
            result = self.bridge.quarantine_mt4_execution_unknown({
                "commandId": command_id,
                "expectedLedgerRevision": 7,
            })

        self.assertTrue(result["ok"])
        self.assertFalse(result["automaticRetry"])
        fake_gateway.quarantine_execution_unknown.assert_called_once_with(
            command_id,
            expected_ledger_revision=7,
        )
        events = self.bridge.tail_jsonl(self.bridge.AUDIT_PATH, limit=20)
        event = next(
            row
            for row in events
            if row.get("type")
            == "mt4_trade_gateway.execution_unknown_quarantined"
        )
        self.assertTrue(event["killSwitchActive"])
        self.assertTrue(event["barClaimRetained"])
        self.assertFalse(event["automaticRetry"])

        invalid = self.bridge.quarantine_mt4_execution_unknown({
            "commandId": command_id,
            "expectedLedgerRevision": 8,
            "retry": True,
        })
        self.assertFalse(invalid["ok"])
        self.assertEqual(invalid["_httpStatus"], 422)

    def test_outcome_read_model_returns_only_validated_gateway_evidence(self) -> None:
        command_id = "cmd-" + ("b" * 24)
        outcome = {
            "schemaVersion": "metafx-hq-mt4-outcome-v1",
            "channelId": self.candidate["candidateId"],
            "commandId": command_id,
            "executionState": "OPEN",
            "ticket": 12345,
        }
        fake_gateway = mock.Mock()
        fake_gateway.read_outcome.return_value = outcome
        with mock.patch.object(
            self.bridge,
            "_mt4_trade_gateway_instance",
            return_value=fake_gateway,
        ):
            result = self.bridge.mt4_trade_gateway_outcome_read_model(command_id)

        self.assertTrue(result["ok"])
        self.assertEqual(result["outcome"], outcome)
        fake_gateway.read_outcome.assert_called_once_with(command_id)

    def test_unanimous_trade_plan_publishes_no_lot_or_risk_fields(self) -> None:
        self.write_ea_status()
        parent = self.parent()
        with self.selected_candidate():
            result = self.bridge.dispatch_ai_trade_council_trade_plan(
                parent,
                self.consensus(),
            )

        self.assertEqual(result["status"], "queued")
        self.assertTrue(result["commandPublished"])
        command_path = self.status_path().with_name("command.json")
        envelope = json.loads(command_path.read_text(encoding="ascii"))
        self.assertEqual(
            list(envelope),
            ["schemaVersion", "algorithm", "keyId", "payloadHex", "signatureHex"],
        )
        self.assertEqual(
            envelope["schemaVersion"],
            "metafx-hq-mt4-signed-envelope-v1",
        )
        self.assertEqual(envelope["algorithm"], "HMAC-SHA256")
        self.assertRegex(envelope["keyId"], r"^hk-[0-9a-f]{64}$")
        self.assertRegex(envelope["payloadHex"], r"^(?:[0-9a-f]{2})+$")
        self.assertRegex(envelope["signatureHex"], r"^[0-9a-f]{64}$")
        command = json.loads(bytes.fromhex(envelope["payloadHex"]).decode("ascii"))
        self.assertEqual(command["schemaVersion"], "metafx-hq-mt4-command-v2")
        self.assertEqual(command["action"], "BUY")
        self.assertIsInstance(command["snapshotObservedAt"], int)
        self.assertEqual(command["referencePrice"], 100)
        self.assertEqual(command["stopLoss"], 95)
        self.assertEqual(command["takeProfit"], 110)
        forbidden = {
            "lot",
            "lots",
            "fixedLot",
            "volume",
            "risk",
            "riskPercent",
            "mode",
            "liveArmed",
        }
        self.assertTrue(forbidden.isdisjoint(command))

    def test_m1_trade_plan_is_blocked_before_gateway_publish(self) -> None:
        self.write_ea_status(timeframe="M5")
        with self.selected_candidate():
            result = self.bridge.dispatch_ai_trade_council_trade_plan(
                self.parent(timeframe="M1"),
                self.consensus(),
            )

        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["reasonCode"], "trade_plan_identity_invalid")
        self.assertFalse(self.status_path().with_name("command.json").exists())

    def test_live_mode_requires_local_ea_live_arm(self) -> None:
        self.write_ea_status(
            mode="live",
            liveArmed=False,
            autoTradingAllowed=True,
            tradeAllowed=True,
        )
        with self.selected_candidate():
            result = self.bridge.dispatch_ai_trade_council_trade_plan(
                self.parent(),
                self.consensus(),
            )

        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["reasonCode"], "live_execution_gate_not_ready")
        self.assertFalse(self.status_path().with_name("command.json").exists())

    def test_demo_mode_blocks_when_ea_execution_guard_is_not_ready(self) -> None:
        self.write_ea_status(
            mode="demo",
            autoTradingAllowed=True,
            tradeAllowed=True,
            executionGuardReady=False,
            executionGuardReason="DAILY_LOSS_LIMIT_REACHED",
        )
        with self.selected_candidate():
            result = self.bridge.dispatch_ai_trade_council_trade_plan(
                self.parent(),
                self.consensus(),
            )

        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["reasonCode"], "execution_guard_not_ready")
        self.assertEqual(result["executionGuardReason"], "DAILY_LOSS_LIMIT_REACHED")
        self.assertFalse(self.status_path().with_name("command.json").exists())

    def test_shadow_mode_can_publish_for_validation_when_execution_guard_is_blocked(self) -> None:
        self.write_ea_status(
            mode="shadow",
            executionGuardReady=False,
            executionGuardReason="AUTO_TRADING_DISABLED",
        )
        with self.selected_candidate():
            result = self.bridge.dispatch_ai_trade_council_trade_plan(
                self.parent(),
                self.consensus(),
            )

        self.assertEqual(result["status"], "queued")
        self.assertTrue(result["commandPublished"])

    def test_frontend_has_no_controls_for_ea_owned_lot_or_live_arm(self) -> None:
        source = (
            PROJECT_ROOT / "frontend" / "src" / "app" / "main.js"
        ).read_text(encoding="utf-8")
        self.assertNotRegex(source, r"<input[^>]+(?:fixedLot|liveArmed|gatewayMode)")
        self.assertNotRegex(source, r"fetch\([^)]*(?:fixedLot|liveArmed|gatewayMode)")
        self.assertIn("Fixed Lot ตั้งค่าที่ EA", source)
        self.assertIn('awaiting_ea: "รอเชื่อม EA"', source)
        self.assertIn('waiting_snapshot: "รอข้อมูลกราฟรอบใหม่"', source)
        self.assertIn("gatewayExecutionGuardReady", source)
        self.assertIn("gatewayRiskTelemetry", source)

    def test_council_report_never_equates_live_arm_with_execution_readiness(self) -> None:
        bridge_source = BRIDGE_PATH.read_text(encoding="utf-8")
        self.assertIn(
            "live_trading_enabled = live_order_execution_available",
            bridge_source,
        )
        self.assertNotRegex(
            bridge_source,
            r"live_trading_enabled\s*=\s*\([^)]*liveArmed[^)]*\)",
        )


if __name__ == "__main__":
    unittest.main()
