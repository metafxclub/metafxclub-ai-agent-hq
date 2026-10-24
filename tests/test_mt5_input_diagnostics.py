from __future__ import annotations

import unittest

import test_mt4_trade_gateway_bridge as fixtures


class MT5InputDiagnosticTests(unittest.TestCase):
    """Only temporary init-status fixtures; no terminal, signing or account calls."""

    setUp = fixtures.Mt4TradeGatewayBridgeTests.setUp
    tearDown = fixtures.Mt4TradeGatewayBridgeTests.tearDown
    status_path = fixtures.Mt4TradeGatewayBridgeTests.status_path
    init_status_path = fixtures.Mt4TradeGatewayBridgeTests.init_status_path
    write_ea_init_status = fixtures.Mt4TradeGatewayBridgeTests.write_ea_init_status

    @classmethod
    def setUpClass(cls):
        cls.bridge = fixtures.load_bridge()

    @staticmethod
    def diagnostic(**overrides):
        return {
            "field": "MaxSnapshotAgeSeconds", "value": 1000,
            "minimum": 5, "maximum": 900,
            "minimumInclusive": True, "maximumInclusive": True,
            "constraint": "range", **overrides,
        }

    def read(self, diagnostic, **overrides):
        self.write_ea_init_status(
            **{"stage": "inputs", "reasonCode": "GATEWAY_INPUT_CONFIGURATION_INVALID",
               "eaAttached": True, "runtimeReady": False,
               "inputValidation": diagnostic, **overrides},
        )
        return self.bridge._read_mt4_trade_gateway_init_status(self.candidate)

    def test_precise_input_diagnostic_is_projected_without_granting_readiness(self):
        status = self.read(self.diagnostic())
        self.assertTrue(status["available"])
        self.assertFalse(status["runtimeReady"])
        self.assertEqual(status["inputValidation"], self.diagnostic())
        text = self.bridge._mt4_trade_gateway_init_status_message_th(status)
        for expected in ("MaxSnapshotAgeSeconds=1000", ">= 5", "<= 900", "OK"):
            self.assertIn(expected, text)
        self.assertNotIn("channelId", status)

    def test_legacy_and_cleared_diagnostics_remain_readable(self):
        self.write_ea_init_status()
        old = self.bridge._read_mt4_trade_gateway_init_status(self.candidate)
        self.assertTrue(old["available"])
        self.assertIsNone(old["inputValidation"])
        ready = self.read(None, severity="info", stage="ready",
                          reasonCode="INIT_SUCCEEDED", runtimeReady=True)
        self.assertTrue(ready["available"])
        self.assertIsNone(ready["inputValidation"])
        self.assertEqual(self.bridge._mt4_trade_gateway_init_status_message_th(ready), "")

    def test_partial_unknown_secret_and_nonfinite_diagnostics_fail_closed(self):
        bad = [
            {key: value for key, value in self.diagnostic().items() if key != "maximum"},
            self.diagnostic(field="TrustedSigningKeyId", value=123),
            self.diagnostic(brokerPassword="must-not-leak"),
            self.diagnostic(value="must-not-leak"),
            self.diagnostic(value=True), self.diagnostic(value=float("inf")),
            self.diagnostic(value=float("nan")), self.diagnostic(value=10 ** 500),
            self.diagnostic(maximum=-1), self.diagnostic(minimum=None, maximum=None),
            self.diagnostic(minimumInclusive=1), self.diagnostic(constraint="arbitrary-text"),
            self.diagnostic(field="FixedLot"), self.diagnostic(field="RequireHeartbeat"),
        ]
        for diagnostic in bad:
            with self.subTest(diagnostic=repr(diagnostic)[:120]):
                result = self.read(diagnostic)
                self.assertFalse(result["available"])
                self.assertEqual(result["readReasonCode"], "gateway_init_status_schema_invalid")
                self.assertIsNone(result["inputValidation"])
                self.assertNotIn("must-not-leak", str(result))

    def test_diagnostic_cannot_attach_to_ready_or_unrelated_failure(self):
        for overrides in (
            {"stage": "crypto"}, {"reasonCode": "CRYPTO_SELF_TEST_FAILED"},
            {"severity": "info"}, {"runtimeReady": True},
        ):
            with self.subTest(overrides=overrides):
                self.assertFalse(self.read(self.diagnostic(), **overrides)["available"])

    def test_open_bounds_nonfinite_marker_and_cross_input_constraints(self):
        cases = [
            self.diagnostic(field="MaxDailyLossPercent", value=None, minimum=0,
                            maximum=100, minimumInclusive=False),
            self.diagnostic(field="MinRewardRiskRatio", value=0, minimum=0,
                            maximum=None, minimumInclusive=False),
            self.diagnostic(field="FixedLot", value=.2, minimum=None, maximum=.1,
                            constraint="at_most_MaxManagedTotalLots"),
            self.diagnostic(field="RequireHeartbeat", value=0, minimum=1, maximum=1,
                            constraint="required_for_execution"),
            self.diagnostic(field="MaxCommandTtlSeconds", value=20, minimum=30, maximum=120),
            self.diagnostic(field="MaxHeartbeatTtlSeconds", value=20, minimum=30, maximum=60),
        ]
        for diagnostic in cases:
            with self.subTest(field=diagnostic["field"]):
                status = self.read(diagnostic)
                self.assertTrue(status["available"])
                self.assertEqual(status["inputValidation"], diagnostic)
                self.assertIn(diagnostic["field"], self.bridge._mt4_trade_gateway_init_status_message_th(status))


if __name__ == "__main__":
    unittest.main()
