import copy
import json
import importlib.util
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PLUGIN_MAP_PATH = PROJECT_ROOT / "contracts" / "workflows" / "equipment-plugin-map.json"
ROLE_MAP_PATH = PROJECT_ROOT / "contracts" / "props" / "property-role-map.json"
PROFILE_MODULE_PATH = PROJECT_ROOT / "backend" / "local-runner" / "equipment_workflow_profiles.py"

EXPECTED_PROPS = {
    "codex_mcp_portal",
    "left_server_racks",
    "right_server_racks",
    "right_tool_console",
    "left_audit_crystals",
    "left_signal_cube",
    "terminal_workstation",
    "right_status_crystals",
}


class EquipmentPluginMapTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.plugin_map = json.loads(PLUGIN_MAP_PATH.read_text(encoding="utf-8"))
        cls.roles = json.loads(ROLE_MAP_PATH.read_text(encoding="utf-8"))["properties"]
        spec = importlib.util.spec_from_file_location("equipment_workflow_profiles_test", PROFILE_MODULE_PATH)
        if spec is None or spec.loader is None:
            raise RuntimeError("equipment workflow profile module unavailable")
        cls.profile_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.profile_module)

    def test_contract_is_backend_owned_and_safe_by_default(self) -> None:
        security = self.plugin_map["security"]
        self.assertTrue(security["frontendIntentOnly"])
        self.assertTrue(security["backendOwnsExecution"])
        self.assertFalse(security["credentialsAcceptedFromFrontend"])
        self.assertFalse(security["externalWritesDefault"])
        self.assertFalse(security["liveTradingAllowed"])
        self.assertEqual(security["secretFields"], [])
        input_contract = self.plugin_map["inputContract"]
        self.assertEqual(
            input_contract["acceptedFieldsSource"],
            "backend/local-runner/bridge_server.py:DASHBOARD_WORKFLOW_ACTIONS.formFields",
        )
        self.assertEqual(
            input_contract["integrationAcceptedFieldsSource"],
            "backend/local-runner/bridge_server.py:/api/integrations/metatrader/discover|select",
        )
        self.assertEqual(input_contract["inputPresetRole"], "trusted_defaults_only")
        self.assertFalse(input_contract["frontendMaySubmitUnknownFields"])

    def test_every_independent_equipment_and_action_has_a_plugin_profile(self) -> None:
        equipment = self.plugin_map["equipment"]
        self.assertEqual(set(equipment), EXPECTED_PROPS)
        for prop_id, profile in equipment.items():
            with self.subTest(prop_id=prop_id):
                if profile.get("serviceMode") == "deterministic_backend_direct":
                    self.assertEqual(prop_id, "left_signal_cube")
                    self.assertIsNone(profile["ownerAgentId"])
                    self.assertEqual(profile["allowedActionIds"], [])
                    self.assertEqual(self.roles[prop_id]["allowedDashboardActions"], [])
                    self.assertEqual(profile["schedule"]["actions"], [])
                    self.assertEqual(profile["schedule"]["manualOrAgentHandoffActions"], [])
                    self.assertEqual(
                        profile["schedule"]["directBackendHandler"],
                        "news_bias_direct_refresh",
                    )
                    self.assertEqual(
                        profile["directEndpoints"],
                        {
                            "refresh": "/api/props/left_signal_cube/news/refresh",
                            "schedule": "/api/props/left_signal_cube/news/schedule",
                        },
                    )
                    self.assertTrue(profile["legacyActionDefinitionsOnly"])
                    self.assertTrue(profile["actions"])
                    for action in profile["actions"].values():
                        self.assertTrue(action["retired"])
                        self.assertEqual(action["rejection"], "direct_service_required")
                    continue
                self.assertIn(profile["ownerAgentId"], {
                    "codex_mcp_operator", "mission_archivist", "ea_developer",
                    "backtest_analyst", "vps_watch",
                })
                allowed = set(self.roles[prop_id]["allowedDashboardActions"])
                self.assertEqual(set(profile["actions"]), allowed)
                for action_id, action in profile["actions"].items():
                    with self.subTest(prop_id=prop_id, action_id=action_id):
                        self.assertTrue(action["pluginSkillId"])
                        self.assertIn(action["automationMode"], self.plugin_map["automationModes"])
                        self.assertIsInstance(action["inputPreset"], dict)
                        self.assertTrue(action["outputFields"])
                        self.assertTrue(action["evidenceRequired"])
                        self.assertTrue(action["reportType"])
                        self.assertTrue(action["failureHelpTh"])

    def test_scheduled_jobs_are_read_only_and_explicit(self) -> None:
        equipment = self.plugin_map["equipment"]
        self.assertEqual(
            equipment["left_server_racks"]["schedule"]["reasonTh"],
            "ต้องเลือกระบบหนึ่งรายการจากคลัง Portal ที่ Backend ตรวจสอบแล้วก่อน",
        )
        for prop_id, profile in equipment.items():
            schedule = profile["schedule"]
            if not schedule.get("supported"):
                self.assertTrue(schedule.get("reasonTh"))
                continue
            self.assertEqual(schedule["timezone"], "Asia/Bangkok")
            self.assertTrue(schedule["defaultTimes"])
            if profile.get("serviceMode") == "deterministic_backend_direct":
                self.assertEqual(schedule["actions"], [])
                self.assertEqual(schedule["manualOrAgentHandoffActions"], [])
                self.assertEqual(schedule["directBackendHandler"], "news_bias_direct_refresh")
                self.assertTrue(schedule["defaultEnabled"])
                self.assertEqual(schedule["defaultTimes"], ["00:00", "12:00"])
                continue
            self.assertTrue(schedule["actions"])
            for action_id in schedule["actions"]:
                action = profile["actions"][action_id]
                self.assertEqual(action["automationMode"], "scheduled_read_only")
                self.assertNotIn("live", action["pluginSkillId"].lower())
            for action_id in schedule.get("manualOrAgentHandoffActions", []):
                action = profile["actions"][action_id]
                self.assertNotEqual(action["automationMode"], "scheduled_read_only")

    def test_terminal_and_ea_lab_work_never_claims_scheduled_execution(self) -> None:
        equipment = self.plugin_map["equipment"]
        for prop_id in ("right_server_racks", "right_tool_console", "terminal_workstation"):
            self.assertFalse(equipment[prop_id]["schedule"]["supported"])
            for action in equipment[prop_id]["actions"].values():
                self.assertNotEqual(action["automationMode"], "scheduled_read_only")

    def test_backend_loader_returns_trusted_copies_with_owner_and_contract_version(self) -> None:
        # Reference plugins are optional design inputs, not packaged runtime
        # dependencies.  Keep this contract test independent of the developer's
        # ~/.codex plugin cache and prove that the Backend-owned procedure still
        # loads truthfully on a clean student/CI machine.
        with mock.patch.object(
            self.profile_module,
            "_installed_skill",
            return_value={"installed": False, "version": None},
        ):
            profile = self.profile_module.equipment_action_profile(
                "codex_mcp_portal", "discover_trading_systems"
            )
            self.assertEqual(profile["pluginSkillId"], "backend-readonly-system-scout")
            self.assertEqual(profile["procedureKind"], "backend_procedure")
            self.assertEqual(profile["referencePluginSkillId"], "metafx-online-system-scout")
            self.assertFalse(profile["referenceSkillInstalled"])
            self.assertIsNone(profile["referenceInstalledVersion"])
            self.assertFalse(profile["referenceVersionMatch"])
            self.assertTrue(profile["versionMatch"])
            self.assertEqual(profile["ownerAgentId"], "codex_mcp_operator")
            self.assertEqual(profile["contractVersion"], "equipment-plugin-map-v1")
            profile["inputPreset"]["market"] = "tampered"
            fresh = self.profile_module.equipment_action_profile(
                "codex_mcp_portal", "discover_trading_systems"
            )
            self.assertEqual(fresh["inputPreset"]["market"], "Multi-asset")
            self.assertEqual(fresh["outputFields"], ["systems"])
            self.assertEqual(fresh["entryContract"]["minimumItemsPerRun"], 3)
        self.assertNotIn(
            "discover_ea_updates",
            self.plugin_map["equipment"]["codex_mcp_portal"]["actions"],
        )
        self.assertIsNone(self.profile_module.equipment_action_profile("unknown", "unknown"))

    def test_skill_discovery_honors_the_codex_home_installation_boundary(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            codex_home = Path(temp_dir) / "isolated-codex-home"
            skill_file = codex_home / "skills" / "ci-hermetic-reference" / "SKILL.md"
            skill_file.parent.mkdir(parents=True)
            skill_file.write_text("# Hermetic reference\n", encoding="utf-8")
            with mock.patch.dict(os.environ, {"CODEX_HOME": str(codex_home)}):
                installed = self.profile_module._installed_skill("ci-hermetic-reference")
                missing = self.profile_module._installed_skill("developer-only-reference")

        self.assertEqual(installed, {"installed": True, "version": "personal"})
        self.assertEqual(missing, {"installed": False, "version": None})

    def test_platform_router_changes_backend_procedure_and_reference_plugin_together(self) -> None:
        installed_reference_versions = {
            "metafx-system6-ea-builder-mt4": "0.1.4",
            "metafx-system6-ea-builder-mt5": "0.1.1+codex.20260616",
            "metafx-ea-full-cycle": "0.1.7+codex.20260611184944",
            "metafx-ea-full-cycle-mt5": "0.1.1+codex.20260616",
            "metafx-optimization-lab-mt4": "0.1.4+codex.20260607131357",
            "metafx-optimization-lab-mt5": "0.1.1+codex.20260616",
            "metafx-ea-discovery-lab-mt4": "0.1.4+codex.20260607132750",
            "metafx-ea-discovery-lab-mt5": "0.1.4+codex.20260616liveguard",
        }

        def installed_skill(skill_id: str) -> dict:
            version = installed_reference_versions.get(skill_id)
            return {"installed": version is not None, "version": version}

        cases = (
            ("right_server_racks", "build_strategy_code", {"platform": "mt5"}, "backend-mql5-source-builder", "metafx-system6-ea-builder-mt5", "0.1.1+codex.20260616"),
            ("right_tool_console", "prepare_backtest_plan", {"platform": "mt5"}, "backend-backtest-plan-mt5", "metafx-ea-full-cycle-mt5", "0.1.1+codex.20260616"),
            ("right_tool_console", "prepare_optimization_plan", {"platform": "mt5"}, "backend-optimization-plan-mt5", "metafx-optimization-lab-mt5", "0.1.1+codex.20260616"),
            ("right_tool_console", "prepare_ea_discovery_plan", {"platform": "mt5"}, "backend-ea-discovery-plan-mt5", "metafx-ea-discovery-lab-mt5", "0.1.4+codex.20260616liveguard"),
            ("terminal_workstation", "develop_ea_source", {"platform": "mql5"}, "backend-mql5-source-developer", "metafx-ea-full-cycle-mt5", "0.1.1+codex.20260616"),
        )
        # Supply a deterministic installation inventory so routing assertions
        # do not depend on whichever plugins happen to exist on the test host.
        with mock.patch.object(
            self.profile_module,
            "_installed_skill",
            side_effect=installed_skill,
        ):
            for prop_id, action_id, selectors, procedure_id, reference_id, reference_version in cases:
                with self.subTest(action=action_id):
                    profile = self.profile_module.equipment_action_profile(prop_id, action_id, selectors)
                    self.assertEqual(profile["pluginSkillId"], procedure_id)
                    self.assertEqual(profile["referencePluginSkillId"], reference_id)
                    self.assertEqual(profile["referencePluginVersion"], reference_version)
                    self.assertTrue(profile["referenceSkillInstalled"])
                    self.assertTrue(profile["referenceVersionMatch"])

            tradingview = self.profile_module.equipment_action_profile(
                "right_server_racks", "build_strategy_code", {"platform": "tradingview"}
            )
            self.assertEqual(tradingview["pluginSkillId"], "backend-tradingview-source-builder")
            self.assertIsNone(tradingview["referencePluginSkillId"])
            self.assertIsNone(tradingview["referencePluginVersion"])
            self.assertNotIn("referenceSkillInstalled", tradingview)

    def test_contract_rejects_incomplete_action_reference_pair(self) -> None:
        cases = (
            ("referencePluginVersion", None),
            ("referencePluginSkillId", None),
        )
        for field, value in cases:
            with self.subTest(field=field):
                payload = copy.deepcopy(self.plugin_map)
                action = payload["equipment"]["codex_mcp_portal"]["actions"]["discover_trading_systems"]
                action[field] = value
                with self.assertRaisesRegex(
                    self.profile_module.EquipmentWorkflowContractError,
                    r"^incomplete_reference_plugin:codex_mcp_portal:discover_trading_systems$",
                ):
                    self.profile_module._validated_payload(payload)

    def test_contract_rejects_candidate_without_plugin_version(self) -> None:
        payload = copy.deepcopy(self.plugin_map)
        candidate = payload["equipment"]["right_server_racks"]["actions"]["build_strategy_code"]["pluginCandidates"][0]
        candidate["pluginVersion"] = None
        with self.assertRaisesRegex(
            self.profile_module.EquipmentWorkflowContractError,
            r"^missing_candidate_plugin_version:right_server_racks:build_strategy_code$",
        ):
            self.profile_module._validated_payload(payload)

    def test_contract_rejects_candidate_with_invalid_procedure_kind(self) -> None:
        payload = copy.deepcopy(self.plugin_map)
        candidate = payload["equipment"]["right_server_racks"]["actions"]["build_strategy_code"]["pluginCandidates"][0]
        candidate["procedureKind"] = "unsafe_external_runner"
        with self.assertRaisesRegex(
            self.profile_module.EquipmentWorkflowContractError,
            r"^invalid_candidate_procedure_kind:right_server_racks:build_strategy_code$",
        ):
            self.profile_module._validated_payload(payload)

    def test_contract_preflight_rejects_unknown_evidence_and_missing_prerequisite(self) -> None:
        payload = copy.deepcopy(self.plugin_map)
        action = payload["equipment"]["codex_mcp_portal"]["actions"]["discover_trading_systems"]
        action["evidenceRequired"].append("future_unreviewed_proof")
        with self.assertRaisesRegex(
            self.profile_module.EquipmentWorkflowContractError,
            r"^unsupported_evidence_kind:codex_mcp_portal:discover_trading_systems:future_unreviewed_proof$",
        ):
            self.profile_module._validated_payload(payload)

        payload = copy.deepcopy(self.plugin_map)
        action = payload["equipment"]["right_server_racks"]["actions"]["discover_metatrader"]
        action["outputFields"].remove("privacy")
        with self.assertRaisesRegex(
            self.profile_module.EquipmentWorkflowContractError,
            r"^missing_evidence_prerequisite:right_server_racks:discover_metatrader:frontend_safe_candidate_registry$",
        ):
            self.profile_module._validated_payload(payload)

    def test_contract_preflight_validates_schedule_and_completion_evidence(self) -> None:
        payload = copy.deepcopy(self.plugin_map)
        payload["equipment"]["codex_mcp_portal"]["schedule"]["actions"] = ["missing_action"]
        with self.assertRaisesRegex(
            self.profile_module.EquipmentWorkflowContractError,
            r"^invalid_scheduled_action:codex_mcp_portal:missing_action$",
        ):
            self.profile_module._validated_payload(payload)

        payload = copy.deepcopy(self.plugin_map)
        payload["equipment"]["left_audit_crystals"]["schedule"]["defaultTimes"] = ["25:61"]
        with self.assertRaisesRegex(
            self.profile_module.EquipmentWorkflowContractError,
            r"^invalid_schedule_times:left_audit_crystals$",
        ):
            self.profile_module._validated_payload(payload)

        payload = copy.deepcopy(self.plugin_map)
        action = payload["equipment"]["right_tool_console"]["actions"]["prepare_backtest_plan"]
        action["completionEvidenceRequired"].append("imaginary_tester_proof")
        with self.assertRaisesRegex(
            self.profile_module.EquipmentWorkflowContractError,
            r"^unsupported_completion_evidence:right_tool_console:prepare_backtest_plan:imaginary_tester_proof$",
        ):
            self.profile_module._validated_payload(payload)

        payload = copy.deepcopy(self.plugin_map)
        action = payload["equipment"]["codex_mcp_portal"]["actions"]["discover_trading_systems"]
        action["entryContract"]["minimumItemsPerRun"] = 1
        with self.assertRaisesRegex(
            self.profile_module.EquipmentWorkflowContractError,
            r"^invalid_trading_system_entry_contract:codex_mcp_portal:discover_trading_systems$",
        ):
            self.profile_module._validated_payload(payload)

    def test_metatrader_integration_contract_is_frontend_safe(self) -> None:
        forbidden = {"executablePath", "dataFolder", "verifiedPath", "processId", "account", "broker"}
        for prop_id in ("right_server_racks", "right_tool_console"):
            discovery = self.plugin_map["equipment"][prop_id]["actions"]["discover_metatrader"]
            selection = self.plugin_map["equipment"][prop_id]["actions"]["select_metatrader_target"]
            self.assertTrue(forbidden.isdisjoint(discovery["outputFields"]))
            self.assertTrue(forbidden.isdisjoint(selection["outputFields"]))
            self.assertEqual(
                discovery["evidenceRequired"],
                ["backend_observed_at", "frontend_safe_candidate_registry"],
            )
            self.assertIn("selectedCandidate", selection["outputFields"])
            self.assertEqual(selection["requiredInputs"], ["candidateId"])


if __name__ == "__main__":
    unittest.main()
