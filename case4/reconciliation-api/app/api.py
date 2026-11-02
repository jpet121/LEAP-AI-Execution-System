"""Authenticated API; errors contain codes, never request bodies or secrets."""
import secrets
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from .config import Settings
from .errors import LedgerError
from .ledger import create_account, get_account, post_transaction
from .models import AccountInput, TransactionInput
from .repository import PostgresRepository

def create_app(settings=None, repository=None):
    settings = settings or Settings.load()
    repository = repository or PostgresRepository(settings.dsn)
    app=FastAPI(docs_url=None,redoc_url=None,openapi_url=None)

    @app.middleware('http')
    async def authenticate(request: Request, call_next):
        supplied=request.headers.getlist('x-api-key')
        if len(supplied) != 1 or not secrets.compare_digest(supplied[0].encode(), settings.api_key.encode()):
            return JSONResponse({'error':{'code':'UNAUTHORIZED'}}, status_code=401)
        return await call_next(request)

    @app.exception_handler(LedgerError)
    async def domain_error(request, exc):
        return JSONResponse({'error':{'code':exc.code}},status_code=exc.status)

    @app.exception_handler(RequestValidationError)
    @app.exception_handler(ValidationError)
    async def validation_error(request, exc):
        return JSONResponse({'error':{'code':'INVALID_REQUEST'}},status_code=422)

    @app.post('/v1/accounts',status_code=201)
    def create(payload: AccountInput):
        return create_account(repository,payload)

    @app.get('/v1/accounts/{account_id}')
    def get(account_id: str):
        return get_account(repository,account_id)

    @app.post('/v1/accounts/{account_id}/transactions')
    def transact(account_id: str, payload: TransactionInput):
        status,result=post_transaction(repository,account_id,payload)
        return JSONResponse(result,status_code=status)
    return app
