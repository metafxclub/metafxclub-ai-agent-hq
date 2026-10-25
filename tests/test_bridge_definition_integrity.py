"""Catch merge duplicates that silently replace reviewed runtime guards."""
import ast
from collections import Counter
from pathlib import Path
import unittest


class BridgeDefinitionIntegrityTests(unittest.TestCase):
    def test_top_level_runtime_definitions_cannot_shadow_each_other(self):
        source = Path(__file__).resolve().parents[1] / "backend/local-runner/bridge_server.py"
        module = ast.parse(source.read_text(encoding="utf-8-sig"))
        definitions = Counter(
            node.name for node in module.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
        )
        duplicates = {name: count for name, count in definitions.items() if count > 1}
        self.assertEqual(duplicates, {}, "Duplicate definitions silently override runtime guards")
