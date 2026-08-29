from __future__ import annotations

import ast
import csv
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BRIDGE_PATH = ROOT / "backend" / "local-runner" / "bridge_server.py"

WRITE_TEMPLATE_BY_PROP = {
    "codex_mcp_portal": ROOT / "contracts" / "research" / "world-system-sheet-template.csv",
    "left_server_racks": ROOT / "contracts" / "research" / "deep-research-sheet-template.csv",
    "left_audit_crystals": ROOT / "contracts" / "research" / "indicator-ea-tool-sheet-template.csv",
}
HEADER_SOURCE_BY_PROP = {
    "codex_mcp_portal": "RESEARCH_SHEET_WORLD_WRITE_HEADERS",
    "left_server_racks": "RESEARCH_SHEET_DEEP_WRITE_HEADERS",
    "left_audit_crystals": "RESEARCH_SHEET_RADAR_WRITE_HEADERS",
}


def assignment_nodes(path: Path) -> dict[str, ast.AST]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    result: dict[str, ast.AST] = {}
    for node in tree.body:
        if (
            isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
        ):
            result[node.targets[0].id] = node.value
    return result


def hub_contract_nodes(assignments: dict[str, ast.AST]) -> dict[str, dict[str, ast.AST]]:
    hub_node = assignments["RESEARCH_SHEET_HUB_PROP_TABS"]
    if not isinstance(hub_node, ast.Dict):
        raise AssertionError("RESEARCH_SHEET_HUB_PROP_TABS must remain a dict literal")
    contracts: dict[str, dict[str, ast.AST]] = {}
    for prop_node, contract_node in zip(hub_node.keys, hub_node.values):
        if prop_node is None or not isinstance(contract_node, ast.Dict):
            raise AssertionError("Research Sheet Hub contracts must use literal prop dictionaries")
        prop_id = ast.literal_eval(prop_node)
        contracts[prop_id] = {
            ast.literal_eval(key_node): value_node
            for key_node, value_node in zip(contract_node.keys, contract_node.values)
            if key_node is not None
        }
    return contracts


def referenced_header_source(node: ast.AST) -> str:
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "list":
        if len(node.args) == 1 and isinstance(node.args[0], ast.Name):
            return node.args[0].id
    if isinstance(node, ast.ListComp) and isinstance(node.generators[0].iter, ast.Name):
        return node.generators[0].iter.id
    raise AssertionError("requiredHeaders must reference the live header constant")


def read_schema_template(path: Path) -> tuple[list[str], list[list[str]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.reader(handle))
    if not rows:
        raise AssertionError(f"Schema template is empty: {path}")
    headers = [cell.strip() for cell in rows[0]]
    return headers, rows


def canonical_headers(headers: list[str]) -> list[str]:
    return [header.split("/", 1)[0].strip() for header in headers]


class ResearchSheetHubSchemaTemplateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.assignments = assignment_nodes(BRIDGE_PATH)
        cls.contracts = hub_contract_nodes(cls.assignments)
        cls.required_by_prop = {
            "codex_mcp_portal": list(
                ast.literal_eval(cls.assignments["RESEARCH_SHEET_WORLD_WRITE_HEADERS"])
            ),
            "left_server_racks": list(
                ast.literal_eval(cls.assignments["RESEARCH_SHEET_DEEP_WRITE_HEADERS"])
            ),
            "left_audit_crystals": list(
                ast.literal_eval(cls.assignments["RESEARCH_SHEET_RADAR_WRITE_HEADERS"])
            ),
        }

    def test_hub_required_headers_reference_the_live_header_sources(self) -> None:
        self.assertEqual(set(self.contracts), set(HEADER_SOURCE_BY_PROP))
        for prop_id, source_name in HEADER_SOURCE_BY_PROP.items():
            with self.subTest(prop_id=prop_id):
                contract = self.contracts[prop_id]
                self.assertEqual(referenced_header_source(contract["requiredHeaders"]), source_name)
                self.assertEqual(ast.literal_eval(contract["keyHeader"]), self.required_by_prop[prop_id][0])

    def test_write_tab_templates_match_live_required_headers_exactly(self) -> None:
        for prop_id, template_path in WRITE_TEMPLATE_BY_PROP.items():
            with self.subTest(prop_id=prop_id, template=template_path.name):
                headers, rows = read_schema_template(template_path)
                canonical = canonical_headers(headers)

                self.assertEqual(rows, [headers], "Schema templates must contain one header row only")
                self.assertEqual(headers, canonical, "Write templates must use canonical machine headers")
                self.assertEqual(canonical, self.required_by_prop[prop_id])
                self.assertEqual(len(canonical), len(set(canonical)), "Duplicate canonical header")

    def test_deep_research_is_the_only_factory_source_tab(self) -> None:
        headers, rows = read_schema_template(WRITE_TEMPLATE_BY_PROP["left_server_racks"])
        self.assertEqual(rows, [headers], "Schema templates must contain one header row only")
        self.assertEqual(len(headers), 49)
        self.assertNotIn("right_server_racks", self.contracts)


if __name__ == "__main__":
    unittest.main()
