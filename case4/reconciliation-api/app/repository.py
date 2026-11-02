"""PostgreSQL adapter; success returns only after transaction commit."""
import psycopg
from .errors import LedgerError

def no_fault(connection, point: str) -> None:
    return None

class PostgresRepository:
    def __init__(self, dsn: str, fault=no_fault):
        self.dsn = dsn
        self.fault = fault

    def create(self, account_id: str, opening: str) -> dict:
        try:
            with psycopg.connect(self.dsn, connect_timeout=5) as c:
                c.execute('INSERT INTO accounts(account_id,balance) VALUES (%s,%s)',(account_id,opening))
        except psycopg.errors.UniqueViolation:
            raise LedgerError(409,'ACCOUNT_EXISTS') from None
        except psycopg.Error:
            raise LedgerError(503,'DATABASE_UNAVAILABLE') from None
        return dict(account_id=account_id, currency='USD', balance=opening)

    def get(self, account_id: str) -> dict:
        try:
            with psycopg.connect(self.dsn, connect_timeout=5) as c:
                row=c.execute('SELECT balance FROM accounts WHERE account_id=%s',(account_id,)).fetchone()
        except psycopg.Error:
            raise LedgerError(503,'DATABASE_UNAVAILABLE') from None
        if row is None:
            raise LedgerError(404,'ACCOUNT_NOT_FOUND')
        return dict(account_id=account_id,currency='USD',balance=format(row[0],'.2f'))

    def transact(self, account_id: str, transaction_id: str, kind: str, amount: str) -> tuple[int, dict]:
        from decimal import Decimal
        from .money import changed
        try:
            with psycopg.connect(self.dsn, connect_timeout=5) as c:
                c.execute("SET LOCAL lock_timeout = '5s'")
                c.execute("SET LOCAL statement_timeout = '10s'")
                account=c.execute('SELECT balance FROM accounts WHERE account_id=%s FOR UPDATE',(account_id,)).fetchone()
                if account is None:
                    raise LedgerError(404,'ACCOUNT_NOT_FOUND')
                prior=c.execute('SELECT kind,amount,resulting_balance FROM ledger_transactions WHERE account_id=%s AND transaction_id=%s',(account_id,transaction_id)).fetchone()
                if prior is not None:
                    if prior[0] != kind or prior[1] != Decimal(amount):
                        raise LedgerError(409,'TRANSACTION_CONFLICT')
                    balance=format(prior[2],'.2f')
                    status=200
                else:
                    try:
                        balance=changed(format(account[0],'.2f'),amount,kind)
                    except ValueError:
                        raise LedgerError(422,'BALANCE_OUT_OF_RANGE') from None
                    c.execute('UPDATE accounts SET balance=%s WHERE account_id=%s',(balance,account_id))
                    self.fault(c,'after_update')
                    c.execute('INSERT INTO ledger_transactions(account_id,transaction_id,kind,amount,resulting_balance) VALUES (%s,%s,%s,%s,%s)',(account_id,transaction_id,kind,amount,balance))
                    self.fault(c,'after_insert')
                    self.fault(c,'before_commit')
                    status=201
        except psycopg.Error:
            raise LedgerError(503,'DATABASE_UNAVAILABLE') from None
        return status,dict(account_id=account_id,transaction_id=transaction_id,kind=kind,amount=amount,balance=balance)
