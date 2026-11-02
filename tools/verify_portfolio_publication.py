#!/usr/bin/env python3
"""Verify immutable owner-designated final Compiler source and published Case 4 snapshot."""
from pathlib import Path
import hashlib, json, sys
ROOT=Path(__file__).resolve().parents[1]
manifest=json.loads((ROOT/'PORTFOLIO_PUBLISH_HASHES.json').read_text())
errors=[]
for group in ('compiler','case4'):
    for name,expected in manifest[group].items():
        p=ROOT/name
        if not p.is_file():errors.append('missing:'+name)
        elif hashlib.sha256(p.read_bytes()).hexdigest()!=expected:errors.append('modified:'+name)
print(json.dumps({'status':'PASS' if not errors else 'FAIL','compiler_count':len(manifest['compiler']),'case4_count':len(manifest['case4']),'problems':errors},indent=2))
sys.exit(bool(errors))
