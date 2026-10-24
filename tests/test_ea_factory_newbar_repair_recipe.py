"""Corrective guidance must not permit entry on the first available bar."""
import re
import shutil
import subprocess
import unittest
from pathlib import Path

import test_ea_factory_source_repair_context as context_support


class EaFactoryNewBarRepairRecipeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        context_support.EaFactorySourceRepairContextTests.setUpClass()

    def setUp(self):
        self.fixture = context_support.EaFactorySourceRepairContextTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.runner = self.fixture.runner
        self.recipe = self.runner.EA_FACTORY_SOURCE_SEMANTIC_REPAIR_RECIPES[
            "ea_closed_bar_execution_guard_missing"
        ]

    def test_actual_corrective_prompt_primes_before_same_bar_guard_and_entry(self):
        original = self.fixture.path.read_bytes()
        prompt = self.runner.build_ea_factory_source_semantic_repair_prompt(
            self.fixture.prompt,
            ["ea_closed_bar_execution_guard_missing"],
            validated_strategy_context=self.fixture.context(),
        )
        section = prompt.split("Exact structural recipes for those findings:", 1)[1].split(
            "Policy-specific interpretation", 1
        )[0]
        self.assertIn(self.recipe, section)
        ordered = (
            "if(currentBar<=0) return;",
            "if(lastBar==0){lastBar=currentBar; return;}",
            "if(currentBar==lastBar) return;",
            "lastBar=currentBar;`",
        )
        positions = [section.index(part) for part in ordered]
        self.assertEqual(positions, sorted(positions))
        self.assertIn("return without entering", section)
        self.assertIn("shift 1 or older", section)
        self.assertIn("No Markdown, explanation, extra fields, tools", prompt)
        self.assertEqual(self.fixture.path.read_bytes(), original)

    def test_emitted_recipe_blocks_zero_startup_and_repeated_bar_then_allows_next(self):
        # Execute only the primitive state transition emitted in the actual
        # recipe; translate its declarations/time read, not its conditions.
        snippet = re.search(r"`([^`]+)`", self.recipe).group(1)
        self.assertEqual(snippet.count("static datetime lastBar=0;"), 1)
        self.assertEqual(snippet.count("datetime currentBar=iTime(_Symbol,PERIOD_CURRENT,0);"), 1)
        transition = snippet.replace("static datetime lastBar=0;", "", 1).replace(
            "datetime currentBar=iTime(_Symbol,PERIOD_CURRENT,0);", "const currentBar=observedBar;", 1
        )
        script = """
const assert=require('node:assert/strict');let lastBar=0,entries=0;
function tick(observedBar){TRANSITION entries++;}
tick(0);assert.equal(lastBar,0);assert.equal(entries,0);
tick(120);assert.equal(lastBar,120);assert.equal(entries,0);
tick(120);assert.equal(entries,0);
tick(180);assert.equal(lastBar,180);assert.equal(entries,1);
tick(180);assert.equal(entries,1);
tick(0);assert.equal(lastBar,180);assert.equal(entries,1);
tick(240);assert.equal(entries,2);
""".replace("TRANSITION", transition)
        node = shutil.which("node") or str(
            Path.home() / ".cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe"
        )
        result = subprocess.run([node, "-"], input=script, text=True,
                                capture_output=True, encoding="utf-8", timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
