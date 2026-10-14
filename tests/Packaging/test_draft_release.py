"""Draft-only GitHub CLI safety regressions; all remote operations are mocked."""
from pathlib import Path
import contextlib
import copy
import hashlib
import importlib.util
import io
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
import package
spec = importlib.util.spec_from_file_location('draft', ROOT / 'tools/create-draft-release.py')
draft = importlib.util.module_from_spec(spec)
spec.loader.exec_module(draft)

REPO = 'hasancse06/QuixDevs-Stripe-Rest-Payments-Woocommerce'
COMMIT = 'a' * 40
TAG = 'v1.0.0'


class FakeGitHub:
    def __init__(self, directory, existing=False):
        self.directory = directory
        self.commands = []
        self.tag_commit = COMMIT
        self.details = self.record() if existing else None
        self.publish_after_upload = False

    def record(self):
        return {'draft': True, 'prerelease': True, 'tag_name': TAG, 'target_commitish': COMMIT,
                'body': draft.release_notes(self.directory), 'assets': [],
                'html_url': f'https://github.com/{REPO}/releases/tag/{TAG}'}

    def api(self, path, allow_missing=False):
        if '/git/ref/tags/' in path:
            return {'object': {'type': 'commit', 'sha': self.tag_commit}}
        if '/releases/tags/' in path:
            if self.details is None and not allow_missing:
                raise draft.ReleaseError('Missing draft')
            return copy.deepcopy(self.details)
        raise AssertionError(path)

    def asset(self, name):
        path = self.directory / name
        return {'name': name, 'state': 'uploaded', 'size': path.stat().st_size,
                'digest': 'sha256:' + hashlib.sha256(path.read_bytes()).hexdigest()}

    def gh(self, arguments):
        self.commands.append(arguments)
        if arguments[:2] == ['release', 'create']:
            self.details = self.record()
        elif arguments[:2] == ['release', 'upload']:
            path = Path(arguments[-1])
            self.details['assets'].append(self.asset(path.name))
            if self.publish_after_upload:
                self.details['draft'] = False
        elif arguments[:2] == ['release', 'download']:
            name = arguments[arguments.index('--pattern') + 1]
            target = Path(arguments[arguments.index('--dir') + 1]) / name
            shutil.copy2(self.directory / name, target)
        else:
            raise AssertionError(arguments)
        return ''


class DraftReleaseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory(prefix='quixdevs-draft-tests-')
        cls.directory = Path(cls.temporary.name)
        # Use the same verified runtime snapshot; only GitHub operations are fake.
        with contextlib.redirect_stdout(io.StringIO()):
            package.build()
        for name in [f'{package.SLUG}.zip', f'{package.SLUG}.zip.sha256', 'package-manifest.json']:
            shutil.copy2(ROOT / 'dist' / name, cls.directory / name)
        (cls.directory / 'release-notes.md').write_text(draft.release_notes(cls.directory))

    @classmethod
    def tearDownClass(cls):
        cls.temporary.cleanup()

    def run_draft(self, fake):
        with patch.object(draft, 'api', side_effect=fake.api), patch.object(draft, 'gh', side_effect=fake.gh), patch.object(draft.subprocess, 'check_output', side_effect=[COMMIT, '']), contextlib.redirect_stdout(io.StringIO()):
            return draft.create_draft(REPO, TAG, self.directory, COMMIT)

    def test_new_release_is_explicit_unpublished_draft_and_attaches_both_assets(self):
        fake = FakeGitHub(self.directory)
        url = self.run_draft(fake)
        self.assertEqual(url, fake.details['html_url'])
        create = fake.commands[0]
        for flag in ['--draft', '--prerelease', '--verify-tag', '--notes-file', '--target']:
            self.assertIn(flag, create)
        self.assertEqual(create[create.index('--target') + 1], COMMIT)
        self.assertEqual({a['name'] for a in fake.details['assets']}, {f'{package.SLUG}.zip', f'{package.SLUG}.zip.sha256'})
        self.assertFalse(any('--clobber' in c or 'edit' in c for c in fake.commands))

    def test_published_release_is_refused_without_mutations(self):
        fake = FakeGitHub(self.directory, existing=True)
        fake.details['draft'] = False
        with self.assertRaisesRegex(draft.ReleaseError, 'published'):
            self.run_draft(fake)
        self.assertEqual(fake.commands, [])

    def test_matching_draft_is_idempotent(self):
        fake = FakeGitHub(self.directory, existing=True)
        fake.details['assets'] = [fake.asset(f'{package.SLUG}.zip'), fake.asset(f'{package.SLUG}.zip.sha256')]
        self.run_draft(fake)
        self.assertEqual(fake.commands, [])

    def test_incomplete_matching_draft_uploads_only_missing_asset(self):
        fake = FakeGitHub(self.directory, existing=True)
        fake.details['assets'] = [fake.asset(f'{package.SLUG}.zip')]
        self.run_draft(fake)
        self.assertEqual(len(fake.commands), 1)
        self.assertTrue(fake.commands[0][-1].endswith('.zip.sha256'))

    def test_conflicting_draft_asset_is_refused_before_upload(self):
        fake = FakeGitHub(self.directory, existing=True)
        asset = fake.asset(f'{package.SLUG}.zip.sha256')
        asset['digest'] = 'sha256:' + '0' * 64
        fake.details['assets'] = [asset]
        with self.assertRaisesRegex(draft.ReleaseError, 'asset differs'):
            self.run_draft(fake)
        self.assertEqual(fake.commands, [])

    def test_maintainer_note_edits_are_not_overwritten(self):
        fake = FakeGitHub(self.directory, existing=True)
        fake.details['body'] = 'Maintainer edited these notes'
        with self.assertRaisesRegex(draft.ReleaseError, 'notes differ'):
            self.run_draft(fake)
        self.assertEqual(fake.commands, [])

    def test_existing_draft_for_other_source_is_refused(self):
        fake = FakeGitHub(self.directory, existing=True)
        fake.details['target_commitish'] = 'b' * 40
        with self.assertRaisesRegex(draft.ReleaseError, 'source differs'):
            self.run_draft(fake)
        self.assertEqual(fake.commands, [])

    def test_moved_remote_tag_is_refused(self):
        fake = FakeGitHub(self.directory)
        fake.tag_commit = 'b' * 40
        with self.assertRaisesRegex(draft.ReleaseError, 'tag changed'):
            self.run_draft(fake)
        self.assertEqual(fake.commands, [])

    def test_publication_during_upload_stops_remaining_uploads(self):
        fake = FakeGitHub(self.directory, existing=True)
        fake.publish_after_upload = True
        with self.assertRaisesRegex(draft.ReleaseError, 'published'):
            self.run_draft(fake)
        self.assertEqual(len(fake.commands), 1)

    def test_assets_without_provider_digest_are_downloaded_and_compared(self):
        fake = FakeGitHub(self.directory, existing=True)
        for name in [f'{package.SLUG}.zip', f'{package.SLUG}.zip.sha256']:
            asset = fake.asset(name)
            del asset['digest']
            fake.details['assets'].append(asset)
        self.run_draft(fake)
        self.assertTrue(all(c[:2] == ['release', 'download'] for c in fake.commands))

    def test_tampered_checksum_is_refused_before_github_calls(self):
        with tempfile.TemporaryDirectory(prefix='quixdevs-corrupt-artifact-') as temporary:
            directory = Path(temporary)
            for path in self.directory.iterdir():
                shutil.copy2(path, directory / path.name)
            (directory / f'{package.SLUG}.zip.sha256').write_text('0' * 64 + '  ' + package.SLUG + '.zip\n')
            with patch.object(draft.subprocess, 'check_output', side_effect=[COMMIT, '']), patch.object(draft, 'api') as client, self.assertRaisesRegex(ValueError, 'sidecar mismatch'):
                draft.create_draft(REPO, TAG, directory, COMMIT)
            client.assert_not_called()

    def test_tampered_artifact_notes_are_refused_before_github_calls(self):
        with tempfile.TemporaryDirectory(prefix='quixdevs-note-artifact-') as temporary:
            directory = Path(temporary)
            for path in self.directory.iterdir():
                shutil.copy2(path, directory / path.name)
            (directory / 'release-notes.md').write_text('Unexpected release notes')
            with patch.object(draft.subprocess, 'check_output', side_effect=[COMMIT, '']), patch.object(draft, 'api') as client, contextlib.redirect_stdout(io.StringIO()), self.assertRaisesRegex(draft.ReleaseError, 'Artifact release notes'):
                draft.create_draft(REPO, TAG, directory, COMMIT)
            client.assert_not_called()

    def test_dirty_checkout_is_refused_before_github_calls(self):
        with patch.object(draft.subprocess, 'check_output', side_effect=[COMMIT, ' M README.md']), patch.object(draft, 'api') as client, self.assertRaisesRegex(draft.ReleaseError, 'clean verified'):
            draft.create_draft(REPO, TAG, self.directory, COMMIT)
        client.assert_not_called()

    def test_tag_repository_and_commit_arguments_are_validated(self):
        for repo, tag, sha in [(REPO, 'v1.0.1', COMMIT), ('bad repo', TAG, COMMIT), (REPO, TAG, 'HEAD')]:
            with self.subTest(repo=repo, tag=tag), self.assertRaises(draft.ReleaseError):
                draft.create_draft(repo, tag, self.directory, sha)

    def test_annotated_remote_tag_is_peeled(self):
        with patch.object(draft, 'api', side_effect=[{'object': {'type': 'tag', 'sha': 'b' * 40}}, {'object': {'type': 'commit', 'sha': COMMIT}}]):
            self.assertEqual(draft.remote_commit(REPO, TAG), COMMIT)

    def test_cyclic_remote_tag_is_rejected(self):
        with patch.object(draft, 'api', return_value={'object': {'type': 'tag', 'sha': 'b' * 40}}):
            with self.assertRaisesRegex(draft.ReleaseError, 'resolve safely'):
                draft.remote_commit(REPO, TAG)

    def test_only_explicit_http_404_is_treated_as_missing_release(self):
        for status, returncode in [(401, 1), (403, 1), (503, 1), (200, 1)]:
            response = subprocess.CompletedProcess([], returncode, f'HTTP/2.0 {status} status\n\n{{}}', 'redacted')
            with self.subTest(status=status), patch.object(draft.subprocess, 'run', return_value=response), self.assertRaises(draft.ReleaseError):
                draft.api('repos/example/repo/releases/tags/v1.0.0', allow_missing=True)
        response = subprocess.CompletedProcess([], 1, 'HTTP/2.0 404 Not Found\r\n\r\n{}', 'redacted')
        with patch.object(draft.subprocess, 'run', return_value=response):
            self.assertIsNone(draft.api('repos/example/repo/releases/tags/v1.0.0', allow_missing=True))

    def test_malformed_api_response_is_rejected(self):
        for output in ['{}', 'HTTP/2.0 200 OK\n\nnot-json', 'HTTP/2.0 200 OK\n\n[]']:
            with self.subTest(output=output), patch.object(draft.subprocess, 'run', return_value=subprocess.CompletedProcess([], 0, output, '')), self.assertRaises(draft.ReleaseError):
                draft.api('repos/example/repo')


if __name__ == '__main__':
    unittest.main()
