"""Evidence-producing verification runner; every failed mandatory command fails."""
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import time

root=Path(__file__).resolve().parent.parent
out=root/'evidence'
out.mkdir(exist_ok=True)
python=sys.executable
commands=[
 ('dependencies',[python,'-m','pip','check']),
 ('migrate',[python,'-c','import os; from app.db import migrate; migrate(os.environ["TEST_PG_DSN"])']),
 ('coverage',[python,'codex/tools/coverage_gate.py','--root','.','--source','app','--tests','unit_tests','--json-out','evidence/coverage_first.json']),
 ('acceptance',[python,'scripts/run_acceptance.py']),
 ('advanced',[python,'-m','unittest','discover','-s','advanced_tests','-v']),
 ('mutation',[python,'scripts/mutation.py']),
 ('typecheck',[python,'-m','mypy','app']),
 ('security_lint',[python,'-m','bandit','-r','app']),
 ('build',[python,'-m','build','--no-isolation']),
]
results=[]
for name,cmd in commands:
    started=time.time()
    with (out/(name+'.log')).open('w') as log:
        cp=subprocess.run(cmd,cwd=root,stdout=log,stderr=subprocess.STDOUT)
    results.append({'name':name,'command':cmd,'returncode':cp.returncode,'seconds':time.time()-started,'log':'evidence/'+name+'.log'})
    if cp.returncode: break
report={'status':'PASS' if len(results)==len(commands) and all(r['returncode']==0 for r in results) else 'FAIL',
        'python':platform.python_version(),'platform':platform.platform(),'checks':results,
        'scope':'Local developer validation, not hosted CI or external audit'}
(out/'verification.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
sys.exit(0 if report['status']=='PASS' else 1)
