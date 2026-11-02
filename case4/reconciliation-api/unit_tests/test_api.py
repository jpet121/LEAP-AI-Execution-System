import unittest
import secrets
import psycopg
from fastapi.testclient import TestClient
from app.config import Settings
from app.main import create_app
from test_database import DSN

class ApiTests(unittest.TestCase):
    def test_api(self):
        with psycopg.connect(DSN) as c:
            c.execute("DELETE FROM ledger_transactions WHERE account_id='W1'")
            c.execute("DELETE FROM accounts WHERE account_id='W1'")
        key=secrets.token_urlsafe(24)
        with TestClient(create_app(Settings(key,DSN))) as c:
            for headers in ({},{'X-API-Key':'wrong'}, [('X-API-Key',key),('X-API-Key',key)]):
                self.assertEqual(c.post('/v1/accounts',json={'account_id':'W1','opening_balance':'1.00'},headers=headers).status_code,401)
            c.headers['X-API-Key']=key
            self.assertEqual(c.get('/v1/accounts/W1').status_code,404)
            self.assertEqual(c.post('/v1/accounts',json={'account_id':'W1','opening_balance':'1.00'}).status_code,201)
            self.assertEqual(c.get('/v1/accounts/W1').json()['balance'],'1.00')
            self.assertEqual(c.post('/v1/accounts/W1/transactions',json={'transaction_id':'T1','kind':'DEBIT','amount':'1.00'}).status_code,201)
            for path in ('/v1/accounts/bad','/v1/accounts/A'):
                self.assertEqual(c.get(path).status_code,422)
            for body in ('{','[]','{"account_id":"X1","opening_balance":1.0}'):
                self.assertEqual(c.post('/v1/accounts',content=body,headers={'Content-Type':'application/json'}).status_code,422)
            self.assertEqual(c.get('/docs').status_code,404)
        with self.assertRaises(ValueError): create_app()
