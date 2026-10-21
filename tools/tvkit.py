#!/usr/bin/env python3
"""Bounded ADB inspection, APK backup and reversible HOME selection. Python 3.10+."""
import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import sys
import uuid

ROOT = Path(__file__).resolve().parents[1]
PROFILE = json.loads((ROOT / 'profiles/c3apro-api34.json').read_text())
PACKAGE = re.compile(r'[A-Za-z][A-Za-z0-9_]*(?:\.[A-Za-z0-9_]+)+\Z')
COMPONENT = re.compile(r'[A-Za-z][A-Za-z0-9_.]+/[A-Za-z0-9_.$]+\Z')


def checked(output):
    """Android shell tools can exit zero while reporting a failed operation."""
    if re.search(r'(?im)^\s*(error(?:\b|:)|failure(?:\b|\[)|exception\b|securityexception\b)', output):
        raise RuntimeError('Android reported failure; inspect the local command output.')
    return output.strip()


def package_state(dump):
    match = re.search(r'^\s*User 0:\s*(.+)$', dump, re.M)
    if not match:
        return {'installed': False, 'hidden': None, 'enabled': None, 'suspended': None}
    fields = dict(re.findall(r'(installed|hidden|enabled|suspended)=([^\s]+)', match.group(1)))
    if not {'installed', 'hidden', 'enabled'} <= fields.keys():
        raise RuntimeError('Unrecognized User 0 package state; stop rather than guess.')
    if any(value not in ('true', 'false') for key, value in fields.items() if key != 'enabled'):
        raise RuntimeError('Unrecognized package boolean state.')
    if fields['enabled'] not in ('0', '1', '2', '3', '4'):
        raise RuntimeError('Unrecognized package enabled state.')
    return {k: (int(v) if k == 'enabled' else v == 'true') for k, v in fields.items()}


def component_from(output):
    candidates = [line.strip() for line in output.splitlines() if COMPONENT.fullmatch(line.strip())]
    if len(candidates) != 1:
        raise RuntimeError('A unique HOME component could not be resolved.')
    return candidates[0]


def canonical(component):
    package, activity = component.split('/', 1)
    return package + '/' + (package + activity if activity.startswith('.') else activity)


def save(path, data):
    """Write local receipts atomically with private filesystem permissions."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    temp = path.with_name(path.name + '.' + uuid.uuid4().hex + '.tmp')
    fd = os.open(temp, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    with os.fdopen(fd, 'w') as stream:
        json.dump(data, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temp, path)


class Device:
    def __init__(self, serial, adb='adb'):
        self.serial = serial
        self.adb = adb

    def run(self, *args, timeout=45):
        proc = subprocess.run([self.adb, '-s', self.serial, *args], capture_output=True,
                              text=True, timeout=timeout)
        if proc.returncode:
            raise RuntimeError('ADB failed: ' + proc.stderr.strip())
        checked(proc.stderr)
        return checked(proc.stdout)

    def shell(self, *args):
        # ADB shell parses a remote shell string, so quote every argument separately.
        return self.run('shell', shlex.join(args))

    def identity(self):
        return {'model': self.shell('getprop', 'ro.product.model'),
                'sdk': self.shell('getprop', 'ro.build.version.sdk'),
                'abi': self.shell('getprop', 'ro.product.cpu.abilist')}

    def guard(self):
        identity = self.identity()
        if (identity['model'], identity['sdk']) != (PROFILE['model'], PROFILE['sdk']):
            raise RuntimeError('Mutation supports C3APRO / API 34 only; no override is provided.')
        if self.shell('am', 'get-current-user') != '0':
            raise RuntimeError('Switch to the device primary user before applying changes.')
        return identity

    def binding(self):
        # Local hash prevents restoring a receipt to another unit; never print raw ID.
        raw = self.shell('settings', '--user', '0', 'get', 'secure', 'android_id')
        if not re.fullmatch(r'[0-9a-fA-F]{16}', raw):
            raise RuntimeError('No stable local device binding is available; stop.')
        return hashlib.sha256(raw.encode()).hexdigest()

    def state(self, package):
        if not PACKAGE.fullmatch(package):
            raise ValueError('Invalid package name')
        return package_state(self.shell('dumpsys', 'package', package))

    def home(self):
        return component_from(self.shell('cmd', 'package', 'resolve-activity', '--brief',
                                         '--user', '0', '-a', 'android.intent.action.MAIN',
                                         '-c', 'android.intent.category.HOME'))


def ready_home(device, component):
    if not COMPONENT.fullmatch(component):
        raise ValueError('Use a package/activity component, not a shell command.')
    state = device.state(component.split('/')[0])
    if (not state['installed'] or state['hidden'] or state['enabled'] not in (0, 1)
            or state.get('suspended') is not False):
        raise RuntimeError('Target HOME is absent, hidden, disabled, suspended or unrecognized.')
    homes = device.shell('cmd', 'package', 'query-activities', '--brief', '--user', '0',
                         '-a', 'android.intent.action.MAIN', '-c', 'android.intent.category.HOME')
    available = {canonical(line.strip()) for line in homes.splitlines()
                 if COMPONENT.fullmatch(line.strip())}
    if canonical(component) not in available:
        raise RuntimeError('Target is not an available HOME activity for user 0.')
    if component.split('/')[0] == 'com.google.android.apps.tv.launcherx':
        flag = device.shell('settings', '--user', '0', 'get', 'secure', 'tv_user_setup_complete')
        if flag != '1':
            raise RuntimeError('Complete normal Google TV onboarding first. No flag will be written.')


def set_home(device, component):
    device.shell('cmd', 'package', 'set-home-activity', '--user', '0', component)
    if canonical(device.home()) != canonical(component):
        raise RuntimeError('HOME resolution did not reach the requested component.')


def switch_home(device, component, apply, directory):
    identity = device.guard()
    ready_home(device, component)
    before = device.home()
    plan = {'operation': 'home', 'before_home': before, 'target_home': component,
            'changes': ['default HOME only'], 'applied': False}
    if not apply:
        return plan
    path = Path(directory) / ('home-' + uuid.uuid4().hex + '.json')
    receipt = dict(plan, schema=1, identity=identity, binding=device.binding(),
                   time=dt.datetime.now(dt.timezone.utc).isoformat(), status='PREPARED')
    save(path, receipt)  # A durable baseline must exist before the first write.
    try:
        receipt['status'] = 'APPLYING'
        save(path, receipt)
        set_home(device, component)
        receipt.update(status='PASS_HOME_RESOLUTION', applied=True,
                       physical_home_key='NOT_RUN')
    except Exception:
        receipt['status'] = 'FAILED'
        save(path, receipt)
        try:
            ready_home(device, before)
            set_home(device, before)
            receipt['rollback'] = 'PASS_HOME_RESOLUTION'
        except Exception:
            receipt['rollback'] = 'FAILED_REQUIRES_LOCAL_REVIEW'
        save(path, receipt)
        raise RuntimeError('HOME change failed; local receipt: ' + str(path)) from None
    save(path, receipt)
    return {'receipt': str(path), 'status': receipt['status'], 'physical_home_key': 'NOT_RUN'}


def restore_home(device, path, apply):
    data = json.loads(Path(path).read_text())
    device.guard()
    if data.get('schema') != 1 or data.get('operation') != 'home':
        raise RuntimeError('Not a HOME transaction receipt.')
    if data['binding'] != device.binding():
        raise RuntimeError('Receipt belongs to a different device.')
    # Restoration is a new transaction, retaining both original and new evidence.
    return switch_home(device, data['before_home'], apply, Path(path).parent)


def inspect(device):
    return {'identity': device.identity(), 'home': device.home(),
            'display': {'size': device.shell('wm', 'size'), 'density': device.shell('wm', 'density')},
            'google': {p: device.state(p) for p in PROFILE['google_core'] + PROFILE['google_native']},
            'scope': 'Read-only; no account, network configuration, screenshot or logcat dump.'}


def backup(device, packages, directory):
    """APK bytes and package flags only, not private application data or a system image."""
    device.guard()
    out = Path(directory) / ('backup-' + uuid.uuid4().hex)
    out.mkdir(parents=True, mode=0o700)
    manifest = {'schema': 1, 'identity': device.identity(), 'binding': device.binding(),
                'status': 'IN_PROGRESS', 'packages': {}, 'scope': 'APK_AND_FLAGS_ONLY'}
    save(out / 'manifest.json', manifest)
    try:
        for package in packages:
            state = device.state(package)
            manifest['packages'][package] = {'state': state, 'files': []}
            save(out / 'manifest.json', manifest)
            if not state['installed']:
                raise RuntimeError('Package is not installed for user 0: ' + package)
            listing = device.shell('pm', 'path', '--user', '0', package)
            paths = [line[8:] for line in listing.splitlines() if line.startswith('package:')]
            if not paths or any(not p.startswith('/') or not p.endswith('.apk') for p in paths):
                raise RuntimeError('Unrecognized APK paths: ' + package)
            for index, remote in enumerate(paths):
                name = package + '-' + str(index) + '.apk'
                local = out / name
                device.run('pull', remote, str(local), timeout=300)
                os.chmod(local, 0o600)
                digest = hashlib.sha256(local.read_bytes()).hexdigest()
                remote_digest = device.shell('sha256sum', remote).split()[0]
                if digest != remote_digest:
                    raise RuntimeError('APK digest mismatch: ' + package)
                manifest['packages'][package]['files'].append({'name': name, 'sha256': digest})
                save(out / 'manifest.json', manifest)
        manifest['status'] = 'PASS_APK_COPY_AND_DIGEST'
    except Exception:
        manifest['status'] = 'FAILED_PARTIAL_BACKUP'
        save(out / 'manifest.json', manifest)
        raise
    save(out / 'manifest.json', manifest)
    return {'directory': str(out), 'status': manifest['status'], 'private_app_data': 'NOT_BACKED_UP'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--serial', required=True, help='Current authorized ADB connection endpoint')
    parser.add_argument('--adb', default='adb')
    commands = parser.add_subparsers(dest='command', required=True)
    commands.add_parser('inspect')
    b = commands.add_parser('backup')
    b.add_argument('--package', action='append', required=True)
    b.add_argument('--out', default=str(ROOT / 'state'))
    h = commands.add_parser('home')
    h.add_argument('--component', required=True)
    h.add_argument('--apply', action='store_true')
    h.add_argument('--out', default=str(ROOT / 'state'))
    r = commands.add_parser('restore-home')
    r.add_argument('--receipt', required=True)
    r.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    device = Device(args.serial, args.adb)
    try:
        if args.command == 'inspect':
            result = inspect(device)
        elif args.command == 'backup':
            result = backup(device, args.package, args.out)
        elif args.command == 'home':
            result = switch_home(device, args.component, args.apply, args.out)
        else:
            result = restore_home(device, args.receipt, args.apply)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except (RuntimeError, ValueError, OSError, KeyError, subprocess.SubprocessError) as error:
        print('STOP: ' + str(error), file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
