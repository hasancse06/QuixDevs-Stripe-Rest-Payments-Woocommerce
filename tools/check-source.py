#!/usr/bin/env python3
"""No external services; checks for accidentally committed credentials and artifacts."""
from pathlib import Path
import re
root=Path(__file__).resolve().parents[1]
skip={'vendor','build','.git','.phpstan-cache','.phpunit.cache'}
for path in root.rglob('*'):
    if not path.is_file() or any(p in skip for p in path.relative_to(root).parts): continue
    assert path.name not in {'.env','wp-config.php','debug.log'}, path
    if path.suffix in {'.php','.md','.json','.yml','.txt'}:
        text=path.read_text()
        assert not re.search(r'(?:sk|rk)_(?:live|test)_[A-Za-z0-9]{20,}',text),path
        assert '-----BEGIN PRIVATE KEY-----' not in text,path
print('Source scan passed; a heuristic scan is not a credential audit.')
