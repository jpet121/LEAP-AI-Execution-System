import json,random,sys,re
from decimal import Decimal
from pathlib import Path
from pydantic import ValidationError,TypeAdapter
sys.path.insert(0, '/mnt/data/case4_review/implementation')
from app.money import money,changed,MAX
from app.models import AccountInput,TransactionInput,Identifier
rng=random.Random(431416)
count=0; errors=[]
def check(condition, message):
 global count
 count+=1
 if not condition: errors.append(message)
for amt in ['0.00','00.00','1.00','00001.23','999999999.99','999999999.98']:
 expected=format(Decimal(amt),'.2f')
 try: actual=money(amt)
 except Exception as e:actual='EXCEPTION:'+repr(e)
 check(actual==expected,f'valid money {amt}: {actual} != {expected}')
for value in ['-1.00','1.0','1.000','1e2','NaN','Infinity','+1.00',' 1.00','1.00 ','1000000000.00','1.', '.01','1,00','1.00\n','１２.００',1.0,True,0,None]:
 try:money(value);allowed=True
 except (ValueError,TypeError):allowed=False
 check(not allowed,f'invalid money accepted {value!r}')
for _ in range(5000):
 cents=rng.randint(0,99_999_999_999)
 source=f'{cents//100}.{cents%100:02d}'
 check(money(source)==f'{cents//100}.{cents%100:02d}',f'money mismatch {source}')
for _ in range(5000):
 initial=rng.randint(0,99_999_999_999); amount=rng.randint(1,99_999_999_999)
 kind=rng.choice(['CREDIT','DEBIT'])
 expected=initial+(amount if kind=='CREDIT' else -amount)
 b=f'{initial//100}.{initial%100:02d}';a=f'{amount//100}.{amount%100:02d}'
 try:result=changed(b,a,kind); valid=True
 except ValueError: valid=False;result=None
 check(valid==(0<=expected<=99_999_999_999),f'range mismatch {b} {a} {kind}')
 if valid:check(result==f'{expected//100}.{expected%100:02d}',f'arithmetic mismatch {b} {a} {kind}')
for data in [dict(account_id='A100',opening_balance='0.00'),dict(account_id='Z123456789012345',opening_balance='999999999.99')]:
 check(AccountInput.model_validate(data).account_id==data['account_id'],f'valid account rejected {data}')
for data in [dict(account_id='a123',opening_balance='1.00'),dict(account_id='AB',opening_balance=1.0),dict(account_id='A100',opening_balance='1e2'),dict(account_id='A100',opening_balance='1.00',unsafe=True),dict(account_id='Z1234567890123456',opening_balance='1.00')]:
 try:AccountInput.model_validate(data);allowed=True
 except ValidationError:allowed=False
 check(not allowed,f'invalid account accepted {data!r}')
for data in [dict(transaction_id='T100',kind='CREDIT',amount='1.00'),dict(transaction_id='T100',kind='DEBIT',amount='999999999.99')]:
 try:TransactionInput.model_validate(data);allowed=True
 except ValidationError:allowed=False
 check(allowed,f'valid transaction rejected {data!r}')
for data in [dict(transaction_id='T100',kind='CREDIT',amount='0.00'),dict(transaction_id='T100',kind='CREDIT',amount=1.0),dict(transaction_id='T100',kind='credit',amount='1.00'),dict(transaction_id='T100',kind='CREDIT',amount='-1.00'),dict(transaction_id='T100',kind='CREDIT',amount='1.00',extra=2)]:
 try:TransactionInput.model_validate(data);allowed=True
 except ValidationError:allowed=False
 check(not allowed,f'invalid transaction accepted {data!r}')
report={'independent_pure_logic_checks':count,'mismatches':len(errors),'errors':errors[:30], 'scope':'money parsing, fixed-point arithmetic, Pydantic schemas; no database/API runtime'}
Path('/mnt/data/case4_review/independent_pure_results.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
if errors: sys.exit(1)
