#!/usr/bin/env python3
"""Create or resume a verified unpublished draft; never create tags or publish."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import tempfile

from package import ROOT, SLUG, VERSION

_SPEC = importlib.util.spec_from_file_location('verify_package', ROOT / 'tools/verify-package.py')
_VERIFY = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_VERIFY)


class ReleaseError(ValueError):
    """A draft invariant failed; error messages must not expose CLI credentials."""


def safe_endpoint(path):
    # Never log query values, request bodies, tokens or arbitrary server text.
    path = path.split('?', 1)[0].strip('/')
    if re.fullmatch(r'repos/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+(?:/(?:git/ref/tags/v[0-9.]+|git/tags/[0-9a-f]{40}|releases(?:/tags/v[0-9.]+|/[0-9]+(?:/assets)?)?|releases/assets/[0-9]+))?', path):
        return '/' + path
    return '/<unverified-endpoint>'


def response_category(path, status, method='GET'):
    endpoint = safe_endpoint(path)
    if endpoint == '/<unverified-endpoint>':
        return 'invalid_or_unrecognized_api_endpoint'
    if status == 401:
        return 'authentication_required_or_invalid'
    if status == 403:
        return 'permission_denied_or_rate_limited'
    if status == 404:
        if re.fullmatch(r'/repos/[^/]+/[^/]+', endpoint):
            return 'repository_missing_or_inaccessible'
        if '/git/ref/tags/' in endpoint:
            return 'tag_missing_or_inaccessible'
        if '/git/tags/' in endpoint:
            return 'tag_object_missing_or_inaccessible'
        if '/releases/tags/' in endpoint:
            return 'published_release_not_found'
        if method == 'POST' and endpoint.endswith('/releases'):
            return 'release_creation_access_or_workflow_restriction'
        if re.fullmatch(r'/repos/[^/]+/[^/]+/releases/[0-9]+', endpoint):
            return 'release_missing_or_inaccessible'
        return 'endpoint_missing_or_inaccessible'
    if status == 422:
        return 'validation_or_existing_release_conflict'
    if status is not None and status >= 500:
        return 'github_server_error'
    return 'unexpected_api_response'


def request_error(method, path, status, category=None):
    category = category or response_category(path, status, method)
    code = str(status) if status is not None else 'unavailable'
    hint = ''
    if category == 'release_creation_access_or_workflow_restriction':
        hint = ' Check contents: write and whether the tagged workflow files differ from the default branch; do not reinterpret this POST 404 as a missing release.'
    return ReleaseError(f'GitHub API {method} {safe_endpoint(path)}: HTTP {code} ({category}); refusing release mutations.' + hint)


def gh(arguments, request=None):
    result = subprocess.run(['gh', *arguments], capture_output=True, text=True, timeout=45)
    if result.returncode:
        # Inspect only a numeric HTTP code; never copy stdout/stderr to logs.
        code = re.search(r'\bHTTP\s+(\d{3})\b', result.stderr + result.stdout)
        if request:
            method, path = request
            # CLI subcommands can perform preliminary GETs before their POST.
            # Use only a recognized same-repository URL, never arbitrary stderr.
            reported = re.search(r'https://(?:api|uploads)\.github\.com/([A-Za-z0-9_./-]+)', result.stderr)
            prefix = '/'.join(path.split('/')[:3]) + '/'
            if reported and reported[1].startswith(prefix) and safe_endpoint(reported[1]) != '/<unverified-endpoint>':
                observed = reported[1]
                if safe_endpoint(observed) != safe_endpoint(path):
                    method = 'GET'  # The CLI's tag/release resolution lookups.
                raise request_error(method, observed, int(code[1]) if code else None)
            status = code[1] if code else 'unavailable'
            raise ReleaseError(f'GitHub CLI failed: HTTP {status} (cli_request_unconfirmed); intended {method} {safe_endpoint(path)}, actual failing endpoint not reported; refusing release mutations.')
        raise ReleaseError('GitHub CLI operation failed (authentication, access or transport); no release state is assumed.')
    return result.stdout


def api(path, allow_missing=False, response_type=dict):
    # Only this exact published-release lookup has a normal missing state.
    if allow_missing and not re.fullmatch(r'repos/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+/releases/tags/v[0-9.]+', path):
        raise request_error('GET', path, None, 'invalid_missing_release_exception')
    result = subprocess.run(['gh', 'api', '--include', '--method', 'GET', path], capture_output=True, text=True, timeout=45)
    raw = result.stdout.replace('\r\n', '\n')
    headers, separator, body = raw.partition('\n\n')
    status = re.match(r'^HTTP/\S+\s+(\d{3})\b', headers)
    if not separator or not status:
        raise request_error('GET', path, None, 'unverifiable_http_response')
    code = int(status[1])
    if code == 404 and allow_missing:
        print(f'GitHub API GET {safe_endpoint(path)}: HTTP 404 (published_release_not_found); checking authenticated draft inventory.')
        return None
    if code != 200 or result.returncode:
        raise request_error('GET', path, code)
    try:
        data = json.loads(body)
    except ValueError as error:
        raise request_error('GET', path, code, 'malformed_json_response') from error
    if not isinstance(data, response_type):
        raise request_error('GET', path, code, 'unexpected_response_shape')
    return data


def confirm_repository(repo):
    path = f'repos/{repo}'
    details = api(path)
    if str(details.get('full_name', '')).lower() != repo.lower():
        raise request_error('GET', path, 200, 'repository_identity_mismatch')


def release_id(details, path):
    identifier = details.get('id')
    if type(identifier) is not int or identifier < 1:
        raise request_error('GET', path, 200, 'invalid_release_identity')
    return identifier


def find_release(repo, tag):
    # The by-tag endpoint finds published releases only. A 404 must never be
    # used as proof that no draft exists. The authenticated list includes drafts
    # for the write-capable workflow token; scan every page before creating one.
    path = f'repos/{repo}/releases/tags/{tag}'
    published = api(path, allow_missing=True)
    if published is not None:
        release_id(published, path)
        return published
    matches = []
    for page in range(1, 101):
        path = f'repos/{repo}/releases?per_page=100&page={page}'
        records = api(path, response_type=list)
        for record in records:
            if not isinstance(record, dict):
                raise request_error('GET', path, 200, 'malformed_release_inventory')
            if record.get('tag_name') == tag:
                release_id(record, path)
                matches.append(record)
        if len(records) < 100:
            if len(matches) > 1:
                raise ReleaseError('Multiple releases/drafts share this tag; review them manually.')
            return matches[0] if matches else None
    raise ReleaseError('Release inventory pagination limit reached; no absence is assumed.')


def get_release(repo, identifier):
    path = f'repos/{repo}/releases/{identifier}'
    details = api(path)
    if release_id(details, path) != identifier:
        raise request_error('GET', path, 200, 'release_identity_mismatch')
    return details


def remote_commit(repo, tag):
    reference = api(f'repos/{repo}/git/ref/tags/{tag}')['object']
    seen = set()
    for _ in range(10):
        sha = reference.get('sha', '')
        if not re.fullmatch(r'[0-9a-f]{40}', sha) or sha in seen:
            break
        seen.add(sha)
        if reference.get('type') == 'commit':
            return sha
        if reference.get('type') != 'tag':
            break
        reference = api(f'repos/{repo}/git/tags/{sha}')['object']
    raise ReleaseError('Remote tag does not resolve safely to a commit.')


def release_notes(directory):
    """Bind professional notes to this exact verified distribution snapshot."""
    directory = Path(directory)
    manifest = json.loads((directory / 'package-manifest.json').read_text())
    notes = (ROOT / 'docs/github-release-notes.md').read_text().strip()
    return (notes + '\n\n## Verified installation asset\n\n'
            + f"`{SLUG}.zip` — {manifest['bytes']:,} bytes, {manifest['files']} runtime files.\n\n"
            + 'SHA-256:\n\n```text\n'
            + (directory / f'{SLUG}.zip.sha256').read_text()
            + '```\n')


def assert_draft(details, tag, expected_commit, notes):
    if details.get('draft') is not True or details.get('tag_name') != tag:
        raise ReleaseError('A published release already exists or draft identity changed; it will not be modified.')
    if details.get('target_commitish') != expected_commit:
        raise ReleaseError('Existing draft source differs; review it manually before retrying.')
    if str(details.get('body', '')).strip() != notes.strip():
        raise ReleaseError('Existing draft notes differ; refusing to overwrite maintainer edits.')
    if not isinstance(details.get('assets'), list):
        raise ReleaseError('Draft asset inventory is unavailable.')


def asset_matches(repo, tag, path, asset):
    if asset.get('state') != 'uploaded' or asset.get('size') != path.stat().st_size:
        return False
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    stored = asset.get('digest')
    if stored is not None:
        return stored == 'sha256:' + digest
    # Older assets may not expose a digest. Download privately and compare bytes.
    with tempfile.TemporaryDirectory(prefix='quixdevs-draft-assets-') as temporary:
        gh(['release', 'download', tag, '--repo', repo, '--pattern', path.name, '--dir', temporary], request=('GET', f"repos/{repo}/releases/assets/{asset.get('id', 0)}"))
        downloaded = Path(temporary) / path.name
        return downloaded.is_file() and not downloaded.is_symlink() and hashlib.sha256(downloaded.read_bytes()).hexdigest() == digest


def create_draft(repo, tag, directory, expected_commit):
    directory = Path(directory).resolve()
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]*/[A-Za-z0-9][A-Za-z0-9_.-]*', repo):
        raise ReleaseError('Supply the confirmed OWNER/REPOSITORY.')
    if tag != 'v' + VERSION or not re.fullmatch(r'[0-9a-f]{40}', expected_commit):
        raise ReleaseError('Use v1.0.0 and the full verified source commit SHA.')
    local = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    if local != expected_commit:
        raise ReleaseError('Checked-out source does not match the verified commit.')
    dirty = subprocess.check_output(['git', 'status', '--porcelain', '--untracked-files=normal'], cwd=ROOT, text=True).strip()
    if dirty:
        raise ReleaseError('Draft preparation requires the clean verified source checkout.')
    # Reuse all existing source/manifest/CRC/PHP/autoload checks on downloaded artifacts.
    _VERIFY.verify(directory / f'{SLUG}.zip')
    expected_notes = release_notes(directory)
    notes_path = directory / 'release-notes.md'
    if notes_path.read_text().replace('\r\n', '\n') != expected_notes:
        raise ReleaseError('Artifact release notes do not match the checked-out source and checksum.')
    confirm_repository(repo)
    if remote_commit(repo, tag) != expected_commit:
        raise ReleaseError('Remote tag changed after CI; refusing draft preparation.')
    details = find_release(repo, tag)
    if details is None:
        # Existing-tag verification prevents implicit tag creation. The source
        # remains development-only, so the unpublished draft is a prerelease.
        gh(['release', 'create', tag, '--repo', repo, '--draft', '--prerelease', '--verify-tag',
            '--target', expected_commit,
            '--title', 'QuixDevs Stripe REST Payments ' + tag + ' — WooCommerce REST Payment Integration',
            '--notes-file', str(notes_path)], request=('POST', f'repos/{repo}/releases'))
        details = find_release(repo, tag)
        if details is None:
            raise ReleaseError('Create returned success but the authenticated inventory has no matching draft; inspect GitHub before retrying.')
    identifier = release_id(details, f'repos/{repo}/releases')
    details = get_release(repo, identifier)
    assert_draft(details, tag, expected_commit, expected_notes)
    paths = [directory / f'{SLUG}.zip', directory / f'{SLUG}.zip.sha256']
    # Preflight all existing assets before any upload. Different draft assets
    # require manual review; --clobber/delete-asset are intentionally absent.
    for path in paths:
        matches = [asset for asset in details['assets'] if asset.get('name') == path.name]
        if len(matches) > 1 or (matches and not asset_matches(repo, tag, path, matches[0])):
            raise ReleaseError('Existing draft asset differs; no assets will be overwritten.')
    for path in paths:
        if remote_commit(repo, tag) != expected_commit:
            raise ReleaseError('Remote tag changed during draft preparation.')
        details = get_release(repo, identifier)
        assert_draft(details, tag, expected_commit, expected_notes)
        existing = [asset for asset in details['assets'] if asset.get('name') == path.name]
        if existing:
            if len(existing) != 1 or not asset_matches(repo, tag, path, existing[0]):
                raise ReleaseError('Draft asset changed during preparation; inspect it manually.')
            continue
        gh(['release', 'upload', tag, '--repo', repo, str(path)], request=('POST', f'repos/{repo}/releases/{identifier}/assets'))
        details = get_release(repo, identifier)
        assert_draft(details, tag, expected_commit, expected_notes)
    if remote_commit(repo, tag) != expected_commit:
        raise ReleaseError('Remote tag changed after draft preparation.')
    details = get_release(repo, identifier)
    assert_draft(details, tag, expected_commit, expected_notes)
    for path in paths:
        matches = [asset for asset in details['assets'] if asset.get('name') == path.name]
        if len(matches) != 1 or not asset_matches(repo, tag, path, matches[0]):
            raise ReleaseError('Uploaded draft asset bytes could not be verified.')
    url = details.get('html_url', '')
    if not url.startswith(f'https://github.com/{repo}/releases/'):
        raise ReleaseError('Draft URL could not be verified.')
    return url


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', required=True)
    parser.add_argument('--tag', required=True)
    parser.add_argument('--expected-commit', required=True)
    parser.add_argument('--artifact-dir', type=Path, default=ROOT / 'dist')
    parser.add_argument('--prepare-notes', action='store_true', help='Write local notes only; never call GitHub')
    args = parser.parse_args()
    try:
        if args.prepare_notes:
            destination = args.artifact_dir / 'release-notes.md'
            destination.write_text(release_notes(args.artifact_dir))
            print(f'Prepared {destination.name}; no GitHub request made.')
        else:
            print(create_draft(args.repo, args.tag, args.artifact_dir, args.expected_commit))
    except (ValueError, OSError, KeyError, subprocess.SubprocessError) as error:
        if isinstance(error, ReleaseError):
            raise SystemExit(str(error)) from error
        raise SystemExit('Draft preparation failed; inspect checks locally. No release publication command was executed.') from error
