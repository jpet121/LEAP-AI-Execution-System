#!/usr/bin/env python3
"""Check packaged source mirrors, case contracts and SHA-256 integrity metadata."""
from __future__ import annotations
import hashlib
import json
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]

def digest(path: Path) -> str:
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
    return h.hexdigest()

def check() -> dict:
    manifest=json.loads((ROOT/'SHA256_MANIFEST.json').read_text(encoding='utf-8'))
    files=manifest['files']
    bad=[]
    for rel,expected in files.items():
        p=ROOT/rel
        if not p.is_file() or digest(p)!=expected:bad.append(rel)
    actual={str(p.relative_to(ROOT)).replace('\\','/') for p in ROOT.rglob('*') if p.is_file() and '__pycache__' not in p.parts and 'reconstructed' not in p.parts and not p.name.endswith('.pyc')}
    untracked=sorted(actual-set(files)-{'SHA256_MANIFEST.json'})
    if untracked:bad.extend(f'untracked:{x}' for x in untracked)
    # All source mirror members are matched to the original unchanged archives.
    snapshot_count=0
    for kind in ('compiler','runner'):
        base=ROOT/'releases'/kind
        pkg=json.loads((base/'archive_manifest.json').read_text(encoding='utf-8'))
        restored=b''.join((base/p['filename']).read_bytes() for p in pkg['parts'])
        if len(restored)!=pkg['archive_size_bytes'] or hashlib.sha256(restored).hexdigest()!=pkg['archive_sha256']:
            bad.append(f'archive:{kind}')
            continue
        from io import BytesIO
        with zipfile.ZipFile(BytesIO(restored)) as z:
            for name in z.namelist():
                if name.endswith('/') or name.startswith('wheelhouse/') or name in {'HASHES.sha256','DEPLOYMENT_MANIFEST.json'}: continue
                p=ROOT/kind/'source'/name
                if not p.is_file() or p.read_bytes()!=z.read(name):bad.append(f'mirror:{kind}/{name}')
                snapshot_count+=1
    required={'Objective','Entities','Tasks','CandidateSets','Propositions','Branches','Dependencies','EvidenceRequirements','UserDecisions','IterationControls','Outputs','ResultPolicy','Provenance'}
    checks=[]
    for example in ['four-day-workweek','payroll-platform-evaluation']:
        p=ROOT/'examples'/example/'contract.xml'
        node=ET.parse(p).getroot()
        if node.tag!='PFContract' or node.attrib.get('contract_version')!='1.0' or not required.issubset({n.tag for n in node}):bad.append(f'contract:{example}')
        checks.append({'name':example,'sha256':digest(p),'xml_tags':len(list(node))})
    return {'status':'PASS' if not bad else 'FAIL','tracked_files':len(files),'source_mirror_members':snapshot_count,'cases':checks,'problems':bad}

if __name__=='__main__':
    result=check();print(json.dumps(result,indent=2));sys.exit(0 if result['status']=='PASS' else 1)
