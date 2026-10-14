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


def gh(arguments):
    result = subprocess.run(['gh', *arguments], capture_output=True, text=True, timeout=45)
    if result.returncode:
        # stdout/stderr can contain server details; never copy them to logs.
        raise ReleaseError('GitHub CLI command failed; no release state is assumed.')
    return result.stdout


def api(path, allow_missing=False):
    result = subprocess.run(['gh', 'api', '--include', '--method', 'GET', path], capture_output=True, text=True, timeout=45)
    raw = result.stdout.replace('\r\n', '\n')
    headers, separator, body = raw.partition('\n\n')
    status = re.match(r'^HTTP/\S+\s+(\d{3})\b', headers)
    if not separator or not status:
        raise ReleaseError('GitHub API did not return a verifiable HTTP response.')
    code = int(status[1])
    if code == 404 and allow_missing:
        return None
    if code != 200 or result.returncode:
        raise ReleaseError(f'GitHub API returned HTTP {code}; refusing release mutations.')
    try:
        data = json.loads(body)
    except ValueError as error:
        raise ReleaseError('GitHub API returned malformed JSON.') from error
    if not isinstance(data, dict):
        raise ReleaseError('Unexpected GitHub API response shape.')
    return data


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
        gh(['release', 'download', tag, '--repo', repo, '--pattern', path.name, '--dir', temporary])
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
    if remote_commit(repo, tag) != expected_commit:
        raise ReleaseError('Remote tag changed after CI; refusing draft preparation.')
    endpoint = f'repos/{repo}/releases/tags/{tag}'
    details = api(endpoint, allow_missing=True)
    if details is None:
        # Existing-tag verification prevents implicit tag creation. The source
        # remains development-only, so the unpublished draft is a prerelease.
        gh(['release', 'create', tag, '--repo', repo, '--draft', '--prerelease', '--verify-tag',
            '--target', expected_commit,
            '--title', 'QuixDevs Stripe REST Payments ' + tag + ' — WooCommerce REST Payment Integration',
            '--notes-file', str(notes_path)])
        details = api(endpoint)
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
        details = api(endpoint)
        assert_draft(details, tag, expected_commit, expected_notes)
        existing = [asset for asset in details['assets'] if asset.get('name') == path.name]
        if existing:
            if len(existing) != 1 or not asset_matches(repo, tag, path, existing[0]):
                raise ReleaseError('Draft asset changed during preparation; inspect it manually.')
            continue
        gh(['release', 'upload', tag, '--repo', repo, str(path)])
        details = api(endpoint)
        assert_draft(details, tag, expected_commit, expected_notes)
    if remote_commit(repo, tag) != expected_commit:
        raise ReleaseError('Remote tag changed after draft preparation.')
    details = api(endpoint)
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
