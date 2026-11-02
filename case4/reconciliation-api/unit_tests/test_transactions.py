import unittest
import psycopg
from app.repository import PostgresRepository
from app.models import TransactionInput
from app.ledger import post_transaction
from app.errors import LedgerError
from test_database import DSN

class TransactionTests(unittest.TestCase):
    def setUp(self):
        with psycopg.connect(DSN) as c:
            c.execute("DELETE FROM ledger_transactions WHERE account_id='V1'")
            c.execute("DELETE FROM accounts WHERE account_id='V1'")
        self.r=PostgresRepository(DSN)
        self.r.create('V1','100.00')
    def test_sequence(self):
        p=TransactionInput(transaction_id='T1',kind='CREDIT',amount='20.00')
        self.assertEqual(post_transaction(self.r,'V1',p),(201,dict(account_id='V1',transaction_id='T1',kind='CREDIT',amount='20.00',balance='120.00')))
        self.assertEqual(self.r.transact('V1','T2','DEBIT','50.00')[1]['balance'],'70.00')
        self.assertEqual(post_transaction(self.r,'V1',p)[0],200)
        self.assertEqual(post_transaction(self.r,'V1',p)[1]['balance'],'120.00')
        for args,code in [(('V1','T1','CREDIT','21.00'),409),(('V1','T1','DEBIT','20.00'),409),(('V1','T3','DEBIT','70.01'),422),(('Q9','T1','CREDIT','1.00'),404)]:
            with self.assertRaises(LedgerError) as e: self.r.transact(*args)
            self.assertEqual(e.exception.status,code)
        self.assertEqual(self.r.get('V1')['balance'],'70.00')
        self.assertEqual(self.r.transact('V1','T3','DEBIT','70.00')[1]['balance'],'0.00')
        with psycopg.connect(DSN) as c:
            self.assertEqual(c.execute("SELECT count(*) FROM ledger_transactions WHERE account_id='V1'").fetchone()[0],3)
        with self.assertRaises(LedgerError) as e: PostgresRepository('postgresql://postgres@127.0.0.1:1/x').transact('V1','T1','CREDIT','1.00')
        self.assertEqual(e.exception.status,503)
