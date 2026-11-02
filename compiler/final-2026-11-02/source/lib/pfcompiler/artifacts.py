"""Safe archive verification and deterministic release replay."""
from pathlib import Path, PurePosixPath
import json
import stat
import zipfile
import jsonschema
from .canonical import canonical, digest, read_json
from .source import RequestState
from .validation import validate_ir
from .protocols import schema, check_challenge
from .render import freeze, contract, portable
from .version import __version__, IR_VERSION, CONTRACT_VERSION


class IntegrityError(ValueError):
    pass


def safe_name(name):
    path = PurePosixPath(name)
    if (not name or "\\" in name or path.is_absolute() or
        any(p in {"", ".", ".."} or any(c in p for c in ':*?"<>|') or any(ord(c)<32 for c in p) or p.rstrip(" .") != p
            or p.split(".")[0].upper() in {"CON", "PRN", "AUX", "NUL", *(f"COM{i}" for i in range(1,10)), *(f"LPT{i}" for i in range(1,10))}
            for p in name.rstrip("/").split("/"))):
        raise IntegrityError("Unsafe package path")
    return path


def zip_members(path, max_files=5000, max_bytes=64_000_000):
    result = {}
    with zipfile.ZipFile(path) as archive:
        members = archive.infolist()
        if len(members) > max_files or sum(m.file_size for m in members) > max_bytes:
            raise IntegrityError("Archive resource cap exceeded")
        names, file_paths = set(), set()
        for m in members:
            safe_name(m.filename)
            folded = m.filename.rstrip("/").casefold()
            if folded in names or stat.S_ISLNK(m.external_attr >> 16) or m.flag_bits & 1:
                raise IntegrityError("Duplicate, symbolic link, or encrypted archive member")
            names.add(folded)
            if m.is_dir():
                continue
            file_paths.add(folded)
            data = archive.read(m)
            if len(data) != m.file_size:
                raise IntegrityError("Archive size mismatch")
            result[m.filename] = data
        for name in names:
            parts = name.split("/")
            if any("/".join(parts[:i]) in file_paths for i in range(1,len(parts))):
                raise IntegrityError("Archive file/directory path collision")
    return result


def verify_package(path):
    files = zip_members(path)
    try:
        manifest = json.loads(files["DEPLOYMENT_MANIFEST.json"])
        hashes = {}
        for line in files["HASHES.sha256"].decode("utf-8").splitlines():
            sha, name = line.split("  ", 1)
            safe_name(name)
            if name in hashes:
                raise IntegrityError("Duplicate hash entry")
            hashes[name] = sha
        if set(hashes) != set(files) - {"HASHES.sha256"}:
            raise IntegrityError("Hash inventory mismatch")
        if manifest["files"] != {n: digest(b) for n,b in files.items()
                                if n not in {"HASHES.sha256", "DEPLOYMENT_MANIFEST.json"}}:
            raise IntegrityError("Manifest inventory mismatch")
        if any(digest(files[n]) != h for n,h in hashes.items()):
            raise IntegrityError("Package hash mismatch")
    except (KeyError, ValueError, UnicodeDecodeError, TypeError) as e:
        raise IntegrityError(str(e)) from e
    return files


def extract_package(path, destination):
    files = verify_package(path)
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=True)
    if any(destination.iterdir()):
        raise IntegrityError("Extraction directory must be empty")
    for name, data in files.items():
        target = destination.joinpath(*safe_name(name).parts)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    return destination


def replay(receipt_path):
    receipt_path = Path(receipt_path)
    receipt = read_json(receipt_path)
    try:
        jsonschema.validate(receipt, schema("compiler_receipt.schema.json"))
    except jsonschema.ValidationError as e:
        raise ValueError("Invalid compiler receipt schema") from e
    if receipt["status"] != "COMPILE_RELEASED" or receipt.get("challenge_verdict") != "PASS":
        raise IntegrityError("Replay requires a released, challenged contract")
    if (receipt["compiler_version"], receipt["ir_version"], receipt["contract_version"]) != (__version__, IR_VERSION, CONTRACT_VERSION):
        raise IntegrityError("Unsupported artifact version")
    directory = receipt_path.parent
    files = {}
    expected = {"request_state.json", "semantic_ir.json", "contract.xml", "portable_brief.txt",
                "diagnostics.json", "clarifications.json", "semantic_audit.json"}
    if set(receipt["artifacts"]) != expected:
        raise IntegrityError("Artifact inventory mismatch")
    for name, sha in receipt["artifacts"].items():
        if len(safe_name(name).parts) != 1:
            raise IntegrityError("Artifact must be a sibling file")
        target = directory / name
        if target.is_symlink() or target.stat().st_size > 16_000_000:
            raise IntegrityError("Unsafe or oversized artifact")
        files[name] = target.read_bytes()
        if digest(files[name]) != sha:
            raise IntegrityError(f"Artifact hash mismatch: {name}")
    state = RequestState.from_dict(json.loads(files["request_state.json"]))
    if state.sha256 != receipt["source_state_sha256"]:
        raise IntegrityError("Receipt/source mismatch")
    ir = json.loads(files["semantic_ir.json"])
    validate_ir(ir, state)
    if canonical(ir) != files["semantic_ir.json"]:
        raise IntegrityError("Noncanonical IR serialization")
    snapshot = freeze(ir)
    audit = json.loads(files["semantic_audit.json"])
    if not audit or audit[-1]["role"] != "challenge" or audit[-1]["candidate_sha256"] != snapshot.sha256 or audit[-1]["source_state_sha256"] != state.sha256:
        raise IntegrityError("Missing final Challenger binding")
    check_challenge(audit[-1]["output"])
    if audit[-1]["output"]["verdict"] != "PASS":
        raise IntegrityError("Final Challenger did not pass")
    if files["contract.xml"] != contract(snapshot) or files["portable_brief.txt"] != portable(snapshot):
        raise IntegrityError("Artifact render is not the exact verified IR state")
    for name,key in [("semantic_ir.json", "verified_ir_sha256"), ("contract.xml", "contract_sha256"),
                     ("portable_brief.txt", "portable_brief_sha256")]:
        if digest(files[name]) != receipt[key]:
            raise IntegrityError("Receipt identity mismatch")
    return {"status": "VERIFIED", "contract_sha256": receipt["contract_sha256"], "runner_required": False}
