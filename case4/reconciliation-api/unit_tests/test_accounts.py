import unittest
import psycopg
from app.models import AccountInput
from app.repository import PostgresRepository
from app.ledger import create_account, get_account
from app.errors import LedgerError
from test_database import DSN

class AccountTests(unittest.TestCase):
    def setUp(self):
        with psycopg.connect(DSN) as c:
            c.execute("DELETE FROM ledger_transactions WHERE account_id='U1'")
            c.execute("DELETE FROM accounts WHERE account_id='U1'")
        self.repo=PostgresRepository(DSN)
    def test_accounts(self):
        with self.assertRaises(LedgerError) as e: get_account(self.repo,'U1')
        self.assertEqual(e.exception.status,404)
        self.assertEqual(create_account(self.repo,AccountInput(account_id='U1',opening_balance='1.00'))['balance'],'1.00')
        with self.assertRaises(LedgerError) as e: self.repo.create('U1','2.00')
        self.assertEqual(e.exception.status,409)
        self.assertEqual(get_account(self.repo,'U1')['balance'],'1.00')
    def test_unavailable(self):
        r=PostgresRepository('postgresql://postgres@127.0.0.1:1/absent')
        for method,args in [(r.get,('U1',)),(r.create,('U1','1.00'))]:
            with self.assertRaises(LedgerError) as e: method(*args)
            self.assertEqual((e.exception.status,e.exception.code),(503,'DATABASE_UNAVAILABLE'))
