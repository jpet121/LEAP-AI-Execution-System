"""Validated domain boundary, independent of HTTP transport."""
from pydantic import TypeAdapter
from .models import AccountInput, Identifier

def create_account(repository, payload: AccountInput) -> dict:
    return repository.create(payload.account_id,payload.opening_balance)

def get_account(repository, account_id: str) -> dict:
    return repository.get(TypeAdapter(Identifier).validate_python(account_id))

def post_transaction(repository, account_id: str, payload) -> tuple[int, dict]:
    account_id=TypeAdapter(Identifier).validate_python(account_id)
    return repository.transact(account_id,payload.transaction_id,payload.kind,payload.amount)
