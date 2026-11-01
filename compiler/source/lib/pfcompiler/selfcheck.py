"""Small deterministic smoke check; explicitly not a semantic model test."""
from tempfile import TemporaryDirectory
from pathlib import Path
from .source import RequestState
from .compiler import Compiler
from .artifacts import replay


def sample_ir(state):
    a = [state.anchor(state.events[0].id)]
    return {"ir_version": "1.0", "source_state_sha256": state.sha256,
            "objective": "Explain the compiler boundary", "entities": [],
            "tasks": [{"id": "T1", "kind": "EXPLAIN", "label": "Explain the compiler boundary",
                       "scope_ref": "GLOBAL", "source_anchors": a}],
            "candidate_sets": [], "propositions": [], "branches": [], "dependencies": [],
            "evidence_requirements": [], "user_decisions": [], "iteration_controls": [],
            "outputs": [{"id": "O1", "label": "Explanation", "requirements": [], "source_anchors": a}],
            "result_policy": {"allowed_states": ["DETERMINED"]}}


class SmokeAdapter:
    """Protocol stub for runtime installation checks; never a user-facing adapter."""
    def interpret(self, state):
        return sample_ir(state)

    def challenge(self, state, candidate):
        return {"verdict": "PASS", "findings": []}


def self_check():
    state = RequestState.capture("Explain the compiler boundary.")
    result = Compiler().compile(state, SmokeAdapter())
    if result.status != "COMPILE_RELEASED":
        raise RuntimeError(result.receipt)
    with TemporaryDirectory() as temp:
        result.write(temp)
        replay(Path(temp) / "compiler_receipt.json")
    return {"status": "PASS", "scope": "deterministic installation smoke test with protocol stub",
            "runner_required": False, "semantic_model_tested": False}
