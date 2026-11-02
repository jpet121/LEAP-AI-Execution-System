import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from verify_repo import check

class TestRepositoryIntegrity(unittest.TestCase):
    def test_frozen_compiler_runner_sources_and_evidence(self):
        data = check()
        self.assertEqual(data['status'], 'PASS', data['problems'])
        self.assertGreater(data['frozen_source_sha256_count'], 30)
        self.assertEqual(data['accepted_case_integrity'], 'PASS')
    def test_historical_examples(self):
        self.assertEqual(len(check()['historical_examples']), 2)
    def test_public_stated_limitations(self):
        text=(ROOT/'README.md').read_text()
        self.assertIn('not been promoted',text)
        self.assertIn('Case 4',text)
        self.assertIn('not currently stored',text)

if __name__ == '__main__': unittest.main()
