from dataclasses import dataclass, asdict
from .canonical import canonical, digest

ROLES = {"USER_DIRECTIVE", "USER_CLARIFICATION", "REFERENCE_MATERIAL", "SYSTEM_POLICY"}
USER_ROLES = {"USER_DIRECTIVE", "USER_CLARIFICATION"}


@dataclass(frozen=True)
class SourceEvent:
    id: str
    role: str
    content: str
    content_sha256: str
    sequence: int
    clarification_target: str | None = None

    @classmethod
    def create(cls, id, role, content, sequence, clarification_target=None):
        content = content.replace("\r\n", "\n").replace("\r", "\n")
        return cls(id, role, content, digest(content.encode("utf-8")), sequence,
                   clarification_target)


@dataclass(frozen=True)
class RequestState:
    events: tuple[SourceEvent, ...]

    def __post_init__(self):
        if not isinstance(self.events, tuple) or not self.events:
            raise ValueError("Source events must be a nonempty immutable tuple")
        ids = set()
        for i, e in enumerate(self.events):
            if not e.id or e.id in ids or e.role not in ROLES or e.sequence != i:
                raise ValueError("Invalid source identity, role, or sequence")
            if e.content_sha256 != digest(e.content.encode("utf-8")):
                raise ValueError("Source content hash mismatch")
            if "\r" in e.content:
                raise ValueError("Source newlines must be normalized at capture")
            if e.role == "USER_CLARIFICATION" and not e.clarification_target:
                raise ValueError("Clarification must identify its question")
            ids.add(e.id)
        if not any(e.role == "USER_DIRECTIVE" for e in self.events):
            raise ValueError("Missing original user directive")

    @classmethod
    def capture(cls, content):
        return cls((SourceEvent.create("S1", "USER_DIRECTIVE", content, 0),))

    @classmethod
    def from_dict(cls, data):
        state = cls(tuple(SourceEvent(**e) for e in data["events"]))
        if data.get("source_state_sha256") != state.sha256:
            raise ValueError("Request-state hash mismatch")
        return state

    @property
    def sha256(self):
        return digest(canonical([asdict(e) for e in self.events]))

    def to_dict(self):
        return {"events": [asdict(e) for e in self.events], "source_state_sha256": self.sha256}

    def append(self, content, role="USER_CLARIFICATION", target=None):
        e = SourceEvent.create(f"S{len(self.events)+1}", role, content, len(self.events), target)
        return RequestState(self.events + (e,))

    def anchor(self, event_id, start=0, end=None):
        e = next(e for e in self.events if e.id == event_id)
        end = len(e.content) if end is None else end
        if not 0 <= start < end <= len(e.content):
            raise ValueError("Invalid source span")
        return {"source_id": e.id, "event_id": e.id, "start": start, "end": end,
                "excerpt_sha256": digest(e.content[start:end].encode("utf-8"))}
