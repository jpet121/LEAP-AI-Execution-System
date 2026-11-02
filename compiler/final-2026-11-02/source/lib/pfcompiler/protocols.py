"""Schema-constrained model boundary; no semantic parsing in Python."""
from typing import Protocol
from pathlib import Path
import jsonschema

FINDING_TYPES = ["OMISSION", "INVENTION", "ALTERATION", "AUTHORITY", "MODALITY", "SCOPE",
                 "SUBJECT_IDENTITY", "CANDIDATE_IDENTITY", "CONDITION", "BRANCH", "DEPENDENCY",
                 "USER_ONLY", "OUTPUT", "NO_RESULT_POLICY", "ITERATION"]


def object_schema(properties, required=None):
    return {"type": "object", "properties": properties,
            "required": list(properties) if required is None else required,
            "additionalProperties": False}


FINDING = object_schema({"kind": {"enum": FINDING_TYPES}, "message": {"type": "string", "minLength": 1},
                         "ir_ids": {"type": "array", "items": {"type": "string"}}})
CHALLENGE = object_schema({"verdict": {"enum": ["PASS", "CHALLENGE"]},
                          "findings": {"type": "array", "items": FINDING}})
QUESTION = object_schema({"id": {"type": "string", "minLength": 1},
                         "question": {"type": "string", "minLength": 1}})
CLASSIFICATION = object_schema({
    "category": {"enum": ["REPRESENTATION_DEFECT", "USER_AMBIGUITY", "UNSUPPORTED"]},
    "explanation": {"type": "string", "minLength": 1},
    "questions": {"type": "array", "items": QUESTION}})


class SemanticAdapter(Protocol):
    def interpret(self, request_state): ...
    def challenge(self, request_state, candidate_ir): ...
    def classify_issue(self, request_state, candidate_ir, findings): ...
    def reconcile(self, request_state, candidate_ir, findings): ...


def schema(name):
    import json
    return json.loads((Path(__file__).parent / "schemas" / name).read_text(encoding="utf-8"))


def check_challenge(value):
    jsonschema.validate(value, CHALLENGE)
    if (value["verdict"] == "PASS") != (not value["findings"]):
        raise ValueError("Challenger verdict and findings disagree")


def check_classification(value):
    jsonschema.validate(value, CLASSIFICATION)
    qs = value["questions"]
    if (value["category"] == "USER_AMBIGUITY") != bool(qs):
        raise ValueError("Only genuine ambiguity can carry clarification questions")
    if len({q["id"] for q in qs}) != len(qs):
        raise ValueError("Duplicate clarification IDs")
