"""Structural/integrity validation. This module never interprets English."""
from datetime import date
from decimal import Decimal, InvalidOperation
from collections import defaultdict
import jsonschema
from .canonical import canonical, digest
from .source import USER_ROLES
from .protocols import schema

COLLECTIONS = ("entities", "tasks", "candidate_sets", "propositions", "branches", "dependencies",
               "evidence_requirements", "user_decisions", "iteration_controls", "outputs")


class InvalidIR(ValueError):
    def __init__(self, findings):
        self.findings = findings
        super().__init__("; ".join(f["developer_detail"] for f in findings))


def validate_ir(ir, state, max_nodes=10000):
    errors = []
    def fail(code, detail, ids=(), anchors=()):
        errors.append({"code": code, "severity": "ERROR", "component": "validator",
                       "source_anchors": list(anchors), "ir_ids": list(ids),
                       "user_message": "The proposed representation did not pass integrity checks.",
                       "developer_detail": detail})
    try:
        jsonschema.Draft202012Validator(schema("semantic_ir.schema.json")).validate(ir)
    except jsonschema.ValidationError as e:
        fail("SCHEMA", f"{list(e.path)}: {e.message}")
        raise InvalidIR(errors) from e
    if ir["source_state_sha256"] != state.sha256:
        fail("SOURCE_IDENTITY", "IR is bound to a different request state")
    nodes = [n for name in COLLECTIONS for n in ir[name]]
    if len(nodes) > max_nodes:
        fail("RESOURCE_LIMIT", "IR node cap exceeded")
    index = {}
    for n in nodes:
        if n["id"] in index or n["id"] == "GLOBAL":
            fail("DUPLICATE_ID", n["id"], [n["id"]])
        index[n["id"]] = n
    types = {n["id"]: col for col in COLLECTIONS for n in ir[col]}
    events = {e.id: e for e in state.events}
    def ref(value, owner, allowed=None, global_ok=False):
        if global_ok and value == "GLOBAL":
            return
        if value not in index or (allowed and types.get(value) not in allowed):
            fail("REFERENCE", f"Invalid reference {value} on {owner}", [owner])
    for n in nodes:
        nid = n["id"]
        for key in ("subject_ref", "dependent_ref", "predecessor_ref", "successor_ref"):
            if key in n:
                ref(n[key], nid)
        if "scope_ref" in n:
            ref(n["scope_ref"], nid, {"branches", "tasks", "candidate_sets"}, True)
        if n.get("condition_ref"):
            ref(n["condition_ref"], nid, {"branches"})
        for key in ("members", "dependent_refs", "active_node_refs"):
            for target in n.get(key, []):
                ref(target, nid, {"entities"} if key == "members" else None)
            if len(set(n.get(key, []))) != len(n.get(key, [])):
                fail("DUPLICATE_REFERENCE", key, [nid])
        if n.get("collection_ref"):
            ref(n["collection_ref"], nid, {"candidate_sets"})
        anchors = n.get("source_anchors", [])
        user = n.get("authority", "USER") == "USER"
        if user and not anchors:
            fail("MISSING_PROVENANCE", "Material node lacks source anchors", [nid])
        user_anchor = False
        for a in anchors:
            e = events.get(a["source_id"])
            if (not e or a["event_id"] != a["source_id"] or
                not 0 <= a["start"] < a["end"] <= len(e.content) or
                digest(e.content[a["start"]:a["end"]].encode("utf-8")) != a["excerpt_sha256"]):
                fail("ANCHOR", "Invalid source span/hash/identity", [nid], [a])
            elif e.role in USER_ROLES:
                user_anchor = True
        if user and not user_anchor:
            fail("AUTHORITY", "USER instruction has no user-originated anchor", [nid], anchors)
        if types[nid] == "propositions":
            validate_value(n["object"], nid, ref, fail)
        if types[nid] == "iteration_controls":
            if n["mode"] == "BOUNDED_COUNT" and n.get("count") is None:
                fail("ITERATION", "Bounded count is missing", [nid])
            if n["mode"] == "UNTIL_CONDITION" and not n.get("stop_condition"):
                fail("ITERATION", "Missing stop condition", [nid])
            if n["mode"] == "OVER_COLLECTION" and not n.get("collection_ref"):
                fail("ITERATION", "Missing collection", [nid])
            if n["mode"] != "BOUNDED_COUNT" and n.get("count") is not None:
                fail("ITERATION", "Count declared outside bounded-count mode", [nid])
    if ir["user_decisions"] and "USER_DECISION_REQUIRED" not in ir["result_policy"]["allowed_states"]:
        fail("USER_ONLY_POLICY", "Reserved user decisions require USER_DECISION_REQUIRED outcome")
    graph = defaultdict(list)
    for edge in ir["dependencies"]:
        graph[edge["predecessor_ref"]].append(edge["successor_ref"])
    # Reserved decisions must explicitly gate their consumers; predecessors remain free.
    for d in ir["user_decisions"]:
        for target in d["dependent_refs"]:
            if target not in graph[d["id"]]:
                fail("USER_ONLY_GATE", "Reserved decision consumer lacks dependency", [d["id"], target])
    def cyclic(g):
        # Iterative DFS avoids stack exhaustion on deep, otherwise valid graphs.
        colors = {}
        for root in list(g):
            stack = [(root, False)]
            while stack:
                node, done = stack.pop()
                if done:
                    colors[node] = 2
                    continue
                if colors.get(node) == 1:
                    return True
                if colors.get(node) == 2:
                    continue
                colors[node] = 1
                stack.append((node, True))
                stack.extend((target, False) for target in g.get(node, []))
        return False
    if cyclic(graph):
        fail("DEPENDENCY_CYCLE", "Dependency graph contains a cycle")
    scopes = {n["id"]: [n["scope_ref"]] for n in nodes if "scope_ref" in n}
    if cyclic(scopes):
        fail("SCOPE_CYCLE", "Scope graph contains a cycle")
    for b in ir["branches"]:
        for target in b["active_node_refs"]:
            n = index.get(target, {})
            if n.get("scope_ref") != b["id"] and n.get("condition_ref") != b["id"]:
                fail("BRANCH_SCOPE", "Branch member must bind branch scope or condition", [b["id"], target])
    if errors:
        raise InvalidIR(errors)
    grouped = defaultdict(list)
    for p in ir["propositions"]:
        if p["modality"] == "REQUIRED" and p["polarity"] == "POSITIVE":
            key = (p["subject_ref"], p["predicate"], p["scope_ref"], p.get("condition_ref"),
                   p["object"]["kind"], p["object"].get("unit"), p["object"].get("currency"))
            grouped[key].append(p)
    for group in grouped.values():
        for i, p in enumerate(group):
            for q in group[i+1:]:
                a, b = p["object"].get("value"), q["object"].get("value")
                if (p["relation"] == q["relation"] == "EQ" and a != b or
                    {p["relation"], q["relation"]} == {"EQ", "NEQ"} and a == b):
                    fail("CONTRADICTION", "Incompatible values in simultaneously active scope", [p["id"], q["id"]])
                if p["object"]["kind"] in {"NUMBER", "MONEY", "PERCENT", "QUANTITY"}:
                    lo, hi = (p, q) if p["relation"] in {"GT", "GTE"} else (q, p)
                    if lo["relation"] in {"GT", "GTE"} and hi["relation"] in {"LT", "LTE"}:
                        x, y = Decimal(str(lo["object"]["value"])), Decimal(str(hi["object"]["value"]))
                        if x > y or x == y and (lo["relation"] == "GT" or hi["relation"] == "LT"):
                            fail("CONTRADICTION", "Empty numeric interval", [p["id"], q["id"]])
    if errors:
        raise InvalidIR(errors)
    return {"schema": "PASS", "provenance": "PASS", "authority": "PASS", "references": "PASS",
            "graphs": "PASS", "scalars": "PASS", "conservative_contradictions": "PASS"}


def validate_value(v, nid, ref, fail):
    kind, value = v["kind"], v.get("value")
    try:
        if kind in {"NUMBER", "MONEY", "PERCENT", "QUANTITY", "DURATION"}:
            if isinstance(value, bool) or not isinstance(value, (int, float, str)):
                raise ValueError("Expected numeric payload")
            number = Decimal(str(value))
            if not number.is_finite():
                raise ValueError("Non-finite scalar")
            if kind in {"QUANTITY", "DURATION"} and not v.get("unit"):
                raise ValueError("Missing unit")
            if kind == "MONEY" and not v.get("currency"):
                raise ValueError("Missing currency")
        elif kind == "BOOLEAN" and type(value) is not bool:
            raise ValueError("Expected boolean")
        elif kind == "DATE":
            if not isinstance(value, str) or date.fromisoformat(value).isoformat() != value:
                raise ValueError("Expected ISO calendar date")
        elif kind == "ENTITY_REF":
            if not isinstance(value, str):
                raise ValueError("Expected entity ID")
            ref(value, nid, {"entities"})
        elif kind == "SET":
            if not isinstance(value, list):
                raise ValueError("Expected typed value list")
            for child in value:
                validate_value(child, nid, ref, fail)
        elif kind == "RANGE":
            if not isinstance(value, dict) or set(value) != {"min", "max"}:
                raise ValueError("Expected min/max range")
            if Decimal(str(value["min"])) > Decimal(str(value["max"])):
                raise ValueError("Inverted range")
        elif kind == "NULL" and value is not None:
            raise ValueError("NULL value must be null")
        elif kind in {"TEXT", "SYMBOL"} and not isinstance(value, str):
            raise ValueError("Expected string")
        claim = v.get("normalization")
        if claim:
            if Decimal(str(claim["input"])) * Decimal(str(claim["multiplier"])) + Decimal(str(claim["offset"])) != Decimal(str(value)):
                raise ValueError("False arithmetic normalization claim")
    except (ValueError, TypeError, KeyError, InvalidOperation) as e:
        fail("SCALAR", str(e), [nid])
