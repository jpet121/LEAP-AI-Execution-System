"""Exercise actual Compose migration and service with ephemeral local secrets."""
import json
import os
from pathlib import Path
import secrets
import subprocess
import tempfile
import time
import urllib.request
import urllib.error

env=dict(os.environ,POSTGRES_PASSWORD=secrets.token_hex(24),LEDGER_API_KEY=secrets.token_urlsafe(32))
with tempfile.TemporaryDirectory() as d:
    override=Path(d)/'images.yaml'
    override.write_text('services:\n  app:\n    image: case4-ledger:validation\n  migrate:\n    image: case4-ledger:validation\n')
    cmd=['docker','--host=unix:///var/run/docker.sock','compose','-p','case4-validation','-f','compose.yaml','-f',str(override)]
    try:
        subprocess.run(cmd+['up','-d','--no-build'],env=env,check=True)
        for _ in range(100):
            try:
                r=urllib.request.Request('http://127.0.0.1:8000/v1/accounts',headers={'X-API-Key':env['LEDGER_API_KEY'],'Content-Type':'application/json'},data=json.dumps({'account_id':'A100','opening_balance':'100.00'}).encode())
                with urllib.request.urlopen(r,timeout=2) as response:
                    assert response.status==201
                    assert json.load(response)=={'account_id':'A100','currency':'USD','balance':'100.00'}
                break
            except OSError: time.sleep(.2)
        else: raise RuntimeError('Container readiness failed')
        print('PASS: Compose healthy PostgreSQL -> migration -> non-root app -> authenticated functional request')
    finally:
        subprocess.run(cmd+['logs','--no-color'],env=env,check=False)
        subprocess.run(cmd+['down','-v'],env=env,check=True)
