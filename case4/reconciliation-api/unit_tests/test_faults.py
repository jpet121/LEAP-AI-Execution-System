import secrets
import unittest
import psycopg
from fastapi.testclient import TestClient
from app.api import create_app
from app.config import Settings
from app.repository import PostgresRepository
from test_database import DSN

class DatabaseFault:
    def __init__(self, point): self.point=point
    def __call__(self,c,point):
        if point==self.point:
            if point=='before_commit':
                # This succeeds now and fails only on actual PostgreSQL COMMIT.
                c.execute('CREATE TEMP TABLE parent_fault (id int PRIMARY KEY)')
                c.execute('CREATE TEMP TABLE child_fault (id int REFERENCES parent_fault(id) DEFERRABLE INITIALLY DEFERRED)')
                c.execute('INSERT INTO child_fault VALUES (1)')
            else:
                c.execute('SELECT 1/0')

class FaultTests(unittest.TestCase):
    def test_rollback_at_three_points(self):
        for point in ('after_update','after_insert','before_commit'):
            with psycopg.connect(DSN) as c:
                c.execute("DELETE FROM ledger_transactions WHERE account_id='F1'")
                c.execute("DELETE FROM accounts WHERE account_id='F1'")
            normal=PostgresRepository(DSN)
            normal.create('F1','5.00')
            key=secrets.token_urlsafe(24)
            app=create_app(Settings(key,DSN),PostgresRepository(DSN,DatabaseFault(point)))
            with TestClient(app) as c:
                r=c.post('/v1/accounts/F1/transactions',headers={'X-API-Key':key},json={'transaction_id':'T1','kind':'CREDIT','amount':'1.00'})
                self.assertEqual(r.status_code,503,point)
                self.assertEqual(r.json(),{'error':{'code':'DATABASE_UNAVAILABLE'}})
            self.assertEqual(normal.get('F1')['balance'],'5.00')
            with psycopg.connect(DSN) as c:
                self.assertEqual(c.execute("SELECT count(*) FROM ledger_transactions WHERE account_id='F1'").fetchone()[0],0)
            self.assertEqual(normal.transact('F1','T1','CREDIT','1.00')[0],201)
