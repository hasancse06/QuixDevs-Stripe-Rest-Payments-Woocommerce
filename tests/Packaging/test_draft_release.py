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
        self.requests = []
        self.fail_path = None
        self.fail_status = 404
        self.tag_commit = COMMIT
        self.details = self.record() if existing else None
        self.publish_after_upload = False

    def record(self):
        return {'id': 123, 'name': 'QuixDevs ' + TAG, 'created_at': '2026-10-15T00:00:00Z', 'draft': True, 'prerelease': True, 'tag_name': TAG, 'target_commitish': COMMIT,
                'body': draft.release_notes(self.directory), 'assets': [],
                'html_url': f'https://github.com/{REPO}/releases/tag/{TAG}'}

    def api(self, path, allow_missing=False, response_type=dict):
        self.requests.append(path)
        if path == self.fail_path:
            raise draft.request_error('GET', path, self.fail_status)
        if path == f'repos/{REPO}':
            return {'full_name': REPO}
        if '/git/ref/tags/' in path:
            return {'object': {'type': 'commit', 'sha': self.tag_commit}}
        if '/releases/tags/' in path:
            # GitHub documents this endpoint as a published-release lookup.
            if self.details is None or self.details['draft']:
                if not allow_missing:
                    raise draft.request_error('GET', path, 404)
                return None
            return copy.deepcopy(self.details)
        if '/releases?' in path:
            return [copy.deepcopy(self.details)] if self.details else []
        if path.endswith('/releases/123'):
            return copy.deepcopy(self.details)
        raise AssertionError(path)

    def asset(self, name):
        path = self.directory / name
        return {'id': 456, 'name': name, 'state': 'uploaded', 'size': path.stat().st_size,
                'digest': 'sha256:' + hashlib.sha256(path.read_bytes()).hexdigest()}

    def gh(self, arguments, request=None):
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
        self.assertIn(f'repos/{REPO}/releases?per_page=100&page=1', fake.requests)
        self.assertIn(f'repos/{REPO}/releases/123', fake.requests)
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

    def test_repository_tag_inventory_and_id_failures_never_create(self):
        for suffix, category in [('', 'repository_missing_or_inaccessible'),
                                 ('/git/ref/tags/' + TAG, 'tag_missing_or_inaccessible'),
                                 ('/releases?per_page=100&page=1', 'endpoint_missing_or_inaccessible'),
                                 ('/releases/123', 'release_missing_or_inaccessible')]:
            fake = FakeGitHub(self.directory, existing=True)
            fake.fail_path = f'repos/{REPO}' + suffix
            with self.subTest(suffix=suffix), self.assertRaisesRegex(draft.ReleaseError, category):
                self.run_draft(fake)
            self.assertEqual(fake.commands, [])

    def test_permission_and_unexpected_failures_never_create(self):
        for status, category in [(401, 'authentication_required_or_invalid'),
                                 (403, 'permission_denied_or_rate_limited'),
                                 (429, 'unexpected_api_response'), (503, 'github_server_error')]:
            fake = FakeGitHub(self.directory)
            fake.fail_path = f'repos/{REPO}/releases?per_page=100&page=1'
            fake.fail_status = status
            with self.subTest(status=status), self.assertRaisesRegex(draft.ReleaseError, category):
                self.run_draft(fake)
            self.assertEqual(fake.commands, [])

    def test_only_published_lookup_can_allow_missing(self):
        for path in [f'repos/{REPO}', f'repos/{REPO}/git/ref/tags/{TAG}',
                     f'repos/{REPO}/releases', f'repos/{REPO}/releases/123',
                     f'repos/{REPO}/releases/tags/{TAG}?token=secret']:
            with self.subTest(path=path), patch.object(draft.subprocess, 'run') as client:
                with self.assertRaisesRegex(draft.ReleaseError, 'invalid_missing_release_exception'):
                    draft.api(path, allow_missing=True)
                client.assert_not_called()

    def test_draft_on_later_inventory_page_is_found(self):
        record = FakeGitHub(self.directory, existing=True).details
        first = [{'id': n + 1, 'tag_name': 'another-tag'} for n in range(100)]
        with patch.object(draft, 'api', side_effect=[None, first, [record], record]) as client:
            self.assertEqual(draft.find_release(REPO, TAG)['id'], 123)
        self.assertIn('page=2', client.call_args_list[-2].args[0])

    def test_distinct_duplicate_or_invalid_release_identity_is_rejected(self):
        record = FakeGitHub(self.directory, existing=True).details
        other = dict(record, id=124, html_url=f'https://github.com/{REPO}/releases/tag/untagged-other')
        output = io.StringIO()
        with patch.object(draft, 'api', side_effect=[None, [record, other], record, other]), contextlib.redirect_stdout(output):
            with self.assertRaisesRegex(draft.ReleaseError, 'Multiple distinct.*123, 124'):
                draft.find_release(REPO, TAG)
        report = json.loads(output.getvalue())
        self.assertEqual(report['unique_release_count'], 2)
        self.assertEqual([r['id'] for r in report['releases']], [123, 124])
        for identifier in [None, True, 0, '123']:
            with self.subTest(identifier=identifier), patch.object(draft, 'api', return_value={'id': identifier}):
                with self.assertRaisesRegex(draft.ReleaseError, 'invalid_release_identity'):
                    draft.get_release(REPO, 123)
        with patch.object(draft, 'api', return_value={'id': 124}):
            with self.assertRaisesRegex(draft.ReleaseError, 'release_identity_mismatch'):
                draft.get_release(REPO, 123)

    def test_inventory_limit_does_not_assume_absence(self):
        with patch.object(draft, 'api', side_effect=[None] + [[{'tag_name': 'other'}] * 100] * 100):
            with self.assertRaisesRegex(draft.ReleaseError, 'pagination limit'):
                draft.find_release(REPO, TAG)

    def test_safe_request_diagnostics_do_not_expose_response_or_query(self):
        path = f'repos/{REPO}/releases?token=SECRET_QUERY'
        response = subprocess.CompletedProcess([], 1,
            'HTTP/2.0 403 Forbidden\nAuthorization: SECRET_HEADER\n\n{"message":"SECRET_BODY"}',
            'SECRET_STDERR')
        with patch.object(draft.subprocess, 'run', return_value=response):
            with self.assertRaises(draft.ReleaseError) as raised:
                draft.api(path, response_type=list)
        message = str(raised.exception)
        self.assertIn(f'GET /repos/{REPO}/releases: HTTP 403', message)
        self.assertIn('permission_denied_or_rate_limited', message)
        self.assertNotIn('SECRET', message)
        self.assertEqual(draft.safe_endpoint('untrusted/SECRET_PATH'), '/<unverified-endpoint>')
        self.assertEqual(draft.response_category('untrusted/SECRET_PATH', 404), 'invalid_or_unrecognized_api_endpoint')

    def test_creation_404_is_an_access_failure_not_missing_release(self):
        response = subprocess.CompletedProcess([], 1, 'SECRET_STDOUT', f'HTTP 404 SECRET_STDERR (https://api.github.com/repos/{REPO}/releases)')
        with patch.object(draft.subprocess, 'run', return_value=response):
            with self.assertRaises(draft.ReleaseError) as raised:
                draft.gh(['release', 'create'], request=('POST', f'repos/{REPO}/releases'))
        message = str(raised.exception)
        self.assertIn(f'POST /repos/{REPO}/releases: HTTP 404', message)
        self.assertIn('release_creation_access_or_workflow_restriction', message)
        self.assertNotIn('SECRET', message)

    def test_cli_preliminary_get_error_reports_actual_request(self):
        path = f'repos/{REPO}/git/ref/tags/{TAG}'
        response = subprocess.CompletedProcess([], 1, '',
            f'HTTP 404 SECRET_STDERR (https://api.github.com/{path}?SECRET_QUERY)')
        with patch.object(draft.subprocess, 'run', return_value=response):
            with self.assertRaises(draft.ReleaseError) as raised:
                draft.gh(['release', 'create'], request=('POST', f'repos/{REPO}/releases'))
        message = str(raised.exception)
        self.assertIn(f'GET /{path}: HTTP 404 (tag_missing_or_inaccessible)', message)
        self.assertNotIn('SECRET', message)

    def test_cli_unreported_endpoint_is_not_guessed(self):
        response = subprocess.CompletedProcess([], 1, 'SECRET_STDOUT', 'HTTP 403 SECRET_STDERR')
        with patch.object(draft.subprocess, 'run', return_value=response):
            with self.assertRaises(draft.ReleaseError) as raised:
                draft.gh(['release', 'create'], request=('POST', f'repos/{REPO}/releases'))
        message = str(raised.exception)
        self.assertIn('cli_request_unconfirmed', message)
        self.assertIn('actual failing endpoint not reported', message)
        self.assertNotIn('SECRET', message)

    def test_workflow_helper_copy_uses_unchanged_source_validation(self):
        # Execute the same temp-file/PYTHONPATH arrangement as Actions. An
        # isolated source tree models the tag; tooling sits outside that tree.
        with tempfile.TemporaryDirectory(prefix='quixdevs-workflow-helper-') as temporary:
            temporary = Path(temporary)
            source = temporary / 'tagged-source'
            source.mkdir()
            archive = subprocess.check_output(['git', 'archive', '--format=zip', 'HEAD'], cwd=ROOT)
            import zipfile
            with zipfile.ZipFile(io.BytesIO(archive)) as files:
                files.extractall(source)
            artifacts = source / 'dist'
            artifacts.mkdir()
            for path in self.directory.iterdir():
                shutil.copy2(path, artifacts / path.name)
            helper = temporary / 'create-draft-release.py'
            shutil.copy2(ROOT / 'tools/create-draft-release.py', helper)
            import os
            environment = dict(os.environ, PYTHONPATH=str(source / 'tools'), PYTHONDONTWRITEBYTECODE='1')
            result = subprocess.run([sys.executable, str(helper), '--prepare-notes', '--repo', REPO,
                '--tag', TAG, '--expected-commit', COMMIT, '--artifact-dir', str(artifacts)],
                cwd=source, env=environment, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual((artifacts / 'release-notes.md').read_text(), draft.release_notes(self.directory))
            # The import is from the tagged source, not the temp helper/workflow
            # commit, so verifier and clean-source guards retain their ROOT.
            result = subprocess.run([sys.executable, '-c', 'import package; print(package.ROOT)'],
                cwd=source, env=environment, capture_output=True, text=True, check=True)
            self.assertEqual(Path(result.stdout.strip()).resolve(), source.resolve())

    def test_workflow_uses_scoped_github_token_and_run_commit_helper(self):
        workflow = (ROOT / '.github/workflows/release.yml').read_text()
        job = workflow.split('\n  draft:\n')[1]
        self.assertIn('contents: write', job)
        self.assertIn('GH_TOKEN: ${{ github.token }}', job)
        self.assertIn('RELEASE_AUTOMATION_COMMIT: ${{ github.workflow_sha }}', job)
        self.assertIn('git show "$RELEASE_AUTOMATION_COMMIT:tools/create-draft-release.py"', job)
        self.assertIn('PYTHONPATH="$GITHUB_WORKSPACE/tools"', job)
        self.assertNotIn('secrets.PAT', workflow)

    def test_repeated_same_id_is_not_a_second_release(self):
        record = FakeGitHub(self.directory, existing=True).details
        with patch.object(draft, 'api', side_effect=[None, [record, record], record]):
            self.assertEqual(draft.find_release(REPO, TAG)['id'], 123)

    def test_repeated_ids_across_pages_are_confirmed_only_once(self):
        record = FakeGitHub(self.directory, existing=True).details
        updated = dict(record, name='Latest name')
        first = [record] + [{'tag_name': 'other'}] * 99
        with patch.object(draft, 'api', side_effect=[first, [record], updated]) as client:
            inventory = draft.matching_inventory(REPO, TAG)
        self.assertEqual(inventory['matching_occurrences'], 2)
        self.assertEqual(inventory['repeated_occurrences'], 1)
        self.assertEqual(inventory['records'], [updated])
        self.assertEqual(client.call_args_list[-1].args[0], f'repos/{REPO}/releases/123')

    def test_true_duplicate_ids_stop_creation_without_mutations(self):
        fake = FakeGitHub(self.directory, existing=True)
        record = fake.details
        other = dict(record, id=124)
        original = fake.api
        def inventory_api(path, **kwargs):
            if '/releases?' in path:
                return [record, other]
            if path.endswith('/releases/124'):
                return other
            return original(path, **kwargs)
        fake.api = inventory_api
        with self.assertRaisesRegex(draft.ReleaseError, 'Multiple distinct'):
            self.run_draft(fake)
        self.assertEqual(fake.commands, [])

    def test_inventory_tag_change_and_disappearing_id_fail_closed(self):
        record = FakeGitHub(self.directory, existing=True).details
        with patch.object(draft, 'api', side_effect=[[record], dict(record, tag_name='v2.0.0')]):
            with self.assertRaisesRegex(draft.ReleaseError, 'tag changed during inventory'):
                draft.matching_inventory(REPO, TAG)
        with patch.object(draft, 'api', side_effect=[[record], draft.request_error('GET', f'repos/{REPO}/releases/123', 404)]):
            with self.assertRaisesRegex(draft.ReleaseError, 'release_missing_or_inaccessible'):
                draft.matching_inventory(REPO, TAG)

    def test_diagnostics_empty_single_and_multiple_are_read_only(self):
        record = FakeGitHub(self.directory, existing=True).details
        other = dict(record, id=124, draft=False, prerelease=False,
                     html_url=f'https://github.com/{REPO}/releases/tag/untagged-second')
        record['assets'] = [{'name': f'{package.SLUG}.zip'}]
        for candidates in [[], [record], [record, other]]:
            with self.subTest(count=len(candidates)), patch.object(draft, 'gh') as cli, \
                 patch.object(draft, 'api', side_effect=[{'full_name': REPO, 'permissions': {'push': True}}, candidates] + candidates), \
                 patch.object(draft, 'create_draft') as create, patch.object(draft, 'remote_commit', return_value=COMMIT) as tag_reader, \
                 patch.object(draft._VERIFY, 'verify') as package_check, contextlib.redirect_stdout(io.StringIO()) as output:
                report = draft.diagnose(REPO, TAG)
            self.assertEqual(report['unique_release_count'], len(candidates))
            self.assertEqual(json.loads(output.getvalue()), report)
            self.assertEqual([r['id'] for r in report['releases']], [r['id'] for r in candidates])
            cli.assert_called_once_with(['auth', 'status', '--hostname', 'github.com'])
            create.assert_not_called()
            self.assertEqual(tag_reader.call_args_list, [unittest.mock.call(REPO, TAG)] * 2)
            self.assertEqual(report['tag_commit'], COMMIT)
            self.assertEqual(report['draft_count'], sum(r['draft'] for r in candidates))
            self.assertEqual(report['published_count'], sum(not r['draft'] for r in candidates))
            package_check.assert_not_called()
            for actual, source in zip(report['releases'], candidates):
                self.assertEqual(set(actual), {'id', 'name', 'tag_name', 'draft', 'prerelease', 'html_url', 'created_at', 'asset_names'})
                self.assertEqual(actual['html_url'], source['html_url'])
                self.assertEqual(actual['asset_names'], [a['name'] for a in source['assets']])

    def test_diagnostics_validate_authentication_and_access(self):
        with patch.object(draft, 'gh', side_effect=draft.ReleaseError('authentication unavailable')), patch.object(draft, 'api') as client:
            with self.assertRaisesRegex(draft.ReleaseError, 'authentication unavailable'):
                draft.diagnose(REPO, TAG)
            client.assert_not_called()
        with patch.object(draft, 'gh'), patch.object(draft, 'api', return_value={'full_name': 'other/repo'}) as client:
            with self.assertRaisesRegex(draft.ReleaseError, 'repository_identity_mismatch'):
                draft.diagnose(REPO, TAG)
            self.assertEqual(client.call_count, 1)
        with patch.object(draft, 'gh') as client:
            for repo, tag in [('bad repo', TAG), (REPO, 'v1.0.1')]:
                with self.subTest(repo=repo, tag=tag), self.assertRaises(draft.ReleaseError):
                    draft.diagnose(repo, tag)
            client.assert_not_called()

    def test_diagnostic_output_redacts_tokens_and_omits_unrequested_fields(self):
        import os
        record = FakeGitHub(self.directory, existing=True).details
        secret = 'ghp_' + 'X' * 36
        workflow_secret = 'nonstandard-workflow-authentication-value'
        record.update(name='Name ' + secret + '\n::warning::injected',
                      body='SECRET_BODY', author={'token': 'SECRET_AUTHOR'},
                      assets=[{'name': secret + '.zip', 'url': 'SECRET_ASSET_URL'}, {'name': workflow_secret + '.sha256'}])
        inventory = {'pages_scanned': 1, 'matching_occurrences': 1, 'repeated_occurrences': 0, 'records': [record]}
        with patch.dict(os.environ, {'GH_TOKEN': secret, 'GITHUB_TOKEN': workflow_secret}), tempfile.TemporaryDirectory() as temporary:
            summary = Path(temporary) / 'summary.md'
            with contextlib.redirect_stdout(io.StringIO()) as output:
                report = draft.diagnostic_report(REPO, TAG, inventory)
                draft.emit_diagnostics(report, summary)
            for text in [output.getvalue(), summary.read_text()]:
                self.assertNotIn(secret, text)
                self.assertNotIn(workflow_secret, text)
                self.assertNotIn('SECRET_', text)
                self.assertNotIn('\n::warning::', text)
                self.assertIn('[redacted]', text)
            self.assertIn(f"<{record['html_url']}>", summary.read_text())

    def test_diagnostics_do_not_emit_untrusted_urls_or_assume_status(self):
        record = FakeGitHub(self.directory, existing=True).details
        for url in ['https://evil.example/SECRET', f'https://github.com/{REPO}/releases/tag/v1.0.0?token=SECRET', None]:
            inventory = {'pages_scanned': 1, 'matching_occurrences': 1, 'repeated_occurrences': 0, 'records': [dict(record, html_url=url)]}
            self.assertIsNone(draft.diagnostic_report(REPO, TAG, inventory)['releases'][0]['html_url'])
        for malformed in [dict(record, draft=None), dict(record, assets=None)]:
            inventory = {'pages_scanned': 1, 'matching_occurrences': 1, 'repeated_occurrences': 0, 'records': [malformed]}
            with self.assertRaises(draft.ReleaseError):
                draft.diagnostic_report(REPO, TAG, inventory)

    def test_diagnostics_cli_requires_no_commit_and_makes_no_mutation(self):
        # A fake gh on PATH models authenticated GETs, rejecting all other API
        # methods/CLI commands. No network or real GitHub credential is used.
        import os
        with tempfile.TemporaryDirectory(prefix='quixdevs-diagnostic-cli-') as temporary:
            cli = Path(temporary) / 'gh'
            cli.write_text("#!/usr/bin/env python3\nimport sys, json\na=sys.argv[1:]\n"
                "if a[:2]==['auth','status']: sys.exit(0)\n"
                "if a[:4]!=['api','--include','--method','GET']: sys.exit(99)\n"
                "data={'full_name':" + repr(REPO) + ", 'permissions':{'push':False}} if a[-1]==" + repr('repos/' + REPO) + " else {'object': {'type':'commit','sha':" + repr(COMMIT) + "}} if '/git/ref/tags/' in a[-1] else []\n"
                "print('HTTP/2.0 200 OK\\n\\n'+json.dumps(data))\n")
            cli.chmod(0o700)
            environment = dict(os.environ, PATH=temporary + os.pathsep + os.environ['PATH'], PYTHONDONTWRITEBYTECODE='1', GH_TOKEN='ghs_' + 'I' * 36)
            result = subprocess.run([sys.executable, str(ROOT / 'tools/create-draft-release.py'),
                '--diagnose', '--repo', REPO, '--tag', TAG], env=environment, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)['unique_release_count'], 0)
            self.assertEqual(json.loads(result.stdout)['tag_commit'], COMMIT)
            self.assertNotIn(environment['GH_TOKEN'], result.stdout + result.stderr)

    def test_installation_token_ignores_collaborator_permissions(self):
        record = FakeGitHub(self.directory, existing=True).details
        other = dict(record, id=124)
        tag_ref = {'object': {'type': 'commit', 'sha': COMMIT}}
        # Both collaborator flags explicitly false and absent must work when
        # the authenticated repository/tag/releases API requests succeed.
        for fields in [{'permissions': {'push': False, 'admin': False, 'maintain': False, 'pull': False}},
                       {'permissions': {}}, {}]:
            for candidates in [[], [record], [record, other]]:
                with self.subTest(fields=fields, count=len(candidates)), \
                     patch.dict(draft.os.environ, {'GH_TOKEN': 'ghs_' + 'I' * 36}), \
                     patch.object(draft, 'gh') as cli, \
                     patch.object(draft, 'api', side_effect=[dict(full_name=REPO, **fields), tag_ref, candidates] + candidates + [tag_ref]) as client, \
                     patch.object(draft, 'create_draft') as create, contextlib.redirect_stdout(io.StringIO()):
                    report = draft.diagnose(REPO, TAG)
                self.assertEqual(report['draft_count'], len(candidates))
                self.assertEqual(report['unique_release_count'], len(candidates))
                self.assertEqual(report['tag_commit'], COMMIT)
                self.assertEqual(client.call_args_list[1].args[0], f'repos/{REPO}/git/ref/tags/{TAG}')
                self.assertIn('per_page=100&page=1', client.call_args_list[2].args[0])
                cli.assert_called_once_with(['auth', 'status', '--hostname', 'github.com'])
                create.assert_not_called()

    def test_installation_token_diagnostics_respect_actual_http_failures(self):
        repository = {'full_name': REPO, 'permissions': {'push': False}}
        tag_ref = {'object': {'type': 'commit', 'sha': COMMIT}}
        record = FakeGitHub(self.directory, existing=True).details
        paths = [f'repos/{REPO}', f'repos/{REPO}/git/ref/tags/{TAG}',
                 f'repos/{REPO}/releases?per_page=100&page=1', f'repos/{REPO}/releases/123']
        for index, path in enumerate(paths):
            for status in [401, 403, 404, 503]:
                def http_response(value, code=200):
                    return subprocess.CompletedProcess([], int(code != 200),
                        f'HTTP/2.0 {code} status\n\n' + json.dumps(value), 'SECRET_STDERR')
                prior = [repository, tag_ref, [record]][:index]
                responses = [http_response(value) for value in prior] + [http_response({'message': 'SECRET_BODY'}, status)]
                with self.subTest(path=path, status=status), \
                     patch.dict(draft.os.environ, {'GH_TOKEN': 'ghs_' + 'I' * 36}), \
                     patch.object(draft, 'gh') as cli, \
                     patch.object(draft.subprocess, 'run', side_effect=responses), \
                     contextlib.redirect_stdout(io.StringIO()) as output:
                    with self.assertRaises(draft.ReleaseError) as raised:
                        draft.diagnose(REPO, TAG)
                message = str(raised.exception)
                self.assertIn('GET ' + draft.safe_endpoint(path), message)
                self.assertIn(f'HTTP {status}', message)
                self.assertNotIn('SECRET', message)
                self.assertEqual(output.getvalue(), '')
                cli.assert_called_once_with(['auth', 'status', '--hostname', 'github.com'])

    def test_installation_token_preserves_pagination_and_id_deduplication(self):
        record = FakeGitHub(self.directory, existing=True).details
        other = dict(record, id=124)
        tag_ref = {'object': {'type': 'commit', 'sha': COMMIT}}
        first = [record] + [{'tag_name': 'other'}] * 99
        responses = [{'full_name': REPO, 'permissions': {'push': False}}, tag_ref,
                     first, [record, other], record, other, tag_ref]
        with patch.object(draft, 'gh') as cli, patch.object(draft, 'api', side_effect=responses) as client, \
             contextlib.redirect_stdout(io.StringIO()):
            report = draft.diagnose(REPO, TAG)
        self.assertEqual(report['unique_release_count'], 2)
        self.assertEqual(report['draft_count'], 2)
        self.assertEqual(report['matching_occurrences'], 3)
        self.assertEqual(report['repeated_occurrences'], 1)
        self.assertEqual(report['pages_scanned'], 2)
        paths = [call.args[0] for call in client.call_args_list]
        self.assertEqual(paths.count(f'repos/{REPO}/releases/123'), 1)
        self.assertEqual(paths.count(f'repos/{REPO}/releases/124'), 1)
        self.assertIn(f'repos/{REPO}/releases?per_page=100&page=2', paths)
        cli.assert_called_once_with(['auth', 'status', '--hostname', 'github.com'])

    def test_diagnostics_peel_annotated_tag_and_reject_changed_tag(self):
        annotation = {'object': {'type': 'tag', 'sha': 'b' * 40}}
        commit = {'object': {'type': 'commit', 'sha': COMMIT}}
        with patch.object(draft, 'gh'), patch.object(draft, 'api', side_effect=[{'full_name': REPO}, annotation, commit, [], annotation, commit]) as client, \
             contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(draft.diagnose(REPO, TAG)['tag_commit'], COMMIT)
        self.assertEqual(client.call_args_list[2].args[0], f"repos/{REPO}/git/tags/{'b' * 40}")
        with patch.object(draft, 'gh'), patch.object(draft, 'api', side_effect=[{'full_name': REPO}, commit, [], {'object': {'type': 'commit', 'sha': 'c' * 40}}]), \
             contextlib.redirect_stdout(io.StringIO()) as output:
            with self.assertRaisesRegex(draft.ReleaseError, 'Remote tag changed during diagnostics'):
                draft.diagnose(REPO, TAG)
        self.assertEqual(output.getvalue(), '')

    def test_workflow_diagnostic_mode_guards_creation_and_uses_summary(self):
        body = (ROOT / '.github/workflows/release.yml').read_text()
        self.assertIn('diagnostics_only:', body)
        self.assertIn('if: ${{ !inputs.diagnostics_only }}', body)
        self.assertIn('--diagnose --repo', body)
        self.assertIn('--summary-file "$GITHUB_STEP_SUMMARY"', body)
        diagnostic = body.split('      - name: Diagnose matching releases')[1].split('      - name: Create or resume')[0]
        self.assertIn('GH_TOKEN: ${{ github.token }}', diagnostic)
        self.assertNotIn('--expected-commit', diagnostic)


if __name__ == '__main__':
    unittest.main()
