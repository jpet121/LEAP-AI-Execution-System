from pathlib import Path
import sys, hashlib, json
root=Path(__file__).resolve().parent
manifest=json.loads((root/'DEPLOYMENT_MANIFEST.json').read_bytes())
expected=set(manifest['files'])
actual={p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file()
        and '__pycache__' not in p.parts and '.vendor' not in p.parts}
if actual != expected | {'DEPLOYMENT_MANIFEST.json','HASHES.sha256'}:
    raise SystemExit('Runtime inventory mismatch')
for n,h in manifest['files'].items():
    p=root/n
    if p.is_symlink() or hashlib.sha256(p.read_bytes()).hexdigest()!=h:
        raise SystemExit('Runtime hash mismatch: '+n)
lines=(root/'HASHES.sha256').read_text().splitlines()
hashes=dict(line.split('  ',1)[::-1] for line in lines)
if len(hashes)!=len(lines) or set(hashes)!=expected | {'DEPLOYMENT_MANIFEST.json'}:
    raise SystemExit('Runtime hash inventory mismatch')
for n,h in hashes.items():
    if hashlib.sha256((root/n).read_bytes()).hexdigest()!=h:
        raise SystemExit('Runtime hash sidecar mismatch: '+n)
sys.path[:0]=[str(root/'lib'),str(root/'.vendor')]
from pfrunner.cli import main
raise SystemExit(main())
