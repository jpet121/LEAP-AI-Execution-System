import unittest
from decimal import localcontext
from pydantic import ValidationError
from app.models import AccountInput, TransactionInput
from app.money import money, changed
from app.errors import LedgerError

class ValidationTests(unittest.TestCase):
    def test_money(self):
        for value in ('1e2','-1.00','NaN','Infinity',True,1.0,100,'1.0','1.00\n','١.00','1000000000.00'):
            with self.assertRaises(ValueError): money(value)
        self.assertEqual(money('0001.00'),'1.00')
        self.assertEqual(money('0.00'),'0.00')
        self.assertEqual(money('999999999.99'),'999999999.99')
        with self.assertRaises(ValueError): money('0.00',positive=True)
        self.assertEqual(changed('5.00','5.00','DEBIT'),'0.00')
        self.assertEqual(changed('5.00','5.00','CREDIT'),'10.00')
        for b,a,k in [('0.00','0.01','DEBIT'),('999999999.99','0.01','CREDIT')]:
            with self.assertRaises(ValueError): changed(b,a,k)
        with localcontext() as c:
            c.prec=2
            self.assertEqual(changed('100.00','0.01','CREDIT'),'100.01')
    def test_models(self):
        self.assertEqual(AccountInput(account_id='A1',opening_balance='0.00').opening_balance,'0.00')
        self.assertEqual(TransactionInput(transaction_id='T1',kind='CREDIT',amount='1.00').amount,'1.00')
        for i in ('a1','A','A'*17,'A_','A1\n',True):
            with self.assertRaises(ValidationError): AccountInput(account_id=i,opening_balance='0.00')
        for payload in ({'account_id':'A1','opening_balance':True},{'account_id':'A1','opening_balance':'0.00','extra':1}):
            with self.assertRaises(ValidationError): AccountInput(**payload)
        with self.assertRaises(ValidationError): TransactionInput(transaction_id='T1',kind='OTHER',amount='1.00')
        self.assertEqual(AccountInput(account_id='A123456789012345',opening_balance='999999999.99').account_id,'A123456789012345')
        for value in ('-0.01','1000000000.00','0.001'):
            with self.assertRaises(ValidationError): AccountInput(account_id='A1',opening_balance=value)
        e=LedgerError(409,'conflict')
        self.assertEqual((e.status,str(e)),(409,'conflict'))
