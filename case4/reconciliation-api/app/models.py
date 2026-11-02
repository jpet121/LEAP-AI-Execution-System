"""Strict HTTP boundary; unknown fields and coercion are forbidden."""
from typing import Annotated, Literal
from pydantic import BaseModel, ConfigDict, StringConstraints, field_validator
from .money import money

Identifier = Annotated[str, StringConstraints(strict=True, pattern=r'^[A-Z][A-Z0-9]{1,15}$')]

class AccountInput(BaseModel):
    model_config = ConfigDict(strict=True, extra='forbid')
    account_id: Identifier
    opening_balance: str

    @field_validator('opening_balance')
    @classmethod
    def opening(cls, value: str) -> str:
        return money(value)

class TransactionInput(BaseModel):
    model_config = ConfigDict(strict=True, extra='forbid')
    transaction_id: Identifier
    kind: Literal['CREDIT', 'DEBIT']
    amount: str

    @field_validator('amount')
    @classmethod
    def positive(cls, value: str) -> str:
        return money(value, positive=True)
