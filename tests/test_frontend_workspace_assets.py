from __future__ import annotations

import re
import unittest
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlsplit


ROOT = Path(__file__).resolve().parents[1]
STYLE_FILES = (
    "main.css",
    "workspace.css",
    "agent-workspace.css",
    "dashboard-workspace.css",
    "home.css",
    "home-panels.css",
)


class FrontendDocument(HTMLParser):
    def __init__(self, source: str) -> None:
        super().__init__(convert_charrefs=True)
        self.stylesheets: list[dict[str, str | None]] = []
        self.elements: dict[str, list[tuple[str, dict[str, str | None]]]] = {}
        self.feed(source)

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        if tag == "link" and "stylesheet" in (attributes.get("rel") or "").split():
            self.stylesheets.append(attributes)
        element_id = attributes.get("id")
        if element_id:
            self.elements.setdefault(element_id, []).append((tag, attributes))


class FrontendWorkspaceAssetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.source = (ROOT / "frontend" / "index.html").read_text(encoding="utf-8")
        cls.document = FrontendDocument(cls.source)

    def element(self, element_id: str) -> tuple[str, dict[str, str | None]]:
        matches = self.document.elements.get(element_id, [])
        self.assertEqual(len(matches), 1, f"Expected one element with id={element_id}")
        return matches[0]

    def test_workspace_styles_load_once_in_cascade_order_from_local_files(self) -> None:
        expected = [f"./frontend/src/styles/{name}" for name in STYLE_FILES]
        actual = []
        for link in self.document.stylesheets:
            href = link.get("href") or ""
            parsed = urlsplit(href)
            with self.subTest(href=href):
                self.assertFalse(parsed.scheme)
                self.assertFalse(parsed.netloc)
                self.assertFalse(parsed.fragment)
                relative = unquote(parsed.path)
                path = (ROOT / relative).resolve()
                self.assertTrue(path.is_relative_to(ROOT.resolve()))
                self.assertTrue(path.is_file(), f"Linked stylesheet is missing: {relative}")
                self.assertNotIn("disabled", link)
                self.assertIn(link.get("media"), (None, "", "all", "screen"))
                text = path.read_bytes().decode("utf-8")
                self.assertTrue(text.strip(), f"Linked stylesheet is empty: {relative}")
                self.assertNotIn("\ufffd", text)
                actual.append(parsed.path)
        self.assertEqual(actual, expected)

    def test_all_stylesheets_share_the_runtime_cache_version(self) -> None:
        build = re.search(r'RUNTIME_BUILD_VERSION\s*=\s*"([^"]+)"', self.source)
        self.assertIsNotNone(build)
        for link in self.document.stylesheets:
            with self.subTest(href=link["href"]):
                query = parse_qs(urlsplit(link["href"]).query)
                self.assertEqual(query.get("v"), [build.group(1)])

    def test_modal_shell_and_nested_dialogs_retain_accessible_names(self) -> None:
        _, modal = self.element("gameModal")
        self.assertEqual(modal.get("role"), "dialog")
        self.assertEqual(modal.get("aria-modal"), "true")
        self.assertEqual(modal.get("aria-hidden"), "true")
        self.assertEqual(modal.get("tabindex"), "-1")
        self.assertIn("inert", modal)
        for element_id in (
            "gameModal",
            "taskDetailDialog",
            "dashboardResultDialog",
            "newsEventDialog",
        ):
            with self.subTest(dialog=element_id):
                tag, attributes = self.element(element_id)
                if element_id != "gameModal":
                    self.assertEqual(tag, "dialog")
                    self.assertNotIn("open", attributes)
                labels = (attributes.get("aria-labelledby") or "").split()
                self.assertTrue(labels)
                for label in labels:
                    self.element(label)

    def test_initial_agent_permissions_stay_backend_gated(self) -> None:
        for element_id in ("modalAgentModelSelect", "modalAgentReasoningSelect"):
            with self.subTest(control=element_id):
                _, attributes = self.element(element_id)
                self.assertIn("disabled", attributes)
        _, full_access = self.element("modalAgentFullAccessButton")
        self.assertEqual(full_access.get("data-state"), "locked")
        self.assertEqual(full_access.get("aria-pressed"), "false")
        self.assertEqual(full_access.get("aria-disabled"), "true")
        _, approval = self.element("modalAgentApprovalPanel")
        self.assertIn("hidden", approval)
        self.assertEqual(approval.get("role"), "alertdialog")


if __name__ == "__main__":
    unittest.main()
