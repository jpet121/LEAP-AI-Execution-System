#!/usr/bin/env python3
"""Check historically frozen source hashes and current case evidence.

SHA256_MANIFEST.json is an October 2026 *historical snapshot*, not a manifest of
new November documentation/evidence. Release binaries/parts are missing; we do
not claim reconstruction or mirror-to-archive equality in this checkout.
"""
from pathlib import Path
import hashlib, json, sys
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIRS = ("compiler/source/", "runner/source/")

def check():
    old = json.loads((ROOT / "SHA256_MANIFEST.json").read_text())['files']
    failures = []
    source_count = 0
    for path, expected in old.items():
        if not path.startswith(SOURCE_DIRS):
            continue
        target = ROOT / path
        source_count += 1
        if not target.is_file() or hashlib.sha256(target.read_bytes()).hexdigest() != expected:
            failures.append("original-source-modified-or-missing:" + path)
    required = {'Objective','Entities','Tasks','CandidateSets','Propositions','Branches','Dependencies','EvidenceRequirements','UserDecisions','IterationControls','Outputs','ResultPolicy','Provenance'}
    examples=[]
    for case in ('four-day-workweek','payroll-platform-evaluation'):
        p=ROOT/'examples'/case/'contract.xml'
        try:
            node=ET.parse(p).getroot()
            if node.tag!='PFContract' or node.get('contract_version')!='1.0' or not required.issubset({n.tag for n in node}):
                failures.append('invalid-legacy-example:' + case)
            examples.append(case)
        except Exception as e:
            failures.append('legacy-example-error:' + case + ':' + repr(e))
    from verify_cases_1_3 import verify
    cases=verify()
    if cases['status']!='PASS':failures.extend(cases['errors'])
    return {'status':'PASS' if not failures else 'FAIL', 'frozen_source_sha256_count':source_count,'historical_examples':examples, 'accepted_case_integrity':cases['status'],'original_offline_runtime_archives_available':False, 'source_mirror_to_archives_reverified':False, 'problems':failures}

if __name__=='__main__':
    output=check();print(json.dumps(output,indent=2));sys.exit(0 if output['status']=='PASS' else 1)
