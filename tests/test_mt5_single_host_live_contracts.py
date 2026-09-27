import json
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class Mt5SingleHostLiveContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.bridge = json.loads(
            (PROJECT_ROOT / "contracts" / "bridge" / "bridge-contract.json").read_text(
                encoding="utf-8"
            )
        )
        cls.reports = json.loads(
            (PROJECT_ROOT / "contracts" / "reports" / "report-contract.json").read_text(
                encoding="utf-8"
            )
        )
        cls.readme = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")
        cls.student_quickstart = (PROJECT_ROOT / "STUDENT-QUICKSTART-TH.md").read_text(
            encoding="utf-8"
        )

    def test_bridge_contract_declares_bounded_mt5_live_parity(self) -> None:
        policy = self.bridge["runner_mode"]["mt4_trade_gateway"]

        self.assertEqual(policy["supportedPlatforms"], ["mt4", "mt5"])
        self.assertEqual(policy["mt5ActivationSequence"], ["shadow", "demo", "live"])
        self.assertEqual(
            policy["mt5LiveInputValues"],
            {
                "GatewayMode": "GATEWAY_LIVE",
                "LiveArmed": True,
                "SingleHostLiveAcknowledged": True,
                "TrustedSigningKeyId": "exact_backend_active_key_id",
            },
        )
        self.assertEqual(
            policy["mt5LiveSafetyScope"],
            "single_windows_user_file_common_only",
        )
        self.assertEqual(
            policy["mt5ConcurrencyBoundary"],
            "same_windows_user_file_common",
        )
        self.assertTrue(policy["mt5SingleHostAcknowledgementRequired"])
        self.assertFalse(policy["mt5SameAccountConcurrentElsewhereAllowed"])
        self.assertFalse(policy["crossVpsDistributedLock"])
        self.assertIn("singleHostLiveAcknowledged", policy["forbiddenAiSignalFields"])
        self.assertIn("singleHostLiveAcknowledged", policy["eaOwnedInputs"])
        self.assertIn("do not submit a real broker order", policy["automatedVerificationBoundary"])

    def test_report_contract_exposes_truthful_mt5_status_evidence(self) -> None:
        council = self.reports["typed_report_schemas"]["prop_report"]["properties"][
            "aiTradeCouncil"
        ]
        gateway = council["tradeGateway"]

        self.assertFalse(gateway["singleHostLiveAcknowledged"])
        self.assertEqual(
            gateway["liveSafetyScope"],
            "single_windows_user_file_common_only",
        )
        self.assertEqual(
            gateway["concurrencyBoundary"],
            "same_windows_user_file_common",
        )
        self.assertFalse(gateway["crossVpsDistributedLock"])

        truth = "\n".join(council["truthRules"])
        self.assertIn("SingleHostLiveAcknowledged=true", truth)
        self.assertIn("crossVpsDistributedLock remains false", truth)
        self.assertIn("do not submit a real broker order", truth)

    def test_operator_docs_require_shadow_demo_live_and_single_host_ack(self) -> None:
        for document in (self.readme, self.student_quickstart):
            self.assertIn("Shadow -> Demo -> Live", document)
            self.assertIn("GatewayMode=GATEWAY_LIVE", document)
            self.assertIn("LiveArmed=true", document)
            self.assertIn("SingleHostLiveAcknowledged=true", document)
            self.assertIn("TrustedSigningKeyId", document)
            self.assertIn("single_windows_user_file_common_only", document)
            self.assertIn("crossVpsDistributedLock=false", document)
            self.assertIn("ไม่ส่งออร์เดอร์จริงไปยังโบรกเกอร์", document)


if __name__ == "__main__":
    unittest.main()
