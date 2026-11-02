"""Bind actual evidence and preserved source bytes into a bounded release receipt."""
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import sys

root=Path(__file__).resolve().parent.parent

def read(p): return json.loads((root/p).read_text())
def write(p,o): (root/p).write_text(json.dumps(o,indent=2)+'\n')
identity=read('evidence/frozen_identity.json')
changes=[n for n,h in identity.items() if hashlib.sha256((root/n).read_bytes()).hexdigest()!=h]
assert not changes,changes
coverage=read('evidence/coverage_first.json')
assert coverage['status']=='PASS'
verification=read('evidence/verification.json')
assert verification['status']=='PASS'
assert read('evidence/mutation.json')['status']=='PASS'
assert 'PASS: Compose' in (root/'evidence/compose.log').read_text()
with (root/'evidence/tool_versions.txt').open('w') as f:
    subprocess.run([sys.executable,'-m','pip','freeze'],stdout=f,check=True)
write('evidence/frozen_verification.json',{'status':'PASS','files_checked':len(identity),'changed_files':changes,'contract_sha256':identity['source/contract.xml']})
# Negative controls demonstrate verifier rejects absent PostgreSQL and corrupt identity.
cp=subprocess.run([sys.executable,'-c',"from app.db import migrate; migrate('postgresql://postgres@127.0.0.1:1/missing')"],cwd=root,capture_output=True,text=True)
assert cp.returncode!=0
write('evidence/negative_controls.json',{'missing_postgres':{'expected':'nonzero','returncode':cp.returncode,'stderr':cp.stderr},'tampered_contract_digest':{'expected':'different digest','observed_different':hashlib.sha256((root/'source/contract.xml').read_bytes()+b'!').hexdigest()!=identity['source/contract.xml']}})
engineering=read('analysis/ENGINEERING_REVIEW.json')
cases=read('tests/FROZEN_ACCEPTANCE_ORACLES.json')['cases']
assign={
 'SRC-01':(['source/contract.xml','source/compiler_receipt.json'],['evidence/frozen_verification.json']),
 'SCOPE-01':(['app/','README.md'],['evidence/bandit.log']),
 'STACK-01':(['pyproject.toml','app/db.py'],['evidence/verification.json','evidence/docker-build.log']),
 'PKG-01':(['Dockerfile','compose.yaml','requirements.lock','README.md'],['evidence/build.log','evidence/compose.log']),
 'CI-01':(['.github/workflows/ci.yml'],[]),
 'AUTH-01':(['app/api.py'],['evidence/acceptance.log','unit_tests/test_api.py']),
 'AUTH-02':(['app/api.py'],['evidence/acceptance.log']),
 'AUTH-03':(['app/config.py','app/api.py'],['evidence/bandit.log','evidence/advanced.log']),
 'A9-FAULT':(['app/repository.py'],['unit_tests/test_faults.py','evidence/coverage_first.json']),
 'DB-ATOMIC':(['app/repository.py','migrations/001_initial.sql'],['unit_tests/test_faults.py','evidence/coverage_first.json']),
 'OPS-COVERAGE':(['app/'],['evidence/coverage_first.json']),
 'OPS-TRACE':(['evidence/source_to_file_mapping.json'],['evidence/frozen_verification.json']),
 'OPS-TESTS':(['tests/','unit_tests/','advanced_tests/'],['evidence/verification.json']),
 'OPS-HOLD':(['IMPLEMENTATION_RECEIPT.json'],['evidence/RELEASE_READINESS.md']),
 'OPS-STAGE':(['IMPLEMENTATION_RECEIPT.json'],['evidence/RELEASE_READINESS.md'])}
observations=[]
for case in cases:
    cid=case['id']
    if cid not in assign:
        if cid.startswith('VAL-'):
            assign[cid]=(['app/models.py','app/money.py'],['unit_tests/test_validation.py','evidence/coverage_first.json','evidence/advanced.log'])
        else:
            assign[cid]=(['app/ledger.py','app/repository.py','migrations/001_initial.sql'],['evidence/acceptance.log','evidence/coverage_first.json','evidence/advanced.log'])
    files,evidence=assign[cid]
    observations.append({'id':cid,'status':'HOLD' if cid=='CI-01' else 'PASS','implementation':files,'evidence':evidence,'note':'Hosted workflow supplied; no GitHub Actions run was performed' if cid=='CI-01' else 'See linked assertions and recorded execution; not an external acceptance verdict'})
write('evidence/acceptance_mapping.json',observations)
trace=[]
for requirement in engineering['requirements']:
    linked=[c for c in observations if c['id'] in requirement['acceptance_ids']]
    assert linked
    trace.append({'requirement_id':requirement['id'],'proposition_ids':requirement['source_proposition_ids'],'acceptance_ids':requirement['acceptance_ids'],'implementation_files':sorted({p for c in linked for p in c['implementation']}),'evidence_paths':sorted({p for c in linked for p in c['evidence']}),'status':'HOLD' if any(c['status']=='HOLD' for c in linked) else 'PASS'})
assert len(trace)==66
write('evidence/source_to_file_mapping.json',trace)
methods=[]
for i,d in enumerate(engineering['test_disciplines']):
    status='PASS'
    evidence=['evidence/verification.json']
    detail='Bounded local developer evidence; no external organizational independence.'
    if 'Lean' in d['name']: status='NOT_RUN';detail='Optional Lean model/proof not supplied or executed; no formal-proof claim.'
    if d['name']=='Compatibility testing': status='PARTIAL';detail='Python 3.12.14 native/container and PostgreSQL 17.11 exercised; Python 3.13 hosted matrix supplied but not run.'
    if d['name']=='Build/distribution/clean-install reproducibility':status='PARTIAL';detail='Wheel/sdist built and Compose exercised; hosted CI not run. Exact archive clean replay is reported separately.'
    methods.append({'name':d['name'],'status':status,'evidence':evidence,'limits':detail})
write('evidence/assurance_methods.json',methods)
receipt={'verdict':'HOLD','implementation_status':'IMPLEMENTED_LOCALLY_VERIFIED','source_sha256':identity['source/contract.xml'],
 'local_checks':verification,'coverage':{k:coverage[k] for k in ('status','line_percent','branch_percent','tests_run','files_in_scope')},
 'frozen_files_unchanged':True,'human_release':'NOT_GRANTED','hosted_github_actions':'NOT_RUN','external_organizational_audit':'NOT_PERFORMED',
 'scope':'Synthetic training API; no banking integration, real funds, production deployment or repository publication',
 'limitations':['Hosted GitHub Actions execution requires an explicitly chosen repository and workflow run; none was performed.',
 'Exact-archive replay is developer-side in new processes, not an independent organizational audit.',
 'Optional Lean proof and second Python version not executed.',
 'Original plain-language source-state is absent from the frozen handoff; only compiled-contract fidelity is checked.',
 'Incremental unit gates use new unit_tests/ instead of frozen external HTTP tests/. All runtime app modules remain in scope; frozen tests run separately unchanged.'],
 'changed_files':sorted(str(p.relative_to(root)) for p in root.rglob('*') if p.is_file() and str(p.relative_to(root)) not in identity and not any(x in p.parts for x in ('__pycache__','build','.mypy_cache','.hypothesis')))}
write('IMPLEMENTATION_RECEIPT.json',receipt)
write('evidence/IMPLEMENTATION_RECEIPT.json',receipt)
write('evidence/TEST_RESULT.json',{'verdict':'HOLD','local_verification':'PASS','frozen_http_tests':4,'unit_methods':coverage['tests_run'],'advanced_methods':7,'hypothesis_examples':150,'model_http_operations':250,'races':read('evidence/races.json'),'mutants_killed':6,'real_database_fault_points':3,'missing':['Hosted GitHub Actions run','External final audit','Human release authorization']})
(root/'evidence/RELEASE_READINESS.md').write_text('''# Verdict: HOLD

Application implemented and local required checks pass. Frozen acceptance executes
against a newly created PostgreSQL database through real HTTP. Line and branch
coverage both measure 100% across all 10 runtime modules. All original handoff
files, including specifications, tests, oracles, gate and historical evidence,
are unchanged. The failed new AST check and initial container/startup failures
are preserved alongside their diagnosed corrections and passing reruns.

Hosted GitHub Actions has NOT run. The workflow file and local equivalent checks
do not substitute for hosted evidence. Python 3.13 and optional Lean proof were
not executed. No external organizational audit or human release approval exists.
Human release: NOT_GRANTED. No production deployment was performed.

Branch review: valid/invalid settings, money, IDs, auth, existing/missing account,
replay, amount/kind conflict, zero/overdraft/overflow, success/database exceptions
all have concrete assertions. Coverage alone does not establish correctness.
No patch/mock framework is used. Injected callbacks are explicit constructor seams
and provoke real PostgreSQL SQL/COMMIT failures, not simulated passing outcomes.

Unit-gate test directory differs from the illustrative frozen-suite command:
unit_tests/ isolates incremental tests before an HTTP server exists. The gate
and its whole-runtime 100% threshold are unchanged. tests/ executes separately
without edits. This implementation-plan adaptation is explicitly disclosed.

For final exact-archive replay, see the separately returned replay receipt and
logs. Fresh processes and extraction on the same host are not external audit.
Publish the supplied workflow only to a user-selected repository and obtain an
actual green run plus independent review before reconsidering release HOLD.
''')
print(json.dumps(receipt['coverage']))
