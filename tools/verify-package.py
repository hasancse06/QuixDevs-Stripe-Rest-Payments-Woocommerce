#!/usr/bin/env python3
"""Verify distribution bytes, SHA-256, syntax and Composer-free autoloading."""
from pathlib import Path
import argparse
import hashlib
import json
import subprocess
import tempfile
import zipfile
from package import ROOT, SLUG, STATUS, VERSION, verify_archive


def verify(archive):
    names = verify_archive(archive)
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    expected = f'{digest}  {archive.name}\n'
    if archive.with_suffix('.zip.sha256').read_text() != expected:
        raise ValueError('SHA-256 sidecar mismatch.')
    manifest = json.loads((archive.parent / 'package-manifest.json').read_text())
    if manifest['status'] != STATUS or manifest['version'] != VERSION or manifest['sha256'] != digest or manifest['files'] != len(names) or manifest['bytes'] != archive.stat().st_size:
        raise ValueError('Package manifest mismatch or changed development restriction.')
    if manifest['composer_required_on_server'] or manifest['bundled_runtime_dependencies']:
        raise ValueError('Unexpected production dependency requirement.')
    for name in names:
        relative = name[len(SLUG) + 1:]
        if manifest['runtime_files'][relative] != hashlib.sha256((ROOT / relative).read_bytes()).hexdigest():
            raise ValueError('Per-file manifest hash mismatch.')
    with tempfile.TemporaryDirectory(prefix='quixdevs-runtime-') as temporary:
        # Paths were matched exactly to the allowlist before extraction.
        with zipfile.ZipFile(archive) as package:
            package.extractall(temporary)
        runtime = Path(temporary) / SLUG
        for path in runtime.rglob('*.php'):
            subprocess.run(['php', '-l', str(path)], check=True, capture_output=True)
        program = r'''
        define('ABSPATH', $argv[1] . '/');
        require $argv[1] . '/includes/Autoload.php';
        $count = 0;
        foreach (json_decode(stream_get_contents(STDIN), true) as $name) {
            if (!str_starts_with($name, 'includes/') || $name === 'includes/Autoload.php') { continue; }
            $class = 'QuixDevs\\StripeRestPayments\\' . str_replace('/', '\\', substr($name, 9, -4));
            if (!class_exists($class) && !interface_exists($class) && !enum_exists($class)) {
                throw new RuntimeException('Cannot autoload ' . $class);
            }
            $reflection = new ReflectionClass($class);
            if (realpath($reflection->getFileName()) !== realpath($argv[1] . '/' . $name)) {
                throw new RuntimeException('Autoload resolved outside package');
            }
            ++$count;
        }
        echo $count . " runtime types autoloaded without Composer.\n";
        '''
        result = subprocess.run(['php', '-r', program, str(runtime)], input=json.dumps(list(manifest['runtime_files'])), text=True, capture_output=True, check=True)
        print(result.stdout.strip())
    print(f'Verified {archive.name}: {len(names)} allowlisted files, {archive.stat().st_size} bytes, SHA-256 {digest}; development-only.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive', type=Path, default=ROOT / 'dist' / f'{SLUG}.zip')
    args = parser.parse_args()
    try:
        verify(args.archive)
    except (ValueError, OSError, subprocess.CalledProcessError, zipfile.BadZipFile) as error:
        raise SystemExit(str(error)) from error
