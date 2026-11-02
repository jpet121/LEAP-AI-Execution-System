"""Post-gate assurance: separate integer model, real DB and HTTP observations."""
import ast
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
import json
import os
from pathlib import Path
import random
import secrets
from threading import Barrier
import time
import unittest
import uuid
import psycopg
from fastapi.testclient import TestClient
from hypothesis import given, settings, strategies as st
from app.api import create_app
from app.config import Settings
from app.models import AccountInput, TransactionInput
from app.money import money
from app.repository import PostgresRepository

DSN=os.environ.get('TEST_PG_DSN','postgresql://postgres@127.0.0.1:55432/ledger')
def ident(): return 'A'+uuid.uuid4().hex[:14].upper()
def usd(cents): return f'{cents//100}.{cents%100:02d}'

class Assurance(unittest.TestCase):
    def setUp(self):
        self.key=secrets.token_urlsafe(24)
        self.repo=PostgresRepository(DSN)
        self.client=TestClient(create_app(Settings(self.key,DSN)))
        self.client.headers['X-API-Key']=self.key
    def tearDown(self): self.client.close()
    def observed(self,account):
        response=self.client.get('/v1/accounts/'+account)
        self.assertEqual(response.status_code,200)
        with psycopg.connect(DSN) as c:
            balance=c.execute('SELECT balance FROM accounts WHERE account_id=%s',(account,)).fetchone()[0]
            count=c.execute('SELECT count(*) FROM ledger_transactions WHERE account_id=%s',(account,)).fetchone()[0]
        self.assertEqual(response.json()['balance'],format(balance,'.2f'))
        return response.json()['balance'],count

    @settings(max_examples=150,deadline=None,derandomize=True)
    @given(st.integers(0,99999999999))
    def test_hypothesis_exact_money(self,cents):
        value=usd(cents)
        self.assertEqual(AccountInput(account_id='A1',opening_balance=value).opening_balance,value)
        self.assertEqual(Decimal(money(value))*100,cents)
        if cents:
            self.assertEqual(TransactionInput(transaction_id='T1',kind='DEBIT',amount=value).amount,value)

    def test_stateful_differential_http_db(self):
        # Integer cents reference does not call app arithmetic or decision logic.
        rng=random.Random(40012)
        account=ident()
        self.assertEqual(self.client.post('/v1/accounts',json={'account_id':account,'opening_balance':'100.00'}).status_code,201)
        current=10000; prior={}
        for index in range(250):
            tx='T'+str(rng.randrange(30))
            kind=rng.choice(['CREDIT','DEBIT'])
            amount=rng.randrange(1,3001)
            if prior and index%4==0:
                tx=rng.choice(list(prior));kind,amount,_=prior[tx]
            body={'transaction_id':tx,'kind':kind,'amount':usd(amount)}
            before=current
            candidate=current+(amount if kind=='CREDIT' else -amount)
            if tx in prior:
                expected=200 if prior[tx][:2]==(kind,amount) else 409
                result=prior[tx][2]
            elif candidate<0:
                expected=422;result=current
            else:
                expected=201;current=candidate;result=current
                prior[tx]=(kind,amount,current)
            response=self.client.post('/v1/accounts/'+account+'/transactions',json=body)
            self.assertEqual(response.status_code,expected,(index,body,response.text))
            if expected in (200,201): self.assertEqual(response.json()['balance'],usd(result))
            balance,count=self.observed(account)
            self.assertEqual((balance,count),(usd(current),len(prior)))
            if expected!=201: self.assertEqual(current,before)

    def test_concurrent_100_same_and_independent_keys(self):
        started=time.monotonic()
        for index in range(200):
            account=ident();self.repo.create(account,'0.00')
            barrier=Barrier(2)
            def submit(n):
                barrier.wait(timeout=10)
                tx='T1' if index%2==0 else 'T'+str(n+1)
                return self.repo.transact(account,tx,'CREDIT','1.00')[0]
            with ThreadPoolExecutor(max_workers=2) as pool:
                result=list(pool.map(submit,range(2)))
            expected=1 if index%2==0 else 2
            self.assertEqual(sorted(result),[200,201] if expected==1 else [201,201])
            self.assertEqual(self.observed(account),(usd(expected*100),expected))
        Path('evidence/races.json').write_text(json.dumps({'repetitions':200,'identical_key_races':100,'independent_key_races':100,'seconds':time.monotonic()-started}))

    def test_adversarial_auth_and_validation(self):
        account=ident();self.repo.create(account,'1.00')
        route='/v1/accounts/'+account+'/transactions'
        for value in ('1e2','-1.00','NaN','Infinity',True,1.0,1,None,[],{},'1.000','1.00\n','١.00','9'*20000+'.00'):
            r=self.client.post(route,json={'transaction_id':'T1','kind':'CREDIT','amount':value})
            self.assertEqual(r.status_code,422,str(value)[:50])
            self.assertEqual(r.json(),{'error':{'code':'INVALID_REQUEST'}})
        for tx in ('a1','A','A'*17,'A1\n',"X1';DROP TABLE accounts;--",'Á1'):
            self.assertEqual(self.client.post(route,json={'transaction_id':tx,'kind':'CREDIT','amount':'1.00'}).status_code,422)
        for body in ('{','null','[]','{"transaction_id":"T1","kind":"OTHER","amount":"1.00"}', '{"transaction_id":"T1","kind":"CREDIT","amount":"1.00","extra":true}'):
            self.assertEqual(self.client.post(route,content=body).status_code,422)
        for key in ('','incorrect'):
            r=self.client.post(route,json={'transaction_id':'T1','kind':'CREDIT','amount':'1.00'},headers={'X-API-Key':key})
            self.assertEqual(r.status_code,401)
            self.assertNotIn(self.key,r.text)
        self.assertEqual(self.observed(account),('1.00',0))
        self.assertEqual(self.client.post('/v1/accounts',json={'account_id':account,'opening_balance':'2.00'}).status_code,409)
        self.assertEqual(self.observed(account),('1.00',0))

    def test_boundary_metamorphic_overflow(self):
        account=ident();self.repo.create(account,'999999999.99')
        route='/v1/accounts/'+account+'/transactions'
        self.assertEqual(self.client.post(route,json={'transaction_id':'T1','kind':'CREDIT','amount':'0.01'}).status_code,422)
        self.assertEqual(self.observed(account),('999999999.99',0))
        body={'transaction_id':'T1','kind':'DEBIT','amount':'999999999.99'}
        self.assertEqual(self.client.post(route,json=body).json()['balance'],'0.00')
        self.assertEqual(self.client.post(route,json=body).status_code,200)
        body['amount']='0999999999.99'
        self.assertEqual(self.client.post(route,json=body).status_code,200)
        self.assertEqual(self.observed(account),('0.00',1))

    def test_source_security_ast(self):
        for p in Path('app').glob('*.py'):
            tree=ast.parse(p.read_text())
            for n in ast.walk(tree):
                if isinstance(n,ast.Call) and isinstance(n.func,ast.Name):
                    self.assertNotIn(n.func.id,('float','eval','exec','print'))
                if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='execute':
                    # Every data-query literal is fixed SQL; user data travels in parameters.
                    if p.name=='db.py':
                        self.assertEqual(ast.unparse(n.args[0]),'migration.read_text()')
                    else:
                        self.assertIsInstance(n.args[0],ast.Constant)

    def test_bounded_parallel_load_and_connection_cleanup(self):
        def operation(_):
            account=ident()
            self.repo.create(account,'0.00')
            return self.repo.transact(account,'T1','CREDIT','1.00')[0]
        with ThreadPoolExecutor(max_workers=8) as pool:
            results=list(pool.map(operation,range(100)))
        self.assertEqual(results,[201]*100)
        with psycopg.connect(DSN) as c:
            active=c.execute("SELECT count(*) FROM pg_stat_activity WHERE datname=current_database() AND pid<>pg_backend_pid()").fetchone()[0]
        self.assertLess(active,10)
