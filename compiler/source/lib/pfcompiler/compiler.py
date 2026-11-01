from dataclasses import dataclass
from copy import deepcopy
from pathlib import Path
import time
import jsonschema
from .canonical import canonical, digest
from .version import __version__, IR_VERSION, CONTRACT_VERSION
from .validation import validate_ir, InvalidIR
from .protocols import check_challenge, check_classification, schema
from .render import freeze, contract, portable


@dataclass(frozen=True)
class ResourcePolicy:
    max_source_bytes: int = 1_000_000
    max_events: int = 100
    max_ir_nodes: int = 10000
    max_repairs: int = 2
    max_artifact_bytes: int = 16_000_000


@dataclass(frozen=True)
class CompileResult:
    status: str
    files: tuple[tuple[str, bytes], ...]

    @property
    def receipt(self):
        import json
        return json.loads(dict(self.files)["compiler_receipt.json"])

    def write(self, directory):
        path = Path(directory)
        path.mkdir(parents=True, exist_ok=True)
        if any(path.iterdir()):
            raise ValueError("Output directory must be empty; preserve prior immutable artifacts")
        # Receipt written last. A partially written directory cannot replay as released.
        files = dict(self.files)
        for name in sorted(files, key=lambda n: n == "compiler_receipt.json"):
            target = path / name
            with target.open("xb") as stream:
                stream.write(files[name])


class Compiler:
    def __init__(self, policy=None):
        self.policy = policy or ResourcePolicy()

    def compile(self, request_state, semantic_adapter):
        state, adapter = request_state, semantic_adapter
        started = time.monotonic()
        transitions, diagnostics, audit, questions = ["RECEIVED"], [], [], []
        repairs, verdict, summary = 0, None, {}
        files = {"request_state.json": canonical(state.to_dict())}
        status = "COMPILE_FAILED"

        def invoke(role, *args):
            # Defensive copies isolate adapter mutation from authoritative state / candidate.
            result = getattr(adapter, role)(state, *(deepcopy(a) for a in args))
            audit.append({"role": role, "source_state_sha256": state.sha256,
                          "candidate_sha256": digest(canonical(args[0])) if args else None,
                          "output": deepcopy(result)})
            if len(canonical(result)) > self.policy.max_artifact_bytes:
                raise ValueError("Model output cap exceeded")
            return deepcopy(result)

        try:
            if len(canonical(state.to_dict())) > self.policy.max_source_bytes or len(state.events) > self.policy.max_events:
                raise ValueError("SYSTEM source resource cap exceeded")
            transitions.append("INTERPRETING")
            ir = invoke("interpret")
            while True:
                transitions.append("VALIDATING_IR")
                structural = False
                try:
                    summary = validate_ir(ir, state, self.policy.max_ir_nodes)
                    findings = []
                except InvalidIR as e:
                    findings, structural = e.findings, True
                    diagnostics.extend(findings)
                if not structural:
                    transitions.append("CHALLENGING")
                    challenge = invoke("challenge", ir)
                    check_challenge(challenge)
                    verdict = challenge["verdict"]
                    findings = challenge["findings"]
                    if verdict == "PASS":
                        break
                # Structural errors always belong to the compiler. Never ask user to fix them.
                if structural:
                    classification = {"category": "REPRESENTATION_DEFECT", "questions": [],
                                      "explanation": "Structural representation defect"}
                else:
                    transitions.append("CLASSIFYING")
                    classification = invoke("classify_issue", ir, findings)
                    check_classification(classification)
                if classification["category"] == "USER_AMBIGUITY":
                    questions = classification["questions"]
                    status = "COMPILE_NEEDS_CLARIFICATION"
                    transitions.append("NEEDS_CLARIFICATION")
                    break
                if classification["category"] == "UNSUPPORTED":
                    status = "COMPILE_UNSUPPORTED"
                    diagnostics.append({"code": "UNSUPPORTED", "severity": "ERROR", "component": "classifier",
                                        "source_anchors": [], "ir_ids": [],
                                        "user_message": classification["explanation"], "developer_detail": ""})
                    transitions.append("UNSUPPORTED")
                    break
                if repairs >= self.policy.max_repairs:
                    raise ValueError("SYSTEM internal repair budget exhausted")
                transitions.extend(["RECONCILING", "INTERPRETING"])
                repairs += 1
                ir = invoke("reconcile", ir, findings)
            else:
                raise AssertionError("Unreachable")
            if verdict == "PASS" and not questions and status == "COMPILE_FAILED":
                transitions.extend(["VERIFIED", "RENDERING"])
                snapshot = freeze(ir)
                files["semantic_ir.json"] = snapshot.data
                files["contract.xml"] = contract(snapshot)
                files["portable_brief.txt"] = portable(snapshot)
                transitions.append("FINAL_VALIDATION")
                if any(len(b) > self.policy.max_artifact_bytes for b in files.values()):
                    raise ValueError("SYSTEM artifact resource cap exceeded")
                status = "COMPILE_RELEASED"
                transitions.append("RELEASED")
        except Exception as e:
            status = "COMPILE_FAILED"
            transitions.append("FAILED")
            for name in ("semantic_ir.json", "contract.xml", "portable_brief.txt"):
                files.pop(name, None)
            diagnostics.append({"code": type(e).__name__, "severity": "ERROR", "component": "compiler",
                                "source_anchors": [], "ir_ids": [], "user_message": str(e),
                                "developer_detail": str(e)})
        files["diagnostics.json"] = canonical(diagnostics)
        files["clarifications.json"] = canonical(questions)
        files["semantic_audit.json"] = canonical(audit)
        receipt = {"status": status, "compiler_version": __version__, "ir_version": IR_VERSION,
                   "contract_version": CONTRACT_VERSION, "source_state_sha256": state.sha256,
                   "verified_ir_sha256": digest(files["semantic_ir.json"]) if "semantic_ir.json" in files else None,
                   "contract_sha256": digest(files["contract.xml"]) if "contract.xml" in files else None,
                   "portable_brief_sha256": digest(files["portable_brief.txt"]) if "portable_brief.txt" in files else None,
                   "challenge_verdict": verdict, "internal_repair_count": repairs,
                   "clarification_event_ids": [e.id for e in state.events if e.role == "USER_CLARIFICATION"],
                   "validation": summary, "transitions": transitions,
                   "timing": {"total_seconds": round(time.monotonic()-started, 6),
                              "model_seconds": (round(adapter.latency_seconds, 6)
                                                if getattr(adapter, "latency_seconds", None) is not None else None)},
                   "resource_policy": self.policy.__dict__,
                   "artifacts": {name: digest(data) for name, data in sorted(files.items())}}
        jsonschema.validate(receipt, schema("compiler_receipt.schema.json"))
        files["compiler_receipt.json"] = canonical(receipt)
        return CompileResult(status, tuple(sorted(files.items())))
