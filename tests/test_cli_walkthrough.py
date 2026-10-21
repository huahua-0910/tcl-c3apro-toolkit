import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


@unittest.skipIf(os.name == 'nt', 'Executable fixture uses the POSIX shebang; use WSL for this test.')
class FirstUseWalkthroughTests(unittest.TestCase):
    def test_isolated_source_tree_inspect_backup_switch_restore(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            project = root / 'source'
            shutil.copytree(ROOT, project, ignore=shutil.ignore_patterns('.git', 'state', 'build', 'dist', '__pycache__'))
            fake = root / 'fake-adb'
            shutil.copyfile(ROOT / 'tests/fake_adb.py', fake)
            fake.chmod(0o700)
            state = root / 'device.json'
            state.write_text(json.dumps({'home': 'org.example.home/.Home', 'writes': []}))
            env = os.environ.copy()
            env['TVKIT_FIXTURE_STATE'] = str(state)
            base = ['python3', 'tools/tvkit.py', '--serial', 'fixture-device', '--adb', str(fake)]

            def run(*args):
                result = subprocess.run([*base, *args], cwd=project, env=env, capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stderr)
                return json.loads(result.stdout)

            inspect = run('inspect', '--out', 'state/inspect-before.json')
            self.assertEqual(inspect['identity']['sdk'], '34')
            self.assertTrue((project / 'state/inspect-before.json').exists())
            backup = run('backup', '--package', 'com.google.android.apps.tv.launcherx')
            self.assertEqual(backup['status'], 'PASS_APK_COPY_AND_DIGEST')
            target = 'com.google.android.apps.tv.launcherx/.home.HomeActivity'
            run('home', '--component', target)
            self.assertEqual(json.loads(state.read_text())['writes'], [])
            change = run('home', '--component', target, '--apply')
            run('restore-home', '--receipt', change['receipt'])
            self.assertEqual(len(json.loads(state.read_text())['writes']), 1)
            run('restore-home', '--receipt', change['receipt'], '--apply')
            self.assertEqual(json.loads(state.read_text())['home'], 'org.example.home/.Home')
            self.assertEqual(len(list((project / 'state').glob('home-*.json'))), 2)
            result = subprocess.run(['python3', 'tools/audit_public.py'], cwd=project, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            # Empty endpoint must be rejected by argparse before even the fake ADB is launched.
            result = subprocess.run(['python3', 'tools/tvkit.py', '--serial', '', 'inspect'],
                                    cwd=project, capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('Set TV_ENDPOINT', result.stderr)


if __name__ == '__main__':
    unittest.main()
