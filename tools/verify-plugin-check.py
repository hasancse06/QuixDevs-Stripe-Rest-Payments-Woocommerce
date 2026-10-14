#!/usr/bin/env python3
"""Fail if Plugin Check strict JSON contains errors or malformed output."""
import json
import sys
from pathlib import Path


def findings(raw):
    if raw.strip() == 'Success: Checks complete. No errors found.':
        return []
    data = json.loads(raw)
    if not isinstance(data, list):
        raise ValueError('Expected Plugin Check strict-json array or exact clean result.')
    for item in data:
        if not isinstance(item, dict) or not {'type', 'code', 'message'} <= item.keys() or str(item['type']).upper() not in {'ERROR', 'WARNING'}:
            raise ValueError('Malformed Plugin Check finding.')
    return data


if __name__ == '__main__':
    try:
        result = findings(Path(sys.argv[1]).read_text())
    except (ValueError, OSError) as error:
        raise SystemExit(str(error)) from error
    errors = [f for f in result if str(f['type']).upper() == 'ERROR']
    warnings = [f for f in result if str(f['type']).upper() == 'WARNING']
    print(f'Plugin Check: {len(errors)} errors, {len(warnings)} warnings.')
    for item in errors + warnings:
        print(f"{item['type']}: {item['code']}: {item['message']}")
    if errors:
        raise SystemExit(1)
