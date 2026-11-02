"""Owner-derived immutable acceptance assertions; run ONLY against a fresh disposable PostgreSQL deployment.
Environment must supply TEST_BASE_URL, TEST_API_KEY and TEST_PG_DSN. No app exists at handoff time.
The test uses independent HTTP observations and direct read-only PostgreSQL counts.
"""
import json
import os
import unittest
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier


class ReconciliationBlackBox(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base = os.environ['TEST_BASE_URL'].rstrip('/')
        cls.key = os.environ['TEST_API_KEY']
        cls.dsn = os.environ['TEST_PG_DSN']
        import psycopg
        cls.psycopg = psycopg

    def request(self, method, path, body=None, key=None):
        data = None if body is None else json.dumps(body).encode('utf-8')
        headers = {'Content-Type': 'application/json'}
        if key is not None:
            headers['X-API-Key'] = key
        req = urllib.request.Request(self.base + path, data=data,
                                     headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                return resp.status, json.load(resp)
        except urllib.error.HTTPError as exc:
            return exc.code, json.load(exc) if exc.readable() else {}

    def rows(self, account):
        with self.psycopg.connect(self.dsn) as cn:
            with cn.cursor() as cur:
                cur.execute('SELECT COUNT(*) FROM ledger_transactions WHERE account_id = %s', (account,))
                return cur.fetchone()[0]

    def test_00_disposable_database_is_empty(self):
        with self.psycopg.connect(self.dsn) as cn:
            with cn.cursor() as cur:
                cur.execute('SELECT COUNT(*) FROM accounts')
                self.assertEqual(cur.fetchone()[0], 0, 'A1-A8 require fresh PostgreSQL')
                cur.execute('SELECT COUNT(*) FROM ledger_transactions')
                self.assertEqual(cur.fetchone()[0], 0, 'A1-A8 require fresh PostgreSQL')

    def test_01_a1_through_a8_frozen_sequence(self):
        key = self.key
        s, o = self.request('POST', '/v1/accounts',
                            {'account_id':'A100','opening_balance':'100.00'}, key)
        self.assertEqual(s, 201); self.assertEqual(o['balance'], '100.00')
        self.assertEqual(o['currency'], 'USD'); self.assertEqual(o['account_id'], 'A100')
        credit = {'transaction_id':'T100','kind':'CREDIT','amount':'20.00'}
        s,o = self.request('POST','/v1/accounts/A100/transactions',credit,key)
        self.assertEqual(s,201); self.assertEqual(o['balance'],'120.00')
        self.assertEqual(self.rows('A100'),1)
        s,o = self.request('POST','/v1/accounts/A100/transactions',credit,key)
        self.assertEqual(s,200); self.assertEqual(o['balance'],'120.00')
        self.assertEqual(self.rows('A100'),1)
        s,o = self.request('POST','/v1/accounts/A100/transactions',
                            {'transaction_id':'T100','kind':'CREDIT','amount':'21.00'},key)
        self.assertEqual(s,409); self.assertEqual(self.rows('A100'),1)
        s,o = self.request('POST','/v1/accounts/A100/transactions',
                            {'transaction_id':'T101','kind':'DEBIT','amount':'50.00'},key)
        self.assertEqual(s,201); self.assertEqual(o['balance'],'70.00')
        self.assertEqual(self.rows('A100'),2)
        s,o = self.request('POST','/v1/accounts/A100/transactions',
                            {'transaction_id':'T102','kind':'DEBIT','amount':'80.00'},key)
        self.assertEqual(s,422); self.assertEqual(self.rows('A100'),2)
        s,o = self.request('GET','/v1/accounts/A100',key=key)
        self.assertEqual(s,200); self.assertEqual(o['balance'],'70.00')
        self.assertEqual(o['currency'],'USD')
        self.assertEqual(self.request('GET','/v1/accounts/A100')[0],401)
        self.assertEqual(self.request('GET','/v1/accounts/A100',key='wrong')[0],401)
        self.assertEqual(self.rows('A100'),2)
        # Replay an older transaction after a later DEBIT; returned balance MUST be original.
        s,o=self.request('POST','/v1/accounts/A100/transactions',credit,key)
        self.assertEqual(s,200); self.assertEqual(o['balance'],'120.00')
        s,o=self.request('GET','/v1/accounts/A100',key=key)
        self.assertEqual(s,200); self.assertEqual(o['balance'],'70.00')
        self.assertEqual(self.rows('A100'),2)
        # A8 must also prevent business writes, not just GET disclosure.
        payload={'account_id':'Z900','opening_balance':'1.00'}
        self.assertEqual(self.request('POST','/v1/accounts',payload)[0],401)
        self.assertEqual(self.request('POST','/v1/accounts',payload,key='wrong')[0],401)
        self.assertEqual(self.request('GET','/v1/accounts/Z900',key=key)[0],404)

    def test_02_identical_concurrent_submission_at_most_one_commit(self):
        key = self.key
        s,o = self.request('POST','/v1/accounts',
                            {'account_id':'C200','opening_balance':'0.00'},key)
        self.assertEqual(s,201)
        barrier = Barrier(2)
        payload = {'transaction_id':'T200','kind':'CREDIT','amount':'1.00'}
        def submit(_):
            barrier.wait(timeout=10)
            return self.request('POST','/v1/accounts/C200/transactions',payload,key)[0]
        with ThreadPoolExecutor(max_workers=2) as pool:
            statuses=list(pool.map(submit,range(2)))
        self.assertLessEqual(statuses.count(201),1, statuses)
        self.assertEqual(self.rows('C200'),1)
        s,o=self.request('GET','/v1/accounts/C200',key=key)
        self.assertEqual(s,200); self.assertEqual(o['balance'],'1.00')

    def test_03_negative_cases_and_zero_balance(self):
        key = self.key
        self.assertEqual(self.request('GET','/v1/accounts/Q999',key=key)[0],404)
        self.assertEqual(self.request('POST','/v1/accounts/Q999/transactions',
                                     {'transaction_id':'T900','kind':'CREDIT','amount':'1.00'},key)[0],404)
        self.assertEqual(self.request('POST','/v1/accounts',
                                     {'account_id':'B200','opening_balance':'5.00'},key)[0],201)
        self.assertEqual(self.request('POST','/v1/accounts/B200/transactions',
                                     {'transaction_id':'T200','kind':'DEBIT','amount':'5.00'},key)[0],201)
        s,o=self.request('GET','/v1/accounts/B200',key=key)
        self.assertEqual(s,200); self.assertEqual(o['balance'],'0.00')
        for amount in ('1e2','-1.00','0.00','1000000000.00','NaN','Infinity',1.0,True):
            s,o=self.request('POST','/v1/accounts/B200/transactions',
                             {'transaction_id':'X901','kind':'CREDIT','amount':amount},key)
            self.assertGreaterEqual(s,400,amount)
        s,o=self.request('GET','/v1/accounts/B200',key=key)
        self.assertEqual(o['balance'],'0.00')
        self.assertEqual(self.rows('B200'),1)


if __name__ == '__main__':
    unittest.main()
