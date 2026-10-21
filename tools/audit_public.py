#!/usr/bin/env python3
"""Audit the actual Git index, a source ZIP tree, or reachable historical blobs."""
import argparse
import ipaddress
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
SKIP = {'.git', 'state', 'build', 'dist', '__pycache__'}
RULES = {
    'private-home-path': re.compile(r'/(?:Users|home)/[\w .-]+/'),
    'private-windows-path': re.compile(r'[A-Za-z]:\\Users\\[^\\\s]+\\'),
    'mac-address': re.compile(r'\b(?:[0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}\b'),
    'private-key': re.compile(r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----'),
    'github-token': re.compile(r'\b(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,})'),
    'private-proxy-uri': re.compile(r'(?:vless|vmess|trojan|ss)://[^\s<>]{12,}'),
    'email': re.compile(r'[A-Za-z0-9_.+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}'),
    'cookie-header': re.compile(r'(?im)^\s*[\"\']?(?:set-cookie|cookie)[\"\']?\s*:\s*\S+'),
    'authorization-header': re.compile(r'(?im)^\s*[\"\']?authorization[\"\']?\s*:\s*\S+'),
    'secret-assignment': re.compile(r'(?im)^\s*(?:export\s+)?[\"\']?(?:[\w]*(?:token|password|secret|api_key|cookie)[\w]*)[\"\']?\s*[:=]\s*[\"\']?[\w+/=.:-]{16,}'),
    'url-userinfo': re.compile(r'https?://[^\s/@]+:[^\s/@]+@'),
}
ALLOWED_SUFFIX = {'.md', '.py', '.java', '.xml', '.json', '.yml', '.yaml', '.txt'}
ALLOWED_NAMES = {'LICENSE', '.gitignore'}
EXAMPLE_NETS = [ipaddress.ip_network(n) for n in
                ['192.0.2.0/24', '198.51.100.0/24', '203.0.113.0/24', '2001:db8::/32']]


def content_findings(name, data):
    """Messages contain only a filename and rule; never include a matched value."""
    path = Path(name)
    if any(part in SKIP for part in path.parts):
        return [(name, 'private/generated directory included')]
    if path.suffix not in ALLOWED_SUFFIX and path.name not in ALLOWED_NAMES:
        return [(name, 'unapproved publication type')]
    if len(data) > 1_000_000:
        return [(name, 'unexpectedly large text file')]
    try:
        text = data.decode('utf-8')
    except UnicodeError:
        return [(name, 'non-UTF8/binary content')]
    errors = [(name, label) for label, rule in RULES.items() if rule.search(text)]
    candidates = re.findall(r'\b(?:\d{1,3}\.){3}\d{1,3}\b|(?<![\w:])(?:[0-9a-fA-F]{0,4}:){2,}[0-9a-fA-F]{0,4}(?![\w:])', text)
    for value in candidates:
        try:
            address = ipaddress.ip_address(value)
        except ValueError:
            continue
        if address.is_loopback or any(address.version == net.version and address in net for net in EXAMPLE_NETS):
            continue
        errors.append((name, 'device-or-public-ip-address'))
        break
    return errors


def scan(paths):
    errors = []
    for path in paths:
        name = str(path.relative_to(ROOT))
        if path.is_symlink():
            errors.append((name, 'symlink'))
            continue
        try:
            errors.extend(content_findings(name, path.read_bytes()))
        except OSError:
            errors.append((name, 'unreadable file'))
    return errors


def git(*args):
    return subprocess.run(['git', '-C', str(ROOT), *args], capture_output=True, check=True).stdout


def is_repository():
    try:
        return Path(git('rev-parse', '--show-toplevel').decode().strip()).resolve() == ROOT.resolve()
    except (OSError, subprocess.CalledProcessError):
        return False


def index_scan():
    errors, count = [], 0
    for entry in git('ls-files', '--stage', '-z').split(b'\0'):
        if not entry:
            continue
        header, name = entry.split(b'\t', 1)
        mode, oid, stage = header.decode().split()
        label = name.decode('utf-8', errors='replace')
        count += 1
        if stage != '0' or mode not in ('100644', '100755'):
            errors.append((label, 'symlink/submodule/unmerged index entry'))
            continue
        errors.extend(content_findings(label, git('cat-file', 'blob', oid)))
    return count, errors


def history_scan():
    errors, count = [], 0
    for entry in git('rev-list', '--objects', '--all').decode().splitlines():
        oid, _, name = entry.partition(' ')
        if git('cat-file', '-t', oid).strip() != b'blob':
            continue
        count += 1
        errors.extend(content_findings(name or 'historical-blob', git('cat-file', 'blob', oid)))
    return count, errors


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', choices=['auto', 'index', 'tree'], default='auto')
    parser.add_argument('--history', action='store_true', help='Also check reachable Git file history')
    args = parser.parse_args(argv)
    repository = is_repository()
    source = ('index' if repository else 'tree') if args.source == 'auto' else args.source
    if source == 'index':
        if not repository:
            print('FAIL: index audit requires a Git checkout; use --source tree for a ZIP.')
            return 1
        count, errors = index_scan()
    else:
        paths = [p for p in ROOT.rglob('*') if not any(x in SKIP for x in p.relative_to(ROOT).parts)
                 and (p.is_file() or p.is_symlink())]
        count, errors = len(paths), scan(paths)
    if args.history:
        if not repository:
            print('FAIL: a ZIP has no Git history; omit --history.')
            return 1
        past, findings = history_scan()
        count += past
        errors.extend(findings)
    if not count:
        errors.append(('.', 'empty publication scope'))
    for name, rule in sorted(set(errors)):
        print('FAIL:', name, rule)
    print('Checked', count, source, 'entries' + (' + history' if args.history else '')
          + ';', len(set(errors)), 'findings. Manual review still required.')
    return bool(errors)


if __name__ == '__main__':
    sys.exit(main())
