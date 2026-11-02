"""Fail-closed settings; never include secret values in errors or repr."""
import os
from dataclasses import dataclass, field
from collections.abc import Mapping

@dataclass(frozen=True)
class Settings:
    api_key: str = field(repr=False)
    dsn: str = field(repr=False)

    @classmethod
    def load(cls, environ: Mapping[str, str] = os.environ):
        key = environ.get('LEDGER_API_KEY', '')
        dsn = environ.get('DATABASE_URL', '')
        if not key or not dsn:
            raise ValueError('LEDGER_API_KEY and DATABASE_URL are required')
        return cls(key, dsn)
