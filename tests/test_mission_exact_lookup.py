from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]


class MissionExactLookupTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        spec = importlib.util.spec_from_file_location(
            "mission_exact_lookup_bridge",
            ROOT / "backend" / "local-runner" / "bridge_server.py",
        )
        assert spec is not None and spec.loader is not None
        cls.bridge = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.bridge)

    def setUp(self) -> None:
        self.bridge._invalidate_missions_read_cache()

    def test_lookup_copies_only_selected_mission_and_keeps_nested_changes_private(self) -> None:
        class UnrelatedArchivePayload:
            def __deepcopy__(self, memo):
                raise AssertionError("An exact lookup copied unrelated archive payload")

        selected = {"id": "selected", "status": "completed", "receipt": {"valid": True}}
        archive = [
            {"id": "unrelated", "payload": UnrelatedArchivePayload()},
            selected,
        ]
        with mock.patch.object(self.bridge, "load_missions", return_value=archive) as loader:
            first = self.bridge.find_mission("selected")
            first["status"] = "cancelled"
            first["receipt"]["valid"] = False
            second = self.bridge.find_mission("selected")
            self.assertIsNone(self.bridge.find_mission("missing"))
        self.assertEqual(second, selected)
        self.assertEqual(second["status"], "completed")
        self.assertTrue(second["receipt"]["valid"])
        self.assertIsNot(second, selected)
        self.assertIsNot(second["receipt"], selected["receipt"])
        self.assertEqual(loader.call_args_list, [mock.call(shared_snapshot=True)] * 3)

    def test_lookup_observes_replaced_store_and_rejects_corruption_instead_of_cached_row(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "missions.json"

            def replace(contents: str) -> None:
                replacement = path.with_suffix(".replacement")
                replacement.write_text(contents, encoding="utf-8")
                replacement.replace(path)

            replace(json.dumps({"missions": [{"id": "selected", "status": "queued"}]}))
            with mock.patch.object(self.bridge, "MISSIONS_PATH", path):
                self.assertEqual(self.bridge.find_mission("selected")["status"], "queued")
                replace(json.dumps({"missions": [{"id": "selected", "status": "completed"}]}))
                self.assertEqual(self.bridge.find_mission("selected")["status"], "completed")
                replace("{invalid-json")
                with self.assertRaises(self.bridge.DataIntegrityError):
                    self.bridge.find_mission("selected")
                self.assertEqual(path.read_text(encoding="utf-8"), "{invalid-json")


if __name__ == "__main__":
    unittest.main()
