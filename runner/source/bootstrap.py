from pathlib import Path
import subprocess, sys, hashlib, json
root=Path(__file__).resolve().parent
m=json.loads((root/'DEPLOYMENT_MANIFEST.json').read_bytes())
for n,h in m['files'].items():
    if hashlib.sha256((root/n).read_bytes()).hexdigest()!=h:
        raise SystemExit('Runtime integrity failure: '+n)
subprocess.run([sys.executable,'-m','pip','install','--no-index','--find-links',str(root/'wheelhouse'),
                '--target',str(root/'.vendor'),'-r',str(root/'requirements.lock')],check=True)
print('Offline dependencies installed. Run python run_runner.py self-check.')
