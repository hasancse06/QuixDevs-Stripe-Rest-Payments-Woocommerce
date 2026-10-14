#!/usr/bin/env python3
"""Build the allowlisted, development-only WordPress installation package."""
from pathlib import Path, PurePosixPath
import hashlib
import json
import re
import zipfile

ROOT = Path(__file__).resolve().parents[1]
SLUG = 'quixdevs-stripe-rest-payments'
STATUS = 'development-only'
VERSION = '1.0.0'
OUT = ROOT / 'dist'


def versions(root=ROOT):
    main = (root / f'{SLUG}.php').read_text()
    readme = (root / 'readme.txt').read_text()
    plugin = re.search(r'^\s*\* Version:\s*(\S+)', main, re.M)
    stable = re.search(r'^Stable tag:\s*(\S+)', readme, re.M)
    if not plugin or not stable or plugin[1] != VERSION or stable[1] != VERSION:
        raise ValueError('Plugin header and Stable tag must remain 1.0.0.')
    return VERSION


def runtime_files(root=ROOT):
    spec = json.loads((root / 'tools/runtime-files.json').read_text())
    names = spec['files']
    if spec['slug'] != SLUG or len(names) != len(set(names)):
        raise ValueError('Invalid runtime allowlist.')
    # There are no Composer production libraries; the plugin has its own loader.
    require = json.loads((root / 'composer.json').read_text()).get('require', {})
    if spec['runtime_dependencies'] or set(require) - {'php'}:
        raise ValueError('New production dependencies require explicit packaging review.')
    for name in names:
        parts = PurePosixPath(name).parts
        if not parts or name.startswith('/') or '..' in parts or '\\' in name:
            raise ValueError(f'Unsafe runtime path: {name}')
        path = root / name
        if not path.is_file() or any((root.joinpath(*parts[:i])).is_symlink() for i in range(1, len(parts) + 1)):
            raise ValueError(f'Missing or symlinked runtime file: {name}')
        scan_content(name, path.read_bytes())
    discovered = {p.relative_to(root).as_posix() for p in (root / 'includes').rglob('*.php')}
    if discovered != {n for n in names if n.startswith('includes/')}:
        raise ValueError('Runtime class tree differs from the explicit allowlist; review it.')
    for required in [f'{SLUG}.php', 'uninstall.php', 'readme.txt', 'LICENSE', 'includes/Autoload.php']:
        if required not in names:
            raise ValueError(f'Required production component missing: {required}')
    versions(root)
    return names


def scan_content(name, data):
    text = data.decode('utf-8')
    if re.search(r'(?:sk|rk)_(?:live|test)_[A-Za-z0-9]{20,}', text) or re.search(r'-----BEGIN (?:[A-Z]+ )?PRIVATE KEY-----', text):
        raise ValueError(f'Credential-like runtime content: {name}')
    if name.endswith('.php') and any(s in text for s in ['var_dump(', "$_POST[", 'WP_API_TOKEN']):
        raise ValueError(f'Legacy/debug runtime pattern: {name}')


def verify_archive(archive, root=ROOT):
    expected = [f'{SLUG}/{n}' for n in runtime_files(root)]
    with zipfile.ZipFile(archive) as package:
        names = package.namelist()
        if names != expected or len(names) != len(set(names)):
            raise ValueError('ZIP root, file order or contents differ from the runtime allowlist.')
        if package.testzip() is not None:
            raise ValueError('ZIP CRC/integrity failure.')
        for name in expected:
            relative = name[len(SLUG) + 1:]
            data = package.read(name)
            if data != (root / relative).read_bytes():
                raise ValueError(f'Runtime source/ZIP mismatch: {relative}')
            scan_content(relative, data)
    return expected


def build(root=ROOT):
    names = runtime_files(root)
    out = root / 'dist'
    out.mkdir(exist_ok=True)
    archive = out / f'{SLUG}.zip'
    temporary = out / f'{SLUG}.zip.tmp'
    try:
        with zipfile.ZipFile(temporary, 'w', zipfile.ZIP_DEFLATED) as package:
            package.comment = b'Development-only; merchant acceptance and publisher review outstanding.'
            for name in names:
                # Fixed metadata makes identical runtime inputs reproducible.
                info = zipfile.ZipInfo(f'{SLUG}/{name}', (2026, 10, 10, 0, 0, 0))
                info.create_system = 3
                info.external_attr = 0o100644 << 16
                info.compress_type = zipfile.ZIP_DEFLATED
                package.writestr(info, (root / name).read_bytes())
        verify_archive(temporary, root)
        temporary.replace(archive)
    finally:
        temporary.unlink(missing_ok=True)
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    checksum = out / f'{archive.name}.sha256'
    checksum.write_text(f'{digest}  {archive.name}\n')
    manifest = {
        'archive': archive.name, 'version': VERSION, 'status': STATUS,
        'bytes': archive.stat().st_size, 'files': len(names), 'sha256': digest,
        'composer_required_on_server': False, 'bundled_runtime_dependencies': [],
        'required_external_plugins': {'woocommerce': '>=10.9', 'woocommerce-gateway-stripe': '11.0.1'},
        'runtime_files': {name: hashlib.sha256((root / name).read_bytes()).hexdigest() for name in names},
    }
    (out / 'package-manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(json.dumps({key: manifest[key] for key in ['archive', 'version', 'status', 'bytes', 'files', 'sha256', 'composer_required_on_server']}, indent=2))
    return manifest


if __name__ == '__main__':
    try:
        build()
    except (ValueError, OSError, zipfile.BadZipFile) as error:
        raise SystemExit(str(error)) from error
