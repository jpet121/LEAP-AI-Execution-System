#!/usr/bin/env python3
"""Reconstruct an original unchanged runtime ZIP from browser-uploadable parts."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()

def reconstruct(kind: str, output_base: Path | None = None) -> Path:
    if kind not in {'compiler', 'runner'}:
        raise ValueError('Expected compiler or runner')
    release = ROOT / 'releases' / kind
    manifest = json.loads((release / 'archive_manifest.json').read_text(encoding='utf-8'))
    outdir = (output_base or ROOT / 'reconstructed') / kind
    outdir.mkdir(parents=True,exist_ok=True)
    target = outdir / manifest['archive_filename']
    if target.exists():
        # Avoid silently overwriting an operator's existing artifact.
        if target.stat().st_size == manifest['archive_size_bytes'] and digest(target) == manifest['archive_sha256']:
            return target
        raise FileExistsError(f'Output exists with incorrect hash: {target}')
    temp = target.with_suffix(target.suffix + '.tmp')
    try:
        h = hashlib.sha256()
        with temp.open('wb') as out:
            for item in manifest['parts']:
                part = release / item['filename']
                if not part.is_file() or part.stat().st_size != item['bytes'] or digest(part) != item['sha256']:
                    raise ValueError(f'Missing or damaged archive part: {part}')
                with part.open('rb') as src:
                    for chunk in iter(lambda: src.read(1024 * 1024), b''):
                        h.update(chunk)
                        out.write(chunk)
        if temp.stat().st_size != manifest['archive_size_bytes'] or h.hexdigest() != manifest['archive_sha256']:
            raise ValueError('Reconstructed archive size/hash mismatch')
        temp.replace(target)
    finally:
        if temp.exists(): temp.unlink()
    return target

if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('kind',choices=['compiler','runner'])
    p.add_argument('--output-base',type=Path)
    args=p.parse_args()
    target=reconstruct(args.kind,args.output_base)
    print(f'PASS {target} sha256={digest(target)}')
