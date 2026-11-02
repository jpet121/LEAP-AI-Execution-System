import os
import unittest
import psycopg
from app.db import migrate

DSN = os.environ.get('TEST_PG_DSN','postgresql://postgres@127.0.0.1:55432/ledger')
class DatabaseTests(unittest.TestCase):
    def test_migration_and_constraints(self):
        migrate(DSN)
        migrate(DSN)
        with psycopg.connect(DSN) as c:
            for account,balance in [('bad','1.00'),('D1','-1.00'),('D1','1000000000.00')]:
                with self.assertRaises(psycopg.Error):
                    with c.transaction(): c.execute('INSERT INTO accounts(account_id,balance) VALUES (%s,%s)',(account,balance))
            with c.transaction(force_rollback=True):
                c.execute("INSERT INTO accounts(account_id,balance) VALUES ('D1',0)")
                for kind,amount in [('BAD','1.00'),('CREDIT','0.00'),('CREDIT','-1.00')]:
                    with self.assertRaises(psycopg.Error):
                        with c.transaction():
                            c.execute("INSERT INTO ledger_transactions VALUES ('D1','T1',%s,%s,0)",(kind,amount))
