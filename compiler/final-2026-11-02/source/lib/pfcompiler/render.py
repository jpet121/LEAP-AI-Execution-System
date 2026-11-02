"""Renderers accept only a verifier-created immutable snapshot."""
from dataclasses import dataclass
from pathlib import Path
import json
from lxml import etree
from .canonical import canonical, digest
from .version import __version__, IR_VERSION, CONTRACT_VERSION

SECTIONS = [("entities", "Entities"), ("tasks", "Tasks"), ("candidate_sets", "CandidateSets"),
            ("propositions", "Propositions"), ("branches", "Branches"), ("dependencies", "Dependencies"),
            ("evidence_requirements", "EvidenceRequirements"), ("user_decisions", "UserDecisions"),
            ("iteration_controls", "IterationControls"), ("outputs", "Outputs"), ("result_policy", "ResultPolicy")]
FOOTER = "This brief is a rendering of a verified Prompt Forge Compiler specification. A downstream system may not enforce Prompt Forge runtime controls."
_TOKEN = object()


@dataclass(frozen=True, init=False)
class VerifiedIR:
    data: bytes

    def __init__(self, data, token=None):
        if token is not _TOKEN:
            raise ValueError("Verified IR must come from compiler verification or replay")
        object.__setattr__(self, "data", bytes(data))

    @property
    def sha256(self):
        return digest(self.data)


def freeze(ir):
    """Internal boundary: caller must validate and obtain Challenger PASS first."""
    return VerifiedIR(canonical(ir), _TOKEN)


def contract(snapshot):
    if not isinstance(snapshot, VerifiedIR):
        raise TypeError("Expected verified immutable IR")
    ir = json.loads(snapshot.data)
    root = etree.Element("PFContract", contract_version=CONTRACT_VERSION, compiler_version=__version__,
                         ir_version=IR_VERSION, source_state_sha256=ir["source_state_sha256"],
                         verified_ir_sha256=snapshot.sha256, contract_id="PF-" + snapshot.sha256)
    etree.SubElement(root, "Objective").text = ir["objective"]
    for key, label in SECTIONS:
        section = etree.SubElement(root, label)
        nodes = [ir[key]] if key == "result_policy" else ir[key]
        for node in nodes:
            etree.SubElement(section, "Node").text = canonical(node).decode().rstrip("\n")
    provenance = etree.SubElement(root, "Provenance")
    anchors = {canonical(a) for key, _ in SECTIONS if isinstance(ir[key], list)
               for node in ir[key] for a in node.get("source_anchors", [])}
    for a in sorted(anchors):
        etree.SubElement(provenance, "Node").text = a.decode().rstrip("\n")
    data = etree.tostring(root, encoding="UTF-8", xml_declaration=True, pretty_print=True)
    validate_xml(data)
    return data


def validate_xml(data):
    if b"<!DOCTYPE" in data.upper() or b"<!ENTITY" in data.upper():
        raise ValueError("DTDs and entities are forbidden")
    parser = etree.XMLParser(resolve_entities=False, no_network=True, load_dtd=False)
    tree = etree.fromstring(data, parser)
    xsd = etree.XMLSchema(etree.parse(str(Path(__file__).parent / "schemas/contract.xsd"), parser))
    xsd.assertValid(tree)
    return tree


def portable(snapshot):
    if not isinstance(snapshot, VerifiedIR):
        raise TypeError("Expected verified immutable IR")
    ir = json.loads(snapshot.data)
    def line(node):
        # Canonical structured payload preserves ALL machine-significant fields.
        return "- " + canonical(node).decode().rstrip("\n")
    groups = [
        ("OBJECTIVE", [ir["objective"]]),
        ("REQUIRED WORK", ir["tasks"]),
        ("HARD REQUIREMENTS", [p for p in ir["propositions"] if p["modality"] == "REQUIRED"]),
        ("PROHIBITIONS", [p for p in ir["propositions"] if p["modality"] == "PROHIBITED"]),
        ("PREFERENCES", [p for p in ir["propositions"] if p["modality"] == "PREFERRED"]),
        ("CANDIDATES / SCOPE", ir["entities"] + ir["candidate_sets"] + ir["branches"]),
        ("EVIDENCE REQUIREMENTS", ir["evidence_requirements"]),
        ("DECISION RULES", ir["dependencies"] + ir["iteration_controls"] +
         [p for p in ir["propositions"] if p["modality"] in {"PERMITTED", "INFORMATIONAL"}]),
        ("USER-RESERVED DECISIONS", ir["user_decisions"]),
        ("ALLOWED OUTCOMES", [ir["result_policy"]]),
        ("REQUIRED OUTPUTS", ir["outputs"]),
        ("SOURCE / AUTHORITY NOTES", [{"source_state_sha256": ir["source_state_sha256"],
                                         "verified_ir_sha256": snapshot.sha256}])]
    return ("\n\n".join(title + "\n" + ("\n".join(line(n) for n in nodes) or "(none)")
                          for title, nodes in groups) + "\n\n" + FOOTER + "\n").encode()
