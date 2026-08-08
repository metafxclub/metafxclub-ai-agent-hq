from __future__ import annotations

import json
import re
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FRONTEND_MAIN_PATH = PROJECT_ROOT / "frontend" / "src" / "app" / "main.js"
MISMATCH_FIXTURE_PATH = PROJECT_ROOT / "tests" / "fixtures" / "frontend-signing-key-mismatch.json"
KEY_ID_PATTERN = re.compile(r"^hk-[0-9a-f]{64}$")


class FrontendSigningKeyCopyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.main = FRONTEND_MAIN_PATH.read_text(encoding="utf-8")

    def _copy_helper_source(self) -> str:
        start = self.main.index("const SIGNAL_SIGNING_KEY_ID_PATTERN")
        end = self.main.index("function renderSignalRiskList", start)
        return self.main[start:end]

    def _risk_list_source(self) -> str:
        start = self.main.index("function renderSignalRiskList")
        end = self.main.index("function signalChartSnapshotModel", start)
        return self.main[start:end]

    def test_mismatch_fixture_uses_backend_key_as_authoritative_copy_value(self) -> None:
        fixture = json.loads(MISMATCH_FIXTURE_PATH.read_text(encoding="utf-8"))
        runtime = fixture["runtime"]
        expected = fixture["expected"]

        self.assertRegex(runtime["backendSigningKeyId"], KEY_ID_PATTERN)
        self.assertRegex(runtime["activeSigningKeyId"], KEY_ID_PATTERN)
        self.assertNotEqual(runtime["backendSigningKeyId"], runtime["activeSigningKeyId"])
        self.assertEqual(expected["copySource"], "backendSigningKeyId")
        self.assertEqual(expected["copyValue"], runtime["backendSigningKeyId"])
        self.assertFalse(expected["ready"])

        helper = self._copy_helper_source()
        self.assertIn("/^hk-[0-9a-f]{64}$/", helper)
        self.assertIn("runtime.backendSigningKeyId", helper)
        self.assertIn("runtime.activeSigningKeyId", helper)
        self.assertIn("eaReportedSigningKeyId !== backendSigningKeyId", helper)
        self.assertIn("copyValue: backendSigningKeyId", helper)
        self.assertIn(expected["message"], helper)

    def test_risk_list_never_copies_ea_reported_active_key(self) -> None:
        risk_list = self._risk_list_source()

        self.assertIn("const signingKey = signalSigningKeyCopyState(runtime);", risk_list)
        self.assertIn(
            '["Key ID สำหรับตั้ง Live", signingKey.ready, signingKey.label, signingKey.copyValue]',
            risk_list,
        )
        self.assertNotIn("Boolean(runtime.activeSigningKeyId)", risk_list)
        self.assertNotIn("navigator.clipboard.writeText(runtime.activeSigningKeyId)", risk_list)
        self.assertIn("คัดลอก Key ID จาก Backend แล้ว", risk_list)

    def test_invalid_or_missing_backend_key_is_not_copyable(self) -> None:
        helper = self._copy_helper_source()

        self.assertIn("if (!backendKeyReady)", helper)
        self.assertIn("Key ID จาก Backend ยังไม่พร้อม • กรุณาตรวจ Local Runner", helper)
        unavailable_branch = helper.split("if (!backendKeyReady)", 1)[1].split(
            "if (eaReportedSigningKeyId", 1
        )[0]
        self.assertIn('copyValue: ""', unavailable_branch)


if __name__ == "__main__":
    unittest.main()
