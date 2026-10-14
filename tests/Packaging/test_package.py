"""Distribution regressions; no WordPress, merchant keys or payment calls."""
from pathlib import Path
import contextlib
import importlib.util
import io
import json
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
import package


def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'tools' / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


prepare = load('prepare', 'prepare-release.py')
plugin_check = load('plugin_check', 'verify-plugin-check.py')


class PackagingTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix='quixdevs-package-tests-')
        self.root = Path(self.directory.name)
        for name in package.runtime_files() + ['tools/runtime-files.json', 'composer.json']:
            target = self.root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / name, target)

    def tearDown(self):
        self.directory.cleanup()

    def build(self):
        with contextlib.redirect_stdout(io.StringIO()):
            return package.build(self.root)

    def archive(self):
        return self.root / 'dist' / f'{package.SLUG}.zip'

    def test_runtime_only_and_reproducible(self):
        first = self.build()
        second = self.build()
        self.assertEqual(first['sha256'], second['sha256'])
        self.assertEqual(first['files'], 27)
        self.assertEqual(first['status'], 'development-only')
        self.assertFalse(first['composer_required_on_server'])
        with zipfile.ZipFile(self.archive()) as archive:
            self.assertIsNone(archive.testzip())
            self.assertTrue(all(name.startswith(package.SLUG + '/') for name in archive.namelist()))
            self.assertFalse(any('/docs/' in name or '/vendor/' in name or '/tests/' in name for name in archive.namelist()))
        self.assertEqual(self.archive().with_suffix('.zip.sha256').read_text(), first['sha256'] + '  ' + self.archive().name + '\n')

    def test_missing_class_fails_before_build(self):
        (self.root / 'includes/Payments/Payment_Lock.php').unlink()
        with self.assertRaisesRegex(ValueError, 'Missing'):
            self.build()

    def test_unreviewed_runtime_class_is_not_silently_omitted(self):
        (self.root / 'includes/New_Class.php').write_text('<?php')
        with self.assertRaisesRegex(ValueError, 'class tree'):
            self.build()

    def test_symlinked_runtime_input_is_refused(self):
        name = 'includes/Payments/Payment_Lock.php'
        (self.root / name).unlink()
        (self.root / name).symlink_to(ROOT / name)
        with self.assertRaisesRegex(ValueError, 'symlinked'):
            self.build()

    def test_unreviewed_production_dependency_is_refused(self):
        path = self.root / 'composer.json'
        data = json.loads(path.read_text())
        data['require']['example/runtime'] = '1.0'
        path.write_text(json.dumps(data))
        with self.assertRaisesRegex(ValueError, 'production dependencies'):
            self.build()

    def test_plugin_version_drift_is_refused(self):
        path = self.root / f'{package.SLUG}.php'
        path.write_text(path.read_text().replace('Version: 1.0.0', 'Version: 1.0.1'))
        with self.assertRaisesRegex(ValueError, 'remain 1.0.0'):
            self.build()

    def test_unexpected_archive_content_is_refused(self):
        self.build()
        with zipfile.ZipFile(self.archive(), 'a') as archive:
            archive.writestr(package.SLUG + '/tests/leaked.php', '<?php')
        with self.assertRaisesRegex(ValueError, 'allowlist'):
            package.verify_archive(self.archive(), self.root)

    def test_changed_runtime_bytes_are_refused(self):
        self.build()
        path = self.root / 'includes/Payments/Payment_Lock.php'
        path.write_text(path.read_text() + '\n')
        with self.assertRaisesRegex(ValueError, 'mismatch'):
            package.verify_archive(self.archive(), self.root)

    def test_wrong_archive_root_is_refused(self):
        self.build()
        with zipfile.ZipFile(self.archive(), 'w') as archive:
            archive.writestr('wrong-plugin/plugin.php', '<?php')
        with self.assertRaisesRegex(ValueError, 'ZIP root'):
            package.verify_archive(self.archive(), self.root)

    def test_credential_pattern_is_refused(self):
        with self.assertRaisesRegex(ValueError, 'Credential'):
            package.scan_content('readme.txt', ('sk_' + 'live_' + 'A' * 30).encode())

    def test_tag_validation_rejects_input_injection_and_version_drift(self):
        for tag in ['v1.0.0\nother', 'master', 'v1.0.1', 'v1.0.0;echo']:
            with self.subTest(tag=tag), self.assertRaises(ValueError):
                prepare.identity(tag, self.root)

    def test_existing_tag_must_match_clean_head(self):
        with patch.object(prepare.subprocess, 'check_output', side_effect=['', 'a' * 40, 'b' * 40]):
            with self.assertRaisesRegex(ValueError, 'checked-out commit'):
                prepare.identity('v1.0.0', self.root)
        with patch.object(prepare.subprocess, 'check_output', return_value=' M README.md'):
            with self.assertRaisesRegex(ValueError, 'clean'):
                prepare.identity('v1.0.0', self.root)
        with patch.object(prepare.subprocess, 'check_output', side_effect=['', 'a' * 40, 'a' * 40]):
            self.assertEqual(prepare.identity('v1.0.0', self.root)['status'], 'development-only')

    def test_plugin_check_output_is_fail_closed(self):
        self.assertEqual(plugin_check.findings('Success: Checks complete. No errors found.\n'), [])
        self.assertEqual(plugin_check.findings('[]'), [])
        for malformed in ['{}', '[{}]', 'Success: ignored errors', 'not JSON']:
            with self.subTest(output=malformed), self.assertRaises(ValueError):
                plugin_check.findings(malformed)

    def test_plugin_check_errors_fail_command(self):
        import subprocess
        report = self.root / 'plugin-check.json'
        report.write_text(json.dumps([{'type': 'ERROR', 'code': 'compressed_files', 'message': 'Unexpected archive'}]))
        result = subprocess.run([sys.executable, str(ROOT / 'tools/verify-plugin-check.py'), str(report)], capture_output=True)
        self.assertEqual(result.returncode, 1)
        self.assertIn(b'1 errors', result.stdout)

    def test_workflow_limits_write_permission_to_unpublished_draft_job(self):
        body = (ROOT / '.github/workflows/release.yml').read_text()
        before, draft = body.split('\n  draft:\n', 1)
        self.assertIn('workflow_dispatch:', body)
        self.assertIn("- 'v*'", body)
        self.assertIn('needs: [identity, quality]', before)
        self.assertIn('needs: [identity, quality, package]', draft)
        self.assertIn('contents: read', before)
        self.assertNotIn('contents: write', before)
        self.assertEqual(draft.count('contents: write'), 1)
        self.assertNotIn('repository.private', body)
        self.assertIn('tools/create-draft-release.py', draft)
        for forbidden in ['continue-on-error:', 'git tag ', 'git push ', 'softprops/action-gh-release', 'gh release edit']:
            self.assertNotIn(forbidden, body)


if __name__ == '__main__':
    unittest.main()
