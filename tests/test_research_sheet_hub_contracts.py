import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_json(relative_path: str) -> dict:
    return json.loads((ROOT / relative_path).read_text(encoding="utf-8"))


EXPECTED_TABS = {
    "codex_mcp_portal": ("World_System", "read_write"),
    "left_server_racks": ("Deep_Research", "read_write"),
    "left_audit_crystals": ("Indicator_EA_Tool", "read_write"),
}
EXCLUDED_PROPS = {"right_tool_console", "terminal_workstation"}
FAIL_CLOSED_STATUSES = {
    "auth_required",
    "permission_denied",
    "schema_mismatch",
}
READY_STATUSES = {
    "read_ready_write_unverified",
    "ready",
}
RUNTIME_STATUSES = FAIL_CLOSED_STATUSES | READY_STATUSES
LIFECYCLE_PHASES = [
    "draft",
    "inspecting",
    "awaiting_confirmation",
    "activating",
    "active",
]
ACTIVE_DISPLAY_FIELDS = {
    "active",
    "sheetId",
    "canonicalUrl",
    "configRevision",
    "activeConfigRevision",
    "activationConfirmedAt",
}
ACTIVATE_REQUEST_FIELDS = {
    "verificationToken",
    "confirmActivate",
    "expectedConfigRevision",
    "idempotencyKey",
}
ACTIVE_CONSUMER_EVIDENCE_FIELDS = {
    "tabName",
    "configRevision",
    "configurationApplied",
    "status",
    "readReady",
    "writeReady",
    "rowCount",
    "cachedRowCount",
    "observedAt",
    "rowsObservedAt",
    "outbox",
}
INSPECTION_CONSUMER_EVIDENCE_FIELDS = {
    "propId",
    "consumerId",
    "tabName",
    "mode",
    "status",
    "readReady",
    "rowCount",
    "cachedRowCount",
    "observedAt",
    "rowsObservedAt",
    "probeEvidence",
    "missingHeaders",
    "duplicateHeaders",
}
INSPECTION_PREVIEW_FIELDS = {
    "schemaVersion",
    "sheetId",
    "canonicalUrl",
    "sheetTitle",
    "baseConfigRevision",
    "proposedConfigRevision",
    "status",
    "readyForConfirmation",
    "verificationToken",
    "issuedAt",
    "expiresAt",
    "totalConsumerCount",
    "verifiedConsumerCount",
    "consumers",
    "credentialsAcceptedByFrontend",
    "oauthSecretsExposed",
}
EXPECTED_LINKED_SYSTEMS = {
    "codex_mcp_portal": ("codex_mcp_portal", "World_System", "read_write"),
    "left_server_racks": ("left_server_racks", "Deep_Research", "read_write"),
    "right_server_racks": ("left_server_racks", "Deep_Research", "read"),
    "left_audit_crystals": ("left_audit_crystals", "Indicator_EA_Tool", "read_write"),
}


class ResearchSheetHubContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.bridge = load_json("contracts/bridge/bridge-contract.json")
        cls.connections = load_json("contracts/connections/dashboard-connection-contract.json")
        cls.tools = load_json("contracts/tools/tool-permission-contract.json")
        cls.reports = load_json("contracts/reports/report-contract.json")
        cls.roles = load_json("contracts/props/property-role-map.json")
        cls.equipment = load_json("contracts/workflows/equipment-plugin-map.json")
        cls.factory = load_json("contracts/workflows/ea-factory-contract.json")
        cls.radar = load_json("contracts/research/radar-website-tool-compatibility-v1.json")

    def test_bridge_declares_one_central_config_and_fixed_consumers(self) -> None:
        hub = self.bridge["research_sheet_hub"]
        self.assertEqual(hub["configurationOwnerPropId"], "mission_strategy_table")
        self.assertEqual(set(hub["statusVocabulary"]) & FAIL_CLOSED_STATUSES, FAIL_CLOSED_STATUSES)
        mappings = {
            item["propId"]: (item["tabName"], item["mode"])
            for item in hub["consumers"]
        }
        self.assertEqual(mappings, EXPECTED_TABS)
        self.assertEqual(set(hub["excludedPropIds"]), EXCLUDED_PROPS)
        self.assertEqual(hub["frontendIntent"]["inspectRequestFields"], ["googleSheetUrlOrId"])
        self.assertEqual(set(hub["frontendIntent"]["activateRequestFields"]), ACTIVATE_REQUEST_FIELDS)
        self.assertTrue(hub["frontendIntent"]["confirmActivateMustBeTrue"])
        self.assertFalse(hub["frontendIntent"]["credentialsAccepted"])
        self.assertTrue(hub["frontendIntent"]["rawSheetIdReturned"])
        self.assertFalse(hub["frontendIntent"]["sheetIdIsCredential"])
        self.assertTrue(hub["frontendIntent"]["persistedValueMayPopulateFrontend"])
        self.assertEqual(hub["lifecycle"]["orderedPhases"], LIFECYCLE_PHASES)
        self.assertEqual(hub["lifecyclePhaseVocabulary"][1:6], LIFECYCLE_PHASES)
        self.assertTrue(hub["lifecycle"]["draftDoesNotReplaceActiveRevision"])
        self.assertTrue(hub["lifecycle"]["inspectionVerifiesAllThreeConsumersBeforeConfirmation"])
        self.assertTrue(hub["lifecycle"]["confirmationRequiredBeforeActivation"])
        self.assertEqual(set(hub["lifecycle"]["activationBindingFields"]), ACTIVATE_REQUEST_FIELDS)
        self.assertTrue(hub["lifecycle"]["verificationTokenIsShortLivedAndOneTime"])
        self.assertTrue(hub["lifecycle"]["configRevisionIncrementsOnlyOnActivation"])
        self.assertTrue(hub["lifecycle"]["activationIsAtomicForAllThreeConsumers"])
        self.assertTrue(hub["lifecycle"]["failedCandidateLeavesActiveRevisionUnchanged"])
        self.assertEqual(
            set(hub["activeSheetReadModel"]["persistentDisplayFields"]),
            ACTIVE_DISPLAY_FIELDS,
        )
        self.assertTrue(hub["activeSheetReadModel"]["frontendMayKeepActiveValueVisibleWhileEditingDraft"])
        self.assertTrue(
            INSPECTION_CONSUMER_EVIDENCE_FIELDS
            <= set(hub["inspectionConsumerEvidenceFields"])
        )
        self.assertEqual(set(hub["inspectionPreviewFields"]), INSPECTION_PREVIEW_FIELDS)
        self.assertEqual(
            set(hub["activationResponseFields"]),
            {"active", "status", "configRevision", "activationConfirmedAt"},
        )
        self.assertTrue(
            ACTIVE_CONSUMER_EVIDENCE_FIELDS <= set(hub["activeConsumerEvidenceFields"])
        )
        self.assertEqual(
            [secondary for item in hub["consumers"] for secondary in item["secondaryReaders"]],
            [{"propId": "right_server_racks", "purpose": "ea_factory_verified_read_only_source", "mode": "read"}],
        )
        self.assertIn("all three fixed consumers", hub["successRule"])
        self.assertIn("permission_denied", hub["failClosedStatusRules"])
        endpoints = self.bridge["endpoints"]
        for endpoint in (
            "GET /api/props/mission_strategy_table/research-sheet",
            "POST /api/props/mission_strategy_table/research-sheet/inspect",
            "POST /api/props/mission_strategy_table/research-sheet/activate",
            "POST /api/props/mission_strategy_table/research-sheet/flush",
        ):
            self.assertIn(endpoint, endpoints)
        for obsolete_endpoint in (
            "POST /api/props/mission_strategy_table/research-sheet",
            "POST /api/props/mission_strategy_table/research-sheet/verify",
            "POST /api/props/mission_strategy_table/research-sheet/confirm",
        ):
            self.assertNotIn(obsolete_endpoint, endpoints)

    def test_connection_profiles_use_backend_runtime_status_without_claiming_connected(self) -> None:
        hub = self.connections["researchSheetHub"]
        self.assertEqual(hub["configurationPropId"], "mission_strategy_table")
        self.assertTrue(hub["rawSheetIdExposed"])
        self.assertFalse(hub["sheetIdIsCredential"])
        self.assertTrue(hub["frontendRetainsConfiguredSheetId"])
        self.assertTrue(hub["applyRequiresTwoStepConfirmation"])
        self.assertTrue(hub["confirmationOccursAfterSuccessfulVerification"])
        self.assertTrue(hub["lifecycleRules"]["activationRequiresCurrentVerificationToken"])
        self.assertTrue(hub["lifecycleRules"]["verificationTokenIsShortLivedAndOneTime"])
        self.assertTrue(hub["lifecycleRules"]["confirmActivateMustBeTrue"])
        self.assertEqual(hub["inspectEndpoint"].rsplit("/", 1)[-1], "inspect")
        self.assertEqual(hub["activateEndpoint"].rsplit("/", 1)[-1], "activate")
        self.assertEqual(hub["inspectRequestFields"], ["googleSheetUrlOrId"])
        self.assertEqual(set(hub["activateRequestFields"]), ACTIVATE_REQUEST_FIELDS)
        self.assertEqual(hub["lifecycleRules"]["orderedPhases"], LIFECYCLE_PHASES)
        self.assertTrue(hub["activeSheetDisplay"]["persistent"])
        self.assertTrue(hub["activeSheetDisplay"]["remainsVisibleDuringDraftAndFailure"])
        self.assertEqual(set(hub["activeSheetDisplay"]["fields"]), ACTIVE_DISPLAY_FIELDS)
        self.assertEqual(set(hub["statusVocabulary"]), RUNTIME_STATUSES)
        self.assertEqual(
            {key: (value["tabName"], value["mode"]) for key, value in hub["consumers"].items()},
            EXPECTED_TABS,
        )
        self.assertEqual(
            {
                key: (value["consumerPropId"], value["tabName"], value["mode"])
                for key, value in hub["linkedSystems"].items()
            },
            EXPECTED_LINKED_SYSTEMS,
        )
        self.assertTrue(
            INSPECTION_CONSUMER_EVIDENCE_FIELDS
            <= set(hub["inspectionConsumerEvidenceFields"])
        )
        self.assertTrue(
            ACTIVE_CONSUMER_EVIDENCE_FIELDS <= set(hub["activeConsumerEvidenceFields"])
        )
        self.assertIn("not a fourth tab", hub["linkedSystemStatusRule"])
        profiles = self.connections["profiles"]
        for prop_id, (tab_name, mode) in EXPECTED_TABS.items():
            sheet_connections = [
                item
                for item in profiles[prop_id]["connections"]
                if item["id"] == "google_sheets_adapter"
            ]
            self.assertEqual(len(sheet_connections), 1)
            self.assertEqual(sheet_connections[0]["tabName"], tab_name)
            self.assertEqual(sheet_connections[0]["mode"], mode)
            self.assertEqual(sheet_connections[0]["runtimeStatusSource"], "researchSheetConsumer")
            self.assertNotEqual(sheet_connections[0]["adapterStatus"], "connected")
        for prop_id in EXCLUDED_PROPS:
            self.assertFalse(profiles[prop_id]["researchSheetHub"]["included"])
            self.assertFalse(any("google_sheet" in item["id"] for item in profiles[prop_id]["connections"]))

    def test_property_roles_and_equipment_map_match_the_same_scope(self) -> None:
        roles = self.roles["properties"]
        mission_hub = roles["mission_strategy_table"]["researchSheetHub"]
        self.assertTrue(mission_hub["configurationOwner"])
        self.assertEqual(mission_hub["lifecyclePhases"], LIFECYCLE_PHASES)
        self.assertTrue(mission_hub["activeRevisionPersistsUntilConfirmedReplacement"])
        self.assertTrue(mission_hub["failedDraftDoesNotReplaceActiveRevision"])
        self.assertEqual(set(mission_hub["activeSheetDisplayFields"]), ACTIVE_DISPLAY_FIELDS)
        self.assertTrue(
            ACTIVE_CONSUMER_EVIDENCE_FIELDS
            <= set(mission_hub["activeConsumerReadEvidenceFields"])
        )
        self.assertEqual(
            {key: (value, EXPECTED_TABS[key][1]) for key, value in mission_hub["consumers"].items()},
            EXPECTED_TABS,
        )
        for prop_id, expected in EXPECTED_TABS.items():
            role_hub = roles[prop_id]["researchSheetHub"]
            self.assertEqual((role_hub["tabName"], role_hub["mode"]), expected)
        for prop_id in EXCLUDED_PROPS:
            self.assertFalse(roles[prop_id]["researchSheetHub"]["included"])

        equipment_hub = self.equipment["researchSheetHub"]
        self.assertEqual(
            {key: (value["tabName"], value["mode"]) for key, value in equipment_hub["equipmentTabs"].items()},
            EXPECTED_TABS,
        )
        self.assertEqual(set(equipment_hub["excludedEquipmentIds"]), EXCLUDED_PROPS)
        self.assertEqual(equipment_hub["frontendCredentialFields"], [])
        self.assertEqual(equipment_hub["lifecyclePhaseVocabulary"][1:6], LIFECYCLE_PHASES)
        self.assertEqual(
            {
                key: (value["consumerPropId"], value["tabName"], value["mode"])
                for key, value in equipment_hub["linkedSystems"].items()
            },
            EXPECTED_LINKED_SYSTEMS,
        )
        self.assertFalse(equipment_hub["linkedSystems"]["right_server_racks"]["fourthTab"])
        self.assertEqual(equipment_hub["inspectRequestFields"], ["googleSheetUrlOrId"])
        self.assertEqual(set(equipment_hub["activateRequestFields"]), ACTIVATE_REQUEST_FIELDS)
        self.assertTrue(
            ACTIVE_CONSUMER_EVIDENCE_FIELDS
            <= set(equipment_hub["activeConsumerReadEvidenceFields"])
        )

    def test_tool_permissions_separate_config_writes_and_factory_read(self) -> None:
        tools = {item["id"]: item for item in self.tools["tools"]}
        configure = tools["research_sheet_hub_configure"]
        self.assertEqual(configure["linkedPropIds"], ["mission_strategy_table"])
        self.assertEqual(configure["frontendCredentialFields"], [])
        self.assertTrue(configure["credentialsBackendOnly"])
        self.assertTrue(configure["rawSheetIdExposed"])
        self.assertFalse(configure["sheetIdIsCredential"])
        self.assertTrue(configure["frontendRetainsConfiguredSheetId"])
        self.assertTrue(configure["applyRequiresTwoStepConfirmation"])
        self.assertTrue(configure["confirmationOccursAfterSuccessfulVerification"])
        self.assertEqual(configure["inspectRequestFields"], ["googleSheetUrlOrId"])
        self.assertEqual(set(configure["activateRequestFields"]), ACTIVATE_REQUEST_FIELDS)
        self.assertEqual(set(configure["activationConfirmationFields"]), ACTIVATE_REQUEST_FIELDS)
        self.assertTrue(configure["verificationTokenIsShortLivedAndOneTime"])
        self.assertTrue(configure["confirmActivateMustBeTrue"])
        self.assertEqual(configure["lifecyclePhases"], LIFECYCLE_PHASES)
        self.assertTrue(configure["candidateFailurePreservesActiveRevision"])
        self.assertTrue(configure["configRevisionIncrementsOnlyOnActivation"])
        self.assertTrue(
            ACTIVE_CONSUMER_EVIDENCE_FIELDS
            <= set(configure["activeConsumerReadEvidenceFields"])
        )
        self.assertIn("permission_denied", configure["runtimeBlockedStatuses"])
        self.assertEqual(set(configure["excludedPropIds"]), EXCLUDED_PROPS)

        sync = tools["google_sheet_catalog_sync"]
        self.assertEqual(
            set(sync["linkedPropIds"]),
            {"codex_mcp_portal", "left_server_racks", "left_audit_crystals"},
        )
        self.assertNotIn("right_server_racks", sync["linkedPropIds"])
        self.assertTrue(sync["unavailableFailsClosedToDurableOutbox"])
        self.assertTrue(sync["credentialsBackendOnly"])

        factory_read = tools["ea_factory_google_sheet_read"]
        self.assertEqual(factory_read["centralConfigurationPropId"], "mission_strategy_table")
        self.assertEqual(factory_read["sheetTabDefault"], "Deep_Research")
        self.assertEqual(factory_read["sheetRange"], "A-AW")
        self.assertEqual(factory_read["sheetHeadersRequired"], 49)
        self.assertEqual(factory_read["internalMapping"], "23 EA strategy fields (not a Sheet range)")
        self.assertEqual(factory_read["frontendIntentFields"], ["configRevision", "idempotencyKey"])
        self.assertFalse(factory_read["externalWriteEnabled"])

    def test_report_projection_is_bounded_to_three_producers_and_three_tabs(self) -> None:
        projection = self.reports["research_sheet_hub_projection"]
        mappings = projection["mappings"]
        self.assertEqual(len(mappings), 3)
        self.assertEqual({item["tabName"] for item in mappings}, {value[0] for value in EXPECTED_TABS.values()})
        self.assertEqual(
            {item["producerPropId"] for item in mappings},
            {"codex_mcp_portal", "left_server_racks", "left_audit_crystals"},
        )
        self.assertFalse(any(item.get("consumerPropId") == "right_server_racks" for item in mappings))
        self.assertEqual(set(projection["excludedPropIds"]), EXCLUDED_PROPS)
        self.assertTrue(projection["delivery"]["exactReadBackRequired"])
        self.assertTrue(projection["activeRevisionRequired"])
        self.assertTrue(projection["candidateDraftReportsNeverProject"])
        self.assertTrue(
            ACTIVE_CONSUMER_EVIDENCE_FIELDS
            <= set(projection["consumerReadEvidenceFields"])
        )

    def test_ea_factory_and_radar_cannot_override_central_sheet_contract(self) -> None:
        factory_sheet = self.factory["sourceContract"]["googleSheets"]
        self.assertEqual(factory_sheet["configurationPropId"], "mission_strategy_table")
        self.assertEqual(factory_sheet["tabName"], "Deep_Research")
        self.assertEqual(factory_sheet["sharedConsumerPropId"], "left_server_racks")
        self.assertFalse(factory_sheet["dedicatedCentralTab"])
        self.assertFalse(factory_sheet["fourthCentralTab"])
        self.assertEqual(factory_sheet["statusSource"], "active_current_revision_left_server_racks_read_proof")
        self.assertTrue(factory_sheet["requiresActiveConfirmedRevision"])
        self.assertTrue(
            {"tabName", "configRevision", "status", "readReady", "rowCount", "cachedRowCount", "observedAt"}
            <= set(factory_sheet["requiredReadEvidenceFields"])
        )
        self.assertEqual(factory_sheet["sourceRangeRequired"], "A-AW (49 required headers; extra columns allowed)")
        self.assertEqual(factory_sheet["internalMapping"], "23 EA strategy fields (not a Sheet range)")
        self.assertEqual(factory_sheet["frontendIntentFields"], ["configRevision", "idempotencyKey"])
        self.assertFalse(factory_sheet["externalWrites"])
        self.assertTrue(factory_sheet["credentialsBackendOnly"])
        self.assertEqual(set(factory_sheet["runtimeStatuses"]), RUNTIME_STATUSES)

        radar_hub = self.radar["researchSheetHub"]
        self.assertEqual(radar_hub["configurationPropId"], "mission_strategy_table")
        self.assertEqual(radar_hub["tabName"], "Indicator_EA_Tool")
        self.assertFalse(radar_hub["configurationAvailableHere"])
        self.assertTrue(radar_hub["requiresActiveConfirmedRevision"])
        self.assertTrue(
            {"tabName", "configRevision", "status", "readReady", "rowCount", "cachedRowCount", "observedAt"}
            <= set(radar_hub["requiredReadEvidenceFields"])
        )
        self.assertEqual(radar_hub["frontendCredentialFields"], [])
        self.assertEqual(set(radar_hub["runtimeStatuses"]), RUNTIME_STATUSES)


if __name__ == "__main__":
    unittest.main()
