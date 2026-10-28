"""Keep the release data/news regression gate in step with its source tests."""
from pathlib import Path
import re
import shlex
import unittest


ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / 'frontend/sentiment-universe-src'


class CiTestInventoryTests(unittest.TestCase):
    def test_both_workflows_run_all_news_tests_and_existing_data_embed_contracts(self):
        # The separate 3D/Three test tier needs npm dependencies. These workflow
        # steps deliberately run the dependency-free market/news/embed tier.
        required = {'tests/market-data.test.mjs', 'tests/sentiment-data.test.mjs', 'tests/hq-embed.test.mjs'}
        news = {path.relative_to(FRONTEND).as_posix() for path in (FRONTEND / 'tests').glob('news-*.test.mjs')}
        self.assertIn('tests/news-ai.test.mjs', news)
        required.update(news)
        for name in ('verify.yml', 'publish-release.yml'):
            with self.subTest(workflow=name):
                text = (ROOT / '.github/workflows' / name).read_text(encoding='utf-8-sig')
                commands = re.findall(r'working-directory:\s*frontend/sentiment-universe-src\s+run:\s*\|\s+(node --test[^\r\n]+)', text)
                self.assertEqual(len(commands), 1, 'Expected one explicit frontend regression gate')
                listed = shlex.split(commands[0])[2:]
                self.assertEqual(len(listed), len(set(listed)), 'Duplicate frontend test invocation')
                self.assertFalse(required - set(listed), f'Missing data/news regression tests: {sorted(required - set(listed))}')
                for relative in listed:
                    self.assertTrue((FRONTEND / relative).is_file(), f'Listed frontend test is absent: {relative}')

    def test_release_notes_include_current_version_details_and_existing_user_prompt(self):
        text = (ROOT / '.github/workflows/publish-release.yml').read_text(encoding='utf-8-sig')
        self.assertIn('docs/prompts/update-github-preserve-settings-th.md', text)
        self.assertIn('"docs/releases/$tag-th.md"', text)
        self.assertIn('Get-Content -LiteralPath $versionNotesPath -Raw -Encoding UTF8', text)
        self.assertIn('--notes-file $releaseNotesPath', text)
        self.assertNotIn('--notes $notes', text)

    def test_upgrade_guard_is_required_at_all_three_publish_boundaries(self):
        text = (ROOT / '.github/workflows/publish-release.yml').read_text(encoding='utf-8-sig')
        for marker in ('foreach ($requiredFile in @(', 'foreach ($requiredInstalledFile in @(', 'foreach ($verifiedRuntimeFile in @('):
            with self.subTest(boundary=marker):
                start = text.index(marker)
                body = text[start:text.index(')) {', start)]
                self.assertIn('"installer\\upgrade_guard.py"', body)


if __name__ == '__main__':
    unittest.main()
