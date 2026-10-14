#!/usr/bin/env python3
"""Check the GitHub presentation and any locally built plugin package, offline."""
from pathlib import Path
from urllib.parse import unquote, urlsplit
import json
import re
import struct
import subprocess
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[1]
SKIP = {'vendor', 'node_modules', '.git', 'build', 'dist', '__pycache__', '.phpunit.cache', '.phpstan-cache'}
LINK = re.compile(r'!?\[[^\]]*\]\(([^\s)]+)(?:\s+"[^"]*")?\)')


def prose(body):
    return re.sub(r'`[^`\n]*`', '', re.sub(r'^```.*?^```[^\n]*$', '', body, flags=re.M | re.S))


def anchors(body):
    return {
        re.sub(r'[^\w\- ]', '', heading.lower()).replace(' ', '-')
        for heading in re.findall(r'^#{1,6}\s+(.+?)\s*#*$', body, re.M)
    }


def check_links(name, body, exists, read):
    count = 0
    for target in LINK.findall(prose(body)):
        parts = urlsplit(target.strip('<>'))
        if parts.scheme or parts.netloc:
            continue
        dest = (name.parent / unquote(parts.path)).resolve() if parts.path else name
        assert dest.is_relative_to(ROOT), f'Outside repository: {name}: {target}'
        assert exists(dest), f'Broken link: {name.relative_to(ROOT)}: {target}'
        if parts.fragment and dest.suffix == '.md':
            assert unquote(parts.fragment) in anchors(read(dest)), f'Broken heading: {name}: {target}'
        count += 1
    return count


links = 0
for path in ROOT.rglob('*.md'):
    if any(part in SKIP for part in path.relative_to(ROOT).parts):
        continue
    if path == ROOT / 'tools/package-readme.md':
        # This template is installed at the package root, not inside tools/.
        continue
    links += check_links(path, path.read_text(), Path.exists, Path.read_text)

sizes = {
    'docs/branding/quixdevs-logo.png': (164, 45),
    'docs/branding/github-social-preview.png': (1280, 640),
    'wordpress-org-assets/banner-772x250.png': (772, 250),
    'wordpress-org-assets/banner-1544x500.png': (1544, 500),
    'wordpress-org-assets/icon-128x128.png': (128, 128),
    'wordpress-org-assets/icon-256x256.png': (256, 256),
}
for name, expected in sizes.items():
    data = (ROOT / name).read_bytes()
    assert data[:8] == b'\x89PNG\r\n\x1a\n', name
    assert struct.unpack('>II', data[16:24]) == expected, name
    assert len(data) < 1_000_000, name

for path in (ROOT / 'docs/branding').glob('*.svg'):
    tree = ET.parse(path)
    for element in tree.iter('{http://www.w3.org/2000/svg}image'):
        href = element.get('{http://www.w3.org/1999/xlink}href', element.get('href', ''))
        assert href.startswith('data:image/png;base64,'), f'External image reference: {path}'

readme = (ROOT / 'README.md').read_text()
assert '<details>' not in readme, 'Keep screenshots visible in GitHub README'
assert len(re.findall(r'!\[[^\]]+\]\(docs/screenshots/[^)]+\)', readme)) == 4
assert '](docs/branding/github-social-preview.png)' in readme
for index, stem in enumerate(['01-stripe-rest-settings', '02-dependency-status', '03-api-endpoints', '04-payment-diagnostics'], 1):
    assert (ROOT / f'docs/screenshots/{stem}.png').read_bytes() == (ROOT / f'wordpress-org-assets/screenshot-{index}.png').read_bytes()

for path in ROOT.rglob('*.json'):
    if not any(part in SKIP for part in path.relative_to(ROOT).parts):
        json.loads(path.read_text())

if (ROOT / '.git').is_dir():
    ignored = ['vendor/autoload.php', 'node_modules/example.js', '.env', '.env.local', 'wp-config.php', 'tests/local-config.php', 'build/plugin.zip', 'dist/plugin.zip', 'store.sql', 'debug.log', '.DS_Store', 'docs/verification/local.txt', 'docs/screenshots/capture-original-test.png']
    tracked = ['composer.lock', 'phpunit.xml.dist', 'phpstan.neon.dist', '.github/workflows/ci.yml', 'tests/Unit/PaymentTest.php', 'docs/branding/github-social-preview.png', 'docs/screenshots/01-stripe-rest-settings.png']
    for candidate in ignored + tracked:
        result = subprocess.run(['git', 'check-ignore', '--no-index', '-q', candidate], cwd=ROOT, check=False)
        assert result.returncode == (0 if candidate in ignored else 1), f'Unexpected ignore rule: {candidate}'

archive = ROOT / 'dist/quixdevs-stripe-rest-payments.zip'
if archive.exists():
    from package import verify_archive
    import hashlib
    names = verify_archive(archive)
    manifest = json.loads((ROOT / 'dist/package-manifest.json').read_text())
    assert hashlib.sha256(archive.read_bytes()).hexdigest() == manifest['sha256']
    assert len(names) == manifest['files']

print(f'Repository checks passed: {links} relative links, 4 visible screenshots, image dimensions, JSON, SVG references and available package/ignore checks.')
