#!/usr/bin/env python3
"""Check tracked publication files; reports filenames/rules, never matched secret values."""
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
SKIP = {'.git', 'state', 'build', 'dist', '__pycache__'}
RULES = {
    'private-macos-path': re.compile(r'/Users/[A-Za-z][A-Za-z0-9_-]*/'),
    'private-windows-path': re.compile(r'[A-Za-z]:\\Users\\[^\\\s]+\\'),
    'private-lan-address': re.compile(r'\b(?:192\.168\.\d{1,3}\.\d{1,3}|10\.\d{1,3}\.\d{1,3}\.\d{1,3}|172\.(?:1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3})\b'),
    'mac-address': re.compile(r'\b(?:[0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}\b'),
    'private-key': re.compile(r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----'),
    'github-token': re.compile(r'\b(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,})'),
    'private-proxy-uri': re.compile(r'(?:vless|vmess|trojan|ss)://[^\s<>]{12,}'),
    'email': re.compile(r'[A-Za-z0-9_.+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}'),
}
ALLOWED_SUFFIX = {'.md', '.py', '.java', '.xml', '.json', '.yml', '.yaml', '.txt'}
ALLOWED_NAMES = {'LICENSE', '.gitignore'}


def scan(paths):
    errors = []
    for path in paths:
        rel = path.relative_to(ROOT)
        if any(part in SKIP for part in rel.parts):
            errors.append((str(rel), 'private/generated directory tracked'))
            continue
        if path.is_symlink():
            errors.append((str(rel), 'symlink'))
            continue
        if path.suffix not in ALLOWED_SUFFIX and path.name not in ALLOWED_NAMES:
            errors.append((str(rel), 'unapproved publication type'))
            continue
        if path.stat().st_size > 1_000_000:
            errors.append((str(rel), 'unexpectedly large text file'))
            continue
        text = path.read_text(encoding='utf-8')
        for name, rule in RULES.items():
            if rule.search(text):
                errors.append((str(rel), name))
    return errors


def main():
    result = subprocess.run(['git', '-C', str(ROOT), 'ls-files', '-z'], capture_output=True, check=True)
    paths = [ROOT / p.decode() for p in result.stdout.split(b'\0') if p]
    if not paths:
        print('FAIL: no tracked publication files')
        return 1
    errors = scan(paths)
    for path, rule in errors:
        print('FAIL:', path, rule)
    print('Checked', len(paths), 'tracked files;', len(errors), 'findings. Manual review still required.')
    return bool(errors)


if __name__ == '__main__':
    sys.exit(main())
