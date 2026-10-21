import json
from pathlib import Path
import re
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
ANDROID = '{http://schemas.android.com/apk/res/android}'


class PublicContractTests(unittest.TestCase):
    def test_settings_apk_has_no_privileged_or_background_components(self):
        doc = ET.parse(ROOT / 'android/settings-hub/AndroidManifest.xml')
        self.assertEqual(doc.findall('uses-permission'), [])
        for tag in ['receiver', 'service', 'provider']:
            self.assertEqual(doc.findall('application/' + tag), [])
        self.assertEqual(len(doc.findall('application/activity')), 1)

    def test_policy_is_test_only_and_manifest_source_profile_allowlists_match(self):
        doc = ET.parse(ROOT / 'android/google-policy/AndroidManifest.xml')
        self.assertEqual(doc.find('application').get(ANDROID + 'testOnly'), 'true')
        self.assertEqual(doc.findall('uses-permission'), [])
        self.assertEqual(doc.findall('application/service'), [])
        profile = json.loads((ROOT / 'profiles/c3apro-api34.json').read_text())
        expected = set(profile['google_core'] + profile['google_native'])
        manifest = {p.get(ANDROID + 'name') for p in doc.findall('queries/package')}
        source = next((ROOT / 'android/google-policy/src').rglob('MainActivity.java')).read_text()
        self.assertEqual(set(re.findall(r'"(com\.[A-Za-z0-9_.]+)"', source)), expected)
        self.assertEqual(manifest, expected)

    def test_local_markdown_links_exist(self):
        for file in ROOT.rglob('*.md'):
            if any(p in {'state', 'build', 'dist', '.git'} for p in file.relative_to(ROOT).parts):
                continue
            for target in re.findall(r'\]\(([^)]+)\)', file.read_text()):
                if '://' in target or target.startswith('#'):
                    continue
                self.assertTrue((file.parent / target.split('#')[0]).exists(), (file, target))


if __name__ == '__main__':
    unittest.main()
