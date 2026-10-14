#!/usr/bin/env python3
"""Validate an existing version tag; never create tags, commits or releases."""
import argparse
import re
import subprocess
from pathlib import Path
from package import ROOT, versions


def identity(tag, root=ROOT):
    if not re.fullmatch(r'v\d+\.\d+\.\d+', tag):
        raise ValueError('Use an existing version tag in vX.Y.Z format.')
    if tag != 'v' + versions(root):
        raise ValueError('Tag does not match the unchanged plugin version/Stable tag.')
    def git(*args):
        return subprocess.check_output(['git', *args], cwd=root, text=True).strip()
    if git('status', '--porcelain', '--untracked-files=normal'):
        raise ValueError('Release validation requires a clean checked-out tag.')
    commit = git('rev-parse', '--verify', f'refs/tags/{tag}^{{commit}}')
    if commit != git('rev-parse', 'HEAD'):
        raise ValueError('Existing tag must point to the checked-out commit.')
    return {'tag': tag, 'version': versions(root), 'commit': commit, 'status': 'development-only'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--tag', required=True)
    parser.add_argument('--github-output', type=Path)
    args = parser.parse_args()
    try:
        data = identity(args.tag)
        if args.github_output:
            with args.github_output.open('a') as output:
                for name, value in data.items():
                    output.write(f'{name}={value}\n')
        print('\n'.join(f'{name}: {value}' for name, value in data.items()))
    except (ValueError, OSError, subprocess.CalledProcessError) as error:
        raise SystemExit(str(error)) from error
