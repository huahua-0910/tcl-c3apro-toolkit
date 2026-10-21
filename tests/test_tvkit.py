import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('tvkit', ROOT / 'tools/tvkit.py')
kit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(kit)
OLD = 'org.example.home/.Home'
NEW = 'com.google.android.apps.tv.launcherx/.home.HomeActivity'


class FakeDevice:
    def __init__(self):
        self.current = OLD
        self.calls = []
        self.writes = []
        self.fail_target = False
        self.fail_rollback = False
        self.flag = '1'
        self.hidden = False
        self.hash_mismatch = False
        self.device_hash = 'same-device-local-hash'

    def guard(self):
        return {'model': 'C3APRO', 'sdk': '34', 'abi': 'armeabi-v7a'}

    identity = guard

    def binding(self):
        return self.device_hash

    def home(self):
        return self.current

    def state(self, package):
        if not kit.PACKAGE.fullmatch(package):
            raise ValueError('bad package')
        return {'installed': True, 'hidden': self.hidden, 'enabled': 0, 'suspended': False}

    def shell(self, *args):
        self.calls.append(args)
        if args[:3] == ('cmd', 'package', 'query-activities'):
            return '2 activities found:\n' + OLD + '\n' + NEW
        if args[:2] == ('settings', '--user'):
            return self.flag
        if args[:3] == ('cmd', 'package', 'set-home-activity'):
            target = args[-1]
            self.writes.append(target)
            if (target == NEW and self.fail_target) or (target == OLD and self.fail_rollback):
                raise RuntimeError('mock first operation failed')
            self.current = target
            return 'Success'
        if args[:2] == ('pm', 'path'):
            return 'package:/data/app/base.apk\npackage:/data/app/split_config.apk'
        if args[0] == 'sha256sum':
            value = b'wrong' if self.hash_mismatch else args[1].encode()
            return hashlib.sha256(value).hexdigest() + ' ' + args[1]
        raise AssertionError(args)

    def run(self, *args, **kwargs):
        if args[0] == 'pull':
            Path(args[2]).write_bytes(args[1].encode())
            return 'copied'
        raise AssertionError(args)


class TransactionTests(unittest.TestCase):
    def test_dry_run_does_not_mutate_or_save(self):
        device = FakeDevice()
        with tempfile.TemporaryDirectory() as folder:
            result = kit.switch_home(device, NEW, False, folder)
            self.assertFalse(result['applied'])
            self.assertEqual(device.writes, [])
            self.assertEqual(list(Path(folder).iterdir()), [])

    def test_success_and_explicit_restore_keep_both_receipts(self):
        device = FakeDevice()
        with tempfile.TemporaryDirectory() as folder:
            result = kit.switch_home(device, NEW, True, folder)
            self.assertEqual(device.current, NEW)
            receipt = json.loads(Path(result['receipt']).read_text())
            self.assertEqual(receipt['physical_home_key'], 'NOT_RUN')
            self.assertEqual(Path(result['receipt']).stat().st_mode & 0o777, 0o600)
            kit.restore_home(device, result['receipt'], True)
            self.assertEqual(device.current, OLD)
            self.assertEqual(len(list(Path(folder).glob('home-*.json'))), 2)

    def test_target_failure_preserves_failure_and_attempts_rollback(self):
        device = FakeDevice()
        device.fail_target = True
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaises(RuntimeError):
                kit.switch_home(device, NEW, True, folder)
            data = json.loads(next(Path(folder).glob('*.json')).read_text())
            self.assertEqual(data['status'], 'FAILED')
            self.assertEqual(data['failure']['message'], 'mock first operation failed')
            self.assertEqual(data['rollback'], 'PASS_HOME_RESOLUTION')
            self.assertEqual(device.writes, [NEW, OLD])

    def test_rollback_failure_is_never_reported_as_pass(self):
        device = FakeDevice()
        device.fail_target = device.fail_rollback = True
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaises(RuntimeError):
                kit.switch_home(device, NEW, True, folder)
            data = json.loads(next(Path(folder).glob('*.json')).read_text())
            self.assertEqual(data['rollback'], 'FAILED_REQUIRES_LOCAL_REVIEW')
            self.assertIn('rollback_failure', data)

    def test_baseline_storage_failure_blocks_first_write(self):
        device = FakeDevice()
        with patch.object(kit, 'save', side_effect=OSError('disk full')):
            with self.assertRaises(OSError):
                kit.switch_home(device, NEW, True, '/unused')
        self.assertEqual(device.writes, [])

    def test_cross_device_restore_refused(self):
        device = FakeDevice()
        with tempfile.TemporaryDirectory() as folder:
            result = kit.switch_home(device, NEW, True, folder)
            device.device_hash = 'other-unit'
            device.writes.clear()
            with self.assertRaises(RuntimeError):
                kit.restore_home(device, result['receipt'], True)
            self.assertEqual(device.writes, [])

    def test_unfinished_google_setup_and_hidden_target_refused(self):
        for flag, hidden in [('0', False), ('1', True)]:
            device = FakeDevice()
            device.flag, device.hidden = flag, hidden
            with self.assertRaises(RuntimeError):
                kit.switch_home(device, NEW, True, '/unused')
            self.assertEqual(device.writes, [])

    def test_backup_copies_and_verifies_every_split(self):
        device = FakeDevice()
        with tempfile.TemporaryDirectory() as folder:
            result = kit.backup(device, ['org.example.home'], folder)
            manifest = json.loads((Path(result['directory']) / 'manifest.json').read_text())
            self.assertEqual(manifest['status'], 'PASS_APK_COPY_AND_DIGEST')
            self.assertEqual(len(manifest['packages']['org.example.home']['files']), 2)
            self.assertEqual(result['private_app_data'], 'NOT_BACKED_UP')

    def test_backup_hash_failure_retains_partial_result(self):
        device = FakeDevice()
        device.hash_mismatch = True
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaises(RuntimeError):
                kit.backup(device, ['org.example.home'], folder)
            data = json.loads(next(Path(folder).glob('*/manifest.json')).read_text())
            self.assertEqual(data['status'], 'FAILED_PARTIAL_BACKUP')


class AdbBoundaryTests(unittest.TestCase):
    def test_android_zero_exit_error_detected(self):
        for output in ['Error: not allowed', 'Failure [INSTALL_FAILED]', 'SecurityException: denied']:
            with self.assertRaises(RuntimeError):
                kit.checked(output)

    def test_shell_arguments_quoted_and_no_local_shell(self):
        result = subprocess.CompletedProcess([], 0, 'ok', '')
        with patch.object(kit.subprocess, 'run', return_value=result) as run:
            kit.Device('endpoint').shell('echo', 'a; echo unexpected')
            args, kwargs = run.call_args
            self.assertEqual(args[0][-1], "echo 'a; echo unexpected'")
            self.assertFalse(kwargs.get('shell', False))

    def test_model_and_user_guards(self):
        device = kit.Device('endpoint')
        with patch.object(device, 'identity', return_value={'model': 'other', 'sdk': '34'}):
            with self.assertRaises(RuntimeError):
                device.guard()
        with patch.object(device, 'identity', return_value={'model': 'C3APRO', 'sdk': '34'}):
            with patch.object(device, 'shell', return_value='10'):
                with self.assertRaises(RuntimeError):
                    device.guard()

    def test_parse_user0_only_and_reject_malformed(self):
        data = '  User 0: installed=true hidden=false suspended=false enabled=0\n  User 10: installed=false hidden=true enabled=3'
        self.assertEqual(kit.package_state(data)['enabled'], 0)
        self.assertFalse(kit.package_state(data)['hidden'])
        with self.assertRaises(RuntimeError):
            kit.package_state('User 0: installed=true')
        with self.assertRaises(RuntimeError):
            kit.package_state('User 0: installed=true hidden=unknown enabled=0')


if __name__ == '__main__':
    unittest.main()
