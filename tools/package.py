#!/usr/bin/env python3
"""Build and inspect a development-only installable ZIP using an allowlist."""
from pathlib import Path
import hashlib, json, re, zipfile
ROOT = Path(__file__).resolve().parents[1]
SLUG = 'quixdevs-stripe-rest-payments'
FILES = ['quixdevs-stripe-rest-payments.php', 'uninstall.php', 'README.md', 'readme.txt', 'LICENSE', 'CHANGELOG.md', 'SECURITY.md']
GUIDES = ['rest-api.md', 'authentication.md', 'payment-flow.md', 'payment-idempotency.md', 'error-codes.md', 'security.md']
files = [ROOT / f for f in FILES] + sorted((ROOT / 'includes').rglob('*.php')) + [ROOT / 'docs' / f for f in GUIDES] + sorted((ROOT / 'docs/examples').glob('*.md')) + sorted((ROOT / 'docs/postman').glob('*'))
for path in files:
    if not path.is_file() or path.is_symlink(): raise SystemExit(f'Missing or unsafe production file: {path}')
    content = path.read_text()
    if re.search(r'(?:sk|rk)_(?:live|test)_[A-Za-z0-9]{20,}', content): raise SystemExit(f'Credential-like content: {path}')
    if path.suffix == '.php' and any(s in content for s in ['var_dump(', "$_POST[", 'WP_API_TOKEN']): raise SystemExit(f'Unsafe legacy/debug pattern: {path}')
out = ROOT / 'build'
out.mkdir(exist_ok=True)
archive = out / (SLUG + '.zip')
with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as z:
    for path in files:
        info = zipfile.ZipInfo(SLUG + '/' + path.relative_to(ROOT).as_posix(), (2026, 10, 10, 0, 0, 0))
        info.external_attr = 0o100644 << 16
        info.compress_type = zipfile.ZIP_DEFLATED
        content = (ROOT / 'tools/package-readme.md').read_bytes() if path.name == 'README.md' and path.parent == ROOT else path.read_bytes()
        z.writestr(info, content)
with zipfile.ZipFile(archive) as z:
    assert z.testzip() is None
    assert all(n.startswith(SLUG + '/') for n in z.namelist())
    assert not any('/vendor/' in n or '/tests/' in n or '/docs/screenshots/' in n or '/docs/branding/' in n or '/.git' in n for n in z.namelist())
manifest = {'archive': archive.name, 'status': 'development-only', 'files': len(files), 'sha256': hashlib.sha256(archive.read_bytes()).hexdigest(), 'composer_required_on_server': False}
(out / 'package-manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
print(json.dumps(manifest, indent=2))
