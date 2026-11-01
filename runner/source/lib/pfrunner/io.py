"""Bounded, non-executing intake and exact-byte integrity utilities."""
import hashlib
import json
import re
import stat
import zipfile
from pathlib import Path

MAX_FILE = 64_000_000
MAX_TOTAL = 128_000_000


class Invalid(ValueError):
    pass


class IntegrityError(Invalid):
    pass


def require(condition, message):
    if not condition:
        raise Invalid(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def canonical(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True,
                       separators=(",", ":"), allow_nan=False) + "\n").encode("utf-8")


def loads(data):
    def pairs(items):
        result = {}
        for k, v in items:
            require(k not in result, "Duplicate JSON key: " + k)
            result[k] = v
        return result
    require(len(data) <= MAX_FILE, "JSON resource cap")
    return json.loads(data, object_pairs_hook=pairs,
                      parse_constant=lambda x: (_ for _ in ()).throw(Invalid(x)))


def safe_name(name):
    require(isinstance(name, str) and name and "\\" not in name, "Unsafe path")
    parts = name.rstrip("/").split("/")
    for p in parts:
        require(p not in {"", ".", ".."} and p == p.rstrip(" .") and
                not any(c in p for c in ':*?"<>|') and not any(ord(c) < 32 for c in p)
                and not re.fullmatch(r"(?i:CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])", p.split('.')[0]),
                "Unsafe path: " + name)
    return parts


def read_file(path):
    p = Path(path)
    require(not linkish(p) and p.is_file() and p.stat().st_size <= MAX_FILE,
            "Unsafe, absent, or oversized file: " + str(p))
    return p.read_bytes()


def linkish(p):
    return p.is_symlink() or (hasattr(p, 'is_junction') and p.is_junction())


def members(path):
    try:
        return _members(path)
    except (zipfile.BadZipFile, RuntimeError) as e:
        raise IntegrityError('Invalid archive: ' + str(e)) from e


def _members(path):
    """Read ZIP or directory into memory; never execute or extract input code."""
    p = Path(path)
    result = {}
    if p.is_dir():
        entries = list(p.rglob('*'))
        require(len(entries) <= 5000 and not linkish(p), "Directory resource cap")
        for f in entries:
            require(not linkish(f), "Symlink/junction forbidden")
            if f.is_file():
                name = f.relative_to(p).as_posix()
                safe_name(name)
                result[name] = read_file(f)
    else:
        with zipfile.ZipFile(p) as z:
            entries = z.infolist()
            require(len(entries) <= 5000 and sum(e.file_size for e in entries) <= MAX_TOTAL,
                    "Archive resource cap")
            names = set()
            for e in entries:
                safe_name(e.filename)
                name = e.filename.rstrip('/').casefold()
                require(name not in names and not stat.S_ISLNK(e.external_attr >> 16)
                        and not e.flag_bits & 1, "Duplicate, link, or encrypted ZIP member")
                names.add(name)
                if not e.is_dir():
                    require(e.file_size <= MAX_FILE, "Member resource cap")
                    result[e.filename] = z.read(e)
    require(sum(map(len, result.values())) <= MAX_TOTAL, "Total resource cap")
    folded = {n.casefold() for n in result}
    require(len(folded) == len(result), "Case collision")
    for n in result:
        parts = safe_name(n)
        require(not any('/'.join(parts[:i]).casefold() in folded for i in range(1, len(parts))),
                "File/directory collision")
    return result


def verify_hash_inventory(files):
    if 'HASHES.sha256' in files:
        hashes = {}
        for line in files['HASHES.sha256'].decode('utf-8').splitlines():
            h, n = line.split('  ', 1)
            safe_name(n)
            require(n not in hashes, "Duplicate hash entry")
            hashes[n] = h
        require(set(hashes) == set(files) - {'HASHES.sha256'}, "Hash inventory mismatch")
        require(all(sha(files[n]) == h for n, h in hashes.items()), "Package hash mismatch")
    if 'DEPLOYMENT_MANIFEST.json' in files:
        m = loads(files['DEPLOYMENT_MANIFEST.json'])
        require(m['files'] == {n: sha(b) for n, b in files.items()
                              if n not in {'HASHES.sha256', 'DEPLOYMENT_MANIFEST.json'}},
                "Deployment manifest mismatch")


def schema(name):
    return loads((Path(__file__).parent / 'schemas' / name).read_bytes())
