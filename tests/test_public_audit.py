import contextlib
import importlib.util
import io
from pathlib import Path
import subprocess
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('audit_public', ROOT / 'tools/audit_public.py')
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


def git(root, *args):
    return subprocess.run(['git', '-C', str(root), *args], capture_output=True, check=True)


class PublicAuditRegressionTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which('git'), 'Git index test requires Git; ZIP tools do not.')
    def test_staged_secret_is_found_after_worktree_is_cleaned(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            git(root, 'init', '-q')
            file = root / 'note.md'
            file.write_text('gh' + 'p_' + 'x' * 36)
            git(root, 'add', 'note.md')
            file.write_text('Clean worktree, but secret remains in the index.\n')
            with patch.object(audit, 'ROOT', root), patch.object(sys, 'argv', ['audit_public.py']):
                with contextlib.redirect_stdout(io.StringIO()) as output:
                    result = audit.main()
            self.assertTrue(result)
            self.assertNotIn('x' * 36, output.getvalue())

    def test_zip_tree_without_git_is_supported(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / 'README.md').write_text('Public documentation.\n')
            with patch.object(audit, 'ROOT', root), patch.object(sys, 'argv', ['audit_public.py']):
                with contextlib.redirect_stdout(io.StringIO()):
                    self.assertFalse(audit.main())

    def test_zip_audit_works_when_git_executable_is_absent(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / 'README.md').write_text('Public documentation.\n')
            with patch.object(audit, 'ROOT', root), patch.object(audit, 'git', side_effect=FileNotFoundError):
                with contextlib.redirect_stdout(io.StringIO()):
                    self.assertFalse(audit.main([]))

    def test_cookie_and_authorization_values_are_flagged(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            file = root / 'note.md'
            for content in ['Cookie: session_id=' + 'x' * 20,
                            'Author' + 'ization: Bearer ' + 'z' * 30]:
                file.write_text(content)
                with patch.object(audit, 'ROOT', root):
                    self.assertTrue(audit.scan([file]), content[:7])


    @unittest.skipUnless(shutil.which('git'), 'History fixture requires Git; ZIP tools do not.')
    def test_historical_secret_is_found_after_clean_commit(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            git(root, 'init', '-q')
            file = root / 'note.md'
            file.write_text('gh' + 'p_' + 'x' * 36)
            git(root, 'add', 'note.md')
            identity = ['-c', 'user.name=review-fixture', '-c', 'user.email=review' + '@' + 'example.invalid']
            git(root, *identity, 'commit', '-qm', 'synthetic sensitive fixture')
            file.write_text('Clean current version.\n')
            git(root, 'add', 'note.md')
            git(root, *identity, 'commit', '-qm', 'clean fixture')
            with patch.object(audit, 'ROOT', root):
                with contextlib.redirect_stdout(io.StringIO()) as output:
                    self.assertTrue(audit.main(['--history']))
            self.assertNotIn('x' * 36, output.getvalue())

    def test_binary_disguised_as_text_is_a_finding(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            file = root / 'note.md'
            file.write_bytes(bytes([255, 254, 0, 1]))
            with patch.object(audit, 'ROOT', root):
                self.assertTrue(audit.scan([file]))

    def test_device_addresses_detected_but_documentation_examples_allowed(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            file = root / 'note.md'
            with patch.object(audit, 'ROOT', root):
                for content in ['172' + '.20.4.9', 'fd12' + ':3456::1']:
                    file.write_text(content)
                    self.assertTrue(audit.scan([file]))
                file.write_text('203.0.113.10 and [2001:db8::1] are documentation examples.')
                self.assertEqual(audit.scan([file]), [])


if __name__ == '__main__':
    unittest.main()
