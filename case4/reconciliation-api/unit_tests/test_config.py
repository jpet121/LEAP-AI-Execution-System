import unittest
from app.config import Settings

class ConfigTests(unittest.TestCase):
    def test_settings(self):
        for env in ({}, {'LEDGER_API_KEY':'test-only'}, {'DATABASE_URL':'test-only'}):
            with self.assertRaises(ValueError): Settings.load(env)
        s=Settings.load({'LEDGER_API_KEY':'test-only','DATABASE_URL':'local-test'})
        self.assertEqual(s.api_key,'test-only')
        self.assertEqual(s.dsn,'local-test')
        self.assertNotIn('test-only',repr(s))
