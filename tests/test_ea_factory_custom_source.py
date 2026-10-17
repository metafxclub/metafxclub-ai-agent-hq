from __future__ import annotations

import importlib.util
import http.client
import inspect
import json
import tempfile
import threading
import unittest
from pathlib import Path
from unittest import mock


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BRIDGE_PATH = PROJECT_ROOT / "backend" / "local-runner" / "bridge_server.py"


def load_bridge():
    spec = importlib.util.spec_from_file_location(
        "metafx_ea_factory_custom_source",
        BRIDGE_PATH,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to import {BRIDGE_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class EaFactoryCustomSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.bridge = load_bridge()

    def setUp(self) -> None:
        self.bridge.EA_FACTORY_STATE_CACHE.update({
            "signature": None,
            "value": None,
        })
        self.bridge._invalidate_ea_factory_read_model_cache()
        self.top_header_locks = mock.patch.object(
            self.bridge,
            "_global_metatrader_platform_context",
            side_effect=self._dual_locked_platform_context,
        )
        self.top_header_locks.start()

    def tearDown(self) -> None:
        self.top_header_locks.stop()

    @staticmethod
    def _dual_locked_platform_context(
        platform: object,
        *,
        require_all_platforms: bool = True,
    ) -> dict | None:
        normalized = str(platform or "").strip().lower()
        if normalized == "tradingview":
            return None
        candidate_id = f"mtc-custom-source-{normalized}"
        return {
            "record": {
                "candidateId": candidate_id,
                "platform": normalized,
            },
            "token": {
                "candidateId": candidate_id,
                "platform": normalized,
                "selectionRevision": 1,
            },
        }

    @staticmethod
    def ema_mt5_payload() -> dict:
        return {
            "platform": "mt5",
            "artifactKind": "ea",
            "systemName": "EMA 10/60 Closed-Bar Smoke EA",
            "systemOverview": (
                "Deterministic MT5 smoke strategy using EMA 10 and EMA 60 "
                "on the chart symbol and timeframe."
            ),
            "entryRules": (
                "On one new bar only, BUY when EMA(10) at closed bar 2 is "
                "less than or equal to EMA(60) and EMA(10) at closed bar 1 "
                "is greater than EMA(60). SELL on the exact inverse closed-bar crossover."
            ),
            "recoveryRules": (
                "No recovery, grid, martingale, averaging, pyramiding, or hedging."
            ),
            "exitRules": (
                "StopLossPips and TakeProfitPips are positive EA inputs. "
                "Close an existing position on the opposite confirmed crossover "
                "before opening the reverse direction."
            ),
            "moneyManagement": (
                "Use one normalized tester-safe fixed lot of 0.01 and never hold "
                "more than one position for this symbol and magic number."
            ),
            "orderExecution": (
                "Use market orders in Strategy Tester only after closed-bar confirmation; "
                "normalize price and broker stop distance and reject invalid orders safely."
            ),
            "displayRequirements": (
                "Show fast and slow EMA values plus BUY signals, SELL signals, "
                "BUY orders, SELL orders, and the latest execution result."
            ),
            "additionalNotes": (
                "The acceptance loop must compile, run a Visual backtest, verify "
                "entry markers against the crossover, save the Backtest report, "
                "and produce the final condition-match summary. Optimization is out of scope."
            ),
        }

    def test_mt5_ema_custom_source_is_stable_durable_and_catalogued(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            with (
                mock.patch.object(self.bridge, "RUNTIME_DIR", root),
                mock.patch.object(self.bridge, "PROJECT_ROOT", root),
                mock.patch.object(self.bridge, "append_audit") as audit,
                mock.patch.object(
                    self.bridge,
                    "_research_sheet_hub_internal",
                    return_value={},
                ),
                mock.patch.object(
                    self.bridge,
                    "_ea_factory_research_source_records",
                    return_value=[],
                ),
            ):
                first = self.bridge.create_ea_factory_custom_source(
                    self.ema_mt5_payload()
                )
                second = self.bridge.create_ea_factory_custom_source(
                    self.ema_mt5_payload()
                )
                state = self.bridge._load_ea_factory_state_unlocked()
                catalog = self.bridge._ea_factory_source_catalog(
                    state=state,
                    reports=[],
                    missions=[],
                )

        self.assertTrue(first["created"])
        self.assertFalse(second["created"])
        self.assertEqual(first["sourceRecordId"], second["sourceRecordId"])
        self.assertEqual(len(state["customSources"]), 1)
        self.assertEqual(catalog[0]["sourceRecordId"], first["sourceRecordId"])
        self.assertEqual(catalog[0]["sourceKind"], "custom_operator")
        self.assertTrue(catalog[0]["buildReady"])
        self.assertEqual(first["source"]["provenance"], "custom_operator")
        self.assertEqual(first["source"]["compatiblePlatforms"], ["mt5"])
        self.assertEqual(first["source"]["customArtifactKind"], "expert_advisor")
        self.assertIn("StopLossPips", catalog[0]["strategyBrief"]["exitRules"])
        self.assertIn("TakeProfitPips", catalog[0]["strategyBrief"]["exitRules"])
        audit.assert_called_once()
        self.assertFalse(audit.call_args.args[0]["liveTradingEnabled"])
        self.assertFalse(audit.call_args.args[0]["contentPersistedInAudit"])

    def test_custom_source_survives_restart_validation_and_rejects_tampering(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            with (
                mock.patch.object(self.bridge, "RUNTIME_DIR", root),
                mock.patch.object(self.bridge, "PROJECT_ROOT", root),
                mock.patch.object(self.bridge, "append_audit"),
            ):
                created = self.bridge.create_ea_factory_custom_source(
                    self.ema_mt5_payload()
                )
                self.bridge._invalidate_ea_factory_state_cache()
                reloaded = self.bridge._load_ea_factory_state_unlocked()
                self.assertEqual(
                    reloaded["customSources"][0]["sourceRecordId"],
                    created["sourceRecordId"],
                )

                state_path = self.bridge._ea_factory_state_path()
                raw = json.loads(state_path.read_text(encoding="utf-8"))
                raw["customSources"][0]["customSource"]["entryRules"] = (
                    "BUY unconditionally"
                )
                state_path.write_text(
                    json.dumps(raw, ensure_ascii=False),
                    encoding="utf-8",
                )
                self.bridge._invalidate_ea_factory_state_cache()
                with self.assertRaises(self.bridge.DataIntegrityError):
                    self.bridge._load_ea_factory_state_unlocked()

    def test_existing_build_flow_accepts_exact_custom_source_only(self) -> None:
        class WorkspaceReached(RuntimeError):
            pass

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            with (
                mock.patch.object(self.bridge, "RUNTIME_DIR", root),
                mock.patch.object(self.bridge, "PROJECT_ROOT", root),
                mock.patch.object(self.bridge, "append_audit"),
            ):
                created = self.bridge.create_ea_factory_custom_source(
                    self.ema_mt5_payload()
                )
                with (
                    mock.patch.object(self.bridge, "load_missions", return_value=[]),
                    mock.patch.object(
                        self.bridge,
                        "load_runtime_reports",
                        return_value=[],
                    ),
                    mock.patch.object(
                        self.bridge,
                        "_research_sheet_hub_internal",
                        return_value={},
                    ),
                    mock.patch.object(
                        self.bridge,
                        "_ea_factory_research_source_records",
                        return_value=[],
                    ),
                    mock.patch.object(
                        self.bridge,
                        "_ea_factory_create_build_workspace",
                        side_effect=WorkspaceReached,
                    ) as workspace,
                ):
                    with self.assertRaises(WorkspaceReached):
                        self.bridge.create_ea_factory_build({
                            "sourceRecordId": created["sourceRecordId"],
                            "platform": "mt5",
                            "artifactKind": "expert_advisor",
                            "idempotencyKey": "custom-ema-mt5-create-1",
                        })
                workspace.assert_called_once()
                source_arg = workspace.call_args.args[1]
                self.assertEqual(source_arg["sourceKind"], "custom_operator")
                self.assertEqual(source_arg["sourceRecordId"], created["sourceRecordId"])

    def test_custom_source_platform_artifact_and_secret_guards_fail_closed(self) -> None:
        payload = self.ema_mt5_payload()
        with self.assertRaises(self.bridge.RequestError) as secret_error:
            self.bridge._ea_factory_custom_source_record({
                **payload,
                "additionalNotes": "api_key=abcd1234",
            })
        self.assertEqual(
            secret_error.exception.code,
            "ea_factory_custom_source_secret_rejected",
        )

        indicator = {
            **payload,
            "platform": "tradingview",
            "artifactKind": "indicator",
        }
        with self.assertRaises(self.bridge.RequestError) as combination_error:
            self.bridge._ea_factory_custom_source_record(indicator)
        self.assertEqual(
            combination_error.exception.code,
            "ea_factory_custom_source_combination_invalid",
        )

        record = self.bridge._ea_factory_custom_source_record(payload)
        empty_state = self.bridge._empty_ea_factory_state()
        with (
            mock.patch.object(self.bridge, "load_missions", return_value=[]),
            mock.patch.object(self.bridge, "load_runtime_reports", return_value=[]),
            mock.patch.object(
                self.bridge,
                "_load_ea_factory_state_unlocked",
                return_value=empty_state,
            ),
            mock.patch.object(
                self.bridge,
                "_ea_factory_source_catalog",
                return_value=[record],
            ),
            mock.patch.object(
                self.bridge,
                "_ea_factory_create_build_workspace",
            ) as workspace,
        ):
            with self.assertRaises(self.bridge.RequestError) as mismatch_error:
                self.bridge.create_ea_factory_build({
                    "sourceRecordId": record["sourceRecordId"],
                    "platform": "mt4",
                    "artifactKind": "expert_advisor",
                    "idempotencyKey": "custom-ema-platform-mismatch-1",
                })
            with self.assertRaises(self.bridge.RequestError) as kind_error:
                self.bridge.create_ea_factory_build({
                    "sourceRecordId": record["sourceRecordId"],
                    "platform": "mt5",
                    "artifactKind": "custom_indicator",
                    "idempotencyKey": "custom-ema-kind-mismatch-1",
                })
        self.assertEqual(
            mismatch_error.exception.code,
            "ea_factory_custom_source_platform_mismatch",
        )
        self.assertEqual(
            kind_error.exception.code,
            "ea_factory_custom_source_artifact_kind_mismatch",
        )
        workspace.assert_not_called()

    def test_post_route_is_registered(self) -> None:
        source = inspect.getsource(self.bridge.BridgeHandler.do_POST)
        self.assertIn(
            '"/api/props/right_server_racks/ea-factory/sources/custom"',
            source,
        )
        self.assertIn("create_ea_factory_custom_source(payload)", source)

        expected = {
            "ok": True,
            "kind": "ea_factory_custom_source",
            "created": True,
            "sourceRecordId": "ea-source-route",
            "source": {},
        }
        with mock.patch.object(
            self.bridge,
            "create_ea_factory_custom_source",
            return_value=expected,
        ) as create:
            server = self.bridge.BridgeHTTPServer(
                ("127.0.0.1", 0),
                self.bridge.BridgeHandler,
            )
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                connection = http.client.HTTPConnection(
                    "127.0.0.1",
                    server.server_port,
                    timeout=5,
                )
                body = json.dumps(self.ema_mt5_payload()).encode("utf-8")
                connection.request(
                    "POST",
                    "/api/props/right_server_racks/ea-factory/sources/custom",
                    body=body,
                    headers={"Content-Type": "application/json"},
                )
                response = connection.getresponse()
                decoded = json.loads(response.read().decode("utf-8"))
                connection.close()
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=3)
        self.assertEqual(response.status, 200)
        self.assertEqual(decoded, expected)
        create.assert_called_once_with(self.ema_mt5_payload())


if __name__ == "__main__":
    unittest.main()
