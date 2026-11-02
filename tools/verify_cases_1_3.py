#!/usr/bin/env python3
"""Verify the three frozen Runner export ZIPs and matching contract receipts.

This checks byte integrity and recorded identities, not semantic truth or new
model-driven execution. No ZIP member is executed or extracted.
"""
import hashlib
import json
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "evidence" / "cases-1-3"

def sha(data):
    return hashlib.sha256(data).hexdigest()

def verify():
    config = json.loads((BASE / "INTEGRITY.json").read_text())
    errors = []
    results = []
    for case, expected in sorted(config["case_run_packages"].items()):
        file = BASE / case / expected["zip"]
        if not file.is_file():
            errors.append(f"{case}: missing ZIP"); continue
        if sha(file.read_bytes()) != expected["zip_sha256"]:
            errors.append(f"{case}: ZIP SHA-256 mismatch"); continue
        with zipfile.ZipFile(file) as z:
            names = [n for n in z.namelist() if not n.endswith("/")]
            if len(names) != len(set(names)) or z.testzip() is not None:
                errors.append(f"{case}: invalid ZIP member/integrity"); continue
            receipt_path = next((n for n in names if n.endswith("run_receipt.json")), None)
            if not receipt_path:
                errors.append(f"{case}: no receipt"); continue
            prefix = receipt_path[:-len("run_receipt.json")]
            ledger_path = prefix + "HASHES.sha256"
            if ledger_path not in names:
                errors.append(f"{case}: no HASHES.sha256"); continue
            entries = {}
            for line in z.read(ledger_path).decode().splitlines():
                expected_sha, sep, relative = line.partition("  ")
                if not sep or relative in entries:
                    errors.append(f"{case}: malformed manifest line"); continue
                entries[relative] = expected_sha
            expected_members = {prefix + p for p in entries} | {ledger_path}
            extras = set(names) - expected_members
            missing = expected_members - set(names)
            if missing or extras - {"host_review_trace.json"}:
                errors.append(f"{case}: member inventory mismatch")
            for relative, digest in entries.items():
                candidate = prefix + relative
                if candidate not in names or sha(z.read(candidate)) != digest:
                    errors.append(f"{case}: hash mismatch {relative}")
            r = json.loads(z.read(receipt_path))
            contract = z.read(prefix + "input_contract.xml")
            if sha(contract) != expected["contract_sha256"] or r.get("contract_sha256") != expected["contract_sha256"]:
                errors.append(f"{case}: contract binding mismatch")
            if r.get("postflight",{}).get("status") != "PASS" or r.get("analytical_outcome") != expected["analytical_outcome"]:
                errors.append(f"{case}: receipt classification/postflight mismatch")
            for relative, inner in [("contract.xml",contract),("run_receipt.json",z.read(receipt_path)),("result.md",z.read(prefix+"result.md"))]:
                disk = BASE / case / relative
                if not disk.is_file() or disk.read_bytes() != inner:
                    errors.append(f"{case}: published extract differs: {relative}")
            results.append({"case":case,"files_verified":len(entries),"sha256":sha(file.read_bytes()),"analytical_outcome":r.get("analytical_outcome")})
    return {"status":"PASS" if not errors else "FAIL", "case_count":len(results),"cases":results,"errors":errors, "scope":"Integrity/identity only; not independent semantic execution"}

if __name__ == "__main__":
    result = verify()
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result["status"] == "PASS" else 1)
