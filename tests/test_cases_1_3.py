import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT / "tools"))
from verify_cases_1_3 import verify

class TestCaseArchiveIntegrity(unittest.TestCase):
    def test_all_three_frozen_runs_have_exact_bytes(self):
        result = verify()
        self.assertEqual(result["status"], "PASS", result["errors"])
        self.assertEqual(result["case_count"], 3)
    def test_compiler_and_runner_sources_remain_visible(self):
        self.assertTrue((ROOT / "compiler/source/lib/pfcompiler/compiler.py").is_file())
        self.assertTrue((ROOT / "runner/source/lib/pfrunner/engine.py").is_file())
    def test_publication_is_not_production_release(self):
        status = (ROOT / "RELEASE_STATUS.json").read_text()
        self.assertIn("NOT GRANTED", status)
        self.assertIn("EXCLUDED", status)
    def test_prior_archive_parts_are_not_falsely_claimed(self):
        for kind in ("compiler", "runner"):
            archive = ROOT / "releases" / kind
            self.assertTrue((archive / "archive_manifest.json").is_file())
        text = (ROOT / "releases/README.md").read_text()
        self.assertIn("not uploaded", text)

if __name__ == "__main__":
    unittest.main()
