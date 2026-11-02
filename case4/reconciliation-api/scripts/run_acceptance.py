"""Create/drop an isolated database; run frozen HTTP acceptance, then local gates.
TEST_PG_DSN must identify a disposable PostgreSQL admin service with CREATEDB.
Never pass production credentials. No shared data is truncated.
"""
import os
from pathlib import Path
import secrets
import subprocess
import sys
import time
import uuid
import urllib.request
import urllib.error
import psycopg
from psycopg import sql
from psycopg.conninfo import conninfo_to_dict, make_conninfo

ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT))
from app.db import migrate


def run():
    admin=os.environ['TEST_PG_DSN']
    name='case4_'+uuid.uuid4().hex
    config=conninfo_to_dict(admin)
    config['dbname']=name
    dsn=make_conninfo(**config)
    with psycopg.connect(admin,autocommit=True) as c:
        c.execute(sql.SQL('CREATE DATABASE {}').format(sql.Identifier(name)))
    server=None
    try:
        migrate(dsn)
        key=secrets.token_urlsafe(32)
        port=os.environ.get('TEST_PORT','58000')
        base='http://127.0.0.1:'+port
        env=dict(os.environ,DATABASE_URL=dsn,LEDGER_API_KEY=key,TEST_API_KEY=key,TEST_BASE_URL=base,TEST_PG_DSN=dsn)
        with open(ROOT/'evidence/server.log','w') as log:
            server=subprocess.Popen([sys.executable,'-m','uvicorn','app.main:create_app','--factory','--host','127.0.0.1','--port',port,'--no-access-log'],cwd=ROOT,env=env,stdout=log,stderr=log)
            for _ in range(100):
                if server.poll() is not None: raise RuntimeError('Server exited; inspect evidence/server.log')
                try:
                    req=urllib.request.Request(base+'/v1/accounts/Q999',headers={'X-API-Key':key})
                    urllib.request.urlopen(req,timeout=1)
                except urllib.error.HTTPError as exc:
                    if exc.code==404: break
                except OSError: pass
                time.sleep(.1)
            else: raise RuntimeError('Readiness timeout')
            subprocess.run([sys.executable,'-m','unittest','discover','-s','tests','-p','test_reconciliation_contract.py','-v'],cwd=ROOT,env=env,check=True)
        # Independent database for unit/API tests: they do not share acceptance state.
    finally:
        if server is not None:
            server.terminate()
            server.wait(timeout=15)
        with psycopg.connect(admin,autocommit=True) as c:
            c.execute(sql.SQL('DROP DATABASE {} WITH (FORCE)').format(sql.Identifier(name)))

if __name__=='__main__':
    run()
