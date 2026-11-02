"""Controlled materialized mutants, each executed in a separate source copy."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

root=Path(__file__).resolve().parent.parent
mutations=[
 ('historical_replay','repository.py',"balance=format(prior[2],'.2f')","balance=format(account[0],'.2f')"),
 ('zero_boundary','money.py','if result < 0 or result > MAX:','if result <= 0 or result > MAX:'),
 ('float_representation','money.py',"return format(amount, '.2f')","return str(float(value))"),
 ('false_success','repository.py',"raise LedgerError(503,'DATABASE_UNAVAILABLE') from None","return 201, {}"),
 ('payload_conflict','repository.py','prior[0] != kind or prior[1] != Decimal(amount)','False'),
 ('authentication','api.py',"if len(supplied) != 1 or not secrets.compare_digest(supplied[0].encode(), settings.api_key.encode()):","if False:"),
]
results=[]
for name,file,before,after in mutations:
    with tempfile.TemporaryDirectory(prefix='case4-mutant-') as temp:
        target=Path(temp)
        shutil.copytree(root/'app',target/'app')
        shutil.copytree(root/'unit_tests',target/'unit_tests')
        shutil.copytree(root/'migrations',target/'migrations')
        p=target/'app'/file
        original=p.read_text()
        assert before in original,name
        p.write_text(original.replace(before,after))
        for cache in target.rglob('__pycache__'): shutil.rmtree(cache)
        cp=subprocess.run([sys.executable,'-m','unittest','discover','-s','unit_tests','-v'],cwd=target,capture_output=True,text=True,timeout=120)
        # Require actual assertion failures, not import or setup errors.
        killed=cp.returncode!=0 and 'FAIL:' in cp.stderr
        results.append({'name':name,'status':'KILLED' if killed else 'SURVIVED_OR_INVALID','returncode':cp.returncode,'stdout':cp.stdout,'stderr':cp.stderr})
report={'status':'PASS' if all(r['status']=='KILLED' for r in results) else 'FAIL','results':results}
(root/'evidence/mutation.json').write_text(json.dumps(report,indent=2))
print(json.dumps({r['name']:r['status'] for r in results},indent=2))
sys.exit(0 if report['status']=='PASS' else 1)
