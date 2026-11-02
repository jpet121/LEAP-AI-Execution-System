#!/usr/bin/env python3
"""Fail-closed Compiler release assembly; does not generate or modify contracts."""
from pathlib import Path
import hashlib, json, sys, tempfile, zipfile
sys.path.insert(0,str(Path(__file__).resolve().parent/'lib'))
from pfcompiler.artifacts import replay, IntegrityError

EXPECTED={'request_state.json','semantic_ir.json','contract.xml','portable_brief.txt',
          'diagnostics.json','clarifications.json','semantic_audit.json','compiler_receipt.json'}

def build(source, destination):
    source=Path(source); destination=Path(destination)
    if destination.exists(): raise IntegrityError('Refusing to overwrite a release archive')
    if not source.is_dir(): raise IntegrityError('Missing complete release directory')
    if {x.name for x in source.iterdir()}!=EXPECTED or any(x.is_symlink() or not x.is_file() for x in source.iterdir()):
        raise IntegrityError('Receipt-bound directory has missing, extra or unsafe members')
    if replay(source/'compiler_receipt.json')['status']!='VERIFIED':
        raise IntegrityError('Compiler replay did not verify')
    receipt=json.loads((source/'compiler_receipt.json').read_bytes())
    if set(receipt['artifacts'])!=EXPECTED-{'compiler_receipt.json'}:
        raise IntegrityError('Receipt inventory is incomplete')
    destination.parent.mkdir(parents=True,exist_ok=True)
    temp=destination.with_name(destination.name+'.tmp')
    if temp.exists():raise IntegrityError('Temporary output exists')
    try:
        with zipfile.ZipFile(temp,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
            for name in sorted(EXPECTED):
                z.write(source/name,arcname=name)
        with zipfile.ZipFile(temp) as z:
            if set(z.namelist())!=EXPECTED:raise IntegrityError('ZIP manifest mismatch')
            for name in EXPECTED:
                data=z.read(name)
                if data!=(source/name).read_bytes():raise IntegrityError('ZIP changed a member')
                if name!='compiler_receipt.json' and hashlib.sha256(data).hexdigest()!=receipt['artifacts'][name]:
                    raise IntegrityError('ZIP member hash differs from receipt')
        temp.rename(destination)
        return {'status':'VERIFIED','path':str(destination),
                'archive_sha256':hashlib.sha256(destination.read_bytes()).hexdigest(),
                'artifact_count':len(EXPECTED)}
    finally:
        if temp.exists():temp.unlink()

if __name__=='__main__':
    if len(sys.argv)!=3:raise SystemExit('Usage: python make_compiler_release.py RELEASE_DIRECTORY OUTPUT.zip')
    print(json.dumps(build(sys.argv[1],sys.argv[2]),sort_keys=True))
