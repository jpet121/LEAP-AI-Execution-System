import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from verify_repo import check
from reassemble_runtime import reconstruct, digest

class TestRepositoryPackaging(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result=check()
    def test_manifest_files_and_source_mirrors(self):
        self.assertEqual(self.result['status'],'PASS',self.result['problems'])
        self.assertGreater(self.result['source_mirror_members'],30)
    def test_two_contracts(self):
        self.assertEqual(len(self.result['cases']),2)
        self.assertTrue(all(x['xml_tags']>=13 for x in self.result['cases']))
    def test_runtime_roundtrip_hashes(self):
        import tempfile,json
        with tempfile.TemporaryDirectory() as d:
            for kind in ('compiler','runner'):
                target=reconstruct(kind,Path(d))
                manifest=json.loads((ROOT/'releases'/kind/'archive_manifest.json').read_text())
                self.assertEqual(digest(target),manifest['archive_sha256'])

    def test_two_chat_commands_and_public_landing_page(self):
        for relative in ('README.md','QUICK_START.md','GITHUB_REPOSITORY_METADATA.txt'):
            document=(ROOT/relative).read_text(encoding='utf-8')
            self.assertIn('COMPILE',document)
            self.assertIn('RUN',document)
            self.assertFalse(any(c in document for c in '\u2014\u2013'),relative)
        self.assertFalse((ROOT/'LICENSE').exists())
        self.assertFalse((ROOT/'LICENSE.txt').exists())

if __name__=='__main__':unittest.main()
