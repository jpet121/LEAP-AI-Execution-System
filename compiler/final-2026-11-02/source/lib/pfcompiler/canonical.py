import hashlib
import json


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical(value) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
                       allow_nan=False) + "\n").encode("utf-8")


def read_json(path, max_bytes=16_000_000):
    from pathlib import Path
    if Path(path).stat().st_size > max_bytes:
        raise ValueError("JSON file exceeds SYSTEM resource cap")
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError(f"Duplicate JSON key: {key}")
            result[key] = value
        return result
    with open(path, encoding="utf-8-sig") as stream:
        return json.load(stream, object_pairs_hook=pairs,
                         parse_constant=lambda x: (_ for _ in ()).throw(ValueError(x)))
