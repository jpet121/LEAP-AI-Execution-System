"""Offline runtime setup. Copied as bootstrap.py into the live runtime ZIP."""
import importlib.metadata
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent


def bootstrap():
    target = ROOT / ".runtime_deps"
    sys.path.insert(0, str(target))
    required = [line for line in (ROOT / "requirements.lock").read_text().splitlines() if line and not line.startswith("#")]
    satisfied = True
    for spec in required:
        name, version = spec.split("==")
        try:
            satisfied &= importlib.metadata.version(name) == version
        except importlib.metadata.PackageNotFoundError:
            satisfied = False
    if not satisfied:
        subprocess.run([sys.executable, "-m", "pip", "install", "--no-index", "--no-deps", "--no-compile",
                        "--find-links", str(ROOT / "wheelhouse"), "--target", str(target),
                        "--upgrade", "-r", str(ROOT / "requirements.lock")], check=True)
    sys.path.insert(0, str(ROOT / "lib"))
    return ROOT


if __name__ == "__main__":
    bootstrap()
    from pfcompiler.selfcheck import self_check
    print(self_check())
